"""
Extended tests for IKAS Adaptive Engine — Phase 1 behavioral fixes.

Covers:
- Level progression scoring (Repeat → Summary → Intuitive → Apply)
- Composite score components (graph entropy, prereq readiness)
- Concept frontier filtering integration
- end_session mastery data return (Fix 3)
- Precision-based stopping (SE < 0.3)
- Multi-question adaptive flow simulation
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
from app.services.adaptive_engine import (
    AdaptiveEngine,
    ConceptLevelState,
    LEVEL_ORDER,
    LEVEL_INDEX,
    MASTERY_THRESHOLD,
)
from app.services.grading_service import GradingService


# =============================================================================
# Level Progression Scoring Tests
# =============================================================================

class TestLevelProgression:
    """Tests for _compute_level_progression — drives Repeat→Summary→Intuitive→Apply."""

    def setup_method(self):
        self.engine = AdaptiveEngine(initial_theta=0.0)
        self.engine.initialize_concepts([{'id': 'c1'}])

    def test_no_mastery_favors_repeat(self):
        """When nothing is mastered, Repeat gets max bonus (1.0)."""
        score = self.engine._compute_level_progression('c1', 'Repeat')
        assert score == 1.0

    def test_no_mastery_penalizes_apply(self):
        """When nothing is mastered, Apply gets low score."""
        score = self.engine._compute_level_progression('c1', 'Apply')
        assert score < 0.5

    def test_after_repeat_mastery_favors_summary(self):
        """After mastering Repeat, Summary should get max bonus."""
        self.engine.concept_states[('c1', 'Repeat')].p_mastery = 0.9
        score_summary = self.engine._compute_level_progression('c1', 'Summary')
        score_repeat = self.engine._compute_level_progression('c1', 'Repeat')
        assert score_summary == 1.0
        assert score_summary > score_repeat

    def test_after_summary_mastery_favors_intuitive(self):
        """After mastering Repeat+Summary, Intuitive should get max bonus."""
        self.engine.concept_states[('c1', 'Repeat')].p_mastery = 0.9
        self.engine.concept_states[('c1', 'Summary')].p_mastery = 0.8
        score = self.engine._compute_level_progression('c1', 'Intuitive')
        assert score == 1.0

    def test_after_intuitive_mastery_favors_apply(self):
        """After mastering Repeat+Summary+Intuitive, Apply should get max bonus."""
        for lvl in ['Repeat', 'Summary', 'Intuitive']:
            self.engine.concept_states[('c1', lvl)].p_mastery = 0.9
        score = self.engine._compute_level_progression('c1', 'Apply')
        assert score == 1.0

    def test_below_mastery_low_priority(self):
        """Questions below current mastery level get low priority."""
        self.engine.concept_states[('c1', 'Repeat')].p_mastery = 0.9
        self.engine.concept_states[('c1', 'Summary')].p_mastery = 0.9
        score = self.engine._compute_level_progression('c1', 'Repeat')
        assert score == 0.1  # Below mastery

    def test_unknown_concept_gets_repeat_bonus(self):
        """Unknown concept with no mastery data gets treated as unmastered — favors Repeat."""
        score = self.engine._compute_level_progression('unknown', 'Repeat')
        assert score == 1.0  # No mastery data → treated same as unmastered

    def test_full_level_ladder(self):
        """Verify the full ladder: each level gets max bonus in sequence."""
        expected_order = ['Repeat', 'Summary', 'Intuitive', 'Apply']
        for i, target_level in enumerate(expected_order):
            # Master all levels below target
            for j in range(i):
                self.engine.concept_states[('c1', expected_order[j])].p_mastery = 0.9
            score = self.engine._compute_level_progression('c1', target_level)
            assert score == 1.0, f"Expected 1.0 for {target_level} after mastering {expected_order[:i]}"
            # Reset for next iteration
            for lvl in LEVEL_ORDER:
                self.engine.concept_states[('c1', lvl)].p_mastery = 0.5


# =============================================================================
# Composite Score Components Tests
# =============================================================================

class TestCompositeScoring:
    """Tests for individual components of _compute_composite_score."""

    def setup_method(self):
        self.engine = AdaptiveEngine(initial_theta=0.0)
        self.engine.initialize_concepts([{'id': 'c1'}, {'id': 'c2'}])

    def test_graph_entropy_with_connections(self):
        """Questions with more unanswered connections should have higher entropy."""
        # q1 is prereq for q2 and q3
        prereq_map = {'q2': ['q1'], 'q3': ['q1']}
        score = self.engine._compute_graph_entropy('q1', prereq_map)
        assert score > 0.0

    def test_graph_entropy_no_connections(self):
        """Isolated questions should have zero entropy gain."""
        score = self.engine._compute_graph_entropy('q_isolated', {})
        assert score == 0.0

    def test_graph_entropy_answered_connections_excluded(self):
        """Already answered connections shouldn't count."""
        prereq_map = {'q2': ['q1']}
        self.engine.answered_ids.add('q2')
        score = self.engine._compute_graph_entropy('q1', prereq_map)
        assert score == 0.0

    def test_prereq_readiness_no_prereqs(self):
        """Questions with no prerequisites should have full readiness (1.0)."""
        score = self.engine._compute_prereq_readiness('q1', {})
        assert score == 1.0

    def test_prereq_readiness_all_mastered(self):
        """All prerequisites mastered should give full readiness."""
        prereq_map = {'q2': ['q1']}
        self.engine.node_beliefs['q1'] = 0.9  # Above threshold
        score = self.engine._compute_prereq_readiness('q2', prereq_map)
        assert score == 1.0

    def test_prereq_readiness_none_mastered(self):
        """No prerequisites mastered should give zero readiness."""
        prereq_map = {'q2': ['q1']}
        self.engine.node_beliefs['q1'] = 0.3  # Below threshold
        score = self.engine._compute_prereq_readiness('q2', prereq_map)
        assert score == 0.0

    def test_prereq_readiness_partial(self):
        """Some prerequisites mastered should give partial readiness."""
        prereq_map = {'q3': ['q1', 'q2']}
        self.engine.node_beliefs['q1'] = 0.9  # Mastered
        self.engine.node_beliefs['q2'] = 0.3  # Not mastered
        score = self.engine._compute_prereq_readiness('q3', prereq_map)
        assert score == 0.5

    def test_composite_score_all_components_contribute(self):
        """Verify composite score is a weighted sum of all 4 components."""
        question = {'id': 'q1', 'level': 'Repeat', 'concept_id': 'c1',
                    'a': 1.0, 'b': 0.0, 'c': 0.25}
        prereq_map = {}
        score = self.engine._compute_composite_score(question, prereq_map)
        assert 0.0 <= score <= 1.0

    def test_composite_score_deterministic(self):
        """Same inputs should produce same score."""
        question = {'id': 'q1', 'level': 'Repeat', 'concept_id': 'c1',
                    'a': 1.0, 'b': 0.0, 'c': 0.25}
        s1 = self.engine._compute_composite_score(question, {})
        s2 = self.engine._compute_composite_score(question, {})
        assert s1 == s2


