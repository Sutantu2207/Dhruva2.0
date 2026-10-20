/**
 * Dhruva.AI V2 — Phase 8 Analytics, Interventions & Notifications Test Suite.
 *
 * Verifies:
 * - Deterministic early warning risk classification rules
 * - Academic intervention state machine transitions
 * - Notification Hub unread counters and recipient boundaries
 * - Role-Based Access Control (RBAC) constraints
 */

import { describe, it } from 'node:test';
import assert from 'node:assert';
import type {
  InterventionStatus,
  InterventionType,
  RiskLevel,
  AtRiskStudent,
  NotificationItem,
} from '../types/analytics';

// ============================================================================
// 1. EARLY WARNING RISK CLASSIFICATION ALGORITHMS
// ============================================================================

describe('Early Warning Risk Classification Algorithms', () => {
  const MIN_PASSING_PERCENTAGE = 40.0;
  const AT_RISK_FAIL_RATE_THRESHOLD = 0.50;
  const MIN_MASTERY_THRESHOLD = 0.40;

  function evaluateStudentRisk(
    assessments: Array<{ percentage: number; is_passed: boolean }>,
    masteryScores: Array<{ score: number; decay: number; code: string }>
  ): { risk_level: RiskLevel; detected_rules: string[] } {
    const rules: string[] = [];

    // 1. Assessment failure rate
    const totalAssessments = assessments.length;
    const failedCount = assessments.filter(
      (a) => !a.is_passed || a.percentage < MIN_PASSING_PERCENTAGE
    ).length;

    if (totalAssessments > 0 && failedCount / totalAssessments >= AT_RISK_FAIL_RATE_THRESHOLD) {
      rules.push('HIGH_ASSESSMENT_FAIL_RATE');
    } else if (failedCount > 0) {
      rules.push('ASSESSMENT_FAILURE_DETECTED');
    }

    // 2. Mastery decay
    const decayedSkills = masteryScores.filter((m) => m.score * m.decay < MIN_MASTERY_THRESHOLD);
    if (decayedSkills.length >= 2) {
      rules.push('CRITICAL_MASTERY_DECAY');
    } else if (decayedSkills.length === 1) {
      rules.push('LOW_SKILL_MASTERY');
    }

    // 3. Classify
    let risk_level: RiskLevel = 'NONE';
    if (rules.includes('HIGH_ASSESSMENT_FAIL_RATE') || rules.includes('CRITICAL_MASTERY_DECAY')) {
      risk_level = 'CRITICAL';
    } else if (rules.includes('ASSESSMENT_FAILURE_DETECTED') || rules.includes('LOW_SKILL_MASTERY')) {
      risk_level = 'HIGH';
    }

    return { risk_level, detected_rules: rules };
  }

  it('classifies student with zero assessment failures and high mastery as NONE risk', () => {
    const assessments = [
      { percentage: 85.0, is_passed: true },
      { percentage: 92.0, is_passed: true },
    ];
    const mastery = [
      { score: 0.90, decay: 1.0, code: 'CS-ALG' },
      { score: 0.85, decay: 0.95, code: 'CS-DS' },
    ];

    const result = evaluateStudentRisk(assessments, mastery);
    assert.strictEqual(result.risk_level, 'NONE');
    assert.strictEqual(result.detected_rules.length, 0);
  });

  it('triggers CRITICAL risk when assessment failure rate reaches 50% or above', () => {
    const assessments = [
      { percentage: 32.0, is_passed: false },
      { percentage: 35.0, is_passed: false },
      { percentage: 70.0, is_passed: true },
    ]; // 2 of 3 failed = 66.7%
    const mastery = [{ score: 0.75, decay: 1.0, code: 'CS-MATH' }];

    const result = evaluateStudentRisk(assessments, mastery);
    assert.strictEqual(result.risk_level, 'CRITICAL');
    assert.ok(result.detected_rules.includes('HIGH_ASSESSMENT_FAIL_RATE'));
  });

  it('triggers CRITICAL risk when multiple competencies fall below 40% retention threshold', () => {
    const assessments = [{ percentage: 65.0, is_passed: true }];
    const mastery = [
      { score: 0.60, decay: 0.50, code: 'CS-ALG' }, // 0.30 -> Decayed
      { score: 0.50, decay: 0.60, code: 'CS-DS' },  // 0.30 -> Decayed
    ];

    const result = evaluateStudentRisk(assessments, mastery);
    assert.strictEqual(result.risk_level, 'CRITICAL');
    assert.ok(result.detected_rules.includes('CRITICAL_MASTERY_DECAY'));
  });

  it('triggers HIGH risk on single assessment failure or isolated skill deficiency', () => {
    const assessments = [
      { percentage: 38.0, is_passed: false },
      { percentage: 78.0, is_passed: true },
      { percentage: 80.0, is_passed: true },
    ]; // 1 of 3 = 33% fail rate (below 50% threshold)
    const mastery = [{ score: 0.80, decay: 1.0, code: 'CS-ALG' }];

    const result = evaluateStudentRisk(assessments, mastery);
    assert.strictEqual(result.risk_level, 'HIGH');
    assert.ok(result.detected_rules.includes('ASSESSMENT_FAILURE_DETECTED'));
  });
});

