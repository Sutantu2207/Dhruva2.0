"""Dhruva.AI V2 — Deterministic Grading Engine.

ZERO AI-GENERATED AUTHORITATIVE GRADES.
Grading operates exclusively on deterministic, verifiable mathematical rules.
Provides itemized breakdown, percentage calculation, and institutional letter grade assignments.
"""

from decimal import Decimal, ROUND_HALF_UP
from typing import Any, Dict, List, Optional, Set, Tuple


class DeterministicGradingEngine:
    """Pure deterministic evaluation engine for assessment submissions."""

    @staticmethod
    def evaluate_mcq(
        student_answer: Any,
        answer_key: Dict[str, Any],
        max_points: float,
    ) -> Tuple[float, str, str]:
        """
        Evaluate Single-Choice Question (MCQ).
        Returns: (awarded_points, status, feedback)
        """
        correct_option_id = str(answer_key.get("correct_option_id", "")).strip()
        if not correct_option_id:
            return 0.0, "INVALID_ANSWER_KEY", "Question missing valid correct_option_id configuration."

        if student_answer is None or str(student_answer).strip() == "":
            return 0.0, "UNANSWERED", "No answer selected."

        submitted_option = str(student_answer).strip()
        if submitted_option == correct_option_id:
            return round(max_points, 4), "CORRECT", "Correct answer."
        return 0.0, "INCORRECT", "Incorrect choice selected."

    @staticmethod
    def evaluate_multi_select(
        student_answer: Any,
        answer_key: Dict[str, Any],
        max_points: float,
    ) -> Tuple[float, str, str]:
        """
        Evaluate Multi-Select Question.
        Policy:
        - Full credit if exact match of all correct options.
        - Proportional partial credit if subset of correct options and zero incorrect options.
        - Zero credit if any incorrect option is selected (anti-guessing penalty).
        Returns: (awarded_points, status, feedback)
        """
        raw_correct = answer_key.get("correct_option_ids", [])
        if not raw_correct or not isinstance(raw_correct, list):
            return 0.0, "INVALID_ANSWER_KEY", "Question missing correct_option_ids list."

        correct_set: Set[str] = {str(opt).strip() for opt in raw_correct if str(opt).strip()}
        if not correct_set:
            return 0.0, "INVALID_ANSWER_KEY", "Question has empty correct_option_ids set."

        if student_answer is None or not isinstance(student_answer, list) or len(student_answer) == 0:
            return 0.0, "UNANSWERED", "No options selected."

        selected_set: Set[str] = {str(opt).strip() for opt in student_answer if str(opt).strip()}
        if not selected_set:
            return 0.0, "UNANSWERED", "No options selected."

        # Check for incorrect options selected
        incorrect_selected = selected_set - correct_set
        if len(incorrect_selected) > 0:
            return 0.0, "INCORRECT", f"Incorrect selection includes options: {', '.join(sorted(incorrect_selected))}."

        # All selected are correct
        if selected_set == correct_set:
            return round(max_points, 4), "CORRECT", "All correct options selected."

        # Partial credit: selected is strict subset of correct with 0 incorrect
        partial_ratio = len(selected_set) / len(correct_set)
        partial_points = round(max_points * partial_ratio, 4)
        return (
            partial_points,
            "PARTIAL",
            f"Selected {len(selected_set)} of {len(correct_set)} required options with zero errors.",
        )

    @staticmethod
    def evaluate_numerical(
        student_answer: Any,
        answer_key: Dict[str, Any],
        max_points: float,
    ) -> Tuple[float, str, str]:
        """
        Evaluate Numerical Answer against target value and tolerance interval.
        Returns: (awarded_points, status, feedback)
        """
        if "target_value" not in answer_key:
            return 0.0, "INVALID_ANSWER_KEY", "Question missing target_value in answer key."

        try:
            target_val = float(answer_key["target_value"])
        except (ValueError, TypeError):
            return 0.0, "INVALID_ANSWER_KEY", "Question target_value is not a valid float."

        try:
            tolerance = abs(float(answer_key.get("tolerance", 0.0)))
        except (ValueError, TypeError):
            tolerance = 0.0

        if student_answer is None or str(student_answer).strip() == "":
            return 0.0, "UNANSWERED", "No numerical value provided."

        try:
            submitted_val = float(student_answer)
        except (ValueError, TypeError):
            return 0.0, "INCORRECT", f"Submitted value '{student_answer}' is not a valid numerical number."

        delta = abs(submitted_val - target_val)
        if delta <= tolerance + 1e-9:
            return round(max_points, 4), "CORRECT", f"Submitted value {submitted_val} within accepted tolerance ±{tolerance}."
        return 0.0, "INCORRECT", f"Submitted value {submitted_val} outside acceptable range [{target_val - tolerance}, {target_val + tolerance}]."

    @classmethod
    def evaluate_structured_text(
        cls,
        student_answer: Any,
        answer_key: Dict[str, Any],
        max_points: float,
    ) -> Tuple[float, str, str]:
        """Subjective structured text answers route to manual evaluation queue."""
        return 0.0, "PENDING_MANUAL", "Subjective response queued for authorized faculty evaluation."

    @classmethod
    def evaluate_question(
        cls,
        question_type: str,
        student_answer: Any,
        answer_key: Dict[str, Any],
        max_points: float,
    ) -> Tuple[float, str, str]:
        """Dispatch evaluation by question type."""
        qtype = question_type.upper().strip()
        if qtype == "MCQ":
            return cls.evaluate_mcq(student_answer, answer_key, max_points)
        elif qtype == "MULTI_SELECT":
            return cls.evaluate_multi_select(student_answer, answer_key, max_points)
        elif qtype == "NUMERICAL":
            return cls.evaluate_numerical(student_answer, answer_key, max_points)
        elif qtype == "STRUCTURED_TEXT":
            return cls.evaluate_structured_text(student_answer, answer_key, max_points)
        else:
            return 0.0, "UNSUPPORTED_TYPE", f"Question type '{question_type}' is not supported by autograder."

    @classmethod
    def compute_letter_grade(cls, percentage: float) -> str:
        """Alias for calculate_grade_letter."""
        return cls.calculate_grade_letter(percentage)

    @classmethod
    def grade_submission(
        cls,
        assessment_questions: List[Dict[str, Any]],
        answers_payload: Dict[str, Any],
        passing_percentage: float = 40.0,
        existing_itemized: Optional[List[Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        """
        Grade complete submission against configured questions.
        assessment_questions: list of dicts with:
          - id (str): question_id
          - question_type (str)
          - points (float): maximum points
          - answer_key (dict)
          - prompt_text (str)
        """
        existing_manual_map: Dict[str, Dict[str, Any]] = {}
        if existing_itemized:
            for item in existing_itemized:
                existing_manual_map[str(item.get("question_id"))] = item

        itemized_breakdown: List[Dict[str, Any]] = []
        total_possible_points = 0.0
        total_awarded_points = 0.0
        has_pending_manual = False

        for q in assessment_questions:
            q_id = str(q["id"])
            q_type = q.get("question_type", "MCQ")
            max_pts = float(q.get("points", 1.0))
            total_possible_points += max_pts

            # Check if this question was already manually graded
            if q_id in existing_manual_map and existing_manual_map[q_id].get("status") == "MANUALLY_GRADED":
                prev_item = existing_manual_map[q_id]
                awarded = min(float(prev_item.get("awarded_points", 0.0)), max_pts)
                total_awarded_points += awarded
                itemized_breakdown.append({
                    "question_id": q_id,
                    "question_type": q_type,
                    "max_points": max_pts,
                    "awarded_points": awarded,
                    "status": "MANUALLY_GRADED",
                    "feedback": prev_item.get("feedback", "Manually graded by reviewer."),
                })
                continue

            student_ans = answers_payload.get(q_id)
            answer_key = q.get("answer_key", {})

            awarded, status, feedback = cls.evaluate_question(
                question_type=q_type,
                student_answer=student_ans,
                answer_key=answer_key,
                max_points=max_pts,
            )

            # Clamp awarded points to [0, max_pts]
            awarded = max(0.0, min(awarded, max_pts))

            if status == "PENDING_MANUAL":
                has_pending_manual = True

            total_awarded_points += awarded
            itemized_breakdown.append({
                "question_id": q_id,
                "question_type": q_type,
                "max_points": max_pts,
                "awarded_points": awarded,
                "status": status,
                "feedback": feedback,
            })

        # Calculations
        raw_score = round(min(total_awarded_points, total_possible_points), 4)
        if total_possible_points > 0:
            percentage = round((raw_score / total_possible_points) * 100.0, 2)
        else:
            percentage = 0.0

        is_passed = percentage >= passing_percentage
        grade_letter = cls.calculate_grade_letter(percentage)

        return {
            "raw_score": raw_score,
            "total_points": round(total_possible_points, 4),
            "percentage": percentage,
            "grade_letter": grade_letter,
            "is_passed": is_passed,
            "is_finalized": not has_pending_manual,
            "itemized_breakdown": itemized_breakdown,
        }

    @staticmethod
    def calculate_grade_letter(percentage: float) -> str:
        """Standard institutional grade scale."""
        if percentage >= 90.0:
            return "A+"
        elif percentage >= 80.0:
            return "A"
        elif percentage >= 70.0:
            return "B"
        elif percentage >= 60.0:
            return "C"
        elif percentage >= 50.0:
            return "D"
        else:
            return "F"
