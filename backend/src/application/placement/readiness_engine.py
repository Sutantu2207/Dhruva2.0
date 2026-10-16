"""Dhruva.AI V2 — Deterministic Career Readiness Engine.

Core Principles:
1. NO SOURCE -> NO DATA.
2. Only persisted mastery records and faculty-verified evidence/projects affect calculations.
3. Unverified student claims or missing records are marked as MISSING_EVIDENCE with score 0.0.
4. Calculations are 100% deterministic, audit-logged, and explainable with zero AI hallucination.
"""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
import uuid


class DeterministicReadinessEngine:
    """Deterministic, explainable calculator aligning student verified competencies with career requirements."""

    RULE_VERSION = "2026.1"

    @classmethod
    def evaluate_career_readiness(
        cls,
        target_role: str,
        required_skill_ids: List[uuid.UUID],
        skills_by_id: Dict[uuid.UUID, Any],
        mastery_by_skill_id: Dict[uuid.UUID, Any],
        verified_project_skill_ids: List[uuid.UUID],
    ) -> Dict[str, Any]:
        """Calculates readiness score, gap analysis, and explainable calculation provenance.

        Args:
            target_role: Target career title or profile designation.
            required_skill_ids: List of skill UUIDs required for this role.
            skills_by_id: Dictionary mapping skill UUID to Skill entity or dict.
            mastery_by_skill_id: Dictionary mapping skill UUID to MasteryRecord entity.
            verified_project_skill_ids: List of skill UUIDs demonstrated in verified projects.

        Returns:
            Dict containing readiness_score, matching_skills_count, total_required_skills,
            target_gap_analysis, and calculation_provenance.
        """
        total_required = len(required_skill_ids)
        if total_required == 0:
            return {
                "readiness_score": 0.0,
                "matching_skills_count": 0,
                "total_required_skills": 0,
                "target_gap_analysis": {
                    "skills_breakdown": [],
                    "met_skills": [],
                    "partial_skills": [],
                    "deficit_skills": [],
                    "summary": "No required skills specified for this target role.",
                },
                "calculation_provenance": {
                    "rule_version": cls.RULE_VERSION,
                    "algorithm": "DETERMINISTIC_SKILL_ALIGNMENT_V1",
                    "explanation": "Career target has zero configured skill requirements.",
                    "evaluated_at": datetime.now(timezone.utc).isoformat(),
                },
            }

        verified_project_set = set(verified_project_skill_ids)
        breakdown: List[Dict[str, Any]] = []
        met_skills: List[str] = []
        partial_skills: List[str] = []
        deficit_skills: List[str] = []
        cumulative_score = 0.0

        for s_id in required_skill_ids:
            skill = skills_by_id.get(s_id)
            skill_code = skill.code if skill and hasattr(skill, "code") else str(s_id)
            skill_name = skill.name if skill and hasattr(skill, "name") else "Skill"
            skill_category = skill.category if skill and hasattr(skill, "category") else "GENERAL"

            mastery_rec = mastery_by_skill_id.get(s_id)
            has_project_evidence = s_id in verified_project_set

            if mastery_rec is None:
                # No persisted record -> Explicitly missing evidence
                item_score = 0.0
                status = "MISSING_EVIDENCE"
                deficit_skills.append(skill_code)
                breakdown.append({
                    "skill_id": str(s_id),
                    "code": skill_code,
                    "name": skill_name,
                    "category": skill_category,
                    "status": status,
                    "score": 0.0,
                    "confidence_score": 0.0,
                    "decay_factor": 1.0,
                    "has_verified_project": has_project_evidence,
                    "gap_note": "No assessed or verified learning evidence found for this competency.",
                })
            else:
                # Calculate decayed mastery score
                raw_score = getattr(mastery_rec, "mastery_score", 0.0)
                decay = getattr(mastery_rec, "decay_factor", 1.0)
                effective_score = min(1.0, max(0.0, raw_score * decay))
                cumulative_score += effective_score

                if effective_score >= 0.70:
                    status = "MET"
                    met_skills.append(skill_code)
                    gap_note = "Competency verified at proficient or mastery level."
                elif effective_score >= 0.40:
                    status = "PARTIAL"
                    partial_skills.append(skill_code)
                    gap_note = "Developing competency. Additional lab practice or project deliverable suggested."
                else:
                    status = "DEFICIT"
                    deficit_skills.append(skill_code)
                    gap_note = "Current mastery score is below the 40% threshold for role readiness."

                breakdown.append({
                    "skill_id": str(s_id),
                    "code": skill_code,
                    "name": skill_name,
                    "category": skill_category,
                    "status": status,
                    "score": round(effective_score, 3),
                    "confidence_score": round(getattr(mastery_rec, "confidence_score", 0.0), 3),
                    "decay_factor": round(decay, 3),
                    "has_verified_project": has_project_evidence,
                    "gap_note": gap_note,
                })

        readiness_score = round(cumulative_score / total_required, 3)
        matching_count = len(met_skills)

        return {
            "readiness_score": readiness_score,
            "matching_skills_count": matching_count,
            "total_required_skills": total_required,
            "target_gap_analysis": {
                "skills_breakdown": breakdown,
                "met_skills": met_skills,
                "partial_skills": partial_skills,
                "deficit_skills": deficit_skills,
                "met_count": matching_count,
                "partial_count": len(partial_skills),
                "deficit_count": len(deficit_skills),
            },
            "calculation_provenance": {
                "rule_version": cls.RULE_VERSION,
                "algorithm": "DETERMINISTIC_SKILL_ALIGNMENT_V1",
                "explanation": (
                    f"Readiness index {readiness_score:.1%} computed from {total_required} required competencies "
                    f"({matching_count} met, {len(partial_skills)} partial, {len(deficit_skills)} deficit)."
                ),
                "evaluated_at": datetime.now(timezone.utc).isoformat(),
            },
        }