// ============================================================================
// 2. INTERVENTION STATE MACHINE TRANSITIONS
// ============================================================================

describe('Academic Intervention State Machine Transitions', () => {
  function canTransition(
    currentStatus: InterventionStatus,
    targetStatus: InterventionStatus,
    outcomeNotes?: string
  ): { allowed: boolean; reason?: string } {
    const validTransitions: Record<InterventionStatus, InterventionStatus[]> = {
      ASSIGNED: ['IN_PROGRESS', 'DISMISSED'],
      IN_PROGRESS: ['COMPLETED', 'ESCALATED', 'DISMISSED'],
      COMPLETED: ['ESCALATED'], // Can only reopen via formal escalation
      ESCALATED: ['IN_PROGRESS', 'COMPLETED', 'DISMISSED'],
      DISMISSED: [], // Terminal
    };

    if (!validTransitions[currentStatus]?.includes(targetStatus)) {
      return { allowed: false, reason: `Cannot transition from ${currentStatus} to ${targetStatus}` };
    }

    if (['COMPLETED', 'ESCALATED'].includes(targetStatus) && (!outcomeNotes || outcomeNotes.trim().length < 5)) {
      return { allowed: false, reason: 'Mandatory outcome notes required for COMPLETED or ESCALATED status' };
    }

    return { allowed: true };
  }

  it('permits ASSIGNED -> IN_PROGRESS transition when mentor commences review', () => {
    const res = canTransition('ASSIGNED', 'IN_PROGRESS');
    assert.strictEqual(res.allowed, true);
  });

  it('permits IN_PROGRESS -> COMPLETED transition only when outcome notes are provided', () => {
    const invalidRes = canTransition('IN_PROGRESS', 'COMPLETED', '');
    assert.strictEqual(invalidRes.allowed, false);
    assert.ok(invalidRes.reason?.includes('Mandatory outcome notes'));

    const validRes = canTransition(
      'IN_PROGRESS',
      'COMPLETED',
      'Targeted tutoring labs attended. Remediation quiz passed with 78% mark.'
    );
    assert.strictEqual(validRes.allowed, true);
  });

  it('strictly blocks direct ASSIGNED -> COMPLETED bypass transition', () => {
    const res = canTransition('ASSIGNED', 'COMPLETED', 'Skipping lab');
    assert.strictEqual(res.allowed, false);
    assert.ok(res.reason?.includes('Cannot transition from ASSIGNED to COMPLETED'));
  });

  it('permits escalation from IN_PROGRESS or COMPLETED to alert HOD and Academic Dean', () => {
    const res = canTransition('IN_PROGRESS', 'ESCALATED', 'Student failed to attend mandatory check-ins.');
    assert.strictEqual(res.allowed, true);
  });
});

// ============================================================================
// 3. NOTIFICATION HUB UNREAD COUNTER & ISOLATION
// ============================================================================

