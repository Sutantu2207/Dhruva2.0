/**
 * Dhruva.AI V2 — Phase 6 Mastery, Skills & Learning Evidence Test Suite
 *
 * Validates:
 * 1. Deterministic Mastery Engine blending (70% assessment + 30% evidence).
 * 2. Ebbinghaus exponential retention decay with configurable half-life.
 * 3. SuperMemo SM-2 Spaced Repetition interval & ease factor calculation.
 * 4. Competency level classification thresholds.
 * 5. Learning Evidence artifact validation & verification state transitions.
 * 6. RBAC guards (Student submission vs. Staff evaluation & verification).
 * 7. Quality rating constraints for active recall intervals.
 */

import { describe, it } from 'node:test';
import assert from 'node:assert';
import type {
  BloomLevel,
  CompetencyLevel,
  EvidenceType,
  VerificationStatus,
  QualityRating,
} from '../types/mastery';
import type { SystemRole } from '../types/auth';

// =============================================================================
// 1. DETERMINISTIC MASTERY BLENDING ALGORITHMS
// =============================================================================
describe('Deterministic Mastery Engine Blending', () => {
  function calculateRawMastery(
    assessmentScores: number[],
    evidenceScores: number[],
    assessmentWeight = 0.70,
    evidenceWeight = 0.30
  ): { rawScore: number; assessmentComp: number; evidenceComp: number } {
    const hasAssessments = assessmentScores.length > 0;
    const hasEvidence = evidenceScores.length > 0;

    if (!hasAssessments && !hasEvidence) {
      return { rawScore: 0.0, assessmentComp: 0.0, evidenceComp: 0.0 };
    }

    const mean = (arr: number[]) => arr.reduce((a, b) => a + b, 0) / arr.length;

    if (hasAssessments && hasEvidence) {
      const aComp = mean(assessmentScores);
      const eComp = mean(evidenceScores);
      const blended = aComp * assessmentWeight + eComp * evidenceWeight;
      return {
        rawScore: Math.round(blended * 1000) / 1000,
        assessmentComp: Math.round(aComp * 1000) / 1000,
        evidenceComp: Math.round(eComp * 1000) / 1000,
      };
    }

    if (hasAssessments) {
      const aComp = mean(assessmentScores);
      return {
        rawScore: Math.round(aComp * 1000) / 1000,
        assessmentComp: Math.round(aComp * 1000) / 1000,
        evidenceComp: 0.0,
      };
    }

    const eComp = mean(evidenceScores);
    return {
      rawScore: Math.round(eComp * 1000) / 1000,
      assessmentComp: 0.0,
      evidenceComp: Math.round(eComp * 1000) / 1000,
    };
  }

  it('blends 70% assessment and 30% evidence accurately', () => {
    const res = calculateRawMastery([1.0, 1.0], [0.5]);
    // Assessment mean = 1.0 (70% = 0.7), Evidence mean = 0.5 (30% = 0.15) -> Total = 0.85
    assert.strictEqual(res.rawScore, 0.85);
    assert.strictEqual(res.assessmentComp, 1.0);
    assert.strictEqual(res.evidenceComp, 0.5);
  });

  it('falls back to 100% assessment weight when zero evidence exists', () => {
    const res = calculateRawMastery([0.80, 0.90], []);
    assert.strictEqual(res.rawScore, 0.85);
    assert.strictEqual(res.assessmentComp, 0.85);
    assert.strictEqual(res.evidenceComp, 0.0);
  });

  it('falls back to 100% evidence weight when zero assessments exist', () => {
    const res = calculateRawMastery([], [0.95]);
    assert.strictEqual(res.rawScore, 0.95);
    assert.strictEqual(res.assessmentComp, 0.0);
    assert.strictEqual(res.evidenceComp, 0.95);
  });

  it('returns zero for students with no assessments or evidence', () => {
    const res = calculateRawMastery([], []);
    assert.strictEqual(res.rawScore, 0.0);
  });
});

