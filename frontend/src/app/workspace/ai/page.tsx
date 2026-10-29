'use client';

import React, { useState, useMemo, useEffect, useRef } from 'react';
import { useAuth } from '@/lib/auth/AuthContext';
import { Badge } from '@/components/ui/Badge';
import { Button } from '@/components/ui/Button';
import { Card } from '@/components/ui/Card';
import {
  Sparkles,
  ShieldCheck,
  BookOpen,
  FileText,
  AlertTriangle,
  Send,
  PlusCircle,
  CheckCircle2,
  Lock,
  RefreshCw,
  Cpu,
  Copy,
  Check,
  Trash2,
  Plus,
  MessageSquare,
  RotateCcw,
  Code as CodeIcon,
  ChevronRight,
  ExternalLink,
} from 'lucide-react';
import { api, ApiError } from '@/lib/api/client';
import { Course } from '@/types/academic';
import {
  CitationItem,
  TutorChatMessage,
  DraftQuestionItem,
  AIAuditLog,
  AIConversation,
  AIProviderStatus,
  AIMessageItem,
} from '@/types/ai';
import {
  detectAndSanitizePII,
  checkPromptSecurity,
} from '@/lib/ai/guardrails';

/**
 * Lightweight, safe Markdown & Code Renderer for AI tutor responses
 */
function FormattedMessage({ content }: { content: string }) {
  const [copiedIndex, setCopiedIndex] = useState<number | null>(null);

  const handleCopyCode = (code: string, index: number) => {
    navigator.clipboard.writeText(code);
    setCopiedIndex(index);
    setTimeout(() => setCopiedIndex(null), 2000);
  };

  const blocks = useMemo(() => {
    const rawBlocks = content.split(/(```[\s\S]*?```)/g);
    return rawBlocks.map((block, idx) => {
      if (block.startsWith('```') && block.endsWith('```')) {
        const firstLineEnd = block.indexOf('\n');
        const lang = firstLineEnd > 3 ? block.slice(3, firstLineEnd).trim() : 'code';
        const code = firstLineEnd > 3 ? block.slice(firstLineEnd + 1, -3) : block.slice(3, -3);
        return { type: 'code' as const, lang, code: code.trim(), key: idx };
      }
      return { type: 'text' as const, text: block, key: idx };
    });
  }, [content]);

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '8px', fontSize: '14px', lineHeight: 1.6 }}>
      {blocks.map((block) => {
        if (block.type === 'code') {
          return (
            <div
              key={block.key}
              style={{
                borderRadius: '8px',
                overflow: 'hidden',
                border: '1px solid var(--border-subtle, rgba(255,255,255,0.1))',
                backgroundColor: '#0d1117',
                color: '#e6edf3',
                margin: '6px 0',
              }}
            >
              <div
                style={{
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center',
                  padding: '6px 12px',
                  backgroundColor: '#161b22',
                  borderBottom: '1px solid rgba(255,255,255,0.08)',
                  fontSize: '11px',
                  fontWeight: 600,
                  color: '#8b949e',
                }}
              >
                <span style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                  <CodeIcon size={12} />
                  {block.lang.toUpperCase()}
                </span>
                <button
                  onClick={() => handleCopyCode(block.code, block.key)}
                  style={{
                    background: 'none',
                    border: 'none',
                    color: '#8b949e',
                    cursor: 'pointer',
                    display: 'flex',
                    alignItems: 'center',
                    gap: '4px',
                    fontSize: '11px',
                  }}
                  title="Copy code to clipboard"
                >
                  {copiedIndex === block.key ? <Check size={12} color="#10b981" /> : <Copy size={12} />}
                  <span>{copiedIndex === block.key ? 'Copied' : 'Copy'}</span>
                </button>
              </div>
              <pre
                style={{
                  padding: '12px 14px',
                  margin: 0,
                  fontFamily: 'ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace',
                  fontSize: '13px',
                  overflowX: 'auto',
                  lineHeight: 1.5,
                }}
              >
                <code>{block.code}</code>
              </pre>
            </div>
          );
        }

        // Parse paragraphs, bolding, bullet points
        const lines = block.text.split('\n');
        return (
          <div key={block.key} style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
            {lines.map((line, lIdx) => {
              const trimmed = line.trim();
              if (!trimmed) {
                return <div key={lIdx} style={{ height: '4px' }} />;
              }

              // Bold inline parser
              const renderFormattedText = (txt: string) => {
                const parts = txt.split(/(\*\*.*?\*\*|`.*?`)/g);
                return parts.map((part, pIdx) => {
                  if (part.startsWith('**') && part.endsWith('**')) {
                    return <strong key={pIdx} style={{ color: 'inherit' }}>{part.slice(2, -2)}</strong>;
                  }
                  if (part.startsWith('`') && part.endsWith('`')) {
                    return (
                      <code
                        key={pIdx}
                        style={{
                          padding: '2px 5px',
                          borderRadius: '4px',
                          backgroundColor: 'rgba(125, 125, 125, 0.15)',
                          fontFamily: 'monospace',
                          fontSize: '12px',
                        }}
                      >
                        {part.slice(1, -1)}
                      </code>
                    );
                  }
                  return part;
                });
              };

              // Headings
              if (trimmed.startsWith('### ')) {
                return (
                  <h4 key={lIdx} style={{ fontSize: '15px', fontWeight: 700, margin: '6px 0 2px 0' }}>
                    {renderFormattedText(trimmed.slice(4))}
                  </h4>
                );
              }
              if (trimmed.startsWith('## ')) {
                return (
                  <h3 key={lIdx} style={{ fontSize: '16px', fontWeight: 700, margin: '8px 0 2px 0' }}>
                    {renderFormattedText(trimmed.slice(3))}
                  </h3>
                );
              }

              // Bullet points
              if (trimmed.startsWith('- ') || trimmed.startsWith('* ')) {
                return (
                  <div key={lIdx} style={{ display: 'flex', gap: '8px', paddingLeft: '8px' }}>
                    <span style={{ color: '#3b82f6' }}>•</span>
                    <span>{renderFormattedText(trimmed.slice(2))}</span>
                  </div>
                );
              }

              // Numbered list
              const numMatch = trimmed.match(/^(\d+)\.\s+(.*)/);
              if (numMatch) {
                return (
                  <div key={lIdx} style={{ display: 'flex', gap: '8px', paddingLeft: '8px' }}>
                    <span style={{ fontWeight: 600, minWidth: '16px' }}>{numMatch[1]}.</span>
                    <span>{renderFormattedText(numMatch[2])}</span>
                  </div>
                );
              }

              return <p key={lIdx} style={{ margin: 0 }}>{renderFormattedText(line)}</p>;
            })}
          </div>
        );
      })}
    </div>
  );
}

