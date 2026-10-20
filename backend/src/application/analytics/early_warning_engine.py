"""Dhruva.AI V2 — Deterministic Early Warning & At-Risk Student Detection Engine.

Core Principles:
1. NO SOURCE -> NO DATA: Risk is derived strictly from real assessment results, mastery records, and enrollment data.
2. 100% Deterministic: Rule triggers are explainable and audited with zero AI hallucination.
"""

from typing import Any, Dict, List, Optional
import uuid


class DeterministicEarlyWarningEngine:
    """Evaluates student performance metrics against early-warning intervention thresholds."""

    RULE_VERSION = "2026.1"

    # Standard Institutional Thresholds
    MIN_PASSING_PERCENTAGE = 40.0
    MIN_MASTERY_THRESHOLD = 0.40
    AT_RISK_FAIL_RATE_THRESHOLD = 0.50

    @classmethod
    def evaluate_student_risk(
        cls,
        student_user_id: uuid.UUID,
        graded_results: List[Any],
        mastery_records: List[Any],
        open_interventions_count: int = 0,
    ) -> Dict[str, Any]:
        """Evaluates student academic signals and classifies risk status.

        Args:
            student_user_id: The student's UUID.
            graded_results: List of AssessmentResult entities or dicts.
            mastery_records: List of MasteryRecord entities or dicts.
            open_interventions_count: Number of currently unresolved interventions.

        Returns:
            Dict containing is_at_risk, risk_level ('HIGH' | 'MEDIUM' | 'LOW' | 'NONE'),
            detected_rules, recommended_intervention_type, and trigger_reason.
        """
        detected_rules: List[Dict[str, Any]] = []

        # 1. Assessment Performance Check
        total_graded = len(graded_results)
        failed_count = 0
        total_percentage = 0.0

        for r in graded_results:
            pct = getattr(r, "percentage", 0.0)
            passed = getattr(r, "is_passed", True)
            total_percentage += pct
            if not passed or pct < cls.MIN_PASSING_PERCENTAGE:
                failed_count += 1

        avg_assessment_pct = (total_percentage / total_graded) if total_graded > 0 else 100.0
        fail_rate = (failed_count / total_graded) if total_graded > 0 else 0.0

        if total_graded > 0 and fail_rate >= cls.AT_RISK_FAIL_RATE_THRESHOLD:
            detected_rules.append({
                "rule_code": "HIGH_ASSESSMENT_FAIL_RATE",
                "severity": "HIGH",
                "details": f"Failed {failed_count} of {total_graded} graded assessments ({fail_rate:.1%}). Average score: {avg_assessment_pct:.1f}%.",
            })
        elif total_graded > 0 and failed_count > 0:
            detected_rules.append({
                "rule_code": "ASSESSMENT_FAILURE_DETECTED",
                "severity": "MEDIUM",
                "details": f"Failed {failed_count} assessment(s) below institutional passing mark.",
            })

        # 2. Competency Mastery & Decay Check
        low_mastery_skills: List[str] = []
        for m in mastery_records:
            score = getattr(m, "mastery_score", 0.0)
            decay = getattr(m, "decay_factor", 1.0)
            effective = score * decay
            skill_code = getattr(getattr(m, "skill", None), "code", str(getattr(m, "skill_id", "")))

            if effective < cls.MIN_MASTERY_THRESHOLD:
                low_mastery_skills.append(skill_code)

        if len(low_mastery_skills) >= 2:
            detected_rules.append({
                "rule_code": "CRITICAL_MASTERY_DECAY",
                "severity": "HIGH",
                "details": f"{len(low_mastery_skills)} competencies ({', '.join(low_mastery_skills[:3])}) below {cls.MIN_MASTERY_THRESHOLD:.0%} retention threshold.",
            })
        elif len(low_mastery_skills) == 1:
            detected_rules.append({
                "rule_code": "LOW_SKILL_MASTERY",
                "severity": "MEDIUM",
                "details": f"Competency {low_mastery_skills[0]} requires active recall review or lab reinforcement.",
            })

        # 3. Classify Overall Risk Level
        has_high = any(r["severity"] == "HIGH" for r in detected_rules)
        has_medium = any(r["severity"] == "MEDIUM" for r in detected_rules)

        if has_high:
            risk_level = "HIGH"
            is_at_risk = True
            rec_type = "REMEDIAL_SESSION"
        elif has_medium:
            risk_level = "MEDIUM"
            is_at_risk = True
            rec_type = "PEER_TUTORING"
        else:
            risk_level = "LOW" if (total_graded > 0 or len(mastery_records) > 0) else "NONE"
            is_at_risk = False
            rec_type = "CURRICULAR_COUNSELING"

        reasons = [r["details"] for r in detected_rules]
        trigger_reason = " | ".join(reasons) if reasons else "Academic progress within normal parameters."

        return {
            "student_user_id": str(student_user_id),
            "is_at_risk": is_at_risk,
            "risk_level": risk_level,
            "detected_rules": detected_rules,
            "recommended_intervention_type": rec_type,
            "trigger_reason": trigger_reason,
            "metrics_summary": {
                "total_graded_assessments": total_graded,
                "failed_assessments_count": failed_count,
                "average_assessment_percentage": round(avg_assessment_pct, 2),
                "low_mastery_skills_count": len(low_mastery_skills),
                "open_interventions_count": open_interventions_count,
            },
            "rule_version": cls.RULE_VERSION,
        }