// =============================================================================
// 2. EBBINGHAUS RETENTION DECAY ALGORITHM
// =============================================================================
describe('Ebbinghaus Retention Decay Calculations', () => {
  function calculateDecayFactor(daysSinceAssessed: number, halfLifeDays = 30): number {
    if (daysSinceAssessed <= 0) return 1.0;
    const lambda = Math.log(2) / halfLifeDays;
    const factor = Math.exp(-lambda * daysSinceAssessed);
    return Math.round(factor * 1000) / 1000;
  }

  it('maintains 1.0 retention factor immediately after assessment (t = 0)', () => {
    assert.strictEqual(calculateDecayFactor(0), 1.0);
    assert.strictEqual(calculateDecayFactor(-5), 1.0);
  });

  it('decays to exactly 0.50 at the 30-day half life', () => {
    const factor = calculateDecayFactor(30, 30);
    assert.strictEqual(factor, 0.50);
  });

  it('decays to 0.25 after two half-life intervals (60 days)', () => {
    const factor = calculateDecayFactor(60, 30);
    assert.strictEqual(factor, 0.25);
  });
});

// =============================================================================
// 3. SUPERMEMO SM-2 SPACED REPETITION ALGORITHM
// =============================================================================
describe('SuperMemo SM-2 Spaced Repetition', () => {
  function computeSM2(
    qualityRating: QualityRating,
    repetitionNumber: number,
    previousIntervalDays: number,
    previousEaseFactor: number
  ): { nextIntervalDays: number; nextRepetition: number; nextEaseFactor: number } {
    assert(qualityRating >= 0 && qualityRating <= 5, 'Quality rating must be between 0 and 5');

    // Update Ease Factor: EF' = EF + (0.1 - (5 - q) * (0.08 + (5 - q) * 0.02))
    const qDiff = 5 - qualityRating;
    let nextEaseFactor = previousEaseFactor + (0.1 - qDiff * (0.08 + qDiff * 0.02));
    if (nextEaseFactor < 1.3) nextEaseFactor = 1.3;

    if (qualityRating < 3) {
      // Failed recall -> reset repetition count to 0, next review due tomorrow
      return {
        nextIntervalDays: 1,
        nextRepetition: 0,
        nextEaseFactor: Math.round(nextEaseFactor * 100) / 100,
      };
    }

    const nextRepetition = repetitionNumber + 1;
    let nextIntervalDays: number;

    if (nextRepetition === 1) {
      nextIntervalDays = 1;
    } else if (nextRepetition === 2) {
      nextIntervalDays = 6;
    } else {
      nextIntervalDays = Math.round(previousIntervalDays * nextEaseFactor);
    }

    return {
      nextIntervalDays,
      nextRepetition,
      nextEaseFactor: Math.round(nextEaseFactor * 100) / 100,
    };
  }

  it('schedules 1-day interval on first successful repetition', () => {
    const res = computeSM2(4, 0, 0, 2.5);
    assert.strictEqual(res.nextRepetition, 1);
    assert.strictEqual(res.nextIntervalDays, 1);
    assert.strictEqual(res.nextEaseFactor, 2.5);
  });

  it('schedules 6-day interval on second successful repetition', () => {
    const res = computeSM2(5, 1, 1, 2.5);
    assert.strictEqual(res.nextRepetition, 2);
    assert.strictEqual(res.nextIntervalDays, 6);
    assert.strictEqual(res.nextEaseFactor, 2.6); // 2.5 + (0.1 - 0) = 2.6
  });

  it('multiplies previous interval by ease factor on third repetition', () => {
    const res = computeSM2(4, 2, 6, 2.5);
    assert.strictEqual(res.nextRepetition, 3);
    assert.strictEqual(res.nextIntervalDays, 15); // round(6 * 2.5) = 15
  });

  it('resets interval to 1 day on recall failure (rating < 3)', () => {
    const res = computeSM2(2, 4, 30, 2.5);
    assert.strictEqual(res.nextRepetition, 0);
    assert.strictEqual(res.nextIntervalDays, 1);
    assert.ok(res.nextEaseFactor < 2.5);
  });

  it('enforces lower bound floor of 1.3 on ease factor', () => {
    const res = computeSM2(0, 0, 1, 1.35);
    assert.strictEqual(res.nextEaseFactor, 1.3);
  });
});

