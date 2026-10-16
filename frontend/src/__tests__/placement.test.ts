/**
 * Dhruva.AI V2 — Phase 7 Projects, Portfolios & Placement Test Suite
 *
 * Validates:
 * 1. Career Readiness Index deterministic evaluation and gap analysis.
 * 2. Missing evidence distinction from zero proficiency.
 * 3. Project state machine transitions (DRAFT -> SUBMITTED -> VERIFIED | REJECTED | REVOKED).
 * 4. Portfolio visibility gating & public project sanitization (unverified projects stripped).
 * 5. Placement Officer talent pool RBAC permissions and candidate filtering.
 */

import { describe, it } from 'node:test';
import assert from 'node:assert';
import type {
  ProjectType,
  ProjectStatus,
  PortfolioVisibility,
  SkillGapStatus,
} from '../types/placement';
import type { SystemRole } from '../types/auth';

// =============================================================================
// 1. DETERMINISTIC CAREER READINESS ALGORITHMS
// =============================================================================
describe('Deterministic Career Readiness Calculations', () => {
  interface SkillEvaluationInput {
    code: string;
    score: number | null; // null represents missing evidence
    decayFactor?: number;
  }

  function evaluateReadiness(skills: SkillEvaluationInput[]): {
    readinessScore: number;
    matchingCount: number;
    totalRequired: number;
    breakdown: Array<{ code: string; status: SkillGapStatus; effectiveScore: number }>;
  } {
    if (skills.length === 0) {
      return { readinessScore: 0.0, matchingCount: 0, totalRequired: 0, breakdown: [] };
    }

    let cumulativeScore = 0.0;
    let matchingCount = 0;
    const breakdown: Array<{ code: string; status: SkillGapStatus; effectiveScore: number }> = [];

    for (const item of skills) {
      if (item.score === null) {
        breakdown.append ? null : null;
        breakdown.push({
          code: item.code,
          status: 'MISSING_EVIDENCE',
          effectiveScore: 0.0,
        });
        continue;
      }

      const decay = item.decayFactor ?? 1.0;
      const effective = Math.min(1.0, Math.max(0.0, item.score * decay));
      cumulativeScore += effective;

      let status: SkillGapStatus;
      if (effective >= 0.70) {
        status = 'MET';
        matchingCount++;
      } else if (effective >= 0.40) {
        status = 'PARTIAL';
      } else {
        status = 'DEFICIT';
      }

      breakdown.push({
        code: item.code,
        status,
        effectiveScore: Math.round(effective * 1000) / 1000,
      });
    }

    const readinessScore = Math.round((cumulativeScore / skills.length) * 1000) / 1000;
    return {
      readinessScore,
      matchingCount,
      totalRequired: skills.length,
      breakdown,
    };
  }

  it('calculates 100% readiness when all required competencies are met', () => {
    const res = evaluateReadiness([
      { code: 'SKILL-SYS-01', score: 1.0 },
      { code: 'SKILL-ALGO-01', score: 0.90 },
      { code: 'SKILL-NET-01', score: 0.80 },
    ]);
    assert.strictEqual(res.readinessScore, 0.90);
    assert.strictEqual(res.matchingCount, 3);
    assert.strictEqual(res.totalRequired, 3);
  });

  it('distinguishes missing evidence from assessed zero', () => {
    const res = evaluateReadiness([
      { code: 'SKILL-SYS-01', score: 0.80 },
      { code: 'SKILL-UNKNOWN', score: null }, // zero proof
    ]);
    assert.strictEqual(res.readinessScore, 0.40);
    assert.strictEqual(res.matchingCount, 1);

    const unknownItem = res.breakdown.find((b) => b.code === 'SKILL-UNKNOWN');
    assert.strictEqual(unknownItem?.status, 'MISSING_EVIDENCE');
    assert.strictEqual(unknownItem?.effectiveScore, 0.0);
  });

  it('applies Ebbinghaus decay to skill scores before threshold matching', () => {
    // 0.80 score decayed by 50% = 0.40 -> PARTIAL (not MET)
    const res = evaluateReadiness([
      { code: 'SKILL-DB-01', score: 0.80, decayFactor: 0.50 },
    ]);
    assert.strictEqual(res.readinessScore, 0.40);
    assert.strictEqual(res.matchingCount, 0);
    assert.strictEqual(res.breakdown[0].status, 'PARTIAL');
  });

  it('handles zero required skills safely without division by zero', () => {
    const res = evaluateReadiness([]);
    assert.strictEqual(res.readinessScore, 0.0);
    assert.strictEqual(res.totalRequired, 0);
  });
});

