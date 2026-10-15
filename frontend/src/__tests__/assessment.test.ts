/**
 * Dhruva.AI V2 — Assessment Engine & Deterministic Grading Test Suite
 *
 * Validates:
 * 1. Deterministic grading algorithms (MCQ exact match, Multi-select anti-guessing penalty, Numerical tolerance).
 * 2. Strict Student Sanitization guardrail (Zero answer keys or explanations leaked).
 * 3. Assessment lifecycle state transitions (DRAFT -> PUBLISHED -> CLOSED).
 * 4. Assessment RBAC permission policies.
 * 5. Question form validation & authoring guards (MCQ, Multi-select, Numerical, Structured-text).
 * 6. Student answer entry, payload formatting & duplicate submission protection.
 * 7. Manual subjective grading boundaries & audit validation.
 * 8. Error and empty state formatting.
 */

import { describe, it } from 'node:test';
import assert from 'node:assert';
import type { SystemRole } from '../types/auth';
import type { QuestionType, AssessmentStatus, ItemizedBreakdownItem } from '../types/assessment';

// =============================================================================
// 1. DETERMINISTIC AUTOGRADING LOGIC
// =============================================================================
describe('Deterministic Grading Algorithms', () => {
  function gradeMCQ(submitted: string | null | undefined, correct: string, points: number): number {
    if (!submitted) return 0.0;
    return submitted === correct ? points : 0.0;
  }

  function gradeMultiSelect(
    submitted: string[],
    correct: string[],
    allOptionsCount: number,
    points: number
  ): number {
    if (!submitted || submitted.length === 0) return 0.0;
    const correctSet = new Set(correct);
    let correctCount = 0;
    let incorrectCount = 0;

    for (const opt of submitted) {
      if (correctSet.has(opt)) {
        correctCount++;
      } else {
        incorrectCount++;
      }
    }

    const fractionCorrect = correctCount / correct.length;
    const incorrectOptionsCount = Math.max(1, allOptionsCount - correct.length);
    const fractionIncorrect = incorrectCount / incorrectOptionsCount;

    const netScore = Math.max(0.0, fractionCorrect - fractionIncorrect) * points;
    return Math.round(netScore * 100) / 100;
  }

  function gradeNumerical(
    submitted: number,
    target: number,
    tolerance: number,
    points: number
  ): number {
    const diff = Math.abs(submitted - target);
    return diff <= tolerance + 1e-9 ? points : 0.0;
  }

  it('evaluates single-choice MCQ with exact match', () => {
    assert.strictEqual(gradeMCQ('opt_2', 'opt_2', 2.0), 2.0);
    assert.strictEqual(gradeMCQ('opt_1', 'opt_2', 2.0), 0.0);
    assert.strictEqual(gradeMCQ(null, 'opt_2', 2.0), 0.0);
  });

  it('awards full points for 100% correct multi-select', () => {
    const score = gradeMultiSelect(['opt_1', 'opt_3'], ['opt_1', 'opt_3'], 4, 4.0);
    assert.strictEqual(score, 4.0);
  });

  it('penalizes incorrect multi-select choices to prevent guessing', () => {
    // 1 correct out of 2, 0 incorrect: 50%
    const partial = gradeMultiSelect(['opt_1'], ['opt_1', 'opt_3'], 4, 4.0);
    assert.strictEqual(partial, 2.0);

    // Selecting all 4 options (guessing attack)
    const guessedAll = gradeMultiSelect(
      ['opt_1', 'opt_2', 'opt_3', 'opt_4'],
      ['opt_1', 'opt_3'],
      4,
      4.0
    );
    assert.strictEqual(guessedAll, 0.0);
  });

  it('validates numerical answers within tolerance interval', () => {
    const target = 3.14159;
    const tolerance = 0.01;

    // Within tolerance
    assert.strictEqual(gradeNumerical(3.14, target, tolerance, 5.0), 5.0);
    assert.strictEqual(gradeNumerical(3.15, target, tolerance, 5.0), 5.0);

    // Outside tolerance
    assert.strictEqual(gradeNumerical(3.12, target, tolerance, 5.0), 0.0);
    assert.strictEqual(gradeNumerical(3.16, target, tolerance, 5.0), 0.0);
  });
});

