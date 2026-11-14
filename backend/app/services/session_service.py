"""
Session Service — Test session lifecycle management.

Orchestrates the adaptive test flow:
1. Start session → initialize AdaptiveEngine with topic concepts
2. Get next question → engine selects via multi-objective optimization
3. Submit answer → grade, store response, update engine (IRT + BKT + graph)
4. End session → store final theta, clean up

Active engines are stored in-memory keyed by session_id.
"""

import uuid
import logging
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional, Tuple

from app.models.db_models import TestSession, Response
from app.extensions import db
from app.services.adaptive_engine import AdaptiveEngine
from app.services.grading_service import GradingService, GradingResult
from app.repositories.question_repo import (
    get_candidate_questions,
    get_question,
    get_resources_for_concept,
)
from app.repositories.graph_repo import (
    get_prerequisite_map,
    get_prerequisite_edges,
    get_concept_ids_for_topic,
    get_concept_prerequisites,
)

logger = logging.getLogger(__name__)

# In-memory store for active engine instances
_active_engines: Dict[str, AdaptiveEngine] = {}

# Test presets as defined in AD-004
TEST_PRESETS = {
    'quick': {
        'name': 'Quick Check',
        'total_questions': 10,
        'time_limit_minutes': 15,
        'description': 'Fast knowledge pulse check on a single level',
    },
    'standard': {
        'name': 'Standard Assessment',
        'total_questions': 25,
        'time_limit_minutes': 45,
        'description': 'Balanced assessment across all 4 levels',
    },
    'comprehensive': {
        'name': 'Comprehensive Exam',
        'total_questions': 50,
        'time_limit_minutes': 90,
        'description': 'Deep evaluation with thorough level coverage',
    },
}


def get_presets() -> List[Dict[str, Any]]:
    """Return available test presets."""
    return [
        {'id': k, **v} for k, v in TEST_PRESETS.items()
    ]


def start_session(
    user_id: str,
    topic_id: str,
    preset: str = 'standard',
    total_questions: Optional[int] = None,
    time_limit_minutes: Optional[int] = None,
) -> TestSession:
    """
    Start a new test session and initialize the adaptive engine.

    Initial theta is seeded from the user's most recent completed session for
    the same topic so the engine doesn't restart at 0.0 every time. A small
    random jitter (±0.1) is added to break scoring ties differently each
    session, preventing identical question orderings across repeated attempts.
    """
    import random

    # Resolve preset defaults
    preset_config = TEST_PRESETS.get(preset, TEST_PRESETS['standard'])
    final_questions = total_questions or preset_config['total_questions']
    final_time = time_limit_minutes or preset_config['time_limit_minutes']

    # ── Seed theta from previous session ──────────────────────────────────
    last_session = (
        TestSession.query
        .filter_by(user_id=user_id, topic_id=topic_id, status='completed')
        .filter(TestSession.final_theta.isnot(None))
        .order_by(TestSession.completed_at.desc())
        .first()
    )
    if last_session:
        # Clamp to ±2.5 so extreme outliers don't over-constrain the new session
        base_theta = max(-2.5, min(2.5, last_session.final_theta))
        logger.info(
            f"Seeding theta={base_theta:.3f} from session {last_session.id}"
        )
    else:
        base_theta = 0.0

    # Small jitter ensures question ordering differs even when theta is the same
    initial_theta = base_theta + random.uniform(-0.1, 0.1)

    session_id = str(uuid.uuid4())
    session = TestSession(
        id=session_id,
        user_id=user_id,
        topic_id=topic_id,
        preset=preset,
        total_questions=final_questions,
        time_limit_minutes=final_time,
        status='active',
    )
    db.session.add(session)
    db.session.commit()

    # Initialize adaptive engine with seeded theta
    engine = AdaptiveEngine(initial_theta=initial_theta)

    # Load concept IDs for this topic and initialize BKT states
    concept_ids = get_concept_ids_for_topic(topic_id)
    engine.initialize_concepts([{'id': cid} for cid in concept_ids])

    _active_engines[session_id] = engine

    logger.info(
        f"Session started: {session_id}, topic={topic_id}, "
        f"preset={preset}, questions={final_questions}, time={final_time}min, "
        f"concepts={len(concept_ids)}, initial_theta={initial_theta:.3f}"
    )
    return session



def get_next_question(session_id: str) -> Optional[Dict[str, Any]]:
    """
    Get the next adaptively selected question for a session.
    Returns full question dict or None if session should end.
    """
    engine = _active_engines.get(session_id)
    if not engine:
        raise ValueError(f"No active engine for session {session_id}")

    session = db.session.get(TestSession, session_id)
    if not session:
        raise ValueError(f"Session {session_id} not found")

    # Check stopping criteria
    should_stop, reason = engine.should_stop(
        max_questions=session.total_questions,
    )
    if should_stop:
        logger.info(f"Session {session_id} stopping: {reason}")
        return None

    # Get candidate questions and prerequisite map
    candidates = get_candidate_questions(
        session.topic_id, list(engine.answered_ids)
    )
    if not candidates:
        logger.info(f"Session {session_id}: no more candidate questions")
        return None

    prerequisite_map = get_prerequisite_map(session.topic_id)

    concept_prereqs = get_concept_prerequisites(session.topic_id)
    all_concept_ids = list(set(q['concept_id'] for q in candidates if q.get('concept_id')))
    frontier_concepts = engine.get_concept_frontier(all_concept_ids, concept_prereqs)
    frontier_candidates = [q for q in candidates if q.get('concept_id') in frontier_concepts]

    final_candidates = frontier_candidates if frontier_candidates else candidates

    logger.info(f"Session {session_id}: {len(frontier_candidates)} frontier candidates out of {len(candidates)} total")

    # Select next question via multi-objective optimization
    selected = engine.select_next_question(final_candidates, prerequisite_map)
    if not selected:
        return None

    # Fetch full question details
    full_question = get_question(selected['id'])
    if not full_question:
        logger.error(f"Question {selected['id']} not found in Neo4j")
        return None

    # Add resources for the concept
    concept_id = full_question.get('concept_id', '')
    if concept_id:
        full_question['resources'] = get_resources_for_concept(concept_id)

    return full_question