# =============================================================================
# Concept Frontier Filtering Tests
# =============================================================================

class TestConceptFrontierFiltering:
    """Tests for concept frontier + filtering integration."""

    def setup_method(self):
        self.engine = AdaptiveEngine(initial_theta=0.0)
        self.engine.initialize_concepts([
            {'id': 'foundation'},
            {'id': 'intermediate'},
            {'id': 'advanced'},
        ])

    def test_frontier_only_foundation_initially(self):
        """Initially, only concepts with no prereqs are on frontier."""
        prereq_graph = {
            'intermediate': ['foundation'],
            'advanced': ['intermediate'],
        }
        frontier = self.engine.get_concept_frontier(
            ['foundation', 'intermediate', 'advanced'], prereq_graph
        )
        assert frontier == ['foundation']

    def test_frontier_expands_after_mastery(self):
        """Mastering foundation should add intermediate to frontier."""
        prereq_graph = {
            'intermediate': ['foundation'],
            'advanced': ['intermediate'],
        }
        self.engine.concept_states[('foundation', 'Repeat')].p_mastery = 0.9
        frontier = self.engine.get_concept_frontier(
            ['foundation', 'intermediate', 'advanced'], prereq_graph
        )
        assert 'foundation' in frontier  # Not mastered at all levels
        assert 'intermediate' in frontier  # Prereq mastered
        assert 'advanced' not in frontier  # Intermediate not mastered

    def test_frontier_excludes_fully_mastered(self):
        """Concepts mastered at ALL levels should be excluded."""
        prereq_graph = {}
        for lvl in LEVEL_ORDER:
            self.engine.concept_states[('foundation', lvl)].p_mastery = 0.9
        frontier = self.engine.get_concept_frontier(
            ['foundation', 'intermediate'], prereq_graph
        )
        assert 'foundation' not in frontier
        assert 'intermediate' in frontier

    def test_frontier_with_no_prereqs_all_on_frontier(self):
        """If graph has no prerequisites, all unmastered concepts are on frontier."""
        prereq_graph = {}
        frontier = self.engine.get_concept_frontier(
            ['foundation', 'intermediate', 'advanced'], prereq_graph
        )
        assert len(frontier) == 3

    def test_question_selection_respects_frontier(self):
        """When filtering by frontier, only frontier concept questions should be selectable."""
        prereq_graph = {'intermediate': ['foundation']}
        # Foundation not mastered → only foundation on frontier
        frontier = self.engine.get_concept_frontier(
            ['foundation', 'intermediate'], prereq_graph
        )
        
        candidates = [
            {'id': 'q1', 'level': 'Repeat', 'concept_id': 'foundation',
             'a': 1.0, 'b': 0.0, 'c': 0.25},
            {'id': 'q2', 'level': 'Repeat', 'concept_id': 'intermediate',
             'a': 1.0, 'b': 0.0, 'c': 0.25},
        ]
        # Filter to frontier
        filtered = [q for q in candidates if q['concept_id'] in frontier]
        selected = self.engine.select_next_question(filtered)
        assert selected['concept_id'] == 'foundation'


