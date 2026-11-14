"""
Report Service — Generates enriched session reports and user progress data.

Sprint 1 additions:
- generate_session_report: real concept names from Neo4j, per-concept×per-level
  mastery breakdown, time stats, real resource recommendations for weak areas.
- get_user_progress: full session history with scores, stats summary block.
"""

from app.models.db_models import TestSession, Response
from app.extensions import db
from app.repositories.graph_repo import get_concept_names
from app.repositories.question_repo import get_resources_for_concept, get_question
from typing import Dict, Any, List

# Cognitive levels in display order
LEVELS = ['Repeat', 'Summary', 'Intuitive', 'Apply']

# Theta range used to normalise to 0-100
THETA_MIN, THETA_MAX = -3.0, 3.0


def _theta_to_score(theta: float) -> int:
    """Convert IRT theta (-3..+3) to 0-100 display score."""
    clamped = max(THETA_MIN, min(THETA_MAX, theta))
    return round(((clamped - THETA_MIN) / (THETA_MAX - THETA_MIN)) * 100)


def generate_session_report(session_id: str) -> Dict[str, Any]:
    """
    Generate a rich post-session report.

    Returns:
      session_id, total_questions, correct_count, score (0-100),
      theta, theta_se,
      level_breakdown: {level: {total, correct, accuracy}},
      concept_mastery: {concept_id: {name, levels: {level: {total, correct, accuracy}}}},
      time_stats: {avg_time_seconds, total_time_seconds, slowest_level},
      recommendations: [{id, title, url, type, target_level, concept_id, concept_name}]
    """
    session = db.session.get(TestSession, session_id)
    if not session:
        raise ValueError("Session not found")

    responses: List[Response] = Response.query.filter_by(session_id=session_id).all()
    total = len(responses)
    correct = sum(1 for r in responses if r.is_correct)

    # ── Resolve concept_id for each question via Neo4j ─────────────────────
    question_concept: Dict[str, str] = {}
    for r in responses:
        if r.question_id not in question_concept:
            q = get_question(r.question_id)
            if q:
                question_concept[r.question_id] = q.get('concept_id', 'unknown')

    # ── Per-concept × per-level tallies ───────────────────────────────────
    concept_level_tallies: Dict[str, Dict[str, Dict[str, int]]] = {}
    for r in responses:
        concept_id = question_concept.get(r.question_id, 'unknown')
        level = r.question_level or 'Repeat'
        if concept_id not in concept_level_tallies:
            concept_level_tallies[concept_id] = {}
        if level not in concept_level_tallies[concept_id]:
            concept_level_tallies[concept_id][level] = {'total': 0, 'correct': 0}
        concept_level_tallies[concept_id][level]['total'] += 1
        if r.is_correct:
            concept_level_tallies[concept_id][level]['correct'] += 1

    # Fetch human-readable concept names in one batch call
    concept_ids = list(concept_level_tallies.keys())
    concept_names_map = get_concept_names(concept_ids)

    concept_mastery: Dict[str, Any] = {}
    for concept_id, level_tallies in concept_level_tallies.items():
        concept_mastery[concept_id] = {
            'name': concept_names_map.get(concept_id, concept_id),
            'levels': {},
        }
        for level, tally in level_tallies.items():
            accuracy = tally['correct'] / tally['total'] if tally['total'] > 0 else 0.0
            concept_mastery[concept_id]['levels'][level] = {
                'total': tally['total'],
                'correct': tally['correct'],
                'accuracy': round(accuracy, 3),
            }

    # ── Overall level breakdown ────────────────────────────────────────────
    level_breakdown: Dict[str, Dict[str, Any]] = {}
    for r in responses:
        lvl = r.question_level or 'Repeat'
        if lvl not in level_breakdown:
            level_breakdown[lvl] = {'total': 0, 'correct': 0}
        level_breakdown[lvl]['total'] += 1
        if r.is_correct:
            level_breakdown[lvl]['correct'] += 1
    for lvl, data in level_breakdown.items():
        data['accuracy'] = round(data['correct'] / data['total'], 3) if data['total'] > 0 else 0.0

    # ── Time stats ─────────────────────────────────────────────────────────
    times = [r.time_taken_seconds for r in responses if r.time_taken_seconds is not None]
    total_time = sum(times)
    avg_time = round(total_time / len(times), 1) if times else 0.0

    level_times: Dict[str, List[int]] = {}
    for r in responses:
        if r.time_taken_seconds is not None:
            lvl = r.question_level or 'Repeat'
            level_times.setdefault(lvl, []).append(r.time_taken_seconds)
    slowest_level = None
    if level_times:
        slowest_level = max(level_times, key=lambda l: sum(level_times[l]) / len(level_times[l]))

    time_stats = {
        'avg_time_seconds': avg_time,
        'total_time_seconds': total_time,
        'slowest_level': slowest_level,
    }

    # ── Recommendations ────────────────────────────────────────────────────
    # Find weak concept × level cells (accuracy < 0.5), pull linked resources.
    recommendations: List[Dict[str, Any]] = []
    seen_resource_ids: set = set()
    for concept_id, data in concept_mastery.items():
        for level, stats in data['levels'].items():
            if stats['accuracy'] < 0.5 and stats['total'] > 0:
                resources = get_resources_for_concept(concept_id)
                for res in resources:
                    if res.get('id') and res['id'] not in seen_resource_ids:
                        seen_resource_ids.add(res['id'])
                        recommendations.append({
                            **res,
                            'target_level': level,
                            'concept_id': concept_id,
                            'concept_name': data['name'],
                        })
                        if len(recommendations) >= 5:
                            break
            if len(recommendations) >= 5:
                break
        if len(recommendations) >= 5:
            break

    theta = session.final_theta or 0.0
    theta_score = _theta_to_score(theta)

    # ── Display score: raw accuracy (correct / total) ─────────────────────
    # IRT theta is preserved as 'theta_score' for the radar chart and adaptive
    # engine continuity, but the headline "Overall Score" shown to the student
    # must be raw accuracy. Theta can read 21% even with 0/10 correct (the
    # guessing parameter c=0.25 floors the estimate), which is misleading.
    raw_score = round((correct / total) * 100) if total > 0 else 0

    # Blended score: 60% raw accuracy + 40% IRT theta score.
    # This rewards correct answers directly while still reflecting question
    # difficulty (a student who answers hard questions correctly scores higher
    # than one who answers easy questions at the same raw rate).
    blended_score = round(0.6 * raw_score + 0.4 * theta_score)

    # ── Persist recommendations snapshot ────────────────────────────────────
    # Store the recommendations that were surfaced for this session so we
    # can later analyse whether acting on them improved the student's score.
    if recommendations and not session.recommendations_snapshot:
        session.recommendations_snapshot = recommendations
        db.session.commit()

    return {
        'session_id': session_id,
        'total_questions': total,
        'correct_count': correct,
        'score': blended_score,        # headline score (60% raw + 40% IRT)
        'raw_score': raw_score,        # pure accuracy %
        'theta_score': theta_score,    # IRT ability estimate (0-100 scale)
        'theta': theta,
        'theta_se': session.theta_se or 0.0,
        'level_breakdown': level_breakdown,
        'concept_mastery': concept_mastery,
        'time_stats': time_stats,
        'recommendations': recommendations,
    }


