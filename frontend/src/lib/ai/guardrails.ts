/**
 * Dhruva.AI V2 — Client-Side AI Guardrails, PII Sanitizer & Question Transformer
 * Ensures zero-leak client pre-flight checks and grounded citation utilities.
 */

import type { PIIDetectionResult, PromptInjectionCheckResult, DraftQuestionItem } from '../../types/ai.ts';
import type { QuestionAdmin } from '../../types/assessment.ts';

// Regex patterns for client-side pre-flight detection
const EMAIL_REGEX = /[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}/gi;
const PHONE_REGEX = /(?:\+?(\d{1,3}))?[-. (]*(\d{3})[-. )]*(\d{3})[-. ]*(\d{4})(?: *x(\d+))?/g;
const ROLL_NO_REGEX = /\b(?:[12]\d{3}[A-Z]{2,4}\d{3,5}|ROLL[:\s-]*[A-Z0-9]+)\b/gi;
const NATIONAL_ID_REGEX = /\b(?:\d{4}[-\s]?\d{4}[-\s]?\d{4}|\d{3}-\d{2}-\d{4})\b/g;

// Adversarial patterns for prompt injection detection
const INJECTION_PATTERNS: Array<{ pattern: RegExp; threat: string }> = [
  {
    pattern: /(?:ignore|disregard|forget)\s+(?:all\s+)?(?:previous|prior|above)\s+instructions/i,
    threat: 'INSTRUCTION_OVERRIDE',
  },
  {
    pattern: /(?:act as|you are now|pretend to be)\s+(?:DAN|developer mode|unrestricted|godmode)/i,
    threat: 'JAILBREAK_ATTEMPT',
  },
  {
    pattern: /(?:print|reveal|output|display)\s+(?:your\s+)?(?:system prompt|initial instructions|hidden prompt)/i,
    threat: 'SYSTEM_PROMPT_EXTRACTION',
  },
  {
    pattern: /(?:retrieve|dump|show)\s+(?:all\s+)?(?:tenants|institutions|database credentials|other students)/i,
    threat: 'CROSS_TENANT_EXFILTRATION',
  },
];

/**
 * Pre-flight client PII detector and sanitizer.
 * Provides instant feedback before network transmission.
 */
export function detectAndSanitizePII(text: string): PIIDetectionResult {
  const detectedTypes: string[] = [];
  let redactionCount = 0;
  let sanitized = text;

  if (EMAIL_REGEX.test(text)) {
    detectedTypes.push('EMAIL_ADDRESS');
    sanitized = sanitized.replace(EMAIL_REGEX, () => {
      redactionCount++;
      return '[REDACTED_EMAIL]';
    });
  }

  if (PHONE_REGEX.test(text)) {
    detectedTypes.push('PHONE_NUMBER');
    sanitized = sanitized.replace(PHONE_REGEX, () => {
      redactionCount++;
      return '[REDACTED_PHONE]';
    });
  }

  if (ROLL_NO_REGEX.test(text)) {
    detectedTypes.push('STUDENT_ROLL_NUMBER');
    sanitized = sanitized.replace(ROLL_NO_REGEX, () => {
      redactionCount++;
      return '[REDACTED_STUDENT_ID]';
    });
  }

  if (NATIONAL_ID_REGEX.test(text)) {
    detectedTypes.push('NATIONAL_ID');
    sanitized = sanitized.replace(NATIONAL_ID_REGEX, () => {
      redactionCount++;
      return '[REDACTED_NATIONAL_ID]';
    });
  }

  return {
    hasPII: detectedTypes.length > 0,
    detectedTypes,
    sanitizedText: sanitized,
    redactionCount,
  };
}

/**
 * Pre-flight prompt injection guardrail.
 */
export function checkPromptSecurity(prompt: string): PromptInjectionCheckResult {
  for (const { pattern, threat } of INJECTION_PATTERNS) {
    if (pattern.test(prompt)) {
      return {
        isSafe: false,
        threatType: threat,
        reason: `Adversarial pattern identified: ${threat.replace(/_/g, ' ')}. Out of syllabus or injection attempts are blocked by the Dhruva.AI safety gateway.`,
      };
    }
  }

  return { isSafe: true };
}

/**
 * Transforms an AI draft question item into a Question Bank QuestionAdmin record
 * for 1-click promotion to DRAFT status in the authoritative question bank.
 */
export function transformDraftToQuestionAdmin(
  draft: DraftQuestionItem,
  institutionId: string,
  questionBankId: string,
  courseId?: string
): QuestionAdmin {
  const options = draft.options.map((opt, idx) => ({
    id: `opt-${idx + 1}`,
    text: opt.text,
  }));

  const correctIndex = draft.options.findIndex((opt) => opt.is_correct);
  const correctOptionId = correctIndex >= 0 ? `opt-${correctIndex + 1}` : 'opt-1';

  return {
    id: `qb-q-${draft.draft_id}-${Date.now()}`,
    institution_id: institutionId,
    question_bank_id: questionBankId,
    question_type: draft.question_type,
    prompt_text: draft.question_text,
    options,
    answer_key: {
      correct_option_id: correctOptionId,
      acceptable_tolerance: draft.question_type === 'NUMERICAL' ? 0.05 : undefined,
    },
    points: draft.points || 1.0,
    difficulty: draft.difficulty,
    explanation: draft.explanation,
    concept_id: null,
    skill_id: null,
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString(),
  };
}

/**
 * Formats citation links into clickable provenance badges.
 */
export function formatCitationBadge(citationId: string, title: string, courseCode: string): string {
  return `[${citationId}: ${courseCode} • ${title}]`;
}
