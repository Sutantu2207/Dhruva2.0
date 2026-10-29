/**
 * Dhruva.AI V2 — Guardrailed AI Gateway & Retrieval Frontend Types (Phase 9)
 */

export interface CitationItem {
  citation_id: string;
  source_type: string;
  entity_id: string;
  title: string;
  course_code: string;
  provenance: string;
}

export interface TutorChatMessage {
  id: string;
  conversation_id?: string;
  role: 'user' | 'assistant' | 'system';
  content: string;
  citations?: CitationItem[];
  model_name?: string;
  pii_detected_count?: number;
  latency_ms?: number;
  is_refusal?: boolean;
  created_at: string;
}

export interface DraftQuestionOption {
  text: string;
  is_correct: boolean;
}

export interface DraftQuestionItem {
  draft_id: string;
  title: string;
  question_text: string;
  question_type: 'MCQ' | 'NUMERICAL' | 'STRUCTURED_TEXT' | 'MULTI_SELECT';
  difficulty: 'EASY' | 'MEDIUM' | 'HARD';
  bloom_level: 'REMEMBER' | 'UNDERSTAND' | 'APPLY' | 'ANALYZE' | 'EVALUATE';
  points: number;
  options: DraftQuestionOption[];
  explanation: string;
}

export interface QuestionDraftResponse {
  course_id: string;
  course_code: string;
  topic: string;
  difficulty: string;
  draft_questions: DraftQuestionItem[];
  total_generated: number;
}

export interface FeedbackSummaryResponse {
  course_id: string;
  course_code: string;
  total_submissions: number;
  pii_sanitized_count: number;
  summary: string;
  strengths: string[];
  areas_for_improvement: string[];
  actionable_recommendations: string[];
}

export interface AIAuditLog {
  id: string;
  institution_id: string;
  user_id: string;
  action: 'TUTOR_CHAT' | 'DRAFT_QUESTIONS' | 'SUMMARIZE_FEEDBACK' | 'BLOCKED_PROMPT';
  prompt_hash: string;
  pii_detected_count: number;
  safety_verdict: 'APPROVED' | 'SANITIZED_PII' | 'BLOCKED_INJECTION';
  tokens_used: number;
  cost_estimate: number;
  metadata_json: Record<string, unknown>;
  created_at: string;
}

export interface PIIDetectionResult {
  hasPII: boolean;
  detectedTypes: string[];
  sanitizedText: string;
  redactionCount: number;
}

export interface PromptInjectionCheckResult {
  isSafe: boolean;
  threatType?: string;
  reason?: string;
}

export interface AIConversation {
  id: string;
  institution_id: string;
  user_id: string;
  context_type: string;
  context_id?: string | null;
  title: string;
  status: string;
  created_at: string;
  updated_at: string;
}

export interface AIProviderStatus {
  active_provider: string;
  active_model: string;
  status: string;
  latency_ms: number;
  configured_providers: {
    google_gemini: { configured: boolean; model: string };
    nvidia_ai: { configured: boolean; model: string };
  };
}

export interface AIMessageItem {
  id: string;
  conversation_id: string;
  role: 'user' | 'assistant' | 'system';
  content: string;
  model_name?: string;
  pii_detected_count?: number;
  latency_ms?: number;
  created_at: string;
}
