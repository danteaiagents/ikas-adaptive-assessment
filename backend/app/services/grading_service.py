"""
MCQ Grading Service — Multi-select grading with partial credit.

All questions in IKAS use multi-select checkboxes (never radio buttons).
Partial credit rewards knowing some correct answers without penalizing
overly harsh for missing one.
"""

from typing import Dict, List, Any
import logging

logger = logging.getLogger(__name__)


class GradingResult:
    """Structured grading result for a single question response."""

    def __init__(
        self,
        is_correct: bool,
        partial_score: float,
        grading_details: Dict[str, Any],
    ):
        self.is_correct = is_correct
        self.partial_score = partial_score
        self.grading_details = grading_details

    def to_dict(self) -> Dict[str, Any]:
        return {
            'is_correct': self.is_correct,
            'partial_score': self.partial_score,
            'grading_details': self.grading_details,
        }


class GradingService:
    """
    Grades multi-select MCQ responses with partial credit scoring.
    
    Scoring formula:
        score = (correct_selected / total_correct) - (incorrect_selected * penalty)
        final = max(0.0, score)
    
    A response is considered "correct" (binary) only if ALL correct options
    are selected AND no incorrect options are selected.
    """

    INCORRECT_PENALTY = 0.5  # Penalty per incorrect selection (as fraction of total)

    @staticmethod
    def grade_mcq(
        selected_options: List[str],
        correct_answers: List[str],
        all_options: List[str] = None,
    ) -> GradingResult:
        """
        Grade a multi-select MCQ response.
        
        Args:
            selected_options: Options the student selected
            correct_answers: The correct option values/IDs
            all_options: All available options (for distractor analysis)
            
        Returns:
            GradingResult with is_correct, partial_score, and grading_details
        """
        if not correct_answers:
            logger.warning("Question has no correct answers defined")
            return GradingResult(
                is_correct=False,
                partial_score=0.0,
                grading_details={'error': 'No correct answers defined'},
            )

        selected_set = set(selected_options)
        correct_set = set(correct_answers)

        correct_selected = selected_set & correct_set
        incorrect_selected = selected_set - correct_set
        missed = correct_set - selected_set

        # Binary correctness: exact match only
        is_correct = (correct_selected == correct_set) and len(incorrect_selected) == 0

        # Partial credit calculation
        if len(correct_set) > 0:
            credit = len(correct_selected) / len(correct_set)
        else:
            credit = 0.0

        # Penalty for selecting incorrect options
        penalty = len(incorrect_selected) * GradingService.INCORRECT_PENALTY / max(len(correct_set), 1)
        partial_score = max(0.0, min(1.0, credit - penalty))

        # Detailed grading breakdown
        grading_details = {
            'correct_options_selected': sorted(correct_selected),
            'incorrect_options_selected': sorted(incorrect_selected),
            'missed_correct_options': sorted(missed),
            'total_correct_options': len(correct_set),
            'total_options_available': len(all_options) if all_options else None,
            'credit_earned': round(credit, 4),
            'penalty_applied': round(penalty, 4),
        }

        logger.info(
            f"Graded MCQ: is_correct={is_correct}, "
            f"partial_score={partial_score:.3f}, "
            f"selected={len(selected_set)}/{len(correct_set)} correct"
        )

        return GradingResult(
            is_correct=is_correct,
            partial_score=round(partial_score, 4),
            grading_details=grading_details,
        )
