"""
IKAS Adaptive Engine — Core intelligence of the assessment system.

Combines IRT (3PL), Bayesian Knowledge Tracing (BKT), Graph Belief Propagation,
and Multi-Objective Item Selection to adaptively select optimal questions
for each learner in real-time.
"""

import logging
import math
from typing import Dict, List, Optional, Tuple, Any

from app.utils.math_utils import (
    irt_3pl_probability,
    fisher_information,
    estimate_theta_eap,
    bkt_update,
    propagate_beliefs,
)

logger = logging.getLogger(__name__)

# Knowledge level progression order
LEVEL_ORDER = ['Repeat', 'Summary', 'Intuitive', 'Apply']
LEVEL_INDEX = {level: i for i, level in enumerate(LEVEL_ORDER)}


def _get_engine_config() -> dict:
    """
    Read adaptive engine tuning parameters from Flask app config.
    Falls back to hardcoded defaults when called outside an app context
    (e.g. in unit tests that don't spin up the full app).
    """
    try:
        from flask import current_app
        cfg = current_app.config
        return {
            'weights': {
                'alpha': cfg.get('ENGINE_WEIGHT_ALPHA', 0.35),
                'beta':  cfg.get('ENGINE_WEIGHT_BETA',  0.25),
                'gamma': cfg.get('ENGINE_WEIGHT_GAMMA', 0.20),
                'delta': cfg.get('ENGINE_WEIGHT_DELTA', 0.20),
            },
            'mastery_threshold': cfg.get('ENGINE_MASTERY_THRESHOLD', 0.70),
            'bkt': {
                'p_init':    0.5,
                'p_transit': cfg.get('BKT_P_TRANSIT', 0.10),
                'p_guess':   cfg.get('BKT_P_GUESS',   0.20),
                'p_slip':    cfg.get('BKT_P_SLIP',    0.10),
            },
        }
    except RuntimeError:
        # No active Flask app context — use defaults (tests, CLI scripts)
        return {
            'weights': {'alpha': 0.35, 'beta': 0.25, 'gamma': 0.20, 'delta': 0.20},
            'mastery_threshold': 0.70,
            'bkt': {'p_init': 0.5, 'p_transit': 0.10, 'p_guess': 0.20, 'p_slip': 0.10},
        }


# Module-level defaults (used directly in tests / non-app contexts)
DEFAULT_WEIGHTS = {'alpha': 0.35, 'beta': 0.25, 'gamma': 0.20, 'delta': 0.20}
MASTERY_THRESHOLD = 0.70
DEFAULT_BKT = {'p_init': 0.5, 'p_transit': 0.10, 'p_guess': 0.20, 'p_slip': 0.10}


class ConceptLevelState:
    """Tracks BKT mastery state for a (concept, level) pair."""

    def __init__(
        self,
        concept_id: str,
        level: str,
        p_mastery: float = 0.5,
        bkt_params: Optional[Dict] = None,
    ):
        self.concept_id = concept_id
        self.level = level
        self.p_mastery = p_mastery
        self.n_attempts = 0
        self.n_correct = 0
        # BKT transition params — supplied by engine, fallback to module defaults
        self._bkt = bkt_params or DEFAULT_BKT

    def update(self, correct: bool) -> float:
        """Update mastery via BKT after observing a response."""
        self.n_attempts += 1
        if correct:
            self.n_correct += 1
        self.p_mastery = bkt_update(
            self.p_mastery,
            correct,
            self._bkt['p_transit'],
            self._bkt['p_guess'],
            self._bkt['p_slip'],
        )
        return self.p_mastery

    def to_dict(self) -> Dict:
        return {
            'concept_id': self.concept_id,
            'level': self.level,
            'p_mastery': self.p_mastery,
            'n_attempts': self.n_attempts,
            'n_correct': self.n_correct,
        }