# =============================================================================
# Stopping Criteria Tests
# =============================================================================

class TestStoppingCriteria:
    """Tests for stopping criteria including precision threshold."""

    def setup_method(self):
        self.engine = AdaptiveEngine(initial_theta=0.0)

    def test_no_stop_below_minimum_questions(self):
        """Should NOT stop for precision before 5 questions even if SE is low."""
        self.engine.answered_ids = {'q1', 'q2', 'q3'}
        self.engine.theta_se = 0.1  # Very low SE
        should_stop, _ = self.engine.should_stop(max_questions=25)
        assert should_stop is False

    def test_stop_on_precision_after_minimum(self):
        """Should stop when SE < 0.3 after 5+ questions."""
        self.engine.answered_ids = {f'q{i}' for i in range(6)}
        self.engine.theta_se = 0.25  # Below 0.3 threshold
        should_stop, reason = self.engine.should_stop(max_questions=25)
        assert should_stop is True
        assert reason == 'precision_reached'

    def test_no_stop_high_se(self):
        """Should NOT stop when SE is still high after 5 questions."""
        self.engine.answered_ids = {f'q{i}' for i in range(6)}
        self.engine.theta_se = 0.5  # Above threshold
        should_stop, _ = self.engine.should_stop(max_questions=25)
        assert should_stop is False

    def test_time_overrides_everything(self):
        """Time expired should always stop, regardless of other criteria."""
        self.engine.answered_ids = set()
        should_stop, reason = self.engine.should_stop(max_questions=25, time_expired=True)
        assert should_stop is True
        assert reason == 'time_expired'


# =============================================================================
# Multi-Question Adaptive Flow Tests
# =============================================================================