def get_user_progress(user_id: int, topic_id: str) -> Dict[str, Any]:
    """
    Return a user's session history for a topic with rich metadata.

    Returns:
      user_id, topic_id,
      history: [{session_id, date, preset, total_questions, correct_count,
                 score (0-100), theta, time_limit_minutes}],
      summary: {total_sessions, avg_score, best_score, latest_theta}
    """
    sessions: List[TestSession] = (
        TestSession.query
        .filter_by(user_id=user_id, topic_id=topic_id, status='completed')
        .order_by(TestSession.completed_at)
        .all()
    )

    history = []
    for s in sessions:
        if s.final_theta is None:
            continue
        responses = Response.query.filter_by(session_id=s.id).all()
        correct = sum(1 for r in responses if r.is_correct)
        total_q = len(responses)
        theta_score = _theta_to_score(s.final_theta)
        raw_score = round((correct / total_q) * 100) if total_q > 0 else 0
        blended_score = round(0.6 * raw_score + 0.4 * theta_score)
        history.append({
            'session_id': s.id,
            'date': s.completed_at.isoformat(),
            'preset': s.preset or 'standard',
            'total_questions': total_q,
            'correct_count': correct,
            'score': blended_score,
            'raw_score': raw_score,
            'theta': s.final_theta,
            'time_limit_minutes': s.time_limit_minutes or 45,
        })

    scores = [h['score'] for h in history]
    thetas = [s.final_theta for s in sessions if s.final_theta is not None]
    summary = {
        'total_sessions': len(history),
        'avg_score': round(sum(scores) / len(scores)) if scores else 0,
        'best_score': max(scores) if scores else 0,
        'latest_theta': thetas[-1] if thetas else None,
    }

    return {
        'user_id': user_id,
        'topic_id': topic_id,
        'history': history,
        'summary': summary,
    }

