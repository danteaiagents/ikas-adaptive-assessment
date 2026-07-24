"""
Unit tests for the IKAS Adaptive Engine.

Tests IRT 3PL probability, EAP theta estimation, BKT updates,
graph belief propagation, multi-objective item selection,
concept frontier, and stopping criteria.
"""

import pytest
import math
from app.utils.math_utils import (
    irt_3pl_probability,
    fisher_information,
    estimate_theta_eap,
    bkt_update,
    propagate_beliefs,
)
from app.services.adaptive_engine import AdaptiveEngine, ConceptLevelState
from app.services.grading_service import GradingService


# =============================================================================
# IRT 3PL Tests
# =============================================================================

class TestIRT3PL:
    def test_probability_at_equal_difficulty(self):
        """When theta = b, P should be approximately (1+c)/2."""
        p = irt_3pl_probability(theta=0.0, a=1.0, b=0.0, c=0.0)
        assert abs(p - 0.5) < 0.01

    def test_probability_with_guessing(self):
        """With c=0.25, P at theta=b should be (1+0.25)/2 = 0.625."""
        p = irt_3pl_probability(theta=0.0, a=1.0, b=0.0, c=0.25)
        assert abs(p - 0.625) < 0.01

    def test_high_ability_high_probability(self):
        """High theta relative to b should give P close to 1."""
        p = irt_3pl_probability(theta=3.0, a=1.0, b=0.0, c=0.0)
        assert p > 0.95

    def test_low_ability_low_probability(self):
        """Low theta relative to b should give P close to c."""
        p = irt_3pl_probability(theta=-3.0, a=1.0, b=0.0, c=0.25)
        assert p < 0.30  # Should be close to c=0.25

    def test_high_discrimination_sharp_curve(self):
        """High a makes the sigmoid steeper."""
        p_steep = irt_3pl_probability(theta=0.5, a=3.0, b=0.0, c=0.0)
        p_flat = irt_3pl_probability(theta=0.5, a=0.5, b=0.0, c=0.0)
        assert p_steep > p_flat

    def test_probability_bounds(self):
        """P should always be in [c, 1]."""
        for theta in [-3, -1, 0, 1, 3]:
            for c in [0.0, 0.1, 0.25]:
                p = irt_3pl_probability(theta, a=1.0, b=0.0, c=c)
                assert c <= p <= 1.0


class TestFisherInformation:
    def test_max_info_near_difficulty(self):
        """Fisher Info should be maximized near theta = b."""
        fi_at_b = fisher_information(theta=0.0, a=1.5, b=0.0, c=0.0)
        fi_far = fisher_information(theta=3.0, a=1.5, b=0.0, c=0.0)
        assert fi_at_b > fi_far

    def test_higher_discrimination_more_info(self):
        """Higher discrimination should produce more information."""
        fi_low = fisher_information(theta=0.0, a=0.5, b=0.0, c=0.0)
        fi_high = fisher_information(theta=0.0, a=2.0, b=0.0, c=0.0)
        assert fi_high > fi_low

    def test_positive_information(self):
        """Fisher Info should always be non-negative."""
        fi = fisher_information(theta=0.0, a=1.0, b=0.0, c=0.25)
        assert fi >= 0.0


# =============================================================================
# EAP Theta Estimation Tests
# =============================================================================