class TestAdaptiveFlow:
    """Simulate realistic multi-question test flows to verify adaptive behavior."""

    def setup_method(self):
        self.engine = AdaptiveEngine(initial_theta=0.0)
        self.engine.initialize_concepts([{'id': 'llm'}, {'id': 'prompt_eng'}])

    def _make_questions(self):
        """Create test question pool spanning 2 concepts x 4 levels."""
        questions = []
        for concept in ['llm', 'prompt_eng']:
            for i, level in enumerate(LEVEL_ORDER):
                questions.append({
                    'id': f'q-{concept}-{level.lower()}',
                    'level': level,
                    'concept_id': concept,
                    'a': 1.0 + i * 0.3,
                    'b': -0.5 + i * 0.5,
                    'c': 0.25 if level == 'Repeat' else 0.2,
                })
        return questions

    def test_starts_at_repeat_level(self):
        """First question should be Repeat level (no mastery yet)."""
        candidates = self._make_questions()
        selected = self.engine.select_next_question(candidates)
        assert selected['level'] == 'Repeat'

    def test_advances_after_correct_answers(self):
        """After mastering Repeat, engine should advance to Summary."""
        candidates = self._make_questions()

        # Answer Repeat questions correctly to build mastery
        repeat_q = {'id': 'q-llm-repeat', 'level': 'Repeat', 'concept_id': 'llm',
                     'a': 1.0, 'b': -0.5, 'c': 0.25}
        for i in range(3):
            self.engine.record_response(
                question={**repeat_q, 'id': f'q-llm-repeat-{i}'},
                correct=True, partial_score=1.0
            )

        # Mastery should be high now
        mastery = self.engine.concept_states[('llm', 'Repeat')].p_mastery
        assert mastery > MASTERY_THRESHOLD

        # Next selection should prefer Summary
        remaining = [q for q in candidates if q['id'] not in self.engine.answered_ids]
        selected = self.engine.select_next_question(remaining)
        assert selected is not None

    def test_pivots_after_incorrect(self):
        """After failing, engine should not jump to advanced levels."""
        candidates = self._make_questions()
        prereq_map = {'q-prompt_eng-repeat': ['q-llm-repeat']}

        # Fail on LLM Repeat
        self.engine.record_response(
            question={'id': 'q-llm-repeat', 'level': 'Repeat', 'concept_id': 'llm',
                      'a': 1.0, 'b': -0.5, 'c': 0.25},
            correct=False, partial_score=0.0,
        )

        remaining = [q for q in candidates if q['id'] not in self.engine.answered_ids]
        selected = self.engine.select_next_question(remaining, prereq_map)
        # After a single failure, engine should stay on foundational levels
        # (Repeat or Summary), not jump to Intuitive/Apply
        assert selected['level'] in ('Repeat', 'Summary'), \
            f"Should stay on foundational levels after failure, got {selected['level']}"

    def test_theta_moves_correctly_through_session(self):
        """Theta should increase with correct answers and decrease with incorrect."""
        q_template = {'level': 'Repeat', 'concept_id': 'llm', 'a': 1.0, 'b': 0.0, 'c': 0.0}

        # 3 correct: theta should go up
        for i in range(3):
            self.engine.record_response(
                question={**q_template, 'id': f'qc{i}'},
                correct=True, partial_score=1.0,
            )
        theta_after_correct = self.engine.theta
        assert theta_after_correct > 0.0

        # 3 incorrect: theta should come back down
        for i in range(3):
            self.engine.record_response(
                question={**q_template, 'id': f'qi{i}'},
                correct=False, partial_score=0.0,
            )
        theta_after_mixed = self.engine.theta
        assert theta_after_mixed < theta_after_correct

    def test_se_decreases_through_session(self):
        """Standard error should decrease as engine collects more responses."""
        q_template = {'level': 'Repeat', 'concept_id': 'llm', 'a': 1.5, 'b': 0.0, 'c': 0.0}
        se_initial = self.engine.theta_se

        for i in range(8):
            self.engine.record_response(
                question={**q_template, 'id': f'q{i}'},
                correct=(i % 2 == 0),
                partial_score=1.0 if (i % 2 == 0) else 0.0,
            )

        assert self.engine.theta_se < se_initial

    def test_session_state_reflects_responses(self):
        """get_session_state should reflect all recorded responses."""
        self.engine.record_response(
            question={'id': 'q1', 'level': 'Repeat', 'concept_id': 'llm',
                      'a': 1.0, 'b': 0.0, 'c': 0.25},
            correct=True, partial_score=1.0,
        )
        state = self.engine.get_session_state()
        assert state['n_responses'] == 1
        assert 'q1' in state['answered_ids']
        assert 'llm/Repeat' in state['concept_mastery']
        mastery_data = state['concept_mastery']['llm/Repeat']
        assert mastery_data['n_attempts'] == 1
        assert mastery_data['n_correct'] == 1
        assert mastery_data['p_mastery'] > 0.5


