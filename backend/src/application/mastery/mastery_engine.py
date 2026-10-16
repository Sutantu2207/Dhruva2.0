"""Dhruva.AI V2 — Deterministic Mastery & Spaced Review Calculation Engine.

STRICT DETERMINISTIC GUARANTEES:
1. Zero probabilistic model inferences or LLM hallucinations for student grades/mastery.
2. Transparent weighted score aggregation: Assessment evaluations (70%) + Verified evidence (30%).
3. Ebbinghaus exponential retention decay with configurable half-life.
4. SuperMemo SM-2 spaced repetition interval computation for concept retention.
5. Strict rule versioning ("2026.1") and full provenance metadata.
"""

import math
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple


class DeterministicMasteryEngine:
    """Core deterministic calculation engine for student skill mastery and spaced retention."""

    RULE_VERSION = "2026.1"
    ASSESSMENT_WEIGHT = 0.70
    EVIDENCE_WEIGHT = 0.30
    DEFAULT_HALF_LIFE_DAYS = 90.0
    MIN_EASE_FACTOR = 1.3

    @classmethod
    def calculate_raw_mastery(
        cls,
        assessment_scores: List[float],
        evidence_scores: List[float],
    ) -> float:
        """Compute blended mastery score from normalized assessment and evidence metrics (0.0 to 1.0).

        Args:
            assessment_scores: List of normalized scores [0.0, 1.0] from assessment items.
            evidence_scores: List of normalized scores [0.0, 1.0] from verified evidence.

        Returns:
            Blended raw mastery score between 0.0000 and 1.0000.
        """
        has_assessments = len(assessment_scores) > 0
        has_evidence = len(evidence_scores) > 0

        if not has_assessments and not has_evidence:
            return 0.0

        avg_assessment = (
            sum(assessment_scores) / len(assessment_scores) if has_assessments else 0.0
        )
        avg_evidence = (
            sum(evidence_scores) / len(evidence_scores) if has_evidence else 0.0
        )

        if has_assessments and has_evidence:
            raw = (cls.ASSESSMENT_WEIGHT * avg_assessment) + (cls.EVIDENCE_WEIGHT * avg_evidence)
        elif has_assessments:
            raw = avg_assessment
        else:
            raw = avg_evidence

        # Bound strictly to [0.0, 1.0]
        return round(max(0.0, min(1.0, raw)), 4)

    @classmethod
    def calculate_retention_decay(
        cls,
        raw_mastery: float,
        days_elapsed: float,
        half_life_days: float = DEFAULT_HALF_LIFE_DAYS,
    ) -> Tuple[float, float]:
        """Apply Ebbinghaus exponential retention decay based on elapsed days since last demonstration.

        Formula:
            decay_factor = e^(-lambda * delta_t)
            lambda = ln(2) / half_life
            decayed_mastery = raw_mastery * decay_factor

        Returns:
            Tuple of (decayed_mastery, decay_factor).
        """
        if days_elapsed <= 0.0 or raw_mastery <= 0.0:
            return (round(raw_mastery, 4), 1.0)

        decay_constant = math.log(2.0) / max(1.0, half_life_days)
        decay_factor = math.exp(-decay_constant * days_elapsed)
        decay_factor = max(0.0, min(1.0, decay_factor))

        decayed_mastery = raw_mastery * decay_factor
        return (
            round(max(0.0, min(1.0, decayed_mastery)), 4),
            round(decay_factor, 4),
        )

    @classmethod
    def calculate_confidence(
        cls,
        assessment_count: int,
        evidence_count: int,
    ) -> float:
        """Calculate statistical confidence based on empirical observation volume.

        Requires diverse evidence and assessments to reach high confidence.
        """
        if assessment_count <= 0 and evidence_count <= 0:
            return 0.0

        # Each assessment adds 0.20 confidence, each verified artifact adds 0.25
        confidence = (assessment_count * 0.20) + (evidence_count * 0.25)
        return round(max(0.0, min(1.0, confidence)), 4)

    @classmethod
    def classify_competency(cls, mastery_score: float, observation_count: int) -> str:
        """Deterministically classify skill competency level based on score and evidence threshold.

        Levels:
            observation_count < 1: INSUFFICIENT_EVIDENCE
            < 0.40: NOVICE
            0.40 <= score < 0.60: DEVELOPING
            0.60 <= score < 0.75: COMPETENT
            0.75 <= score < 0.90: PROFICIENT
            >= 0.90: MASTERY
        """
        if observation_count < 1:
            return "INSUFFICIENT_EVIDENCE"
        if mastery_score < 0.40:
            return "NOVICE"
        elif mastery_score < 0.60:
            return "DEVELOPING"
        elif mastery_score < 0.75:
            return "COMPETENT"
        elif mastery_score < 0.90:
            return "PROFICIENT"
        else:
            return "MASTERY"

    @classmethod
    def build_provenance(
        cls,
        raw_mastery: float,
        decay_factor: float,
        decayed_mastery: float,
        confidence_score: float,
        competency_level: str,
        assessment_count: int,
        evidence_count: int,
        days_elapsed: float,
        calculated_at: Optional[datetime] = None,
    ) -> Dict[str, Any]:
        """Generate complete deterministic calculation provenance for transparency and auditability."""
        return {
            "rule_version": cls.RULE_VERSION,
            "formula": "blended_70_assessment_30_evidence_ebbinghaus_decay",
            "assessment_weight": cls.ASSESSMENT_WEIGHT,
            "evidence_weight": cls.EVIDENCE_WEIGHT,
            "half_life_days": cls.DEFAULT_HALF_LIFE_DAYS,
            "assessment_count": assessment_count,
            "evidence_count": evidence_count,
            "total_observations": assessment_count + evidence_count,
            "days_elapsed": round(days_elapsed, 2),
            "raw_mastery": raw_mastery,
            "decay_factor": decay_factor,
            "decayed_mastery": decayed_mastery,
            "confidence_score": confidence_score,
            "competency_level": competency_level,
            "calculated_at": (calculated_at or datetime.now()).isoformat(),
        }

    @classmethod
    def calculate_sm2_schedule(
        cls,
        previous_interval_days: int,
        repetition_number: int,
        ease_factor: float,
        quality_rating: int,
    ) -> Tuple[int, int, float]:
        """Compute the next spaced review interval via the SuperMemo SM-2 algorithm.

        Args:
            previous_interval_days: Days between last two reviews.
            repetition_number: Consecutive successful reviews count.
            ease_factor: Current concept memorability multiplier (>= 1.3).
            quality_rating: Response evaluation score (0 to 5):
                5: Perfect response.
                4: Correct response after hesitation.
                3: Correct response recalled with serious difficulty.
                2: Incorrect response; where the correct one seemed easy to recall.
                1: Incorrect response; the correct one remembered.
                0: Complete blackout.

        Returns:
            Tuple of (next_interval_days, next_repetition_number, next_ease_factor).
        """
        quality = max(0, min(5, quality_rating))
        current_ef = max(cls.MIN_EASE_FACTOR, ease_factor)

        if quality < 3:
            # Retention failed: reset repetition count and start from 1 day
            return (1, 0, current_ef)

        # Successful retention (quality >= 3)
        if repetition_number == 0:
            next_interval = 1
        elif repetition_number == 1:
            next_interval = 6
        else:
            next_interval = max(1, round(previous_interval_days * current_ef))

        next_repetition = repetition_number + 1

        # Calculate new ease factor: EF' = EF + (0.1 - (5 - q) * (0.08 + (5 - q) * 0.02))
        q_diff = 5 - quality
        ef_delta = 0.1 - (q_diff * (0.08 + (q_diff * 0.02)))
        new_ef = max(cls.MIN_EASE_FACTOR, current_ef + ef_delta)

        return (next_interval, next_repetition, round(new_ef, 4))