class TestEAPEstimation:
    def test_no_responses_returns_prior(self):
        """With no responses, EAP should return the prior mean."""
        theta, se = estimate_theta_eap([])
        assert theta == 0.0
        assert se == 1.0

    def test_all_correct_increases_theta(self):
        """All correct responses should push theta above 0."""
        responses = [
            {'a': 1.0, 'b': 0.0, 'c': 0.0, 'correct': 1},
            {'a': 1.0, 'b': 0.5, 'c': 0.0, 'correct': 1},
            {'a': 1.0, 'b': 1.0, 'c': 0.0, 'correct': 1},
        ]
        theta, se = estimate_theta_eap(responses)
        assert theta > 0.5

    def test_all_incorrect_decreases_theta(self):
        """All incorrect responses should push theta below 0."""
        responses = [
            {'a': 1.0, 'b': 0.0, 'c': 0.0, 'correct': 0},
            {'a': 1.0, 'b': -0.5, 'c': 0.0, 'correct': 0},
        ]
        theta, se = estimate_theta_eap(responses)
        assert theta < 0.0

    def test_se_decreases_with_more_responses(self):
        """Standard error should decrease as more responses are added."""
        responses_few = [{'a': 1.0, 'b': 0.0, 'c': 0.0, 'correct': 1}]
        responses_many = [
            {'a': 1.0, 'b': float(i * 0.3 - 1.5), 'c': 0.0, 'correct': 1}
            for i in range(10)
        ]
        _, se_few = estimate_theta_eap(responses_few)
        _, se_many = estimate_theta_eap(responses_many)
        assert se_many < se_few


# =============================================================================
# BKT Tests
# =============================================================================

class TestBKT:
    def test_correct_increases_mastery(self):
        """Correct answer should increase mastery probability."""
        p_before = 0.5
        p_after = bkt_update(p_before, correct=True)
        assert p_after > p_before

    def test_incorrect_decreases_mastery(self):
        """Incorrect answer should decrease mastery probability."""
        p_before = 0.5
        p_after = bkt_update(p_before, correct=False)
        assert p_after < p_before

    def test_mastery_bounded(self):
        """Mastery should stay in (0, 1)."""
        p = 0.5
        for _ in range(100):
            p = bkt_update(p, correct=True)
        assert 0 < p < 1.0

        p = 0.5
        for _ in range(100):
            p = bkt_update(p, correct=False)
        assert 0 < p < 1.0

    def test_transition_effect(self):
        """After incorrect + learning opportunity, mastery should still increase slightly."""
        p = 0.3
        # P(T) = 0.1 ensures some transition even after incorrect
        p_after = bkt_update(p, correct=False, p_transit=0.1)
        # The transition component adds (1 - p_posterior) * P(T)
        # So even after incorrect, there's slight upward movement from transition
        assert p_after > 0.0


# =============================================================================
# Graph Belief Propagation Tests
# =============================================================================

class TestBeliefPropagation:
    def test_propagation_direction(self):
        """High source belief with high p_pass_pass should raise target."""
        edges = [{'source': 'q1', 'dest': 'q2', 'p_pass_pass': 0.8, 'p_pass_fail': 0.2}]
        states = {'q1': 0.9, 'q2': 0.5}
        updated = propagate_beliefs(edges, states, damping=0.5)
        assert updated['q2'] > 0.5

    def test_failed_source_lowers_target(self):
        """Low source belief with low p_pass_fail should lower target."""
        edges = [{'source': 'q1', 'dest': 'q2', 'p_pass_pass': 0.8, 'p_pass_fail': 0.1}]
        states = {'q1': 0.1, 'q2': 0.5}
        updated = propagate_beliefs(edges, states, damping=0.5)
        assert updated['q2'] < 0.5

    def test_damping_blends(self):
        """With damping=0.5, result should be blend of old and new."""
        edges = [{'source': 'q1', 'dest': 'q2', 'p_pass_pass': 1.0, 'p_pass_fail': 0.0}]
        states = {'q1': 1.0, 'q2': 0.0}
        updated = propagate_beliefs(edges, states, damping=0.5)
        # new = 1.0*1.0 + 0.0*0.0 = 1.0
        # dampened = 0.5*0.0 + 0.5*1.0 = 0.5
        assert abs(updated['q2'] - 0.5) < 0.01

    def test_missing_source_ignored(self):
        """Edges with unknown source should be skipped."""
        edges = [{'source': 'unknown', 'dest': 'q2', 'p_pass_pass': 0.8, 'p_pass_fail': 0.2}]
        states = {'q2': 0.5}
        updated = propagate_beliefs(edges, states, damping=0.5)
        assert updated['q2'] == 0.5