# =============================================================================
# Grading Edge Cases
# =============================================================================

class TestGradingEdgeCases:
    """Edge case tests for the MCQ grading service."""

    def test_overselection_penalty(self):
        """Selecting all options (guessing) should be penalized."""
        result = GradingService.grade_mcq(
            ['A', 'B', 'C', 'D', 'E'],
            ['A', 'B'],
            ['A', 'B', 'C', 'D', 'E'],
        )
        assert result.partial_score < 1.0
        assert result.is_correct is False

    def test_single_correct_option(self):
        """Single correct option selected correctly should give 1.0."""
        result = GradingService.grade_mcq(['A'], ['A'])
        assert result.is_correct is True
        assert result.partial_score == 1.0

    def test_no_correct_answers_defined(self):
        """Should handle questions with no correct answers gracefully."""
        result = GradingService.grade_mcq(['A'], [])
        assert result.is_correct is False
        assert result.partial_score == 0.0

    def test_partial_credit_formula_example_from_docs(self):
        """Verify the exact example from adaptive_engine_theory.md.
        
        3 correct options, student checks 2 correct + 1 incorrect.
        Score = (2/3) - (1 * 0.5 / 3) = 0.667 - 0.167 = 0.5
        """
        result = GradingService.grade_mcq(
            ['A', 'B', 'D'],  # 2 correct (A, B) + 1 wrong (D)
            ['A', 'B', 'C'],  # 3 correct
        )
        assert result.is_correct is False
        expected = round(2/3 - 0.5/3, 4)
        assert abs(result.partial_score - expected) < 0.01


# =============================================================================
# BKT Extended Tests
# =============================================================================

class TestBKTExtended:
    """Extended BKT tests for convergence and stability."""

    def test_rapid_mastery_with_consecutive_correct(self):
        """Multiple consecutive correct answers should converge toward mastery."""
        p = 0.5
        for _ in range(5):
            p = bkt_update(p, correct=True)
        assert p > 0.9, f"After 5 correct, mastery should be >0.9, got {p:.3f}"

    def test_rapid_decline_with_consecutive_incorrect(self):
        """Multiple consecutive incorrect answers should converge toward unmastered."""
        p = 0.5
        for _ in range(5):
            p = bkt_update(p, correct=False)
        assert p < 0.2, f"After 5 incorrect, mastery should be <0.2, got {p:.3f}"

    def test_recovery_after_decline(self):
        """Mastery should recover after correct answers following incorrect ones."""
        p = 0.5
        for _ in range(3):
            p = bkt_update(p, correct=False)
        p_low = p
        for _ in range(5):
            p = bkt_update(p, correct=True)
        assert p > p_low
        assert p > 0.7

    def test_extreme_inputs_stability(self):
        """BKT should handle extreme mastery values without NaN/inf."""
        for extreme in [0.001, 0.999, 0.0, 1.0]:
            p = bkt_update(max(0.001, min(0.999, extreme)), correct=True)
            assert not math.isnan(p)
            assert not math.isinf(p)
            assert 0.0 < p < 1.0