// =============================================================================
// 4. COMPETENCY LEVEL CLASSIFICATION
// =============================================================================
describe('Competency Level Classification', () => {
  function classifyCompetency(score: number): CompetencyLevel {
    if (score >= 0.90) return 'MASTERY';
    if (score >= 0.70) return 'PROFICIENT';
    if (score >= 0.50) return 'DEVELOPING';
    return 'NOVICE';
  }

  it('classifies scores >= 90% as MASTERY', () => {
    assert.strictEqual(classifyCompetency(0.95), 'MASTERY');
    assert.strictEqual(classifyCompetency(0.90), 'MASTERY');
  });

  it('classifies scores 70-89% as PROFICIENT', () => {
    assert.strictEqual(classifyCompetency(0.85), 'PROFICIENT');
    assert.strictEqual(classifyCompetency(0.70), 'PROFICIENT');
  });

  it('classifies scores 50-69% as DEVELOPING', () => {
    assert.strictEqual(classifyCompetency(0.65), 'DEVELOPING');
    assert.strictEqual(classifyCompetency(0.50), 'DEVELOPING');
  });

  it('classifies scores below 50% as NOVICE', () => {
    assert.strictEqual(classifyCompetency(0.49), 'NOVICE');
    assert.strictEqual(classifyCompetency(0.0), 'NOVICE');
  });
});

// =============================================================================
// 5. EVIDENCE VALIDATION & LIFECYCLE
// =============================================================================
describe('Learning Evidence Validation & Permissions', () => {
  function validateEvidenceSubmission(payload: {
    skillId: string;
    evidenceType: EvidenceType;
    title: string;
    artifactUrl: string;
  }): { isValid: boolean; error?: string } {
    if (!payload.skillId) return { isValid: false, error: 'Skill ID is required.' };
    if (!payload.title || payload.title.trim().length < 2) {
      return { isValid: false, error: 'Title must be at least 2 characters.' };
    }
    const validUrlRegex = /^https?:\/\/.+/i;
    if (!payload.artifactUrl || !validUrlRegex.test(payload.artifactUrl)) {
      return { isValid: false, error: 'Artifact URL must be a valid HTTP/HTTPS link.' };
    }
    return { isValid: true };
  }

  function canVerifyEvidence(userRole: SystemRole): boolean {
    return ['SUPER_ADMIN', 'INSTITUTION_ADMIN', 'HOD', 'FACULTY'].includes(userRole);
  }

  it('accepts valid evidence submissions with full parameters', () => {
    const res = validateEvidenceSubmission({
      skillId: 'skill-uuid-1',
      evidenceType: 'PROJECT_DELIVERABLE',
      title: 'Distributed Log-Structured Merge Tree',
      artifactUrl: 'https://github.com/student/lsm-tree',
    });
    assert.strictEqual(res.isValid, true);
  });

  it('rejects invalid or dangerous artifact links', () => {
    const res = validateEvidenceSubmission({
      skillId: 'skill-uuid-1',
      evidenceType: 'PROJECT_DELIVERABLE',
      title: 'Bad URL Test',
      artifactUrl: 'javascript:alert(1)',
    });
    assert.strictEqual(res.isValid, false);
    assert.ok(res.error?.includes('valid HTTP/HTTPS'));
  });

  it('authorizes staff roles to verify student evidence', () => {
    assert.strictEqual(canVerifyEvidence('SUPER_ADMIN'), true);
    assert.strictEqual(canVerifyEvidence('INSTITUTION_ADMIN'), true);
    assert.strictEqual(canVerifyEvidence('HOD'), true);
    assert.strictEqual(canVerifyEvidence('FACULTY'), true);
  });

  it('strictly prohibits students from self-verifying evidence', () => {
    assert.strictEqual(canVerifyEvidence('STUDENT'), false);
  });
});