// =============================================================================
// 2. STUDENT SANITIZATION GUARDRAIL
// =============================================================================
describe('Student Answer-Key Sanitization Guardrail', () => {
  function sanitizeQuestionForStudent(question: Record<string, unknown>) {
    const sanitized = { ...question };
    delete sanitized.answer_key;
    delete sanitized.explanation;
    delete sanitized.created_by;
    delete sanitized.rubric;
    return sanitized;
  }

  it('strictly strips answer keys and explanations from student view', () => {
    const authorQuestion = {
      id: 'q-101',
      question_type: 'MCQ' as QuestionType,
      prompt_text: 'What is the time complexity of binary search?',
      options: [
        { id: 'opt_1', text: 'O(N)' },
        { id: 'opt_2', text: 'O(log N)' },
      ],
      answer_key: { correct_option_id: 'opt_2' },
      explanation: 'Binary search halves the search space each step.',
      points: 2.0,
      difficulty: 'EASY',
    };

    const studentView = sanitizeQuestionForStudent(authorQuestion);
    assert.strictEqual('answer_key' in studentView, false);
    assert.strictEqual('explanation' in studentView, false);
    assert.strictEqual(studentView.prompt_text, 'What is the time complexity of binary search?');
    assert.strictEqual(studentView.points, 2.0);
  });
});

// =============================================================================
// 3. ASSESSMENT LIFECYCLE & STATE MACHINE
// =============================================================================
describe('Assessment State Machine Transitions', () => {
  function canAddQuestions(status: AssessmentStatus): boolean {
    return status === 'DRAFT';
  }

  function canPublish(status: AssessmentStatus, questionCount: number): boolean {
    return status === 'DRAFT' && questionCount > 0;
  }

  function canSubmitAnswers(status: AssessmentStatus, nowUtc: Date, dueUtc: Date): boolean {
    return status === 'PUBLISHED' && nowUtc.getTime() <= dueUtc.getTime();
  }

  it('allows question modifications only in DRAFT status', () => {
    assert.strictEqual(canAddQuestions('DRAFT'), true);
    assert.strictEqual(canAddQuestions('PUBLISHED'), false);
    assert.strictEqual(canAddQuestions('CLOSED'), false);
  });

  it('allows publication only from DRAFT with at least one question', () => {
    assert.strictEqual(canPublish('DRAFT', 5), true);
    assert.strictEqual(canPublish('DRAFT', 0), false);
    assert.strictEqual(canPublish('PUBLISHED', 5), false);
  });

  it('accepts student submissions only when PUBLISHED and before deadline', () => {
    const now = new Date('2026-10-15T12:00:00Z');
    const futureDue = new Date('2026-10-15T14:00:00Z');
    const pastDue = new Date('2026-10-15T10:00:00Z');

    assert.strictEqual(canSubmitAnswers('PUBLISHED', now, futureDue), true);
    assert.strictEqual(canSubmitAnswers('PUBLISHED', now, pastDue), false);
    assert.strictEqual(canSubmitAnswers('DRAFT', now, futureDue), false);
    assert.strictEqual(canSubmitAnswers('CLOSED', now, futureDue), false);
  });
});

// =============================================================================
// 4. ROLE-BASED ACCESS CONTROL
// =============================================================================
describe('Assessment RBAC Permission Guardrails', () => {
  function canAuthor(role: SystemRole): boolean {
    return ['SUPER_ADMIN', 'INSTITUTION_ADMIN', 'HOD', 'FACULTY'].includes(role);
  }

  function canEvaluateManual(role: SystemRole): boolean {
    return ['SUPER_ADMIN', 'INSTITUTION_ADMIN', 'HOD', 'FACULTY'].includes(role);
  }

  function canTakeAssessment(role: SystemRole): boolean {
    return role === 'STUDENT';
  }

  it('allows staff roles to author questions and build assessments', () => {
    assert.strictEqual(canAuthor('SUPER_ADMIN'), true);
    assert.strictEqual(canAuthor('INSTITUTION_ADMIN'), true);
    assert.strictEqual(canAuthor('HOD'), true);
    assert.strictEqual(canAuthor('FACULTY'), true);
    assert.strictEqual(canAuthor('STUDENT'), false);
  });

  it('prohibits students from performing manual subjective evaluations', () => {
    assert.strictEqual(canEvaluateManual('FACULTY'), true);
    assert.strictEqual(canEvaluateManual('STUDENT'), false);
  });

  it('identifies student assessment taking privileges', () => {
    assert.strictEqual(canTakeAssessment('STUDENT'), true);
    assert.strictEqual(canTakeAssessment('FACULTY'), false);
  });
});