class AdaptiveEngine:
    """
    Adaptive question selection engine using IRT + BKT + Graph Propagation.
    
    One instance per test session. Maintains session state including:
    - Latent ability estimate (theta)
    - Per-concept-level BKT mastery states
    - Response history for EAP estimation
    - Graph belief states
    """

    def __init__(
        self,
        initial_theta: float = 0.0,
        weights: Optional[Dict[str, float]] = None,
        mastery_threshold: Optional[float] = None,
    ):
        # Load from Flask config (or fall back to hardcoded defaults in tests)
        engine_cfg = _get_engine_config()

        self.theta: float = initial_theta
        self.theta_se: float = 1.0  # Standard error of theta
        # Explicit overrides (from tests) take priority over config
        self.weights = weights or engine_cfg['weights']
        self.mastery_threshold = mastery_threshold if mastery_threshold is not None \
            else engine_cfg['mastery_threshold']
        self._bkt = engine_cfg['bkt']

        # Response history for EAP estimation: [{a, b, c, correct}, ...]
        self.response_history: List[Dict] = []

        # BKT states: {(concept_id, level): ConceptLevelState}
        self.concept_states: Dict[Tuple[str, str], ConceptLevelState] = {}

        # Graph node belief states: {question_id: P(pass)}
        self.node_beliefs: Dict[str, float] = {}

        # Already answered question IDs
        self.answered_ids: set = set()

    def initialize_concepts(self, concepts: List[Dict]) -> None:
        """
        Initialize BKT states for all concepts in the test scope.

        Args:
            concepts: List of dicts with 'id' and optionally 'levels'
        """
        for concept in concepts:
            concept_id = concept['id']
            for level in LEVEL_ORDER:
                key = (concept_id, level)
                if key not in self.concept_states:
                    self.concept_states[key] = ConceptLevelState(
                        concept_id, level, self._bkt['p_init'], bkt_params=self._bkt
                    )

    def record_response(
        self,
        question: Dict,
        correct: bool,
        partial_score: float,
        prerequisite_edges: Optional[List[Dict]] = None,
    ) -> Dict[str, Any]:
        """
        Record a student response and update all internal states.
        
        Args:
            question: Question dict with 'id', 'level', 'a', 'b', 'c', 'concept_id'
            correct: Whether the answer was correct (binary for IRT)
            partial_score: Partial credit score 0.0 to 1.0
            prerequisite_edges: Edges for graph propagation
            
        Returns:
            Dict with updated state information
        """
        q_id = question['id']
        level = question.get('level', 'Repeat')
        concept_id = question.get('concept_id', '')
        a = question.get('a', 1.0)
        b = question.get('b', 0.0)
        c = question.get('c', 0.25)

        self.answered_ids.add(q_id)

        # 1. Update IRT theta via EAP
        self.response_history.append({
            'a': a, 'b': b, 'c': c,
            'correct': 1 if correct else 0,
        })
        self.theta, self.theta_se = estimate_theta_eap(
            self.response_history,
            prior_mean=0.0,
            prior_std=1.0,
        )

        # 2. Update BKT mastery for this concept-level
        state_key = (concept_id, level)
        if state_key not in self.concept_states:
            self.concept_states[state_key] = ConceptLevelState(
                concept_id, level, self._bkt['p_init'], bkt_params=self._bkt
            )
        new_mastery = self.concept_states[state_key].update(correct)

        # 3. Update graph node beliefs
        self.node_beliefs[q_id] = partial_score

        # 4. Propagate beliefs through prerequisite edges
        if prerequisite_edges:
            self.node_beliefs = propagate_beliefs(
                prerequisite_edges,
                self.node_beliefs,
                damping=0.5,
            )

        logger.info(
            f"Response recorded: q={q_id}, correct={correct}, "
            f"theta={self.theta:.3f}±{self.theta_se:.3f}, "
            f"mastery({concept_id}/{level})={new_mastery:.3f}"
        )

        return {
            'theta': self.theta,
            'theta_se': self.theta_se,
            'concept_mastery': new_mastery,
            'concept_id': concept_id,
            'level': level,
        }

    def select_next_question(
        self,
        candidates: List[Dict],
        prerequisite_map: Optional[Dict[str, List[str]]] = None,
    ) -> Optional[Dict]:
        """
        Select the next question using multi-objective optimization.
        
        Score(q) = α·FisherInfo + β·GraphEntropy + γ·PrereqReadiness + δ·LevelProgression
        
        Candidates are filtered to the "concept frontier" — concepts whose 
        prerequisites are mastered but which themselves are not yet mastered.
        
        Args:
            candidates: List of question dicts with IRT params and metadata
            prerequisite_map: {question_id: [prerequisite_question_ids]}
            
        Returns:
            Selected question dict, or None if no candidates available
        """
        if not candidates:
            return None

        prerequisite_map = prerequisite_map or {}

        # Filter out already answered questions
        available = [q for q in candidates if q['id'] not in self.answered_ids]
        if not available:
            return None

        # Score each candidate
        scored = []
        for q in available:
            score = self._compute_composite_score(q, prerequisite_map)
            scored.append((score, q))

        # Sort by score descending, select best
        scored.sort(key=lambda x: x[0], reverse=True)
        selected = scored[0][1]

        logger.info(
            f"Selected question: {selected['id']} "
            f"(level={selected.get('level')}, score={scored[0][0]:.4f})"
        )
        return selected

    def _compute_composite_score(
        self,
        question: Dict,
        prerequisite_map: Dict[str, List[str]],
    ) -> float:
        """Compute multi-objective composite score for a candidate question."""
        q_id = question['id']
        level = question.get('level', 'Repeat')
        concept_id = question.get('concept_id', '')
        a = question.get('a', 1.0)
        b = question.get('b', 0.0)
        c = question.get('c', 0.25)

        # Component 1: Fisher Information
        fi = fisher_information(self.theta, a, b, c)
        # Normalize to [0, 1] range (max Fisher Info for well-discriminating items is ~2.25)
        fi_normalized = min(fi / 2.25, 1.0)

        # Component 2: Graph Entropy — how much does answering this reduce uncertainty
        graph_entropy = self._compute_graph_entropy(q_id, prerequisite_map)

        # Component 3: Prerequisite Readiness — are prerequisites mastered?
        prereq_readiness = self._compute_prereq_readiness(q_id, prerequisite_map)

        # Component 4: Level Progression — bonus for appropriate cognitive level
        level_progression = self._compute_level_progression(concept_id, level)

        # Weighted composite
        score = (
            self.weights['alpha'] * fi_normalized +
            self.weights['beta'] * graph_entropy +
            self.weights['gamma'] * prereq_readiness +
            self.weights['delta'] * level_progression
        )

        return score

    def _compute_graph_entropy(
        self,
        question_id: str,
        prerequisite_map: Dict[str, List[str]],
    ) -> float:
        """
        Compute information gain — how much answering this question
        would reduce uncertainty across connected graph nodes.
        """
        # Count connected nodes that haven't been answered
        connected = set()
        for q_id, prereqs in prerequisite_map.items():
            if question_id in prereqs and q_id not in self.answered_ids:
                connected.add(q_id)
        
        # Also check if this question is a prereq for others
        dependents = prerequisite_map.get(question_id, [])
        for dep in dependents:
            if dep not in self.answered_ids:
                connected.add(dep)

        if not connected:
            return 0.0

        # More unanswered connections = higher entropy gain
        # Use log to prevent extreme values
        return min(math.log2(1 + len(connected)) / 3.0, 1.0)

    def _compute_prereq_readiness(
        self,
        question_id: str,
        prerequisite_map: Dict[str, List[str]],
    ) -> float:
        """
        Compute what proportion of prerequisite questions have been answered
        correctly. Avoids asking questions the student isn't ready for.
        """
        prereqs = prerequisite_map.get(question_id, [])
        if not prereqs:
            return 1.0  # No prerequisites = fully ready

        mastered_count = 0
        for prereq_id in prereqs:
            belief = self.node_beliefs.get(prereq_id, 0.5)
            if belief >= self.mastery_threshold:
                mastered_count += 1

        return mastered_count / len(prereqs)

    def _compute_level_progression(
        self, concept_id: str, level: str
    ) -> float:
        """
        Compute bonus for testing the next cognitive level up from
        current demonstrated mastery.
        
        Drives progression: Repeat → Summary → Intuitive → Apply
        """
        if not concept_id or level not in LEVEL_INDEX:
            return 0.5

        target_idx = LEVEL_INDEX[level]

        # Find the highest mastered level for this concept
        highest_mastered = -1
        for lvl in LEVEL_ORDER:
            key = (concept_id, lvl)
            state = self.concept_states.get(key)
            if state and state.p_mastery >= self.mastery_threshold:
                highest_mastered = LEVEL_INDEX[lvl]

        # Ideal: target is exactly one level above highest mastered
        if highest_mastered == -1:
            # No mastery yet — Repeat questions get highest bonus
            return 1.0 if target_idx == 0 else max(0.0, 1.0 - target_idx * 0.3)

        gap = target_idx - highest_mastered
        if gap == 1:
            return 1.0  # Next level up — maximum bonus
        elif gap == 0:
            return 0.4  # Same level — moderate (reinforcement)
        elif gap < 0:
            return 0.1  # Below mastery — low priority
        else:
            return max(0.0, 0.6 - (gap - 1) * 0.2)  # Jumping levels — decreasing

    def get_concept_frontier(
        self,
        all_concepts: List[str],
        prerequisite_graph: Dict[str, List[str]],
    ) -> List[str]:
        """
        Compute the concept frontier — concepts whose prerequisites are 
        mastered but which themselves are not yet mastered.
        
        This mirrors the Zone of Proximal Development (ZPD).
        """
        frontier = []
        for concept_id in all_concepts:
            # Check if concept is already mastered at all levels
            all_mastered = all(
                self.concept_states.get((concept_id, lvl), ConceptLevelState(concept_id, lvl)).p_mastery
                >= self.mastery_threshold
                for lvl in LEVEL_ORDER
            )
            if all_mastered:
                continue

            # Check if prerequisites are mastered
            prereqs = prerequisite_graph.get(concept_id, [])
            if not prereqs:
                # No prerequisites — always on frontier
                frontier.append(concept_id)
                continue

            prereqs_mastered = all(
                self.concept_states.get((p, 'Repeat'), ConceptLevelState(p, 'Repeat')).p_mastery
                >= self.mastery_threshold
                for p in prereqs
            )
            if prereqs_mastered:
                frontier.append(concept_id)

        return frontier

    def should_stop(self, max_questions: int, time_expired: bool = False) -> Tuple[bool, str]:
        """
        Evaluate stopping criteria for the test.
        
        Returns:
            (should_stop, reason)
        """
        if time_expired:
            return True, 'time_expired'

        if len(self.answered_ids) >= max_questions:
            return True, 'question_limit_reached'

        # Stop if theta is precisely estimated (SE < 0.3)
        if len(self.answered_ids) >= 5 and self.theta_se < 0.3:
            return True, 'precision_reached'

        return False, ''

    def get_session_state(self) -> Dict[str, Any]:
        """Get the full current state of the engine for serialization."""
        return {
            'theta': self.theta,
            'theta_se': self.theta_se,
            'n_responses': len(self.response_history),
            'answered_ids': list(self.answered_ids),
            'concept_mastery': {
                f"{k[0]}/{k[1]}": v.to_dict()
                for k, v in self.concept_states.items()
            },
            'node_beliefs': self.node_beliefs,
        }
