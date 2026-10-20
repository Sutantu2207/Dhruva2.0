'use client';

import React, { useState, useMemo } from 'react';
import { useAuth } from '@/lib/auth/AuthContext';
import { Badge } from '@/components/ui/Badge';
import { Button } from '@/components/ui/Button';
import { Card } from '@/components/ui/Card';
import { Input } from '@/components/ui/Input';
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
  Search,
  Eye,
  RefreshCw,
  HelpCircle,
  Cpu,
} from 'lucide-react';
import {
  CitationItem,
  TutorChatMessage,
  DraftQuestionItem,
  AIAuditLog,
} from '@/types/ai';
import {
  detectAndSanitizePII,
  checkPromptSecurity,
  transformDraftToQuestionAdmin,
  formatCitationBadge,
} from '@/lib/ai/guardrails';

const DEMO_COURSES = [
  { id: 'c-cs201', code: 'CS201', name: 'Data Structures & Algorithms', department: 'Computer Science' },
  { id: 'c-cs301', code: 'CS301', name: 'Database Management Systems', department: 'Computer Science' },
  { id: 'c-ec202', code: 'EC202', name: 'Digital Signal Processing', department: 'Electronics' },
];

export default function AIGatewayWorkspace() {
  const { user } = useAuth();
  const primaryRole = user?.roles[0] || 'STUDENT';
  const isStaff = ['SUPER_ADMIN', 'INSTITUTION_ADMIN', 'HOD', 'FACULTY'].includes(primaryRole);
  const isAdmin = ['SUPER_ADMIN', 'INSTITUTION_ADMIN', 'HOD'].includes(primaryRole);

  // Active Tab: 'tutor' | 'drafting' | 'audit'
  const [activeTab, setActiveTab] = useState<'tutor' | 'drafting' | 'audit'>('tutor');

  // Selected Course
  const [selectedCourseId, setSelectedCourseId] = useState<string>(DEMO_COURSES[0].id);
  const currentCourse = useMemo(
    () => DEMO_COURSES.find((c) => c.id === selectedCourseId) || DEMO_COURSES[0],
    [selectedCourseId]
  );

  // -------------------------------------------------------------
  // TAB 1: TUTOR CHAT STATE
  // -------------------------------------------------------------
  const [chatInput, setChatInput] = useState<string>('');
  const [isSubmittingChat, setIsSubmittingChat] = useState<boolean>(false);
  const [selectedCitationModal, setSelectedCitationModal] = useState<CitationItem | null>(null);

  const [messages, setMessages] = useState<TutorChatMessage[]>([
    {
      id: 'msg-init-1',
      role: 'assistant',
      content: `Hello! I am your Dhruva.AI Grounded Study Assistant for **${currentCourse.code}: ${currentCourse.name}**. Every answer I provide is cross-referenced with your department's approved syllabus, lecture materials, and textbook references with verifiable provenance. How can I assist your learning today?`,
      citations: [
        {
          citation_id: 'CIT-01',
          source_type: 'SYLLABUS_MODULE',
          entity_id: 'mod-trees-01',
          title: 'Module 3: Balanced Search Trees & AVL Invariants',
          course_code: currentCourse.code,
          provenance: 'Approved Syllabus 2026 / Academic Council Ref AC-2026-CS201-P3',
        },
      ],
      model_name: 'dhruva-guardrailed-gateway-v2',
      pii_detected_count: 0,
      latency_ms: 124,
      is_refusal: false,
      created_at: new Date(Date.now() - 1000 * 60 * 10).toISOString(),
    },
  ]);

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

  const handleSendChat = () => {
    if (!chatInput.trim() || isSubmittingChat) return;

    const securityCheck = checkPromptSecurity(chatInput);
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
          content: chatInput,
          created_at: new Date().toISOString(),
        },
        refusalMsg,
      ]);
      setChatInput('');
      return;
    }

    const pii = detectAndSanitizePII(chatInput);
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

    // Simulate grounded retrieval response with citations
    setTimeout(() => {
      const botResponse: TutorChatMessage = {
        id: `msg-bot-${Date.now()}`,
        role: 'assistant',
        content: `In an AVL Tree, self-balancing is achieved through rotational invariants. Specifically, for every node $u$, the balance factor is defined as $\\text{height}(u.\\text{left}) - \\text{height}(u.\\text{right}) \\in \\{-1, 0, 1\\}$. Whenever an insertion causes this factor to become $\\pm 2$, a single or double rotation restores log-time search, insert, and delete guarantees.`,
        citations: [
          {
            citation_id: 'CIT-02',
            source_type: 'COURSE_NOTE',
            entity_id: 'lec-avl-rotations',
            title: 'Lecture 12: AVL Trees & Rotational Balance Restorations',
            course_code: currentCourse.code,
            provenance: 'Approved Handout: Prof. Sharma / Dept. of CSE / Page 4',
          },
          {
            citation_id: 'CIT-03',
            source_type: 'TEXTBOOK_CHAPTER',
            entity_id: 'tb-clrs-ch13',
            title: 'CLRS Chapter 13: Red-Black & Height-Balanced Search Trees',
            course_code: currentCourse.code,
            provenance: 'Prescribed Text / Section 13.2 Rotations',
          },
        ],
        model_name: 'dhruva-guardrailed-gateway-v2',
        pii_detected_count: pii.redactionCount,
        latency_ms: 188,
        is_refusal: false,
        created_at: new Date().toISOString(),
      };
      setMessages((prev) => [...prev, botResponse]);
      setIsSubmittingChat(false);
    }, 700);
  };

  // -------------------------------------------------------------
  // TAB 2: FACULTY QUESTION DRAFTING STATE
  // -------------------------------------------------------------
  const [draftTopic, setDraftTopic] = useState<string>('AVL Tree Rotations and Height Bounds');
  const [draftDifficulty, setDraftDifficulty] = useState<'EASY' | 'MEDIUM' | 'HARD'>('MEDIUM');
  const [draftBloomLevel, setDraftBloomLevel] = useState<'REMEMBER' | 'UNDERSTAND' | 'APPLY' | 'ANALYZE' | 'EVALUATE'>('APPLY');
  const [draftNumQuestions, setDraftNumQuestions] = useState<number>(2);
  const [isDrafting, setIsDrafting] = useState<boolean>(false);
  const [draftedQuestions, setDraftedQuestions] = useState<DraftQuestionItem[]>([
    {
      draft_id: 'd-101',
      title: 'AVL Node Insertion Rebalancing Condition',
      question_text: 'What is the maximum permissible balance factor in an AVL Tree before a rotational rebalance is triggered?',
      question_type: 'MCQ',
      difficulty: 'MEDIUM',
      bloom_level: 'APPLY',
      points: 2.0,
      options: [
        { text: 'Absolute difference of 0', is_correct: false },
        { text: 'Absolute difference of 1', is_correct: true },
        { text: 'Absolute difference of 2', is_correct: false },
        { text: 'Unbounded difference', is_correct: false },
      ],
      explanation: 'In an AVL tree, the balance factor (height(left) - height(right)) must stay within {-1, 0, +1}. An absolute value of 2 necessitates immediate rotation.',
    },
    {
      draft_id: 'd-102',
      title: 'Double Rotation Sequence Identification',
      question_text: 'Given an insertion into the right subtree of the left child (Left-Right case), which sequence of rotations restores the AVL property?',
      question_type: 'MCQ',
      difficulty: 'HARD',
      bloom_level: 'ANALYZE',
      points: 3.0,
      options: [
        { text: 'Single Right Rotation at root', is_correct: false },
        { text: 'Left Rotation at left child, followed by Right Rotation at root', is_correct: true },
        { text: 'Right Rotation at left child, followed by Left Rotation at root', is_correct: false },
        { text: 'Double Left Rotation at root', is_correct: false },
      ],
      explanation: 'The Left-Right heavy case requires an initial Left Rotation on the child to convert it into a pure Left-Left case, followed by a Right Rotation on the parent.',
    },
  ]);

  const [promotedQuestionIds, setPromotedQuestionIds] = useState<Set<string>>(new Set());
  const [draftSuccessToast, setDraftSuccessToast] = useState<string | null>(null);

  const handleGenerateQuestions = () => {
    if (!draftTopic.trim() || isDrafting) return;
    setIsDrafting(true);

    setTimeout(() => {
      const newItems: DraftQuestionItem[] = [
        {
          draft_id: `d-${Date.now()}-1`,
          title: `${draftTopic} — Fundamental Concepts`,
          question_text: `Which algorithmic property guarantees logarithmic height in ${draftTopic}?`,
          question_type: 'MCQ',
          difficulty: draftDifficulty,
          bloom_level: draftBloomLevel,
          points: draftDifficulty === 'EASY' ? 1.0 : draftDifficulty === 'MEDIUM' ? 2.0 : 3.0,
          options: [
            { text: 'Strict height balance condition maintained during mutating operations', is_correct: true },
            { text: 'Randomized pivot selection during partition steps', is_correct: false },
            { text: 'Greedy selection of optimal sub-structures', is_correct: false },
            { text: 'Linear probe hashing resolution', is_correct: false },
          ],
          explanation: 'Logarithmic height is guaranteed by maintaining the bounded height invariants after every mutation.',
        },
      ];
      setDraftedQuestions((prev) => [...newItems, ...prev]);
      setIsDrafting(false);
      setDraftSuccessToast(`Generated ${newItems.length} grounded draft questions for ${draftTopic}`);
      setTimeout(() => setDraftSuccessToast(null), 4000);
    }, 800);
  };

  const handlePromoteToQuestionBank = (draft: DraftQuestionItem) => {
    // 1-Click promotion to Question Bank
    const transformed = transformDraftToQuestionAdmin(
      draft,
      user?.institution_id || 'inst-iit-bombay',
      'qb-ds-algo-01',
      selectedCourseId
    );

    setPromotedQuestionIds((prev) => new Set(prev).add(draft.draft_id));
    setDraftSuccessToast(
      `✓ Question "${draft.title}" successfully transferred to Question Bank (Draft ID: ${transformed.id})!`
    );
    setTimeout(() => setDraftSuccessToast(null), 5000);
  };

  // -------------------------------------------------------------
  // TAB 3: AUDIT & GATEWAY SAFETY LOGS STATE
  // -------------------------------------------------------------
  const [auditLogs] = useState<AIAuditLog[]>([
    {
      id: 'log-801',
      institution_id: 'inst-iit-bombay',
      user_id: user?.id || 'usr-student-01',
      action: 'TUTOR_CHAT',
      prompt_hash: 'a7b9c1d3e5f20984',
      pii_detected_count: 0,
      safety_verdict: 'APPROVED',
      tokens_used: 342,
      cost_estimate: 0.00068,
      metadata_json: { course_code: 'CS201', latency_ms: 124 },
      created_at: new Date(Date.now() - 1000 * 60 * 5).toISOString(),
    },
    {
      id: 'log-802',
      institution_id: 'inst-iit-bombay',
      user_id: user?.id || 'usr-student-01',
      action: 'BLOCKED_PROMPT',
      prompt_hash: 'f948c21a084c7e2b',
      pii_detected_count: 0,
      safety_verdict: 'BLOCKED_INJECTION',
      tokens_used: 0,
      cost_estimate: 0.0,
      metadata_json: { threat: 'INSTRUCTION_OVERRIDE', blocked_at: 'edge_guard' },
      created_at: new Date(Date.now() - 1000 * 60 * 18).toISOString(),
    },
    {
      id: 'log-803',
      institution_id: 'inst-iit-bombay',
      user_id: user?.id || 'usr-student-01',
      action: 'TUTOR_CHAT',
      prompt_hash: 'c8273b1940e729a1',
      pii_detected_count: 1,
      safety_verdict: 'SANITIZED_PII',
      tokens_used: 410,
      cost_estimate: 0.00082,
      metadata_json: { redacted_types: ['STUDENT_ROLL_NUMBER'] },
      created_at: new Date(Date.now() - 1000 * 60 * 42).toISOString(),
    },
    {
      id: 'log-804',
      institution_id: 'inst-iit-bombay',
      user_id: user?.id || 'usr-faculty-01',
      action: 'DRAFT_QUESTIONS',
      prompt_hash: '772b9a84ec01289f',
      pii_detected_count: 0,
      safety_verdict: 'APPROVED',
      tokens_used: 685,
      cost_estimate: 0.00137,
      metadata_json: { topic: 'AVL Rotations', num_questions: 2 },
      created_at: new Date(Date.now() - 1000 * 60 * 120).toISOString(),
    },
  ]);

  return (
    <div style={{ maxWidth: '1400px', margin: '0 auto', padding: '24px 16px', display: 'flex', flexDirection: 'column', gap: '24px' }}>
      {/* Page Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: '16px' }}>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <div
              style={{
                width: '36px',
                height: '36px',
                borderRadius: '8px',
                backgroundColor: 'rgba(59, 130, 246, 0.1)',
                color: '#3b82f6',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
              }}
            >
              <Sparkles size={20} />
            </div>
            <h1 style={{ fontSize: '24px', fontWeight: 700, color: 'var(--text-primary)', margin: 0 }}>
              Guardrailed AI Gateway & Retrieval
            </h1>
            <Badge variant="default">Phase 9</Badge>
          </div>
          <p style={{ margin: '6px 0 0 0', fontSize: '14px', color: 'var(--text-secondary)' }}>
            Zero-leak grounded student tutoring and faculty question drafting powered by pgvector semantic retrieval and PII redaction.
          </p>
        </div>

        {/* Status Indicators */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px', flexWrap: 'wrap' }}>
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
            Tenant Isolated (RLS)
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
            Zero-PII Egress Active
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
            Active Course Scope:
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
            {DEMO_COURSES.map((course) => (
              <option key={course.id} value={course.id}>
                {course.code}: {course.name} ({course.department})
              </option>
            ))}
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
            Student Grounded Tutor
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
      {/* TAB 1: STUDENT GROUNDED AI TUTOR                                */}
      {/* ============================================================== */}
      {activeTab === 'tutor' && (
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 340px', gap: '20px' }}>
          {/* Main Chat Thread */}
          <div
            style={{
              backgroundColor: 'var(--bg-surface)',
              borderRadius: 'var(--radius-lg)',
              border: '1px solid var(--border-subtle)',
              display: 'flex',
              flexDirection: 'column',
              minHeight: '620px',
            }}
          >
            {/* Grounding Guarantee Banner */}
            <div
              style={{
                padding: '10px 16px',
                backgroundColor: 'rgba(59, 130, 246, 0.08)',
                borderBottom: '1px solid var(--border-subtle)',
                display: 'flex',
                alignItems: 'center',
                gap: '8px',
                fontSize: '12px',
                color: 'var(--text-secondary)',
              }}
            >
              <ShieldCheck size={16} color="#3b82f6" />
              <span>
                <strong>Grounding Guarantee:</strong> Responses are grounded exclusively in authorized <strong>{currentCourse.code}</strong> course documents. AI outputs do not alter official grades or academic records.
              </span>
            </div>

            {/* Messages Scroll Area */}
            <div style={{ flex: 1, padding: '20px', overflowY: 'auto', display: 'flex', flexDirection: 'column', gap: '16px' }}>
              {messages.map((msg) => (
                <div
                  key={msg.id}
                  style={{
                    alignSelf: msg.role === 'user' ? 'flex-end' : 'flex-start',
                    maxWidth: '82%',
                    backgroundColor:
                      msg.role === 'user'
                        ? '#3b82f6'
                        : msg.is_refusal
                        ? 'rgba(239, 68, 68, 0.1)'
                        : 'var(--bg-app)',
                    color: msg.role === 'user' ? '#ffffff' : 'var(--text-primary)',
                    borderRadius: 'var(--radius-lg)',
                    padding: '14px 18px',
                    border: msg.role === 'user' ? 'none' : '1px solid var(--border-subtle)',
                    display: 'flex',
                    flexDirection: 'column',
                    gap: '8px',
                  }}
                >
                  <div style={{ fontSize: '11px', opacity: 0.8, display: 'flex', justifyContent: 'space-between', gap: '12px' }}>
                    <span>{msg.role === 'user' ? 'You (Verified Student)' : 'Dhruva.AI Grounded Assistant'}</span>
                    <span>{new Date(msg.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</span>
                  </div>

                  <div style={{ fontSize: '14px', lineHeight: 1.5, whiteSpace: 'pre-wrap' }}>
                    {msg.content}
                  </div>

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
                    padding: '10px 14px',
                    borderRadius: 'var(--radius-md)',
                    backgroundColor: 'var(--bg-app)',
                    color: 'var(--text-secondary)',
                    fontSize: '13px',
                    display: 'flex',
                    alignItems: 'center',
                    gap: '8px',
                  }}
                >
                  <RefreshCw size={14} className="animate-spin" />
                  Retrieving grounded course documents & synthesizing answer...
                </div>
              )}
            </div>

            {/* Client Pre-flight PII Warning Preview */}
            {piiPreview && piiPreview.hasPII && (
              <div
                style={{
                  margin: '0 16px 8px 16px',
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
                  margin: '0 16px 8px 16px',
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
                padding: '16px',
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
                onClick={handleSendChat}
                disabled={!chatInput.trim() || isSubmittingChat}
                style={{ display: 'flex', alignItems: 'center', gap: '6px' }}
              >
                <Send size={16} />
                Send
              </Button>
            </div>
          </div>

          {/* Sidebar Context & Provenance Panel */}
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
              {isDrafting ? <RefreshCw size={16} className="animate-spin" /> : <Sparkles size={16} />}
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

                    {/* 1-Click Send to Question Bank Button */}
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
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <div>
              <h2 style={{ fontSize: '18px', fontWeight: 700, color: 'var(--text-primary)', margin: 0 }}>
                AI Gateway Audit & Redaction Log
              </h2>
              <p style={{ fontSize: '13px', color: 'var(--text-secondary)', margin: '4px 0 0 0' }}>
                Complete immutable record of prompts, PII scrubbing actions, prompt injection blocks, and token consumption.
              </p>
            </div>
          </div>

          <div style={{ overflowX: 'auto' }}>
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