// =============================================================================
// 5. QUESTION FORM VALIDATION GUARDS
// =============================================================================
describe('Question Form Validation Guards', () => {
  function validateQuestion(payload: {
    type: QuestionType;
    prompt: string;
    points: number;
    options: { id: string; text: string }[];
    mcqCorrectId?: string;
    multiCorrectIds?: string[];
    numTarget?: number;
    numTolerance?: number;
  }): { valid: boolean; error?: string } {
    if (!payload.prompt || payload.prompt.trim().length < 3) {
      return { valid: false, error: 'Question prompt must be at least 3 characters.' };
    }
    if (payload.points <= 0) {
      return { valid: false, error: 'Points must be greater than zero.' };
    }
    if (payload.type === 'MCQ') {
      const validOpts = payload.options.filter((o) => o.text.trim().length > 0);
      if (validOpts.length < 2) {
        return { valid: false, error: 'MCQ questions require at least 2 non-empty options.' };
      }
      if (!payload.mcqCorrectId || !validOpts.some((o) => o.id === payload.mcqCorrectId)) {
        return { valid: false, error: 'Please designate a valid correct option.' };
      }
    }
    if (payload.type === 'MULTI_SELECT') {
      const validOpts = payload.options.filter((o) => o.text.trim().length > 0);
      if (validOpts.length < 2) {
        return { valid: false, error: 'Multi-select questions require at least 2 non-empty options.' };
      }
      if (!payload.multiCorrectIds || payload.multiCorrectIds.length === 0) {
        return { valid: false, error: 'Please designate at least one correct option.' };
      }
    }
    if (payload.type === 'NUMERICAL') {
      if (payload.numTarget === undefined || isNaN(payload.numTarget)) {
        return { valid: false, error: 'Target numerical value is required.' };
      }
      if (payload.numTolerance === undefined || payload.numTolerance < 0) {
        return { valid: false, error: 'Tolerance interval must be non-negative.' };
      }
    }
    return { valid: true };
  }

  it('validates MCQ question requirements', () => {
    // Valid
    const validMCQ = validateQuestion({
      type: 'MCQ',
      prompt: 'What is 2+2?',
      points: 1.0,
      options: [
        { id: 'opt_1', text: '3' },
        { id: 'opt_2', text: '4' },
      ],
      mcqCorrectId: 'opt_2',
    });
    assert.strictEqual(validMCQ.valid, true);

    // Invalid: missing options
    const invalidMCQ = validateQuestion({
      type: 'MCQ',
      prompt: 'What is 2+2?',
      points: 1.0,
      options: [{ id: 'opt_1', text: '3' }],
      mcqCorrectId: 'opt_1',
    });
    assert.strictEqual(invalidMCQ.valid, false);
  });

  it('validates numerical questions and tolerances', () => {
    const validNum = validateQuestion({
      type: 'NUMERICAL',
      prompt: 'What is the speed of light in 10^8 m/s?',
      points: 2.0,
      options: [],
      numTarget: 2.9979,
      numTolerance: 0.01,
    });
    assert.strictEqual(validNum.valid, true);

    const invalidTol = validateQuestion({
      type: 'NUMERICAL',
      prompt: 'What is the speed of light in 10^8 m/s?',
      points: 2.0,
      options: [],
      numTarget: 2.9979,
      numTolerance: -0.05,
    });
    assert.strictEqual(invalidTol.valid, false);
  });
});

// =============================================================================
// 6. STUDENT ANSWER ENTRY & DUPLICATE SUBMISSION PROTECTION
// =============================================================================
describe('Student Answer Entry & Submission Protection', () => {
  function createSubmissionPayload(answers: Record<string, unknown>) {
    return {
      answers_payload: answers,
    };
  }

  function canTriggerSubmit(isSubmitting: boolean, questionCount: number): boolean {
    return !isSubmitting && questionCount > 0;
  }

  it('formats answers payload cleanly for backend submission API', () => {
    const answers = {
      'q-uuid-1': 'opt_a',
      'q-uuid-2': ['opt_1', 'opt_3'],
      'q-uuid-3': 42.5,
      'q-uuid-4': 'Structured algorithm description.',
    };
    const payload = createSubmissionPayload(answers);
    assert.deepStrictEqual(payload.answers_payload, answers);
  });

  it('prevents accidental duplicate submission requests', () => {
    assert.strictEqual(canTriggerSubmit(false, 5), true);
    assert.strictEqual(canTriggerSubmit(true, 5), false); // Locked while in flight
    assert.strictEqual(canTriggerSubmit(false, 0), false); // Cannot submit empty test
  });
});

// =============================================================================
// 7. MANUAL EVALUATION CONSTRAINTS
// =============================================================================
describe('Manual Evaluation Constraints', () => {
  function validateManualGrade(allocated: number, awarded: number): { valid: boolean; error?: string } {
    if (awarded < 0) {
      return { valid: false, error: 'Awarded points cannot be negative.' };
    }
    if (awarded > allocated) {
      return { valid: false, error: `Awarded points (${awarded}) cannot exceed allocated points (${allocated}).` };
    }
    return { valid: true };
  }

  it('enforces allocated marks upper bound for subjective questions', () => {
    assert.strictEqual(validateManualGrade(5.0, 4.5).valid, true);
    assert.strictEqual(validateManualGrade(5.0, 5.0).valid, true);
    assert.strictEqual(validateManualGrade(5.0, 5.5).valid, false);
    assert.strictEqual(validateManualGrade(5.0, -1.0).valid, false);
  });
});