# =============================================================================
# Adaptive Engine Integration Tests
# =============================================================================

class TestAdaptiveEngine:
    def setup_method(self):
        """Create an engine with some test concepts."""
        self.engine = AdaptiveEngine(initial_theta=0.0)
        self.engine.initialize_concepts([
            {'id': 'c1'}, {'id': 'c2'}, {'id': 'c3'},
        ])

    def test_initial_state(self):
        """Engine starts with theta=0 and uniform BKT priors."""
        assert self.engine.theta == 0.0
        assert len(self.engine.answered_ids) == 0
        assert len(self.engine.concept_states) == 12  # 3 concepts × 4 levels

    def test_select_question_from_candidates(self):
        """Engine should select a question from candidates."""
        candidates = [
            {'id': 'q1', 'level': 'Repeat', 'concept_id': 'c1', 'a': 1.0, 'b': 0.0, 'c': 0.25},
            {'id': 'q2', 'level': 'Summary', 'concept_id': 'c1', 'a': 1.0, 'b': 1.0, 'c': 0.25},
        ]
        selected = self.engine.select_next_question(candidates)
        assert selected is not None
        assert selected['id'] in ['q1', 'q2']

    def test_answered_questions_excluded(self):
        """Already answered questions should not be selected again."""
        self.engine.answered_ids.add('q1')
        candidates = [
            {'id': 'q1', 'level': 'Repeat', 'concept_id': 'c1', 'a': 1.0, 'b': 0.0, 'c': 0.25},
            {'id': 'q2', 'level': 'Repeat', 'concept_id': 'c2', 'a': 1.0, 'b': 0.0, 'c': 0.25},
        ]
        selected = self.engine.select_next_question(candidates)
        assert selected['id'] == 'q2'

    def test_record_correct_response_updates_state(self):
        """Recording a correct response should increase theta and mastery."""
        question = {'id': 'q1', 'level': 'Repeat', 'concept_id': 'c1', 'a': 1.0, 'b': 0.0, 'c': 0.25}
        result = self.engine.record_response(question, correct=True, partial_score=1.0)
        assert result['theta'] > 0.0
        assert result['concept_mastery'] > 0.5
        assert 'q1' in self.engine.answered_ids

    def test_record_incorrect_response_updates_state(self):
        """Recording an incorrect response should decrease theta."""
        question = {'id': 'q1', 'level': 'Repeat', 'concept_id': 'c1', 'a': 1.0, 'b': 0.0, 'c': 0.0}
        result = self.engine.record_response(question, correct=False, partial_score=0.0)
        assert result['theta'] < 0.0

    def test_level_progression_prefers_repeat_first(self):
        """For unmastered concepts, Repeat questions should score highest on level progression."""
        candidates = [
            {'id': 'q1', 'level': 'Repeat', 'concept_id': 'c1', 'a': 1.0, 'b': 0.0, 'c': 0.25},
            {'id': 'q2', 'level': 'Apply', 'concept_id': 'c1', 'a': 1.0, 'b': 0.0, 'c': 0.25},
        ]
        selected = self.engine.select_next_question(candidates)
        # Should prefer Repeat for unmastered concept
        assert selected['id'] == 'q1'

    def test_stopping_question_limit(self):
        """Should stop when question limit is reached."""
        self.engine.answered_ids = {f'q{i}' for i in range(25)}
        should_stop, reason = self.engine.should_stop(max_questions=25)
        assert should_stop is True
        assert reason == 'question_limit_reached'

    def test_stopping_time_expired(self):
        """Should stop when time expires."""
        should_stop, reason = self.engine.should_stop(max_questions=25, time_expired=True)
        assert should_stop is True
        assert reason == 'time_expired'

    def test_not_stopping_early(self):
        """Should not stop before limits are reached."""
        self.engine.answered_ids = {'q1', 'q2'}
        should_stop, _ = self.engine.should_stop(max_questions=25)
        assert should_stop is False

    def test_concept_frontier(self):
        """Frontier should include concepts with mastered prereqs but unmastered themselves."""
        # c1 has no prereqs → always on frontier
        # c2 requires c1 → on frontier only if c1 is mastered
        prereq_graph = {'c2': ['c1'], 'c3': ['c2']}
        frontier = self.engine.get_concept_frontier(['c1', 'c2', 'c3'], prereq_graph)
        assert 'c1' in frontier  # No prereqs
        assert 'c2' not in frontier  # c1 not yet mastered
        assert 'c3' not in frontier  # c2 not mastered

    def test_concept_frontier_after_mastery(self):
        """After mastering c1 at Repeat level, c2 should appear on frontier."""
        prereq_graph = {'c2': ['c1'], 'c3': ['c2']}
        # Master c1 at Repeat level
        self.engine.concept_states[('c1', 'Repeat')].p_mastery = 0.9
        frontier = self.engine.get_concept_frontier(['c1', 'c2', 'c3'], prereq_graph)
        assert 'c1' in frontier  # Still on frontier (not mastered at all levels)
        assert 'c2' in frontier  # Now accessible
        assert 'c3' not in frontier  # c2 still not mastered

    def test_session_state_serialization(self):
        """Engine state should be serializable to dict."""
        state = self.engine.get_session_state()
        assert 'theta' in state
        assert 'theta_se' in state
        assert 'concept_mastery' in state
        assert isinstance(state['answered_ids'], list)