def submit_answer(
    session_id: str,
    question_id: str,
    selected_options: List[str],
    time_taken_seconds: int,
) -> Tuple[GradingResult, Dict[str, Any]]:
    """
    Submit an answer: grade it, store the response, and update the adaptive engine.
    """
    engine = _active_engines.get(session_id)
    if not engine:
        raise ValueError(f"No active engine for session {session_id}")

    session = db.session.get(TestSession, session_id)
    if not session:
        raise ValueError(f"Session {session_id} not found")

    # Fetch question data
    q_data = get_question(question_id)
    if not q_data:
        raise ValueError(f"Question {question_id} not found")

    # Map selected option IDs (e.g., "opt_0") to their text values for grading
    options_list = q_data.get('options', [])
    option_id_to_text = {
        opt.get('id', f'opt_{i}'): opt.get('text', str(opt))
        if isinstance(opt, dict) else str(opt)
        for i, opt in enumerate(options_list)
    }
    selected_texts = [option_id_to_text.get(oid, oid) for oid in selected_options]

    # Grade the answer
    grading_result = GradingService.grade_mcq(
        selected_options=selected_texts,
        correct_answers=q_data.get('correct_answers', []),
        all_options=[opt.get('text', opt) if isinstance(opt, dict) else opt
                     for opt in options_list],
    )

    # Store response in PostgreSQL
    response = Response(
        session_id=session_id,
        user_id=session.user_id,
        question_id=question_id,
        question_level=q_data.get('level', 'Repeat'),
        user_answer=selected_options,
        is_correct=grading_result.is_correct,
        partial_score=grading_result.partial_score,
        grading_details=grading_result.grading_details,
        time_taken_seconds=time_taken_seconds,
    )
    db.session.add(response)
    db.session.commit()

    # Get prerequisite edges for graph belief propagation
    prereq_edges = get_prerequisite_edges(question_id)

    # Update adaptive engine (IRT theta + BKT mastery + graph propagation)
    update_info = engine.record_response(
        question={
            'id': question_id,
            'level': q_data.get('level', 'Repeat'),
            'concept_id': q_data.get('concept_id', ''),
            'a': q_data.get('a', 1.0),
            'b': q_data.get('b', 0.0),
            'c': q_data.get('c', 0.25),
        },
        correct=grading_result.is_correct,
        partial_score=grading_result.partial_score,
        prerequisite_edges=prereq_edges,
    )

    logger.info(
        f"Answer submitted: session={session_id}, q={question_id}, "
        f"correct={grading_result.is_correct}, score={grading_result.partial_score:.3f}, "
        f"theta={update_info['theta']:.3f}"
    )

    return grading_result, update_info


def end_session(session_id: str) -> Tuple[Optional[TestSession], Optional[Dict[str, Any]]]:
    """End a test session, store final theta + mastery snapshot, and clean up engine."""
    engine = _active_engines.get(session_id)
    engine_state = engine.get_session_state() if engine else None

    # Pop the engine before DB writes to free memory
    _active_engines.pop(session_id, None)

    session = db.session.get(TestSession, session_id)

    if not session:
        return None, None

    session.status = 'completed'
    session.completed_at = datetime.now(timezone.utc)

    if engine:
        session.final_theta = engine.theta
        session.theta_se = engine.theta_se

        # ── Persist concept mastery snapshot ────────────────────────────────
        # Reshape from {(concept_id, level): ConceptLevelState} to
        # {concept_id: {level: {p_mastery, n_attempts, n_correct}}}
        # This preserves the full BKT state at session end for continuity analysis.
        mastery_snapshot: Dict[str, Any] = {}
        for (concept_id, level), state in engine.concept_states.items():
            if concept_id not in mastery_snapshot:
                mastery_snapshot[concept_id] = {}
            mastery_snapshot[concept_id][level] = {
                'p_mastery':  round(state.p_mastery, 4),
                'n_attempts': state.n_attempts,
                'n_correct':  state.n_correct,
            }
        session.concept_mastery_snapshot = mastery_snapshot or None

    db.session.commit()

    logger.info(
        f"Session ended: {session_id}, "
        f"theta={session.final_theta:.3f}, se={session.theta_se:.3f}, "
        f"concepts_snapshotted={len(session.concept_mastery_snapshot or {})}"
    )
    return session, engine_state


def get_engine_state(session_id: str) -> Optional[Dict[str, Any]]:
    """Get the current state of an active engine (for debugging/admin)."""
    engine = _active_engines.get(session_id)
    if not engine:
        return None
    return engine.get_session_state()