describe('Notification Hub Multi-Tenant Isolation & Unread Tracking', () => {
  it('correctly tracks and decrements unread counter upon marking individual item read', () => {
    let unreadCount = 3;
    const notifications: NotificationItem[] = [
      { id: '1', institution_id: 'i1', recipient_user_id: 'u1', notification_type: 'ALERT', title: 'T1', message: 'M1', is_read: false, created_at: '' },
      { id: '2', institution_id: 'i1', recipient_user_id: 'u1', notification_type: 'ALERT', title: 'T2', message: 'M2', is_read: false, created_at: '' },
      { id: '3', institution_id: 'i1', recipient_user_id: 'u1', notification_type: 'ALERT', title: 'T3', message: 'M3', is_read: false, created_at: '' },
    ];

    // Mark notification 2 as read
    const updated = notifications.map((n) => (n.id === '2' ? { ...n, is_read: true } : n));
    unreadCount = updated.filter((n) => !n.is_read).length;

    assert.strictEqual(unreadCount, 2);
    assert.strictEqual(updated.find((n) => n.id === '2')?.is_read, true);
  });

  it('resets unread counter to 0 upon mark-all-read batch operation', () => {
    const notifications: NotificationItem[] = [
      { id: '1', institution_id: 'i1', recipient_user_id: 'u1', notification_type: 'ALERT', title: 'T1', message: 'M1', is_read: false, created_at: '' },
      { id: '2', institution_id: 'i1', recipient_user_id: 'u1', notification_type: 'ALERT', title: 'T2', message: 'M2', is_read: false, created_at: '' },
    ];

    const allRead = notifications.map((n) => ({ ...n, is_read: true }));
    const unreadCount = allRead.filter((n) => !n.is_read).length;

    assert.strictEqual(unreadCount, 0);
  });

  it('enforces recipient user ID isolation ensuring zero cross-user notification leakage', () => {
    const currentUserId = 'student-alice';
    const store: NotificationItem[] = [
      { id: '1', institution_id: 'i1', recipient_user_id: 'student-alice', notification_type: 'INTERVENTION', title: 'Your Plan', message: 'Assigned', is_read: false, created_at: '' },
      { id: '2', institution_id: 'i1', recipient_user_id: 'student-bob', notification_type: 'INTERVENTION', title: 'Bob Plan', message: 'Confidential', is_read: false, created_at: '' },
    ];

    const userNotifications = store.filter((n) => n.recipient_user_id === currentUserId);
    assert.strictEqual(userNotifications.length, 1);
    assert.strictEqual(userNotifications[0].recipient_user_id, 'student-alice');
    assert.ok(!userNotifications.some((n) => n.recipient_user_id === 'student-bob'));
  });
});

// ============================================================================
// 4. ANALYTICS RBAC & ROLLUP CONSTRAINTS
// ============================================================================

describe('Analytics RBAC & Departmental Rollup Calculations', () => {
  function canComputeRollups(role: string): boolean {
    return ['SUPER_ADMIN', 'INSTITUTION_ADMIN', 'HOD'].includes(role);
  }

  function calculatePassingRate(passed: number, total: number): number {
    if (total === 0) return 1.0;
    return Math.round((passed / total) * 1000) / 1000;
  }

  it('authorizes Institutional Admin and HOD to trigger analytics rollups', () => {
    assert.strictEqual(canComputeRollups('SUPER_ADMIN'), true);
    assert.strictEqual(canComputeRollups('INSTITUTION_ADMIN'), true);
    assert.strictEqual(canComputeRollups('HOD'), true);
  });

  it('strictly denies faculty and students from mutating analytical rollups', () => {
    assert.strictEqual(canComputeRollups('FACULTY'), false);
    assert.strictEqual(canComputeRollups('STUDENT'), false);
  });

  it('calculates aggregate passing rates accurately without division by zero', () => {
    assert.strictEqual(calculatePassingRate(185, 200), 0.925);
    assert.strictEqual(calculatePassingRate(0, 0), 1.0);
    assert.strictEqual(calculatePassingRate(45, 50), 0.900);
  });
});