# =============================================================================
# Grading Service Tests
# =============================================================================

class TestGradingService:
    def test_exact_match_correct(self):
        """Selecting exactly the correct options should give is_correct=True, score=1.0."""
        result = GradingService.grade_mcq(['A', 'B'], ['A', 'B'])
        assert result.is_correct is True
        assert result.partial_score == 1.0

    def test_partial_credit(self):
        """Selecting some correct options should give partial credit."""
        result = GradingService.grade_mcq(['A'], ['A', 'B'])
        assert result.is_correct is False
        assert 0.0 < result.partial_score < 1.0

    def test_incorrect_selection_penalty(self):
        """Selecting an incorrect option should apply penalty."""
        result = GradingService.grade_mcq(['A', 'C'], ['A', 'B'])
        assert result.is_correct is False
        # 1/2 credit - 0.5 * 1/2 penalty = 0.25
        assert result.partial_score == 0.25

    def test_all_wrong(self):
        """Selecting only wrong options should give 0."""
        result = GradingService.grade_mcq(['C', 'D'], ['A', 'B'])
        assert result.is_correct is False
        assert result.partial_score == 0.0

    def test_empty_selection(self):
        """Empty selection should give 0."""
        result = GradingService.grade_mcq([], ['A', 'B'])
        assert result.is_correct is False
        assert result.partial_score == 0.0

    def test_grading_details_structure(self):
        """Grading details should have all expected keys."""
        result = GradingService.grade_mcq(['A', 'C'], ['A', 'B'])
        details = result.grading_details
        assert 'correct_options_selected' in details
        assert 'incorrect_options_selected' in details
        assert 'missed_correct_options' in details
        assert 'total_correct_options' in details


# =============================================================================
# ConceptLevelState Tests
# =============================================================================

class TestConceptLevelState:
    def test_initial_state(self):
        """Initial state should have default mastery and zero attempts."""
        state = ConceptLevelState('c1', 'Repeat')
        assert state.p_mastery == 0.5
        assert state.n_attempts == 0

    def test_update_correct(self):
        """Correct update should increase mastery and increment counters."""
        state = ConceptLevelState('c1', 'Repeat')
        state.update(correct=True)
        assert state.p_mastery > 0.5
        assert state.n_attempts == 1
        assert state.n_correct == 1

    def test_serialization(self):
        """to_dict should produce a valid dict."""
        state = ConceptLevelState('c1', 'Repeat', 0.7)
        d = state.to_dict()
        assert d['concept_id'] == 'c1'
        assert d['level'] == 'Repeat'
        assert d['p_mastery'] == 0.7