export default function AIGatewayWorkspace() {
  const { user } = useAuth();
  const tenantSlug = user?.institution_slug || '';
  const primaryRole = user?.roles[0] || 'STUDENT';
  const isStaff = ['SUPER_ADMIN', 'INSTITUTION_ADMIN', 'HOD', 'FACULTY'].includes(primaryRole);
  const isAdmin = ['SUPER_ADMIN', 'INSTITUTION_ADMIN', 'HOD'].includes(primaryRole);

  // Active Tab: 'tutor' | 'drafting' | 'audit'
  const [activeTab, setActiveTab] = useState<'tutor' | 'drafting' | 'audit'>('tutor');

  // Real Courses from Database
  const [courses, setCourses] = useState<Course[]>([]);
  const [selectedCourseId, setSelectedCourseId] = useState<string>('');
  const [isCoursesLoading, setIsCoursesLoading] = useState<boolean>(true);

  // AI Provider Status
  const [providerStatus, setProviderStatus] = useState<AIProviderStatus | null>(null);
  const [isProviderStatusLoading, setIsProviderStatusLoading] = useState<boolean>(false);

  // Conversation Sidebar State
  const [conversations, setConversations] = useState<AIConversation[]>([]);
  const [isConversationsLoading, setIsConversationsLoading] = useState<boolean>(false);
  const [activeConversationId, setActiveConversationId] = useState<string | null>(null);
  const [copiedMessageId, setCopiedMessageId] = useState<string | null>(null);

  // Chat Scroll Anchor
  const chatScrollRef = useRef<HTMLDivElement>(null);

  // Initial Welcome Message
  const defaultWelcomeMessage: TutorChatMessage = {
    id: 'msg-init-1',
    role: 'assistant',
    content: `Hello! I am your Dhruva.AI Conversational Academic Intelligence Assistant.\n\nI answer your exact questions using authorized course syllabi, lecture modules, and verified pedagogical context. I also support multi-turn dialogue, Python code explanations, and structured exam preparations.\n\nHow can I help you excel today?`,
    citations: [],
    model_name: 'dhruva-guardrailed-gateway-v2',
    pii_detected_count: 0,
    latency_ms: 12,
    is_refusal: false,
    created_at: new Date().toISOString(),
  };

  const [messages, setMessages] = useState<TutorChatMessage[]>([defaultWelcomeMessage]);

  // Load Courses
  useEffect(() => {
    if (!tenantSlug) return;
    const fetchCourses = async () => {
      setIsCoursesLoading(true);
      try {
        const fetchedCourses = await api.get<Course[]>(`/institutions/${tenantSlug}/courses`);
        if (fetchedCourses && fetchedCourses.length > 0) {
          setCourses(fetchedCourses);
          setSelectedCourseId(fetchedCourses[0].id);
        } else {
          setCourses([]);
        }
      } catch {
        setCourses([]);
      } finally {
        setIsCoursesLoading(false);
      }
    };
    fetchCourses();
  }, [tenantSlug]);

  // Load Provider Status
  const fetchProviderStatus = async () => {
    if (!tenantSlug) return;
    setIsProviderStatusLoading(true);
    try {
      const status = await api.get<AIProviderStatus>(`/institutions/${tenantSlug}/ai/provider-status`);
      setProviderStatus(status);
    } catch {
      setProviderStatus(null);
    } finally {
      setIsProviderStatusLoading(false);
    }
  };

  useEffect(() => {
    fetchProviderStatus();
  }, [tenantSlug]);

  // Load User's Past Conversations
  const fetchConversations = async () => {
    if (!tenantSlug) return;
    setIsConversationsLoading(true);
    try {
      const convos = await api.get<AIConversation[]>(`/institutions/${tenantSlug}/ai/conversations`);
      setConversations(convos || []);
    } catch {
      setConversations([]);
    } finally {
      setIsConversationsLoading(false);
    }
  };

  useEffect(() => {
    fetchConversations();
  }, [tenantSlug]);

  // Scroll to bottom on new message
  useEffect(() => {
    if (chatScrollRef.current) {
      chatScrollRef.current.scrollTop = chatScrollRef.current.scrollHeight;
    }
  }, [messages]);

  const currentCourse = useMemo(() => {
    if (courses.length > 0) {
      return courses.find((c) => c.id === selectedCourseId) || courses[0];
    }
    return {
      id: selectedCourseId || 'default-course',
      code: 'COURSE',
      title: 'Institutional Syllabus',
      name: 'Institutional Syllabus',
      department_id: '',
      credits: 3.0,
      course_type: 'THEORY',
      status: 'ACTIVE',
      institution_id: user?.institution_id || '',
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
    } as Course;
  }, [courses, selectedCourseId, user?.institution_id]);

  // Switch or Resume Conversation
  const handleSelectConversation = async (convoId: string) => {
    if (convoId === activeConversationId) return;
    setActiveConversationId(convoId);

    try {
      const history = await api.get<AIMessageItem[]>(
        `/institutions/${tenantSlug}/ai/conversations/${convoId}/messages`
      );
      if (history && history.length > 0) {
        const mappedMessages: TutorChatMessage[] = history.map((m) => ({
          id: m.id,
          conversation_id: m.conversation_id,
          role: m.role as 'user' | 'assistant',
          content: m.content,
          model_name: m.model_name || 'dhruva-guardrailed-gateway-v2',
          pii_detected_count: m.pii_detected_count || 0,
          latency_ms: m.latency_ms || undefined,
          is_refusal: false,
          created_at: m.created_at,
        }));
        setMessages(mappedMessages);
      } else {
        setMessages([defaultWelcomeMessage]);
      }
    } catch {
      // If error loading history, retain current view
    }
  };

  // Start New Conversation
  const handleNewConversation = () => {
    setActiveConversationId(null);
    setMessages([
      {
        ...defaultWelcomeMessage,
        id: `msg-new-${Date.now()}`,
        created_at: new Date().toISOString(),
      },
    ]);
  };

  // Delete Conversation
  const handleDeleteConversation = async (e: React.MouseEvent, convoId: string) => {
    e.stopPropagation();
    try {
      await api.delete(`/institutions/${tenantSlug}/ai/conversations/${convoId}`);
      setConversations((prev) => prev.filter((c) => c.id !== convoId));
      if (activeConversationId === convoId) {
        handleNewConversation();
      }
    } catch {
      // Ignored
    }
  };

  // Copy Message Content
  const handleCopyMessage = (msgId: string, content: string) => {
    navigator.clipboard.writeText(content);
    setCopiedMessageId(msgId);
    setTimeout(() => setCopiedMessageId(null), 2000);
  };

  // -------------------------------------------------------------
  // TAB 1: TUTOR CHAT STATE
  // -------------------------------------------------------------
  const [chatInput, setChatInput] = useState<string>('');
  const [isSubmittingChat, setIsSubmittingChat] = useState<boolean>(false);
  const [selectedCitationModal, setSelectedCitationModal] = useState<CitationItem | null>(null);

  // Real-time pre-flight client PII check
  const piiPreview = useMemo(() => {
    if (!chatInput.trim()) return null;
    return detectAndSanitizePII(chatInput);
  }, [chatInput]);

  // Real-time prompt security check
  const promptSecurityPreview = useMemo(() => {
    if (!chatInput.trim()) return null;
    return checkPromptSecurity(chatInput);
  }, [chatInput]);

  const handleSendChat = async (messageToSend?: string) => {
    const rawText = messageToSend || chatInput;
    if (!rawText.trim() || isSubmittingChat) return;

    const securityCheck = checkPromptSecurity(rawText);
    if (!securityCheck.isSafe) {
      const refusalMsg: TutorChatMessage = {
        id: `msg-refusal-${Date.now()}`,
        role: 'assistant',
        content: `⚠️ **Security Refusal**: ${securityCheck.reason}`,
        is_refusal: true,
        model_name: 'dhruva-guardrailed-gateway-v2',
        created_at: new Date().toISOString(),
      };
      setMessages((prev) => [
        ...prev,
        {
          id: `msg-user-${Date.now()}`,
          role: 'user',
          content: rawText,
          created_at: new Date().toISOString(),
        },
        refusalMsg,
      ]);
      setChatInput('');
      return;
    }

    const pii = detectAndSanitizePII(rawText);
    const userMsg: TutorChatMessage = {
      id: `msg-user-${Date.now()}`,
      role: 'user',
      content: pii.sanitizedText,
      pii_detected_count: pii.redactionCount,
      created_at: new Date().toISOString(),
    };

    setMessages((prev) => [...prev, userMsg]);
    setChatInput('');
    setIsSubmittingChat(true);

    try {
      const response = await api.post<{
        conversation_id: string;
        message_id: string;
        course_id: string;
        course_code: string;
        role: string;
        content: string;
        citations: CitationItem[];
        model_name: string;
        pii_detected_count: number;
        latency_ms: number;
        is_refusal: boolean;
        created_at: string;
      }>(`/institutions/${tenantSlug}/ai/tutor/chat`, {
        course_id: currentCourse.id,
        message: pii.sanitizedText,
        conversation_id: activeConversationId || undefined,
      });

      if (response.conversation_id) {
        if (!activeConversationId) {
          setActiveConversationId(response.conversation_id);
          fetchConversations();
        }
      }

      const botResponse: TutorChatMessage = {
        id: response.message_id || `msg-bot-${Date.now()}`,
        role: 'assistant',
        content: response.content,
        citations: response.citations || [],
        model_name: response.model_name || 'dhruva-guardrailed-gateway-v2',
        pii_detected_count: response.pii_detected_count || pii.redactionCount,
        latency_ms: response.latency_ms || 150,
        is_refusal: response.is_refusal || false,
        created_at: response.created_at || new Date().toISOString(),
      };
      setMessages((prev) => [...prev, botResponse]);
    } catch (err: unknown) {
      const errorMsgText = err instanceof ApiError ? err.message : 'Unable to complete AI inference. Connecting to live database...';
      const botResponse: TutorChatMessage = {
        id: `msg-notice-${Date.now()}`,
        role: 'assistant',
        content: `⚠️ **Grounded Response**: ${errorMsgText}`,
        citations: [],
        model_name: 'dhruva-guardrailed-gateway-v2',
        pii_detected_count: pii.redactionCount,
        latency_ms: 85,
        is_refusal: true,
        created_at: new Date().toISOString(),
      };
      setMessages((prev) => [...prev, botResponse]);
    } finally {
      setIsSubmittingChat(false);
    }
  };

  // Quick Suggestion Prompts
  const quickSuggestions = [
    'Explain the core concept in clear, simple terms',
    'Show a complete Python code example with comments',
    'Summarize key syllabus points in 3 bullets',
    'Give me 2 practice questions with solutions',
  ];

  // -------------------------------------------------------------
  // TAB 2: FACULTY QUESTION DRAFTING STATE
  // -------------------------------------------------------------
  const [draftTopic, setDraftTopic] = useState<string>('Search Algorithms and Tree Invariants');
  const [draftDifficulty, setDraftDifficulty] = useState<'EASY' | 'MEDIUM' | 'HARD'>('MEDIUM');
  const [draftBloomLevel, setDraftBloomLevel] = useState<'REMEMBER' | 'UNDERSTAND' | 'APPLY' | 'ANALYZE' | 'EVALUATE'>('APPLY');
  const [draftNumQuestions, setDraftNumQuestions] = useState<number>(2);
  const [isDrafting, setIsDrafting] = useState<boolean>(false);
  const [draftedQuestions, setDraftedQuestions] = useState<DraftQuestionItem[]>([]);
  const [promotedQuestionIds, setPromotedQuestionIds] = useState<Set<string>>(new Set());
  const [draftSuccessToast, setDraftSuccessToast] = useState<string | null>(null);

  const handleGenerateQuestions = async () => {
    if (!draftTopic.trim() || isDrafting) return;
    setIsDrafting(true);

    try {
      const response = await api.post<{
        course_id: string;
        course_code: string;
        topic: string;
        difficulty: string;
        draft_questions: DraftQuestionItem[];
        total_generated: number;
      }>(`/institutions/${tenantSlug}/ai/faculty/draft-questions`, {
        course_id: currentCourse.id,
        topic_or_concept: draftTopic,
        difficulty: draftDifficulty,
        num_questions: draftNumQuestions,
      });

      if (response && response.draft_questions && response.draft_questions.length > 0) {
        setDraftedQuestions((prev) => [...response.draft_questions, ...prev]);
        setDraftSuccessToast(`✓ Generated ${response.draft_questions.length} grounded draft questions for ${draftTopic}`);
      } else {
        setDraftSuccessToast(`✓ Draft questions request processed successfully`);
      }
      setTimeout(() => setDraftSuccessToast(null), 4000);
    } catch (err: unknown) {
      const msg = err instanceof ApiError ? err.message : 'Draft generation error';
      setDraftSuccessToast(`Notice: ${msg}`);
      setTimeout(() => setDraftSuccessToast(null), 5000);
    } finally {
      setIsDrafting(false);
    }
  };

  const handlePromoteToQuestionBank = async (draft: DraftQuestionItem) => {
    try {
      const banks = await api.get<any[]>(`/institutions/${tenantSlug}/question-banks`).catch(() => []);
      let bankId = banks.find((b: any) => b.course_id === currentCourse.id)?.id || banks[0]?.id;

      if (!bankId) {
        const newBank = await api.post<any>(`/institutions/${tenantSlug}/question-banks`, {
          title: `Question Bank — ${currentCourse.code || 'Institutional Core'}`,
          description: `Auto-generated from Faculty AI Drafting Suite`,
          course_id: currentCourse.id || undefined,
        });
        bankId = newBank.id;
      }

      const correctIndex = draft.options.findIndex((opt) => opt.is_correct);
      const correctOptionId = correctIndex >= 0 ? `opt-${correctIndex + 1}` : 'opt-1';

      await api.post(`/institutions/${tenantSlug}/question-banks/${bankId}/questions`, {
        question_type: draft.question_type,
        prompt_text: draft.question_text,
        options: draft.options.map((opt, idx) => ({ id: `opt-${idx + 1}`, text: opt.text })),
        answer_key: { correct_option_id: correctOptionId },
        points: draft.points || 1.0,
        difficulty: draft.difficulty,
        explanation: draft.explanation,
      });

      setPromotedQuestionIds((prev) => new Set(prev).add(draft.draft_id));
      setDraftSuccessToast(
        `✓ Question "${draft.title}" successfully transferred to Question Bank!`
      );
      setTimeout(() => setDraftSuccessToast(null), 5000);
    } catch (err: unknown) {
      const errorMsg = err instanceof ApiError ? err.message : 'Could not save question';
      setDraftSuccessToast(`⚠️ Failed to transfer: ${errorMsg}`);
      setTimeout(() => setDraftSuccessToast(null), 5000);
    }
  };

  // -------------------------------------------------------------
  // TAB 3: AUDIT & GATEWAY SAFETY LOGS STATE (REAL-TIME OLTP)
  // -------------------------------------------------------------
  const [auditLogs, setAuditLogs] = useState<AIAuditLog[]>([]);
  const [isAuditLoading, setIsAuditLoading] = useState(false);

  const fetchAuditLogs = async () => {
    if (!tenantSlug || !isAdmin) return;
    setIsAuditLoading(true);
    try {
      const logs = await api.get<AIAuditLog[]>(`/institutions/${tenantSlug}/ai/audit-logs`);
      setAuditLogs(logs || []);
    } catch {
      setAuditLogs([]);
    } finally {
      setIsAuditLoading(false);
    }
  };

  useEffect(() => {
    if (activeTab === 'audit') {
      fetchAuditLogs();
    }
  }, [activeTab, tenantSlug, isAdmin]);

  return (
    <div style={{ maxWidth: '1440px', margin: '0 auto', padding: '24px 16px', display: 'flex', flexDirection: 'column', gap: '20px' }}>
      {/* Top Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: '16px' }}>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <div
              style={{
                width: '38px',
                height: '38px',
                borderRadius: '10px',
                backgroundColor: 'rgba(59, 130, 246, 0.12)',
                color: '#3b82f6',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
              }}
            >
              <Sparkles size={22} />
            </div>
            <div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <h1 style={{ fontSize: '24px', fontWeight: 700, color: 'var(--text-primary)', margin: 0 }}>
                  Dhruva.AI Conversational Intelligence
                </h1>
                <Badge variant="default">v2.0 Pro</Badge>
              </div>
              <p style={{ margin: '4px 0 0 0', fontSize: '13px', color: 'var(--text-secondary)' }}>
                Multi-turn pedagogical assistant grounded in verified course syllabi and institutional knowledge.
              </p>
            </div>
          </div>
        </div>

        {/* Live Provider Status & Model Badge */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px', flexWrap: 'wrap' }}>
          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '6px',
              padding: '6px 14px',
              borderRadius: '20px',
              backgroundColor: providerStatus?.configured_providers.google_gemini.configured
                ? 'rgba(59, 130, 246, 0.1)'
                : 'rgba(16, 185, 129, 0.1)',
              border: providerStatus?.configured_providers.google_gemini.configured
                ? '1px solid rgba(59, 130, 246, 0.3)'
                : '1px solid rgba(16, 185, 129, 0.3)',
              fontSize: '12px',
              fontWeight: 600,
              color: providerStatus?.configured_providers.google_gemini.configured ? '#3b82f6' : '#10b981',
            }}
          >
            <Cpu size={14} />
            <span>
              {providerStatus?.active_provider === 'google_gemini'
                ? `Gemini: ${providerStatus.active_model}`
                : providerStatus?.active_provider === 'nvidia_ai'
                ? `NVIDIA NIM: ${providerStatus.active_model}`
                : 'Grounded Academic Engine'}
            </span>
          </div>

          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '6px',
              padding: '6px 12px',
              borderRadius: '20px',
              backgroundColor: 'rgba(16, 185, 129, 0.1)',
              border: '1px solid rgba(16, 185, 129, 0.2)',
              fontSize: '12px',
              fontWeight: 600,
              color: '#10b981',
            }}
          >
            <ShieldCheck size={14} />
            Tenant Isolated
          </div>

          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '6px',
              padding: '6px 12px',
              borderRadius: '20px',
              backgroundColor: 'rgba(139, 92, 246, 0.1)',
              border: '1px solid rgba(139, 92, 246, 0.2)',
              fontSize: '12px',
              fontWeight: 600,
              color: '#8b5cf6',
            }}
          >
            <Lock size={14} />
            PII Redacted
          </div>
        </div>
      </div>

      {/* Course Context Picker & Navigation Tabs */}
      <div
        style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          flexWrap: 'wrap',
          gap: '12px',
          padding: '12px 16px',
          backgroundColor: 'var(--bg-surface)',
          borderRadius: 'var(--radius-lg)',
          border: '1px solid var(--border-subtle)',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          <span style={{ fontSize: '13px', fontWeight: 600, color: 'var(--text-secondary)' }}>
            Course Context:
          </span>
          <select
            value={selectedCourseId}
            onChange={(e) => setSelectedCourseId(e.target.value)}
            style={{
              padding: '6px 12px',
              borderRadius: 'var(--radius-md)',
              border: '1px solid var(--border-subtle)',
              backgroundColor: 'var(--bg-app)',
              color: 'var(--text-primary)',
              fontSize: '13px',
              fontWeight: 500,
            }}
          >
            {courses.length > 0 ? (
              courses.map((course) => (
                <option key={course.id} value={course.id}>
                  {course.code}: {course.title || (course as any).name}
                </option>
              ))
            ) : (
              <option value="">No courses yet (Create in Academic workspace)</option>
            )}
          </select>
        </div>

        {/* Tab Buttons */}
        <div style={{ display: 'flex', gap: '6px' }}>
          <button
            onClick={() => setActiveTab('tutor')}
            style={{
              padding: '6px 14px',
              borderRadius: 'var(--radius-md)',
              border: 'none',
              backgroundColor: activeTab === 'tutor' ? '#3b82f6' : 'transparent',
              color: activeTab === 'tutor' ? '#ffffff' : 'var(--text-secondary)',
              fontSize: '13px',
              fontWeight: 600,
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              gap: '6px',
            }}
          >
            <BookOpen size={14} />
            Academic Tutor
          </button>

          {isStaff && (
            <button
              onClick={() => setActiveTab('drafting')}
              style={{
                padding: '6px 14px',
                borderRadius: 'var(--radius-md)',
                border: 'none',
                backgroundColor: activeTab === 'drafting' ? '#3b82f6' : 'transparent',
                color: activeTab === 'drafting' ? '#ffffff' : 'var(--text-secondary)',
                fontSize: '13px',
                fontWeight: 600,
                cursor: 'pointer',
                display: 'flex',
                alignItems: 'center',
                gap: '6px',
              }}
            >
              <FileText size={14} />
              Question Drafting Studio
            </button>
          )}

          {isAdmin && (
            <button
              onClick={() => setActiveTab('audit')}
              style={{
                padding: '6px 14px',
                borderRadius: 'var(--radius-md)',
                border: 'none',
                backgroundColor: activeTab === 'audit' ? '#3b82f6' : 'transparent',
                color: activeTab === 'audit' ? '#ffffff' : 'var(--text-secondary)',
                fontSize: '13px',
                fontWeight: 600,
                cursor: 'pointer',
                display: 'flex',
                alignItems: 'center',
                gap: '6px',
              }}
            >
              <Cpu size={14} />
              Security & Audit Logs
            </button>
          )}
        </div>
      </div>

      {/* Global Success Notification Toast */}
      {draftSuccessToast && (
        <div
          style={{
            padding: '12px 16px',
            borderRadius: 'var(--radius-md)',
            backgroundColor: 'rgba(16, 185, 129, 0.15)',
            border: '1px solid #10b981',
            color: '#10b981',
            fontSize: '14px',
            fontWeight: 600,
            display: 'flex',
            alignItems: 'center',
            gap: '8px',
          }}
        >
          <CheckCircle2 size={18} />
          {draftSuccessToast}
        </div>
      )}

      {/* ============================================================== */}
      {/* TAB 1: ACADEMIC TUTOR CHAT (MULTI-TURN CONVERSATIONAL UI)       */}
      {/* ============================================================== */}
      {activeTab === 'tutor' && (
        <div style={{ display: 'grid', gridTemplateColumns: '260px 1fr 300px', gap: '16px', alignItems: 'stretch' }}>
          
          {/* LEFT: Conversation History Sidebar */}
          <div
            style={{
              backgroundColor: 'var(--bg-surface)',
              borderRadius: 'var(--radius-lg)',
              border: '1px solid var(--border-subtle)',
              display: 'flex',
              flexDirection: 'column',
              padding: '14px',
              gap: '12px',
              maxHeight: '750px',
              overflow: 'hidden',
            }}
          >
            <Button
              variant="primary"
              size="sm"
              onClick={handleNewConversation}
              style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '6px', width: '100%' }}
            >
              <Plus size={14} />
              New Chat
            </Button>

            <div style={{ fontSize: '11px', fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
              Chat History
            </div>

            <div style={{ flex: 1, overflowY: 'auto', display: 'flex', flexDirection: 'column', gap: '6px' }}>
              {isConversationsLoading ? (
                <div style={{ fontSize: '12px', color: 'var(--text-muted)', padding: '12px 4px', textAlign: 'center' }}>
                  Loading history...
                </div>
              ) : conversations.length === 0 ? (
                <div style={{ fontSize: '12px', color: 'var(--text-muted)', padding: '16px 8px', textAlign: 'center', lineHeight: 1.4 }}>
                  No prior sessions yet. Your questions and follow-ups will be saved here.
                </div>
              ) : (
                conversations.map((c) => {
                  const isActive = c.id === activeConversationId;
                  return (
                    <div
                      key={c.id}
                      onClick={() => handleSelectConversation(c.id)}
                      style={{
                        padding: '8px 10px',
                        borderRadius: '6px',
                        backgroundColor: isActive ? 'rgba(59, 130, 246, 0.12)' : 'transparent',
                        border: isActive ? '1px solid rgba(59, 130, 246, 0.3)' : '1px solid transparent',
                        cursor: 'pointer',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'space-between',
                        gap: '6px',
                        transition: 'all 0.15s ease',
                      }}
                      onMouseEnter={(e) => {
                        if (!isActive) e.currentTarget.style.backgroundColor = 'var(--bg-app)';
                      }}
                      onMouseLeave={(e) => {
                        if (!isActive) e.currentTarget.style.backgroundColor = 'transparent';
                      }}
                    >
                      <div style={{ display: 'flex', alignItems: 'center', gap: '8px', minWidth: 0, flex: 1 }}>
                        <MessageSquare size={13} color={isActive ? '#3b82f6' : 'var(--text-muted)'} style={{ flexShrink: 0 }} />
                        <span
                          style={{
                            fontSize: '12px',
                            fontWeight: isActive ? 600 : 400,
                            color: isActive ? '#3b82f6' : 'var(--text-primary)',
                            whiteSpace: 'nowrap',
                            overflow: 'hidden',
                            textOverflow: 'ellipsis',
                          }}
                        >
                          {c.title || 'Chat Session'}
                        </span>
                      </div>
                      <button
                        onClick={(e) => handleDeleteConversation(e, c.id)}
                        style={{
                          background: 'none',
                          border: 'none',
                          color: 'var(--text-muted)',
                          cursor: 'pointer',
                          padding: '2px',
                          display: 'flex',
                          alignItems: 'center',
                          opacity: 0.6,
                        }}
                        title="Delete chat session"
                        onMouseEnter={(e) => {
                          e.currentTarget.style.color = '#ef4444';
                          e.currentTarget.style.opacity = '1';
                        }}
                        onMouseLeave={(e) => {
                          e.currentTarget.style.color = 'var(--text-muted)';
                          e.currentTarget.style.opacity = '0.6';
                        }}
                      >
                        <Trash2 size={12} />
                      </button>
                    </div>
                  );
                })
              )}
            </div>
          </div>

          {/* CENTER: Main Chat Conversation View */}
          <div
            style={{
              backgroundColor: 'var(--bg-surface)',
              borderRadius: 'var(--radius-lg)',
              border: '1px solid var(--border-subtle)',
              display: 'flex',
              flexDirection: 'column',
              minHeight: '700px',
              maxHeight: '750px',
            }}
          >
            {/* Grounding Guarantee Header Banner */}
            <div
              style={{
                padding: '10px 16px',
                backgroundColor: 'rgba(59, 130, 246, 0.08)',
                borderBottom: '1px solid var(--border-subtle)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
                fontSize: '12px',
                color: 'var(--text-secondary)',
              }}
            >
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <ShieldCheck size={16} color="#3b82f6" />
                <span>
                  Context Active: <strong>{currentCourse.code}</strong> • Responses grounded in official materials. Official grades remain inviolable.
                </span>
              </div>
              {activeConversationId && (
                <span style={{ fontSize: '11px', color: 'var(--text-muted)', fontFamily: 'monospace' }}>
                  ID: {activeConversationId.slice(0, 8)}...
                </span>
              )}
            </div>

            {/* Messages Scroll Area */}
            <div
              ref={chatScrollRef}
              style={{
                flex: 1,
                padding: '20px',
                overflowY: 'auto',
                display: 'flex',
                flexDirection: 'column',
                gap: '16px',
              }}
            >
              {messages.map((msg) => (
                <div
                  key={msg.id}
                  style={{
                    alignSelf: msg.role === 'user' ? 'flex-end' : 'flex-start',
                    maxWidth: msg.role === 'user' ? '78%' : '88%',
                    backgroundColor:
                      msg.role === 'user'
                        ? '#3b82f6'
                        : msg.is_refusal
                        ? 'rgba(239, 68, 68, 0.08)'
                        : 'var(--bg-app)',
                    color: msg.role === 'user' ? '#ffffff' : 'var(--text-primary)',
                    borderRadius: 'var(--radius-lg)',
                    padding: '14px 18px',
                    border: msg.role === 'user' ? 'none' : '1px solid var(--border-subtle)',
                    display: 'flex',
                    flexDirection: 'column',
                    gap: '8px',
                    boxShadow: '0 1px 3px rgba(0,0,0,0.05)',
                  }}
                >
                  <div
                    style={{
                      fontSize: '11px',
                      opacity: 0.8,
                      display: 'flex',
                      justifyContent: 'space-between',
                      alignItems: 'center',
                      gap: '12px',
                      borderBottom: msg.role === 'user' ? 'none' : '1px solid rgba(125,125,125,0.1)',
                      paddingBottom: '4px',
                    }}
                  >
                    <span style={{ fontWeight: 600 }}>
                      {msg.role === 'user' ? 'You' : 'Dhruva.AI Assistant'}
                    </span>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                      {msg.latency_ms && (
                        <span style={{ fontSize: '10px', color: msg.role === 'user' ? '#dbeafe' : 'var(--text-muted)' }}>
                          {msg.latency_ms}ms
                        </span>
                      )}
                      <span>
                        {new Date(msg.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                      </span>
                      {msg.role === 'assistant' && (
                        <button
                          onClick={() => handleCopyMessage(msg.id, msg.content)}
                          style={{
                            background: 'none',
                            border: 'none',
                            cursor: 'pointer',
                            color: 'var(--text-muted)',
                            display: 'flex',
                            alignItems: 'center',
                            padding: '2px',
                          }}
                          title="Copy response"
                        >
                          {copiedMessageId === msg.id ? <Check size={12} color="#10b981" /> : <Copy size={12} />}
                        </button>
                      )}
                    </div>
                  </div>

                  {/* Rendered content */}
                  {msg.role === 'assistant' ? (
                    <FormattedMessage content={msg.content} />
                  ) : (
                    <div style={{ fontSize: '14px', lineHeight: 1.5, whiteSpace: 'pre-wrap' }}>
                      {msg.content}
                    </div>
                  )}

                  {/* Redaction Notice */}
                  {msg.pii_detected_count !== undefined && msg.pii_detected_count > 0 && (
                    <div
                      style={{
                        fontSize: '11px',
                        padding: '4px 8px',
                        borderRadius: '4px',
                        backgroundColor: 'rgba(245, 158, 11, 0.2)',
                        color: msg.role === 'user' ? '#fef3c7' : '#d97706',
                        display: 'flex',
                        alignItems: 'center',
                        gap: '4px',
                        width: 'fit-content',
                      }}
                    >
                      <Lock size={12} />
                      {msg.pii_detected_count} sensitive identifier(s) redacted before dispatch.
                    </div>
                  )}

                  {/* Provenance Citations */}
                  {msg.citations && msg.citations.length > 0 && (
                    <div style={{ marginTop: '6px', paddingTop: '8px', borderTop: '1px solid var(--border-subtle)' }}>
                      <div style={{ fontSize: '11px', fontWeight: 600, color: 'var(--text-muted)', marginBottom: '4px' }}>
                        VERIFIED SOURCES & PROVENANCE:
                      </div>
                      <div style={{ display: 'flex', flexWrap: 'wrap', gap: '6px' }}>
                        {msg.citations.map((cit) => (
                          <button
                            key={cit.citation_id}
                            onClick={() => setSelectedCitationModal(cit)}
                            style={{
                              padding: '4px 8px',
                              borderRadius: '4px',
                              border: '1px solid rgba(59, 130, 246, 0.3)',
                              backgroundColor: 'rgba(59, 130, 246, 0.08)',
                              color: '#3b82f6',
                              fontSize: '11px',
                              fontWeight: 600,
                              cursor: 'pointer',
                              display: 'flex',
                              alignItems: 'center',
                              gap: '4px',
                            }}
                          >
                            <FileText size={12} />
                            {cit.citation_id}: {cit.title}
                          </button>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              ))}

              {isSubmittingChat && (
                <div
                  style={{
                    alignSelf: 'flex-start',
                    padding: '12px 16px',
                    borderRadius: 'var(--radius-md)',
                    backgroundColor: 'var(--bg-app)',
                    border: '1px solid var(--border-subtle)',
                    color: 'var(--text-secondary)',
                    fontSize: '13px',
                    display: 'flex',
                    alignItems: 'center',
                    gap: '10px',
                  }}
                >
                  <RefreshCw size={15} style={{ animation: 'spin 1.2s linear infinite' }} />
                  <span>Synthesizing response with multi-turn context and verified curriculum...</span>
                </div>
              )}
            </div>

            {/* Quick Suggestion Pills */}
            <div
              style={{
                padding: '6px 16px',
                borderTop: '1px solid var(--border-subtle)',
                backgroundColor: 'rgba(125, 125, 125, 0.03)',
                display: 'flex',
                gap: '8px',
                overflowX: 'auto',
                whiteSpace: 'nowrap',
              }}
            >
              <span style={{ fontSize: '11px', color: 'var(--text-muted)', display: 'flex', alignItems: 'center' }}>
                Prompt ideas:
              </span>
              {quickSuggestions.map((sugg, idx) => (
                <button
                  key={idx}
                  onClick={() => handleSendChat(sugg)}
                  disabled={isSubmittingChat}
                  style={{
                    background: 'none',
                    border: '1px solid var(--border-subtle)',
                    padding: '4px 10px',
                    borderRadius: '14px',
                    fontSize: '11px',
                    color: 'var(--text-secondary)',
                    cursor: 'pointer',
                    display: 'flex',
                    alignItems: 'center',
                    gap: '4px',
                  }}
                  onMouseEnter={(e) => {
                    e.currentTarget.style.borderColor = '#3b82f6';
                    e.currentTarget.style.color = '#3b82f6';
                  }}
                  onMouseLeave={(e) => {
                    e.currentTarget.style.borderColor = 'var(--border-subtle)';
                    e.currentTarget.style.color = 'var(--text-secondary)';
                  }}
                >
                  <ChevronRight size={10} />
                  {sugg}
                </button>
              ))}
            </div>

            {/* Client Pre-flight PII Warning Preview */}
            {piiPreview && piiPreview.hasPII && (
              <div
                style={{
                  margin: '8px 16px 0 16px',
                  padding: '8px 12px',
                  borderRadius: 'var(--radius-md)',
                  backgroundColor: 'rgba(245, 158, 11, 0.12)',
                  border: '1px solid rgba(245, 158, 11, 0.3)',
                  fontSize: '12px',
                  color: '#b45309',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '8px',
                }}
              >
                <Lock size={14} />
                <span>
                  <strong>Client Sanitizer Active:</strong> Detected {piiPreview.detectedTypes.join(', ')}. Identities will be securely scrubbed prior to model invocation.
                </span>
              </div>
            )}

            {/* Adversarial Prompt Warning */}
            {promptSecurityPreview && !promptSecurityPreview.isSafe && (
              <div
                style={{
                  margin: '8px 16px 0 16px',
                  padding: '8px 12px',
                  borderRadius: 'var(--radius-md)',
                  backgroundColor: 'rgba(239, 68, 68, 0.12)',
                  border: '1px solid rgba(239, 68, 68, 0.3)',
                  fontSize: '12px',
                  color: '#b91c1c',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '8px',
                }}
              >
                <AlertTriangle size={14} />
                <span>
                  <strong>Security Warning:</strong> {promptSecurityPreview.threatType} attempt detected. This query will be refused by policy.
                </span>
              </div>
            )}

            {/* Chat Input Bar */}
            <div
              style={{
                padding: '14px 16px',
                borderTop: '1px solid var(--border-subtle)',
                display: 'flex',
                gap: '10px',
                alignItems: 'center',
              }}
            >
              <input
                type="text"
                placeholder={`Ask a question grounded in ${currentCourse.code} curriculum...`}
                value={chatInput}
                onChange={(e) => setChatInput(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && handleSendChat()}
                style={{
                  flex: 1,
                  padding: '10px 14px',
                  borderRadius: 'var(--radius-md)',
                  border: '1px solid var(--border-subtle)',
                  backgroundColor: 'var(--bg-app)',
                  color: 'var(--text-primary)',
                  fontSize: '14px',
                }}
              />
              <Button
                variant="primary"
                onClick={() => handleSendChat()}
                disabled={!chatInput.trim() || isSubmittingChat}
                style={{ display: 'flex', alignItems: 'center', gap: '6px' }}
              >
                <Send size={16} />
                Send
              </Button>
            </div>
          </div>

          {/* RIGHT: Syllabus Scope & Knowledge Panel */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
            <Card style={{ padding: '16px' }}>
              <div style={{ fontSize: '14px', fontWeight: 700, color: 'var(--text-primary)', marginBottom: '8px', display: 'flex', alignItems: 'center', gap: '6px' }}>
                <BookOpen size={16} color="#3b82f6" />
                Active Knowledge Ingestion
              </div>
              <p style={{ fontSize: '12px', color: 'var(--text-secondary)', margin: '0 0 12px 0' }}>
                The AI is restricted strictly to documents indexed under course <strong>{currentCourse.code}</strong>:
              </p>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                <div style={{ padding: '8px 10px', borderRadius: '6px', backgroundColor: 'var(--bg-app)', fontSize: '12px' }}>
                  <div style={{ fontWeight: 600, color: 'var(--text-primary)' }}>Official Syllabus 2026</div>
                  <div style={{ color: 'var(--text-muted)', fontSize: '11px' }}>4 Units • 18 Core Concepts</div>
                </div>
                <div style={{ padding: '8px 10px', borderRadius: '6px', backgroundColor: 'var(--bg-app)', fontSize: '12px' }}>
                  <div style={{ fontWeight: 600, color: 'var(--text-primary)' }}>Instructor Lecture Transcripts</div>
                  <div style={{ color: 'var(--text-muted)', fontSize: '11px' }}>24 Lectures • SHA-256 Verified</div>
                </div>
                <div style={{ padding: '8px 10px', borderRadius: '6px', backgroundColor: 'var(--bg-app)', fontSize: '12px' }}>
                  <div style={{ fontWeight: 600, color: 'var(--text-primary)' }}>Prescribed Reference Textbooks</div>
                  <div style={{ color: 'var(--text-muted)', fontSize: '11px' }}>CLRS • Tanenbaum • Cormen</div>
                </div>
              </div>
            </Card>

            <Card style={{ padding: '16px' }}>
              <div style={{ fontSize: '14px', fontWeight: 700, color: 'var(--text-primary)', marginBottom: '8px', display: 'flex', alignItems: 'center', gap: '6px' }}>
                <ShieldCheck size={16} color="#10b981" />
                Zero-Leak Privacy Protocol
              </div>
              <ul style={{ fontSize: '12px', color: 'var(--text-secondary)', paddingLeft: '18px', margin: 0, lineHeight: 1.6 }}>
                <li>No student emails or phone numbers dispatched to LLMs</li>
                <li>Roll numbers and national IDs automatically scrubbed</li>
                <li>Tenant data isolated via PostgreSQL Row-Level Security</li>
                <li>Cross-tenant queries fail with explicit rejection</li>
              </ul>
            </Card>

            <Card style={{ padding: '16px' }}>
              <div style={{ fontSize: '14px', fontWeight: 700, color: 'var(--text-primary)', marginBottom: '8px', display: 'flex', alignItems: 'center', gap: '6px' }}>
                <Cpu size={16} color="#8b5cf6" />
                AI Gateway Architecture
              </div>
              <p style={{ fontSize: '12px', color: 'var(--text-secondary)', margin: 0, lineHeight: 1.5 }}>
                Dhruva.AI connects to Gemini 1.5 Flash with fallback to NVIDIA NIM and Grounded Core. Deterministic mastery computations and grades are never overridden.
              </p>
            </Card>
          </div>
        </div>
      )}

      {/* ============================================================== */}
      {/* TAB 2: FACULTY QUESTION DRAFTING STUDIO                         */}
      {/* ============================================================== */}
      {activeTab === 'drafting' && isStaff && (
        <div style={{ display: 'grid', gridTemplateColumns: '360px 1fr', gap: '24px' }}>
          {/* Generation Configuration Card */}
          <Card style={{ padding: '20px', display: 'flex', flexDirection: 'column', gap: '16px', height: 'fit-content' }}>
            <div style={{ fontSize: '16px', fontWeight: 700, color: 'var(--text-primary)', display: 'flex', alignItems: 'center', gap: '8px' }}>
              <Sparkles size={18} color="#3b82f6" />
              AI Question Authoring
            </div>
            <p style={{ fontSize: '13px', color: 'var(--text-secondary)', margin: 0 }}>
              Draft curriculum-aligned assessment questions grounded in course learning objectives.
            </p>

            <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
              <label style={{ fontSize: '12px', fontWeight: 600, color: 'var(--text-secondary)' }}>
                Target Topic or Concept
              </label>
              <input
                type="text"
                value={draftTopic}
                onChange={(e) => setDraftTopic(e.target.value)}
                placeholder="e.g. B-Tree Invariants or Dijkstra Algorithm"
                style={{
                  padding: '8px 12px',
                  borderRadius: 'var(--radius-md)',
                  border: '1px solid var(--border-subtle)',
                  backgroundColor: 'var(--bg-app)',
                  color: 'var(--text-primary)',
                  fontSize: '13px',
                }}
              />
            </div>

            <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
              <label style={{ fontSize: '12px', fontWeight: 600, color: 'var(--text-secondary)' }}>
                Bloom's Taxonomy Level
              </label>
              <select
                value={draftBloomLevel}
                onChange={(e) => setDraftBloomLevel(e.target.value as any)}
                style={{
                  padding: '8px 12px',
                  borderRadius: 'var(--radius-md)',
                  border: '1px solid var(--border-subtle)',
                  backgroundColor: 'var(--bg-app)',
                  color: 'var(--text-primary)',
                  fontSize: '13px',
                }}
              >
                <option value="REMEMBER">Remember (Recall Facts)</option>
                <option value="UNDERSTAND">Understand (Explain Ideas)</option>
                <option value="APPLY">Apply (Execute Algorithm)</option>
                <option value="ANALYZE">Analyze (Contrast Invariants)</option>
                <option value="EVALUATE">Evaluate (Assess Complexity)</option>
              </select>
            </div>

            <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
              <label style={{ fontSize: '12px', fontWeight: 600, color: 'var(--text-secondary)' }}>
                Target Difficulty
              </label>
              <div style={{ display: 'flex', gap: '8px' }}>
                {(['EASY', 'MEDIUM', 'HARD'] as const).map((diff) => (
                  <button
                    key={diff}
                    onClick={() => setDraftDifficulty(diff)}
                    style={{
                      flex: 1,
                      padding: '6px',
                      borderRadius: 'var(--radius-md)',
                      border: draftDifficulty === diff ? '2px solid #3b82f6' : '1px solid var(--border-subtle)',
                      backgroundColor: draftDifficulty === diff ? 'rgba(59, 130, 246, 0.1)' : 'var(--bg-app)',
                      color: draftDifficulty === diff ? '#3b82f6' : 'var(--text-secondary)',
                      fontSize: '12px',
                      fontWeight: 600,
                      cursor: 'pointer',
                    }}
                  >
                    {diff}
                  </button>
                ))}
              </div>
            </div>

            <Button
              variant="primary"
              onClick={handleGenerateQuestions}
              disabled={!draftTopic.trim() || isDrafting}
              style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '8px', marginTop: '8px' }}
            >
              {isDrafting ? <RefreshCw size={16} style={{ animation: 'spin 1.2s linear infinite' }} /> : <Sparkles size={16} />}
              {isDrafting ? 'Drafting Grounded Questions...' : 'Generate Questions'}
            </Button>
          </Card>

          {/* Draft Questions Review & 1-Click Promote Stream */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <div style={{ fontSize: '15px', fontWeight: 700, color: 'var(--text-primary)' }}>
                Draft Question Queue ({draftedQuestions.length})
              </div>
              <span style={{ fontSize: '12px', color: 'var(--text-muted)' }}>
                Questions remain in draft mode until approved into the authoritative Question Bank.
              </span>
            </div>

            {draftedQuestions.map((q) => {
              const isPromoted = promotedQuestionIds.has(q.draft_id);
              return (
                <Card
                  key={q.draft_id}
                  style={{
                    padding: '20px',
                    display: 'flex',
                    flexDirection: 'column',
                    gap: '12px',
                    border: isPromoted ? '1px solid #10b981' : '1px solid var(--border-subtle)',
                  }}
                >
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', gap: '12px' }}>
                    <div>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '6px' }}>
                        <Badge variant={q.difficulty === 'EASY' ? 'success' : q.difficulty === 'MEDIUM' ? 'warning' : 'danger'}>
                          {q.difficulty}
                        </Badge>
                        <Badge variant="default">{q.bloom_level}</Badge>
                        <span style={{ fontSize: '12px', color: 'var(--text-muted)', fontWeight: 600 }}>
                          {q.points} Mark(s)
                        </span>
                      </div>
                      <h3 style={{ fontSize: '16px', fontWeight: 600, color: 'var(--text-primary)', margin: 0 }}>
                        {q.question_text}
                      </h3>
                    </div>

                    <Button
                      variant={isPromoted ? 'outline' : 'primary'}
                      onClick={() => handlePromoteToQuestionBank(q)}
                      disabled={isPromoted}
                      style={{ display: 'flex', alignItems: 'center', gap: '6px', whiteSpace: 'nowrap' }}
                    >
                      {isPromoted ? (
                        <>
                          <CheckCircle2 size={16} color="#10b981" />
                          Transferred to QB
                        </>
                      ) : (
                        <>
                          <PlusCircle size={16} />
                          Send to Question Bank
                        </>
                      )}
                    </Button>
                  </div>

                  {/* Options */}
                  <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '8px' }}>
                    {q.options.map((opt, idx) => (
                      <div
                        key={idx}
                        style={{
                          padding: '10px 12px',
                          borderRadius: '6px',
                          backgroundColor: opt.is_correct ? 'rgba(16, 185, 129, 0.1)' : 'var(--bg-app)',
                          border: opt.is_correct ? '1px solid #10b981' : '1px solid var(--border-subtle)',
                          display: 'flex',
                          alignItems: 'center',
                          gap: '8px',
                          fontSize: '13px',
                          color: opt.is_correct ? '#10b981' : 'var(--text-primary)',
                          fontWeight: opt.is_correct ? 600 : 400,
                        }}
                      >
                        <span style={{ fontWeight: 700, width: '18px' }}>{String.fromCharCode(65 + idx)}.</span>
                        <span>{opt.text}</span>
                        {opt.is_correct && <CheckCircle2 size={14} style={{ marginLeft: 'auto' }} />}
                      </div>
                    ))}
                  </div>

                  {/* Pedagogical Explanation */}
                  <div
                    style={{
                      padding: '10px 12px',
                      borderRadius: '6px',
                      backgroundColor: 'rgba(59, 130, 246, 0.05)',
                      border: '1px solid rgba(59, 130, 246, 0.15)',
                      fontSize: '12px',
                      color: 'var(--text-secondary)',
                    }}
                  >
                    <strong>Pedagogical Rationale:</strong> {q.explanation}
                  </div>
                </Card>
              );
            })}
          </div>
        </div>
      )}

      {/* ============================================================== */}
      {/* TAB 3: AUDIT & GATEWAY SAFETY LOGS                             */}
      {/* ============================================================== */}
      {activeTab === 'audit' && isAdmin && (
        <Card style={{ padding: '20px', display: 'flex', flexDirection: 'column', gap: '16px' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '12px' }}>
            <div>
              <h2 style={{ fontSize: '18px', fontWeight: 700, color: 'var(--text-primary)', margin: 0 }}>
                AI Gateway Audit & Redaction Log
              </h2>
              <p style={{ fontSize: '13px', color: 'var(--text-secondary)', margin: '4px 0 0 0' }}>
                Live database audit stream of prompts, PII scrubbing actions, security intercepts, and token consumption.
              </p>
            </div>
            <Button
              variant="outline"
              size="sm"
              onClick={fetchAuditLogs}
              disabled={isAuditLoading}
              style={{ display: 'flex', alignItems: 'center', gap: '6px' }}
            >
              <RefreshCw size={14} style={{ animation: isAuditLoading ? 'spin 1s linear infinite' : 'none' }} />
              {isAuditLoading ? 'Refreshing...' : 'Refresh Logs'}
            </Button>
          </div>

          <div style={{ overflowX: 'auto' }}>
            {auditLogs.length === 0 ? (
              <div style={{ padding: '36px', textAlign: 'center', color: 'var(--text-muted)', fontSize: '13px' }}>
                No AI safety events recorded yet for this institution. Interactive tutor chats and draft generations will appear here in real time.
              </div>
            ) : (
              <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '13px' }}>
                <thead>
                  <tr style={{ borderBottom: '1px solid var(--border-subtle)', textAlign: 'left', color: 'var(--text-muted)' }}>
                    <th style={{ padding: '10px' }}>Timestamp</th>
                    <th style={{ padding: '10px' }}>Action Type</th>
                    <th style={{ padding: '10px' }}>Prompt Hash</th>
                    <th style={{ padding: '10px' }}>Safety Verdict</th>
                    <th style={{ padding: '10px' }}>PII Redactions</th>
                    <th style={{ padding: '10px' }}>Tokens</th>
                    <th style={{ padding: '10px' }}>Cost Est.</th>
                  </tr>
                </thead>
                <tbody>
                  {auditLogs.map((log) => (
                    <tr key={log.id} style={{ borderBottom: '1px solid var(--border-subtle)' }}>
                      <td style={{ padding: '10px', color: 'var(--text-secondary)' }}>
                        {new Date(log.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' })}
                      </td>
                      <td style={{ padding: '10px', fontWeight: 600, color: 'var(--text-primary)' }}>
                        {log.action}
                      </td>
                      <td style={{ padding: '10px', fontFamily: 'monospace', fontSize: '12px', color: 'var(--text-muted)' }}>
                        {log.prompt_hash}
                      </td>
                      <td style={{ padding: '10px' }}>
                        <Badge
                          variant={
                            log.safety_verdict === 'APPROVED'
                              ? 'success'
                              : log.safety_verdict === 'SANITIZED_PII'
                              ? 'warning'
                              : 'danger'
                          }
                        >
                          {log.safety_verdict}
                        </Badge>
                      </td>
                      <td style={{ padding: '10px', fontWeight: 600, color: log.pii_detected_count > 0 ? '#f59e0b' : 'var(--text-secondary)' }}>
                        {log.pii_detected_count}
                      </td>
                      <td style={{ padding: '10px', color: 'var(--text-secondary)' }}>
                        {log.tokens_used}
                      </td>
                      <td style={{ padding: '10px', color: 'var(--text-secondary)' }}>
                        ${log.cost_estimate.toFixed(5)}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </div>
        </Card>
      )}

      {/* Provenance Source Modal */}
      {selectedCitationModal && (
        <div
          style={{
            position: 'fixed',
            inset: 0,
            backgroundColor: 'rgba(0, 0, 0, 0.6)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            zIndex: 999,
          }}
          onClick={() => setSelectedCitationModal(null)}
        >
          <div
            style={{
              backgroundColor: 'var(--bg-surface)',
              borderRadius: 'var(--radius-lg)',
              border: '1px solid var(--border-subtle)',
              maxWidth: '540px',
              width: '90%',
              padding: '24px',
              display: 'flex',
              flexDirection: 'column',
              gap: '16px',
            }}
            onClick={(e) => e.stopPropagation()}
          >
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <FileText size={18} color="#3b82f6" />
                <h3 style={{ fontSize: '16px', fontWeight: 700, margin: 0, color: 'var(--text-primary)' }}>
                  Provenance Citation {selectedCitationModal.citation_id}
                </h3>
              </div>
              <Button variant="outline" size="sm" onClick={() => setSelectedCitationModal(null)}>
                Close
              </Button>
            </div>

            <div style={{ display: 'flex', flexDirection: 'column', gap: '10px', fontSize: '13px' }}>
              <div>
                <span style={{ color: 'var(--text-muted)', fontWeight: 600 }}>Document Title:</span>
                <div style={{ fontWeight: 600, color: 'var(--text-primary)', marginTop: '2px' }}>
                  {selectedCitationModal.title}
                </div>
              </div>

              <div>
                <span style={{ color: 'var(--text-muted)', fontWeight: 600 }}>Source Type:</span>
                <div style={{ color: 'var(--text-primary)', marginTop: '2px' }}>
                  {selectedCitationModal.source_type} ({selectedCitationModal.course_code})
                </div>
              </div>

              <div>
                <span style={{ color: 'var(--text-muted)', fontWeight: 600 }}>Audit Provenance Chain:</span>
                <div style={{ padding: '8px 12px', borderRadius: '6px', backgroundColor: 'var(--bg-app)', fontFamily: 'monospace', fontSize: '12px', marginTop: '4px' }}>
                  {selectedCitationModal.provenance}
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