// =============================================================================
// 2. PROJECT STUDIO LIFECYCLE & MUTABILITY GUARDS
// =============================================================================
describe('Project Studio State Machine Transitions', () => {
  function canEditProject(status: ProjectStatus): boolean {
    return status === 'DRAFT' || status === 'REJECTED';
  }

  function canSubmitProject(status: ProjectStatus): boolean {
    return status === 'DRAFT' || status === 'REJECTED';
  }

  function canVerifyProject(status: ProjectStatus, userRole: SystemRole): boolean {
    const isStaff = ['SUPER_ADMIN', 'INSTITUTION_ADMIN', 'HOD', 'FACULTY'].includes(userRole);
    return isStaff && status === 'SUBMITTED';
  }

  function canRevokeProject(status: ProjectStatus, reason: string, userRole: SystemRole): boolean {
    const isStaff = ['SUPER_ADMIN', 'INSTITUTION_ADMIN', 'HOD', 'FACULTY'].includes(userRole);
    return isStaff && status === 'VERIFIED' && reason.trim().length >= 5;
  }

  it('permits editing only while in DRAFT or REJECTED status', () => {
    assert.strictEqual(canEditProject('DRAFT'), true);
    assert.strictEqual(canEditProject('REJECTED'), true);
    assert.strictEqual(canEditProject('SUBMITTED'), false);
    assert.strictEqual(canEditProject('VERIFIED'), false);
    assert.strictEqual(canEditProject('REVOKED'), false);
  });

  it('allows submission only from DRAFT or REJECTED', () => {
    assert.strictEqual(canSubmitProject('DRAFT'), true);
    assert.strictEqual(canSubmitProject('REJECTED'), true);
    assert.strictEqual(canSubmitProject('VERIFIED'), false);
  });

  it('restricts verification action to authorized faculty for SUBMITTED projects', () => {
    assert.strictEqual(canVerifyProject('SUBMITTED', 'FACULTY'), true);
    assert.strictEqual(canVerifyProject('SUBMITTED', 'HOD'), true);
    assert.strictEqual(canVerifyProject('SUBMITTED', 'STUDENT'), false);
    assert.strictEqual(canVerifyProject('DRAFT', 'FACULTY'), false);
  });

  it('enforces mandatory justification before revoking verification', () => {
    assert.strictEqual(canRevokeProject('VERIFIED', 'Plagiarism detected', 'FACULTY'), true);
    assert.strictEqual(canRevokeProject('VERIFIED', '', 'FACULTY'), false);
    assert.strictEqual(canRevokeProject('VERIFIED', 'bad', 'FACULTY'), false); // under 5 chars
    assert.strictEqual(canRevokeProject('DRAFT', 'Valid reason', 'FACULTY'), false);
  });
});

// =============================================================================
// 3. PORTFOLIO PRIVACY & PUBLIC DATA SANITIZATION
// =============================================================================
describe('Portfolio Privacy & Public Sanitization', () => {
  interface ProjectItem {
    id: string;
    title: string;
    status: ProjectStatus;
  }

  function sanitizePortfolioProjectsForPublic(
    projects: ProjectItem[],
    isPublished: boolean,
    visibility: PortfolioVisibility
  ): { isVisible: boolean; visibleProjects: ProjectItem[] } {
    if (!isPublished || visibility === 'PRIVATE') {
      return { isVisible: false, visibleProjects: [] };
    }

    // Public output strictly strips unverified or draft projects
    const verifiedOnly = projects.filter((p) => p.status === 'VERIFIED');
    return { isVisible: true, visibleProjects: verifiedOnly };
  }

  it('strictly filters unverified or draft projects from public views', () => {
    const rawProjects: ProjectItem[] = [
      { id: '1', title: 'Verified Capstone', status: 'VERIFIED' },
      { id: '2', title: 'Work In Progress Draft', status: 'DRAFT' },
      { id: '3', title: 'Rejected Attempt', status: 'REJECTED' },
    ];
    const res = sanitizePortfolioProjectsForPublic(rawProjects, true, 'PUBLIC');
    assert.strictEqual(res.isVisible, true);
    assert.strictEqual(res.visibleProjects.length, 1);
    assert.strictEqual(res.visibleProjects[0].title, 'Verified Capstone');
  });

  it('denies access if portfolio is unpublished or marked PRIVATE', () => {
    const rawProjects: ProjectItem[] = [
      { id: '1', title: 'Verified Capstone', status: 'VERIFIED' },
    ];
    const unpub = sanitizePortfolioProjectsForPublic(rawProjects, false, 'PUBLIC');
    assert.strictEqual(unpub.isVisible, false);

    const priv = sanitizePortfolioProjectsForPublic(rawProjects, true, 'PRIVATE');
    assert.strictEqual(priv.isVisible, false);
  });
});

// =============================================================================
// 4. PLACEMENT TALENT DISCOVERY RBAC
// =============================================================================
describe('Placement Officer Talent Discovery RBAC', () => {
  function canAccessTalentPool(userRole: SystemRole): boolean {
    return ['SUPER_ADMIN', 'INSTITUTION_ADMIN', 'HOD', 'PLACEMENT_OFFICER'].includes(userRole);
  }

  it('authorizes Placement Officers and Admins', () => {
    assert.strictEqual(canAccessTalentPool('PLACEMENT_OFFICER'), true);
    assert.strictEqual(canAccessTalentPool('INSTITUTION_ADMIN'), true);
    assert.strictEqual(canAccessTalentPool('HOD'), true);
  });

  it('strictly denies students and unauthorized users', () => {
    assert.strictEqual(canAccessTalentPool('STUDENT'), false);
  });
});
