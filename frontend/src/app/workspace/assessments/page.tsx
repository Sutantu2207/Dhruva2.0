'use client';

import React, { useEffect, useState, useMemo } from 'react';
import { useAuth } from '@/lib/auth/AuthContext';
import { api, ApiError } from '@/lib/api/client';
import {
  QuestionBank,
  QuestionAdmin,
  Assessment,
  AssessmentStudentDetail,
  Submission,
  AssessmentResult,
  QuestionType,
  AssessmentType,
  DifficultyLevel,
} from '@/types/assessment';
import { Course } from '@/types/academic';
import { PageHeader } from '@/components/ui/PageHeader';
import { Button } from '@/components/ui/Button';
import { Badge } from '@/components/ui/Badge';
import { EmptyState } from '@/components/ui/EmptyState';
import { ErrorState } from '@/components/ui/ErrorState';
import { Dialog } from '@/components/ui/Dialog';
import { Input } from '@/components/ui/Input';
import { Select } from '@/components/ui/Select';
import { Alert } from '@/components/ui/Alert';

export default function AssessmentManagementPage() {
  const { user } = useAuth();
  const tenantSlug = user?.institution_slug || '';

  const isStaff = useMemo(() => {
    if (!user) return false;
    return user.roles.some((r) =>
      ['SUPER_ADMIN', 'INSTITUTION_ADMIN', 'HOD', 'FACULTY'].includes(r)
    );
  }, [user]);

  // Main navigation tabs
  const [activeTab, setActiveTab] = useState<'banks' | 'assessments' | 'grading' | 'runner'>(
    isStaff ? 'banks' : 'runner'
  );

  // Common shared state
  const [courses, setCourses] = useState<Course[]>([]);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [error, setError] = useState<{ message: string; code?: string; requestId?: string } | null>(null);

  // =========================================================================
  // TAB 1: QUESTION BANKS & QUESTIONS
  // =========================================================================
  const [questionBanks, setQuestionBanks] = useState<QuestionBank[]>([]);
  const [selectedBankId, setSelectedBankId] = useState<string>('');
  const [bankQuestions, setBankQuestions] = useState<QuestionAdmin[]>([]);
  const [isBankLoading, setIsBankLoading] = useState<boolean>(false);

  // Dialogs for Question Banks
  const [isNewBankOpen, setIsNewBankOpen] = useState(false);
  const [newBankTitle, setNewBankTitle] = useState('');
  const [newBankDesc, setNewBankDesc] = useState('');
  const [newBankCourseId, setNewBankCourseId] = useState('');

  // Dialog for Question Authoring
  const [isNewQuestionOpen, setIsNewQuestionOpen] = useState(false);
  const [qType, setQType] = useState<QuestionType>('MCQ');
  const [qPrompt, setQPrompt] = useState('');
  const [qPoints, setQPoints] = useState<number>(1.0);
  const [qDifficulty, setQDifficulty] = useState<DifficultyLevel>('MEDIUM');
  const [qExplanation, setQExplanation] = useState('');
  // MCQ & Multi-select options
  const [qOptions, setQOptions] = useState<{ id: string; text: string }[]>([
    { id: 'opt_1', text: '' },
    { id: 'opt_2', text: '' },
    { id: 'opt_3', text: '' },
    { id: 'opt_4', text: '' },
  ]);
  const [mcqCorrectOpt, setMcqCorrectOpt] = useState('opt_1');
  const [multiCorrectOpts, setMultiCorrectOpts] = useState<string[]>(['opt_1']);
  // Numerical fields
  const [numTarget, setNumTarget] = useState<number>(0);
  const [numTolerance, setNumTolerance] = useState<number>(0.05);
  // Structured text
  const [sampleSolution, setSampleSolution] = useState('');

  // =========================================================================
  // TAB 2: ASSESSMENTS & BUILDER
  // =========================================================================
  const [assessments, setAssessments] = useState<Assessment[]>([]);
  const [selectedAssessmentId, setSelectedAssessmentId] = useState<string>('');
  const [selectedAssessmentDetail, setSelectedAssessmentDetail] = useState<Assessment | null>(null);

  // New Assessment Dialog
  const [isNewAssessmentOpen, setIsNewAssessmentOpen] = useState(false);
  const [assTitle, setAssTitle] = useState('');
  const [assInstructions, setAssInstructions] = useState('');
  const [assType, setAssType] = useState<AssessmentType>('QUIZ');
  const [assOfferingId, setAssOfferingId] = useState('');
  const [assDuration, setAssDuration] = useState<number>(60);
  const [assPassingPct, setAssPassingPct] = useState<number>(40);
  const [assMaxAttempts, setAssMaxAttempts] = useState<number>(1);
  const [assPublishAt, setAssPublishAt] = useState(new Date().toISOString().slice(0, 16));
  const [assDueAt, setAssDueAt] = useState(
    new Date(Date.now() + 7 * 24 * 3600 * 1000).toISOString().slice(0, 16)
  );

  // Add Question to Assessment Dialog
  const [isAddQToAssOpen, setIsAddQToAssOpen] = useState(false);
  const [selectedAddBankId, setSelectedAddBankId] = useState('');
  const [availableQuestionsForAdd, setAvailableQuestionsForAdd] = useState<QuestionAdmin[]>([]);
  const [selectedQToAddId, setSelectedQToAddId] = useState('');
  const [addQPoints, setAddQPoints] = useState<number>(1.0);

  // =========================================================================
  // TAB 3: GRADING & MANUAL REVIEW
  // =========================================================================
  const [selectedGradingAssessmentId, setSelectedGradingAssessmentId] = useState('');
  const [assessmentSubmissions, setAssessmentSubmissions] = useState<Submission[]>([]);
  const [isSubmissionsLoading, setIsSubmissionsLoading] = useState(false);
  const [selectedSubmission, setSelectedSubmission] = useState<Submission | null>(null);
  const [manualGradeModalOpen, setManualGradeModalOpen] = useState(false);
  const [manualGradeQuestionId, setManualGradeQuestionId] = useState('');
  const [manualGradeAwardedPoints, setManualGradeAwardedPoints] = useState(0);
  const [manualGradeFeedback, setManualGradeFeedback] = useState('');

  // =========================================================================
  // TAB 4: STUDENT TEST RUNNER
  // =========================================================================
  const [runnerAssessmentId, setRunnerAssessmentId] = useState('');
  const [studentAssessment, setStudentAssessment] = useState<AssessmentStudentDetail | null>(null);
  const [studentAnswers, setStudentAnswers] = useState<Record<string, unknown>>({});
  const [timerSecondsRemaining, setTimerSecondsRemaining] = useState<number | null>(null);
  const [activeQuestionIdx, setActiveQuestionIdx] = useState(0);
  const [submissionCompletedResult, setSubmissionCompletedResult] = useState<AssessmentResult | null>(null);

  // Feedback states
  const [formSubmitting, setFormSubmitting] = useState(false);
  const [successNotice, setSuccessNotice] = useState<string | null>(null);

  // 1. Initial Data Fetch
  useEffect(() => {
    if (!tenantSlug) return;
    const fetchCore = async () => {
      setIsLoading(true);
      setError(null);
      try {
        const [courseList, banks, assessList] = await Promise.all([
          api.get<Course[]>(`/institutions/${tenantSlug}/courses`).catch(() => []),
          api.get<QuestionBank[]>(`/institutions/${tenantSlug}/question-banks`).catch(() => []),
          api.get<Assessment[]>(`/institutions/${tenantSlug}/assessments`).catch(() => []),
        ]);
        setCourses(courseList);
        setQuestionBanks(banks);
        if (banks.length > 0) {
          setSelectedBankId(banks[0].id);
        }
        setAssessments(assessList);
        if (assessList.length > 0) {
          setSelectedAssessmentId(assessList[0].id);
          setRunnerAssessmentId(assessList[0].id);
        }
      } catch (err: unknown) {
        if (err instanceof ApiError) {
          setError({ message: err.message, code: err.code, requestId: err.requestId });
        } else {
          setError({ message: 'Failed to initialize assessment workspace.' });
        }
      } finally {
        setIsLoading(false);
      }
    };
    fetchCore();
  }, [tenantSlug]);

  // 2. Fetch Bank Questions when selected bank changes
  useEffect(() => {
    if (!tenantSlug || !selectedBankId) return;
    const fetchQuestions = async () => {
      setIsBankLoading(true);
      try {
        const qs = await api.get<QuestionAdmin[]>(
          `/institutions/${tenantSlug}/question-banks/${selectedBankId}/questions`
        );
        setBankQuestions(qs);
      } catch {
        setBankQuestions([]);
      } finally {
        setIsBankLoading(false);
      }
    };
    fetchQuestions();
  }, [tenantSlug, selectedBankId]);

  // 3. Fetch Assessment Detail when selected assessment changes
  useEffect(() => {
    if (!tenantSlug || !selectedAssessmentId) return;
    const fetchAssessment = async () => {
      try {
        const detail = await api.get<Assessment>(
          `/institutions/${tenantSlug}/assessments/${selectedAssessmentId}`
        );
        setSelectedAssessmentDetail(detail);
      } catch {
        setSelectedAssessmentDetail(null);
      }
    };
    fetchAssessment();
  }, [tenantSlug, selectedAssessmentId]);

  // Fetch Submissions for Grading Review Tab
  useEffect(() => {
    if (!tenantSlug || !selectedGradingAssessmentId) {
      setAssessmentSubmissions([]);
      return;
    }
    const fetchSubmissions = async () => {
      setIsSubmissionsLoading(true);
      try {
        const subs = await api.get<Submission[]>(
          `/institutions/${tenantSlug}/assessments/${selectedGradingAssessmentId}/submissions`
        );
        setAssessmentSubmissions(subs);
      } catch {
        setAssessmentSubmissions([]);
      } finally {
        setIsSubmissionsLoading(false);
      }
    };
    fetchSubmissions();
  }, [tenantSlug, selectedGradingAssessmentId]);

  // 4. Timer for student runner
  useEffect(() => {
    if (timerSecondsRemaining === null || timerSecondsRemaining <= 0) return;
    const timer = setInterval(() => {
      setTimerSecondsRemaining((prev) => {
        if (prev === null || prev <= 1) {
          clearInterval(timer);
          return 0;
        }
        return prev - 1;
      });
    }, 1000);
    return () => clearInterval(timer);
  }, [timerSecondsRemaining]);

  // =========================================================================
  // ACTIONS: Question Banks & Authoring
  // =========================================================================
  const handleCreateBank = async (e: React.FormEvent) => {
    e.preventDefault();
    setFormSubmitting(true);
    try {
      const created = await api.post<QuestionBank>(`/institutions/${tenantSlug}/question-banks`, {
        title: newBankTitle,
        description: newBankDesc,
        course_id: newBankCourseId || null,
      });
      setQuestionBanks((prev) => [created, ...prev]);
      setSelectedBankId(created.id);
      setIsNewBankOpen(false);
      setNewBankTitle('');
      setNewBankDesc('');
      setSuccessNotice('Question Bank created successfully.');
    } catch (err: unknown) {
      if (err instanceof ApiError) alert(err.message);
    } finally {
      setFormSubmitting(false);
    }
  };

  const handleCreateQuestion = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedBankId) return;
    setFormSubmitting(true);

    let answer_key: Record<string, unknown> = {};
    const filteredOptions = qOptions.filter((o) => o.text.trim() !== '');

    if (qType === 'MCQ') {
      answer_key = { correct_option_id: mcqCorrectOpt };
    } else if (qType === 'MULTI_SELECT') {
      answer_key = { correct_option_ids: multiCorrectOpts };
    } else if (qType === 'NUMERICAL') {
      answer_key = { target_value: numTarget, tolerance: numTolerance, precision: 2 };
    } else if (qType === 'STRUCTURED_TEXT') {
      answer_key = { sample_solution: sampleSolution };
    }

    try {
      const created = await api.post<QuestionAdmin>(
        `/institutions/${tenantSlug}/question-banks/${selectedBankId}/questions`,
        {
          question_type: qType,
          prompt_text: qPrompt,
          options: ['MCQ', 'MULTI_SELECT'].includes(qType) ? filteredOptions : [],
          answer_key,
          points: qPoints,
          difficulty: qDifficulty,
          explanation: qExplanation,
        }
      );
      setBankQuestions((prev) => [...prev, created]);
      setIsNewQuestionOpen(false);
      setQPrompt('');
      setQExplanation('');
      setSuccessNotice('Question authored and stored with deterministic answer key.');
    } catch (err: unknown) {
      if (err instanceof ApiError) alert(err.message);
    } finally {
      setFormSubmitting(false);
    }
  };

  // =========================================================================
  // ACTIONS: Assessment Builder
  // =========================================================================
  const handleCreateAssessment = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!assOfferingId) {
      alert('Please specify a Course Offering UUID.');
      return;
    }
    setFormSubmitting(true);
    try {
      const created = await api.post<Assessment>(`/institutions/${tenantSlug}/assessments`, {
        course_offering_id: assOfferingId,
        title: assTitle,
        instructions: assInstructions,
        assessment_type: assType,
        publish_at: new Date(assPublishAt).toISOString(),
        due_at: new Date(assDueAt).toISOString(),
        duration_minutes: assDuration || null,
        passing_percentage: assPassingPct,
        max_attempts: assMaxAttempts,
      });
      setAssessments((prev) => [created, ...prev]);
      setSelectedAssessmentId(created.id);
      setIsNewAssessmentOpen(false);
      setAssTitle('');
      setAssInstructions('');
      setSuccessNotice('Assessment draft created.');
    } catch (err: unknown) {
      if (err instanceof ApiError) alert(err.message);
    } finally {
      setFormSubmitting(false);
    }
  };

  const handlePublishAssessment = async (id: string) => {
    if (!confirm('Publishing will lock all questions and open testing to enrolled students. Proceed?')) {
      return;
    }
    try {
      const updated = await api.post<Assessment>(
        `/institutions/${tenantSlug}/assessments/${id}/publish`,
        {}
      );
      setAssessments((prev) => prev.map((a) => (a.id === id ? updated : a)));
      setSelectedAssessmentDetail(updated);
      setSuccessNotice('Assessment published successfully. Questions are now immutably locked.');
    } catch (err: unknown) {
      if (err instanceof ApiError) alert(err.message);
    }
  };

  const handleCloseAssessment = async (id: string) => {
    if (!confirm('Close this assessment to finalize submissions?')) return;
    try {
      const updated = await api.post<Assessment>(
        `/institutions/${tenantSlug}/assessments/${id}/close`,
        {}
      );
      setAssessments((prev) => prev.map((a) => (a.id === id ? updated : a)));
      setSelectedAssessmentDetail(updated);
      setSuccessNotice('Assessment closed.');
    } catch (err: unknown) {
      if (err instanceof ApiError) alert(err.message);
    }
  };

  const handleOpenAddQuestionModal = async () => {
    if (!selectedBankId && questionBanks.length > 0) {
      setSelectedAddBankId(questionBanks[0].id);
    } else {
      setSelectedAddBankId(selectedBankId);
    }
    setIsAddQToAssOpen(true);
  };

  useEffect(() => {
    if (!tenantSlug || !selectedAddBankId) return;
    api
      .get<QuestionAdmin[]>(
        `/institutions/${tenantSlug}/question-banks/${selectedAddBankId}/questions`
      )
      .then((qs) => {
        setAvailableQuestionsForAdd(qs);
        if (qs.length > 0) {
          setSelectedQToAddId(qs[0].id);
          setAddQPoints(qs[0].points);
        }
      })
      .catch(() => setAvailableQuestionsForAdd([]));
  }, [tenantSlug, selectedAddBankId]);

  const handleAddQuestionToAssessment = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedAssessmentId || !selectedQToAddId) return;
    setFormSubmitting(true);
    try {
      await api.post(
        `/institutions/${tenantSlug}/assessments/${selectedAssessmentId}/questions`,
        {
          question_id: selectedQToAddId,
          points: addQPoints,
          sort_order: (selectedAssessmentDetail?.questions?.length || 0) + 1,
        }
      );
      // Refresh assessment detail
      const updated = await api.get<Assessment>(
        `/institutions/${tenantSlug}/assessments/${selectedAssessmentId}`
      );
      setSelectedAssessmentDetail(updated);
      setIsAddQToAssOpen(false);
      setSuccessNotice('Question linked to assessment.');
    } catch (err: unknown) {
      if (err instanceof ApiError) alert(err.message);
    } finally {
      setFormSubmitting(false);
    }
  };

  // =========================================================================
  // ACTIONS: Student Test Taking
  // =========================================================================
  const handleStartAssessmentRunner = async (assessmentId: string) => {
    setIsLoading(true);
    setError(null);
    setSubmissionCompletedResult(null);
    setStudentAnswers({});
    try {
      const data = await api.get<AssessmentStudentDetail>(
        `/institutions/${tenantSlug}/assessments/${assessmentId}`
      );
      setStudentAssessment(data);
      setActiveQuestionIdx(0);
      if (data.duration_minutes) {
        setTimerSecondsRemaining(data.duration_minutes * 60);
      } else {
        setTimerSecondsRemaining(null);
      }
    } catch (err: unknown) {
      if (err instanceof ApiError) {
        setError({ message: err.message, code: err.code, requestId: err.requestId });
      } else {
        setError({ message: 'Unable to start assessment runner.' });
      }
    } finally {
      setIsLoading(false);
    }
  };

  const handleAnswerChange = (qId: string, val: unknown) => {
    setStudentAnswers((prev) => ({ ...prev, [qId]: val }));
  };

  const handleSubmitStudentAssessment = async () => {
    if (!studentAssessment) return;
    if (!confirm('Are you sure you want to finalize and submit your assessment now?')) return;
    setFormSubmitting(true);
    try {
      const resp = await api.post<Submission>(
        `/institutions/${tenantSlug}/assessments/${studentAssessment.id}/submit`,
        { answers_payload: studentAnswers }
      );
      if (resp.result) {
        setSubmissionCompletedResult(resp.result);
      } else {
        // Fetch submission result
        const sub = await api.get<Submission>(
          `/institutions/${tenantSlug}/submissions/${resp.id}`
        );
        setSubmissionCompletedResult(sub.result || null);
      }
      setTimerSecondsRemaining(null);
      setSuccessNotice('Assessment submitted successfully. Deterministic grading completed.');
    } catch (err: unknown) {
      if (err instanceof ApiError) alert(err.message);
    } finally {
      setFormSubmitting(false);
    }
  };

  // =========================================================================
  // ACTIONS: Manual Grading Review
  // =========================================================================
  const handleManualGradeSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedSubmission || !manualGradeQuestionId) return;
    setFormSubmitting(true);
    try {
      const updatedResult = await api.post<AssessmentResult>(
        `/institutions/${tenantSlug}/submissions/${selectedSubmission.id}/grade-manual`,
        {
          question_id: manualGradeQuestionId,
          awarded_points: manualGradeAwardedPoints,
          feedback: manualGradeFeedback,
        }
      );
      setSelectedSubmission((prev) =>
        prev
          ? {
              ...prev,
              status: updatedResult.is_finalized ? 'GRADED' : 'PENDING_MANUAL',
              result: updatedResult,
            }
          : null
      );
      // Refresh submissions list if viewing an assessment
      if (selectedGradingAssessmentId) {
        api.get<Submission[]>(
          `/institutions/${tenantSlug}/assessments/${selectedGradingAssessmentId}/submissions`
        ).then(setAssessmentSubmissions).catch(() => {});
      }
      setManualGradeModalOpen(false);
      setSuccessNotice('Subjective mark recorded with immutable audit trail.');
    } catch (err: unknown) {
      if (err instanceof ApiError) alert(err.message);
    } finally {
      setFormSubmitting(false);
    }
  };

  const formatTimer = (secs: number) => {
    const mins = Math.floor(secs / 60);
    const remainder = secs % 60;
    return `${mins.toString().padStart(2, '0')}:${remainder.toString().padStart(2, '0')}`;
  };

  if (isLoading) {
    return (
      <div style={{ padding: '32px', color: 'var(--text-secondary)' }}>
        Loading Assessment & Grading Studio...
      </div>
    );
  }

  return (
    <div style={{ padding: '32px', maxWidth: '1440px', margin: '0 auto' }}>
      <PageHeader
        title="Assessment & Deterministic Grading Studio"
        description="Zero-mock question banking, server-authoritative assessment execution, and mathematically verified grading."
        action={
          isStaff && activeTab === 'banks' ? (
            <Button variant="primary" onClick={() => setIsNewBankOpen(true)}>
              + New Question Bank
            </Button>
          ) : isStaff && activeTab === 'assessments' ? (
            <Button variant="primary" onClick={() => setIsNewAssessmentOpen(true)}>
              + Create Assessment
            </Button>
          ) : null
        }
      />

      {successNotice && (
        <div style={{ marginBottom: '20px' }}>
          <Alert variant="success" title="Action Completed">
            {successNotice}
          </Alert>
        </div>
      )}

      {error && (
        <div style={{ marginBottom: '20px' }}>
          <ErrorState
            title="Assessment Gateway Error"
            message={error.message}
            code={error.code}
            requestId={error.requestId}
            onRetry={() => window.location.reload()}
          />
        </div>
      )}

      {/* Tabs */}
      <div
        style={{
          display: 'flex',
          gap: '8px',
          borderBottom: '1px solid var(--border-subtle)',
          marginBottom: '24px',
        }}
      >
        {isStaff && (
          <>
            <button
              onClick={() => setActiveTab('banks')}
              style={{
                padding: '12px 18px',
                fontWeight: 600,
                fontSize: '14px',
                border: 'none',
                background: 'none',
                cursor: 'pointer',
                color: activeTab === 'banks' ? 'var(--brand-primary)' : 'var(--text-secondary)',
                borderBottom:
                  activeTab === 'banks'
                    ? '2px solid var(--brand-primary)'
                    : '2px solid transparent',
              }}
            >
              📚 Question Bank Studio
            </button>
            <button
              onClick={() => setActiveTab('assessments')}
              style={{
                padding: '12px 18px',
                fontWeight: 600,
                fontSize: '14px',
                border: 'none',
                background: 'none',
                cursor: 'pointer',
                color:
                  activeTab === 'assessments'
                    ? 'var(--brand-primary)'
                    : 'var(--text-secondary)',
                borderBottom:
                  activeTab === 'assessments'
                    ? '2px solid var(--brand-primary)'
                    : '2px solid transparent',
              }}
            >
              📝 Assessment Builder
            </button>
            <button
              onClick={() => setActiveTab('grading')}
              style={{
                padding: '12px 18px',
                fontWeight: 600,
                fontSize: '14px',
                border: 'none',
                background: 'none',
                cursor: 'pointer',
                color: activeTab === 'grading' ? 'var(--brand-primary)' : 'var(--text-secondary)',
                borderBottom:
                  activeTab === 'grading'
                    ? '2px solid var(--brand-primary)'
                    : '2px solid transparent',
              }}
            >
              ⚖️ Manual Grading Review
            </button>
          </>
        )}
        <button
          onClick={() => setActiveTab('runner')}
          style={{
            padding: '12px 18px',
            fontWeight: 600,
            fontSize: '14px',
            border: 'none',
            background: 'none',
            cursor: 'pointer',
            color: activeTab === 'runner' ? 'var(--brand-primary)' : 'var(--text-secondary)',
            borderBottom:
              activeTab === 'runner'
                ? '2px solid var(--brand-primary)'
                : '2px solid transparent',
          }}
        >
          🎯 Student Assessment Runner & Results
        </button>
      </div>

      {/* ========================================================================= */}
      {/* TAB 1: QUESTION BANK STUDIO */}
      {/* ========================================================================= */}
      {activeTab === 'banks' && isStaff && (
        <div style={{ display: 'grid', gridTemplateColumns: '320px 1fr', gap: '24px' }}>
          {/* Left: Banks List */}
          <div
            style={{
              backgroundColor: 'var(--bg-surface)',
              borderRadius: 'var(--radius-lg)',
              border: '1px solid var(--border-subtle)',
              padding: '16px',
            }}
          >
            <div
              style={{
                fontSize: '14px',
                fontWeight: 700,
                color: 'var(--text-primary)',
                marginBottom: '12px',
              }}
            >
              Authoring Banks ({questionBanks.length})
            </div>
            {questionBanks.length === 0 ? (
              <EmptyState
                title="No Banks Yet"
                description="Create a question bank to organize itemized questions."
              />
            ) : (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                {questionBanks.map((bank) => (
                  <div
                    key={bank.id}
                    onClick={() => setSelectedBankId(bank.id)}
                    style={{
                      padding: '12px',
                      borderRadius: 'var(--radius-md)',
                      backgroundColor:
                        selectedBankId === bank.id
                          ? 'rgba(59, 130, 246, 0.1)'
                          : 'var(--bg-surface-elevated, #ffffff)',
                      border:
                        selectedBankId === bank.id
                          ? '1px solid var(--brand-primary)'
                          : '1px solid var(--border-subtle)',
                      cursor: 'pointer',
                      transition: 'all 0.2s ease',
                    }}
                  >
                    <div
                      style={{
                        fontSize: '14px',
                        fontWeight: 600,
                        color: 'var(--text-primary)',
                      }}
                    >
                      {bank.title}
                    </div>
                    {bank.description && (
                      <div
                        style={{
                          fontSize: '12px',
                          color: 'var(--text-muted)',
                          marginTop: '4px',
                          overflow: 'hidden',
                          textOverflow: 'ellipsis',
                          whiteSpace: 'nowrap',
                        }}
                      >
                        {bank.description}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Right: Questions in Selected Bank */}
          <div
            style={{
              backgroundColor: 'var(--bg-surface)',
              borderRadius: 'var(--radius-lg)',
              border: '1px solid var(--border-subtle)',
              padding: '24px',
            }}
          >
            <div
              style={{
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center',
                marginBottom: '20px',
              }}
            >
              <div>
                <h3 style={{ margin: 0, fontSize: '18px', color: 'var(--text-primary)' }}>
                  Questions in Selected Bank
                </h3>
                <div style={{ fontSize: '12px', color: 'var(--text-muted)', marginTop: '4px' }}>
                  Authoritative view: includes full deterministic answer keys and rubrics.
                </div>
              </div>
              {selectedBankId && (
                <Button variant="primary" onClick={() => setIsNewQuestionOpen(true)}>
                  + Add Question
                </Button>
              )}
            </div>

            {isBankLoading ? (
              <div style={{ padding: '24px', color: 'var(--text-secondary)' }}>
                Loading bank items...
              </div>
            ) : bankQuestions.length === 0 ? (
              <EmptyState
                title="No Questions Authored"
                description="Add MCQ, Multi-Select, Numerical, or Structured Text questions."
              />
            ) : (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
                {bankQuestions.map((q, idx) => (
                  <div
                    key={q.id}
                    style={{
                      border: '1px solid var(--border-subtle)',
                      borderRadius: 'var(--radius-md)',
                      padding: '16px',
                      backgroundColor: 'var(--bg-app)',
                    }}
                  >
                    <div
                      style={{
                        display: 'flex',
                        justifyContent: 'space-between',
                        alignItems: 'flex-start',
                        marginBottom: '8px',
                      }}
                    >
                      <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
                        <span
                          style={{
                            fontWeight: 700,
                            color: 'var(--brand-primary)',
                            fontSize: '13px',
                          }}
                        >
                          Q{idx + 1}.
                        </span>
                        <Badge variant="default">{q.question_type}</Badge>
                        <Badge
                          variant={
                            q.difficulty === 'HARD'
                              ? 'danger'
                              : q.difficulty === 'MEDIUM'
                              ? 'warning'
                              : 'success'
                          }
                        >
                          {q.difficulty}
                        </Badge>
                      </div>
                      <span
                        style={{
                          fontSize: '13px',
                          fontWeight: 600,
                          color: 'var(--text-primary)',
                        }}
                      >
                        {q.points} {q.points === 1 ? 'mark' : 'marks'}
                      </span>
                    </div>

                    <div
                      style={{
                        fontSize: '14px',
                        color: 'var(--text-primary)',
                        marginBottom: '12px',
                        lineHeight: 1.5,
                      }}
                    >
                      {q.prompt_text}
                    </div>

                    {/* Options if MCQ / MULTI_SELECT */}
                    {['MCQ', 'MULTI_SELECT'].includes(q.question_type) &&
                      q.options &&
                      q.options.length > 0 && (
                        <div
                          style={{
                            display: 'grid',
                            gridTemplateColumns: 'repeat(auto-fill, minmax(280px, 1fr))',
                            gap: '8px',
                            marginBottom: '12px',
                          }}
                        >
                          {q.options.map((opt) => {
                            const isCorrect =
                              q.question_type === 'MCQ'
                                ? (q.answer_key as Record<string, unknown>)?.correct_option_id === opt.id
                                : Array.isArray((q.answer_key as Record<string, unknown>)?.correct_option_ids) &&
                                  ((q.answer_key as Record<string, unknown>).correct_option_ids as string[]).includes(opt.id);
                            return (
                              <div
                                key={opt.id}
                                style={{
                                  padding: '8px 12px',
                                  borderRadius: 'var(--radius-sm)',
                                  fontSize: '13px',
                                  border: isCorrect
                                    ? '1px solid var(--brand-success, #10b981)'
                                    : '1px solid var(--border-subtle)',
                                  backgroundColor: isCorrect
                                    ? 'rgba(16, 185, 129, 0.08)'
                                    : 'var(--bg-surface)',
                                  color: isCorrect
                                    ? 'var(--brand-success, #10b981)'
                                    : 'var(--text-secondary)',
                                  fontWeight: isCorrect ? 600 : 400,
                                }}
                              >
                                {isCorrect ? '✓ ' : '• '} {opt.text}
                              </div>
                            );
                          })}
                        </div>
                      )}

                    {/* Numerical or Structured Text Answer Key Details */}
                    {q.question_type === 'NUMERICAL' && (
                      <div
                        style={{
                          fontSize: '12px',
                          color: 'var(--text-secondary)',
                          marginBottom: '8px',
                          background: 'rgba(59, 130, 246, 0.05)',
                          padding: '8px 12px',
                          borderRadius: 'var(--radius-sm)',
                        }}
                      >
                        Target Value:{' '}
                        <strong>
                          {String((q.answer_key as Record<string, unknown>)?.target_value ?? '')}
                        </strong>{' '}
                        ± {String((q.answer_key as Record<string, unknown>)?.tolerance ?? '')}
                      </div>
                    )}

                    {q.question_type === 'STRUCTURED_TEXT' && (
                      <div
                        style={{
                          fontSize: '12px',
                          color: 'var(--text-secondary)',
                          marginBottom: '8px',
                          background: 'rgba(168, 85, 247, 0.05)',
                          padding: '8px 12px',
                          borderRadius: 'var(--radius-sm)',
                        }}
                      >
                        Sample Solution / Rubric:{' '}
                        <em>{String((q.answer_key as Record<string, unknown>)?.sample_solution ?? '')}</em>
                      </div>
                    )}

                    {q.explanation && (
                      <div
                        style={{
                          fontSize: '12px',
                          color: 'var(--text-muted)',
                          fontStyle: 'italic',
                        }}
                      >
                        💡 Educational Explanation: {q.explanation}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      )}

      {/* ========================================================================= */}
      {/* TAB 2: ASSESSMENT BUILDER */}
      {/* ========================================================================= */}
      {activeTab === 'assessments' && isStaff && (
        <div style={{ display: 'grid', gridTemplateColumns: '340px 1fr', gap: '24px' }}>
          {/* Assessment List */}
          <div
            style={{
              backgroundColor: 'var(--bg-surface)',
              borderRadius: 'var(--radius-lg)',
              border: '1px solid var(--border-subtle)',
              padding: '16px',
            }}
          >
            <div
              style={{
                fontSize: '14px',
                fontWeight: 700,
                color: 'var(--text-primary)',
                marginBottom: '12px',
              }}
            >
              Assessments ({assessments.length})
            </div>
            {assessments.length === 0 ? (
              <EmptyState
                title="No Assessments"
                description="Create a quiz, assignment, or examination."
              />
            ) : (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                {assessments.map((a) => (
                  <div
                    key={a.id}
                    onClick={() => setSelectedAssessmentId(a.id)}
                    style={{
                      padding: '12px',
                      borderRadius: 'var(--radius-md)',
                      backgroundColor:
                        selectedAssessmentId === a.id
                          ? 'rgba(59, 130, 246, 0.1)'
                          : 'var(--bg-surface-elevated, #ffffff)',
                      border:
                        selectedAssessmentId === a.id
                          ? '1px solid var(--brand-primary)'
                          : '1px solid var(--border-subtle)',
                      cursor: 'pointer',
                    }}
                  >
                    <div
                      style={{
                        display: 'flex',
                        justifyContent: 'space-between',
                        alignItems: 'center',
                        marginBottom: '4px',
                      }}
                    >
                      <span
                        style={{
                          fontSize: '14px',
                          fontWeight: 600,
                          color: 'var(--text-primary)',
                        }}
                      >
                        {a.title}
                      </span>
                      <Badge
                        variant={
                          a.status === 'PUBLISHED'
                            ? 'success'
                            : a.status === 'CLOSED'
                            ? 'default'
                            : 'warning'
                        }
                      >
                        {a.status}
                      </Badge>
                    </div>
                    <div style={{ fontSize: '11px', color: 'var(--text-muted)' }}>
                      {a.assessment_type} • {a.total_points} total marks • Max Attempts:{' '}
                      {a.max_attempts}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Assessment Configuration and Question Allocations */}
          <div
            style={{
              backgroundColor: 'var(--bg-surface)',
              borderRadius: 'var(--radius-lg)',
              border: '1px solid var(--border-subtle)',
              padding: '24px',
            }}
          >
            {selectedAssessmentDetail ? (
              <div>
                <div
                  style={{
                    display: 'flex',
                    justifyContent: 'space-between',
                    alignItems: 'flex-start',
                    borderBottom: '1px solid var(--border-subtle)',
                    paddingBottom: '16px',
                    marginBottom: '20px',
                  }}
                >
                  <div>
                    <h2 style={{ margin: 0, fontSize: '20px', color: 'var(--text-primary)' }}>
                      {selectedAssessmentDetail.title}
                    </h2>
                    <div
                      style={{
                        fontSize: '13px',
                        color: 'var(--text-secondary)',
                        marginTop: '6px',
                        display: 'flex',
                        gap: '12px',
                        flexWrap: 'wrap',
                      }}
                    >
                      <span>
                        <strong>Status:</strong> {selectedAssessmentDetail.status}
                      </span>
                      <span>
                        <strong>Type:</strong> {selectedAssessmentDetail.assessment_type}
                      </span>
                      <span>
                        <strong>Duration:</strong>{' '}
                        {selectedAssessmentDetail.duration_minutes
                          ? `${selectedAssessmentDetail.duration_minutes} min`
                          : 'Untimed'}
                      </span>
                      <span>
                        <strong>Total Points:</strong> {selectedAssessmentDetail.total_points}
                      </span>
                      <span>
                        <strong>Pass Rate:</strong>{' '}
                        {selectedAssessmentDetail.passing_percentage}%
                      </span>
                    </div>
                  </div>

                  {/* State Machine Actions */}
                  <div style={{ display: 'flex', gap: '8px' }}>
                    {selectedAssessmentDetail.status === 'DRAFT' && (
                      <>
                        <Button
                          variant="secondary"
                          onClick={handleOpenAddQuestionModal}
                        >
                          + Add Question
                        </Button>
                        <Button
                          variant="primary"
                          onClick={() =>
                            handlePublishAssessment(selectedAssessmentDetail.id)
                          }
                        >
                          🚀 Publish Assessment
                        </Button>
                      </>
                    )}
                    {selectedAssessmentDetail.status === 'PUBLISHED' && (
                      <Button
                        variant="secondary"
                        onClick={() =>
                          handleCloseAssessment(selectedAssessmentDetail.id)
                        }
                      >
                        🔒 Close Assessment
                      </Button>
                    )}
                  </div>
                </div>

                {selectedAssessmentDetail.status === 'PUBLISHED' && (
                  <div style={{ marginBottom: '16px' }}>
                    <Alert variant="info" title="Questions Immutably Locked">
                      This assessment is live. Question additions and score mutations are locked to protect student integrity.
                    </Alert>
                  </div>
                )}

                {/* Allocated Questions List */}
                <h4 style={{ margin: '0 0 12px 0', color: 'var(--text-primary)' }}>
                  Assigned Question Items (
                  {selectedAssessmentDetail.questions?.length || 0})
                </h4>

                {(!selectedAssessmentDetail.questions ||
                  selectedAssessmentDetail.questions.length === 0) ? (
                  <EmptyState
                    title="No Questions Linked"
                    description="Link questions from authoring banks into this assessment."
                  />
                ) : (
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
                    {selectedAssessmentDetail.questions.map((aq, index) => (
                      <div
                        key={aq.id}
                        style={{
                          padding: '12px 16px',
                          border: '1px solid var(--border-subtle)',
                          borderRadius: 'var(--radius-md)',
                          display: 'flex',
                          justifyContent: 'space-between',
                          alignItems: 'center',
                          backgroundColor: 'var(--bg-app)',
                        }}
                      >
                        <div>
                          <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
                            <span style={{ fontWeight: 700, color: 'var(--brand-primary)' }}>
                              #{index + 1}
                            </span>
                            <Badge variant="default">{aq.question.question_type}</Badge>
                            <span
                              style={{
                                fontSize: '13px',
                                fontWeight: 500,
                                color: 'var(--text-primary)',
                              }}
                            >
                              {aq.question.prompt_text}
                            </span>
                          </div>
                        </div>
                        <Badge variant="info">{aq.points} pts</Badge>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            ) : (
              <EmptyState
                title="Select an Assessment"
                description="Choose an assessment from the left panel to inspect parameters and question allocations."
              />
            )}
          </div>
        </div>
      )}

      {/* ========================================================================= */}
      {/* TAB 3: MANUAL GRADING REVIEW */}
      {/* ========================================================================= */}
      {activeTab === 'grading' && isStaff && (
        <div
          style={{
            backgroundColor: 'var(--bg-surface)',
            borderRadius: 'var(--radius-lg)',
            border: '1px solid var(--border-subtle)',
            padding: '24px',
          }}
        >
          <div style={{ marginBottom: '20px' }}>
            <h3 style={{ margin: 0, fontSize: '18px', color: 'var(--text-primary)' }}>
              Deterministic & Manual Evaluation Center
            </h3>
            <div style={{ fontSize: '12px', color: 'var(--text-muted)', marginTop: '4px' }}>
              Autograded items are finalized deterministically. Subjective structured-text answers are audited here.
            </div>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px', marginBottom: '24px' }}>
            <Select
              label="Select Assessment to View Submissions"
              value={selectedGradingAssessmentId}
              onChange={(e) => {
                setSelectedGradingAssessmentId(e.target.value);
                setSelectedSubmission(null);
              }}
              options={[
                { value: '', label: '-- Choose Assessment to View All Submissions --' },
                ...assessments.map((a) => ({
                  value: a.id,
                  label: `${a.title} (${a.status}) — ${a.total_points} pts`,
                })),
              ]}
            />
            <Input
              label="Or Lookup Direct Submission UUID"
              placeholder="e.g. 123e4567-e89b-12d3-a456-426614174000"
              value={selectedSubmission?.id || ''}
              onChange={async (e) => {
                const subId = e.target.value.trim();
                if (subId.length === 36) {
                  try {
                    const sub = await api.get<Submission>(
                      `/institutions/${tenantSlug}/submissions/${subId}`
                    );
                    setSelectedSubmission(sub);
                  } catch {
                    // Ignore transient errors
                  }
                }
              }}
            />
          </div>

          {/* Submissions Table for Selected Assessment */}
          {selectedGradingAssessmentId && (
            <div style={{ marginBottom: '24px' }}>
              <div
                style={{
                  fontSize: '14px',
                  fontWeight: 700,
                  color: 'var(--text-primary)',
                  marginBottom: '12px',
                }}
              >
                Submissions for Assessment ({assessmentSubmissions.length})
              </div>
              {isSubmissionsLoading ? (
                <div style={{ padding: '20px', color: 'var(--text-secondary)' }}>
                  Loading assessment submissions...
                </div>
              ) : assessmentSubmissions.length === 0 ? (
                <EmptyState
                  title="No Submissions Yet"
                  description="No students have submitted attempts for this assessment yet."
                />
              ) : (
                <div style={{ overflowX: 'auto', border: '1px solid var(--border-subtle)', borderRadius: 'var(--radius-md)' }}>
                  <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left', fontSize: '13px' }}>
                    <thead>
                      <tr style={{ backgroundColor: 'var(--bg-app)', borderBottom: '1px solid var(--border-subtle)' }}>
                        <th style={{ padding: '12px 16px', color: 'var(--text-secondary)' }}>Student UUID</th>
                        <th style={{ padding: '12px 16px', color: 'var(--text-secondary)' }}>Attempt #</th>
                        <th style={{ padding: '12px 16px', color: 'var(--text-secondary)' }}>Status</th>
                        <th style={{ padding: '12px 16px', color: 'var(--text-secondary)' }}>Score</th>
                        <th style={{ padding: '12px 16px', color: 'var(--text-secondary)', textAlign: 'right' }}>Action</th>
                      </tr>
                    </thead>
                    <tbody>
                      {assessmentSubmissions.map((sub) => {
                        const isSelected = selectedSubmission?.id === sub.id;
                        return (
                          <tr
                            key={sub.id}
                            style={{
                              borderBottom: '1px solid var(--border-subtle)',
                              backgroundColor: isSelected ? 'rgba(59, 130, 246, 0.08)' : 'transparent',
                            }}
                          >
                            <td style={{ padding: '12px 16px', fontFamily: 'monospace', color: 'var(--text-primary)' }}>
                              {sub.student_user_id}
                            </td>
                            <td style={{ padding: '12px 16px', color: 'var(--text-secondary)' }}>
                              #{sub.attempt_number}
                            </td>
                            <td style={{ padding: '12px 16px' }}>
                              <Badge
                                variant={
                                  sub.status === 'GRADED'
                                    ? 'success'
                                    : sub.status === 'PENDING_MANUAL'
                                    ? 'warning'
                                    : 'info'
                                }
                              >
                                {sub.status}
                              </Badge>
                            </td>
                            <td style={{ padding: '12px 16px', fontWeight: 600, color: 'var(--text-primary)' }}>
                              {sub.result ? `${sub.result.raw_score} / ${sub.result.total_points} (${sub.result.percentage}%)` : '—'}
                            </td>
                            <td style={{ padding: '12px 16px', textAlign: 'right' }}>
                              <Button
                                variant={isSelected ? 'primary' : 'secondary'}
                                onClick={() => setSelectedSubmission(sub)}
                              >
                                {isSelected ? 'Viewing' : 'Inspect Breakdown'}
                              </Button>
                            </td>
                          </tr>
                        );
                      })}
                    </tbody>
                  </table>
                </div>
              )}
            </div>
          )}

          {selectedSubmission ? (
            <div>
              <div
                style={{
                  display: 'flex',
                  justifyContent: 'space-between',
                  padding: '16px',
                  backgroundColor: 'var(--bg-app)',
                  borderRadius: 'var(--radius-md)',
                  marginBottom: '20px',
                }}
              >
                <div>
                  <div style={{ fontSize: '13px', color: 'var(--text-muted)' }}>
                    Submission ID: {selectedSubmission.id}
                  </div>
                  <div style={{ fontSize: '13px', color: 'var(--text-muted)' }}>
                    Student UUID: {selectedSubmission.student_user_id}
                  </div>
                </div>
                <div style={{ textAlign: 'right' }}>
                  <Badge
                    variant={
                      selectedSubmission.status === 'GRADED'
                        ? 'success'
                        : selectedSubmission.status === 'PENDING_MANUAL'
                        ? 'warning'
                        : 'info'
                    }
                  >
                    {selectedSubmission.status}
                  </Badge>
                  {selectedSubmission.result && (
                    <div
                      style={{
                        fontSize: '16px',
                        fontWeight: 700,
                        color: 'var(--brand-primary)',
                        marginTop: '6px',
                      }}
                    >
                      {selectedSubmission.result.raw_score} / {selectedSubmission.result.total_points} (
                      {selectedSubmission.result.percentage}%)
                    </div>
                  )}
                </div>
              </div>

              {/* Itemized Score Breakdown */}
              <h4 style={{ margin: '0 0 12px 0', color: 'var(--text-primary)' }}>
                Itemized Scoring Breakdown
              </h4>
              {selectedSubmission.result?.itemized_breakdown?.map((item, idx) => (
                <div
                  key={item.question_id || idx}
                  style={{
                    padding: '14px',
                    border: '1px solid var(--border-subtle)',
                    borderRadius: 'var(--radius-md)',
                    marginBottom: '10px',
                    display: 'flex',
                    justifyContent: 'space-between',
                    alignItems: 'center',
                  }}
                >
                  <div>
                    <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
                      <Badge variant="default">{item.question_type}</Badge>
                      <span style={{ fontSize: '12px', color: 'var(--text-muted)' }}>
                        Question: {item.question_id}
                      </span>
                      <Badge
                        variant={
                          item.grading_method === 'DETERMINISTIC_AUTOGRADE' ? 'info' : 'warning'
                        }
                      >
                        {item.grading_method}
                      </Badge>
                    </div>
                    {item.feedback && (
                      <div
                        style={{
                          fontSize: '12px',
                          color: 'var(--text-secondary)',
                          marginTop: '6px',
                        }}
                      >
                        Feedback: {item.feedback}
                      </div>
                    )}
                  </div>
                  <div style={{ display: 'flex', gap: '12px', alignItems: 'center' }}>
                    <span style={{ fontWeight: 700, fontSize: '14px' }}>
                      {item.awarded_points} / {item.allocated_points} pts
                    </span>
                    {item.question_type === 'STRUCTURED_TEXT' && (
                      <Button
                        variant="secondary"
                        onClick={() => {
                          setManualGradeQuestionId(item.question_id);
                          setManualGradeAwardedPoints(item.awarded_points);
                          setManualGradeFeedback(item.feedback || '');
                          setManualGradeModalOpen(true);
                        }}
                      >
                        Evaluate
                      </Button>
                    )}
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <EmptyState
              title="No Submission Loaded"
              description="Enter a submission UUID to inspect deterministic autograding formulas or review subjective answers."
            />
          )}
        </div>
      )}

      {/* ========================================================================= */}
      {/* TAB 4: STUDENT TEST RUNNER & RESULTS */}
      {/* ========================================================================= */}
      {activeTab === 'runner' && (
        <div>
          {!studentAssessment && !submissionCompletedResult && (
            <div
              style={{
                backgroundColor: 'var(--bg-surface)',
                borderRadius: 'var(--radius-lg)',
                border: '1px solid var(--border-subtle)',
                padding: '24px',
              }}
            >
              <h3 style={{ margin: '0 0 16px 0', color: 'var(--text-primary)' }}>
                Select an Assessment to Begin
              </h3>
              <div style={{ display: 'flex', gap: '12px', alignItems: 'flex-end' }}>
                <div style={{ flex: 1 }}>
                  <Select
                    label="Choose Assessment"
                    value={runnerAssessmentId}
                    onChange={(e) => setRunnerAssessmentId(e.target.value)}
                    options={assessments
                      .filter((a) => a.status === 'PUBLISHED')
                      .map((a) => ({
                        value: a.id,
                        label: `${a.title} (${a.total_points} marks, ${
                          a.duration_minutes ? `${a.duration_minutes} min` : 'Untimed'
                        })`,
                      }))}
                  />
                </div>
                <Button
                  variant="primary"
                  onClick={() => handleStartAssessmentRunner(runnerAssessmentId)}
                  disabled={!runnerAssessmentId}
                >
                  🚀 Launch Test Interface
                </Button>
              </div>
            </div>
          )}

          {/* Running Assessment Interface */}
          {studentAssessment && !submissionCompletedResult && (
            <div
              style={{
                backgroundColor: 'var(--bg-surface)',
                borderRadius: 'var(--radius-lg)',
                border: '1px solid var(--border-subtle)',
                padding: '24px',
              }}
            >
              {/* Header with Title and Countdown Timer */}
              <div
                style={{
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center',
                  borderBottom: '1px solid var(--border-subtle)',
                  paddingBottom: '16px',
                  marginBottom: '20px',
                }}
              >
                <div>
                  <h2 style={{ margin: 0, fontSize: '20px', color: 'var(--text-primary)' }}>
                    {studentAssessment.title}
                  </h2>
                  <div style={{ fontSize: '12px', color: 'var(--text-muted)', marginTop: '4px' }}>
                    {studentAssessment.instructions || 'Answer all questions to the best of your ability.'}
                  </div>
                </div>

                {timerSecondsRemaining !== null && (
                  <div
                    style={{
                      padding: '8px 16px',
                      borderRadius: 'var(--radius-md)',
                      backgroundColor:
                        timerSecondsRemaining < 300
                          ? 'rgba(239, 68, 68, 0.1)'
                          : 'rgba(59, 130, 246, 0.1)',
                      color:
                        timerSecondsRemaining < 300
                          ? 'var(--brand-error, #ef4444)'
                          : 'var(--brand-primary)',
                      fontWeight: 800,
                      fontSize: '18px',
                      fontFamily: 'monospace',
                    }}
                  >
                    ⏱ {formatTimer(timerSecondsRemaining)}
                  </div>
                )}
              </div>

              {/* Question Navigation Bubbles */}
              <div
                style={{
                  display: 'flex',
                  gap: '8px',
                  flexWrap: 'wrap',
                  marginBottom: '24px',
                }}
              >
                {studentAssessment.questions.map((q, idx) => {
                  const isAnswered = studentAnswers[q.question.id] !== undefined;
                  const isActive = idx === activeQuestionIdx;
                  return (
                    <button
                      key={q.id}
                      onClick={() => setActiveQuestionIdx(idx)}
                      style={{
                        width: '36px',
                        height: '36px',
                        borderRadius: 'var(--radius-md)',
                        border: isActive
                          ? '2px solid var(--brand-primary)'
                          : '1px solid var(--border-subtle)',
                        backgroundColor: isActive
                          ? 'var(--brand-primary)'
                          : isAnswered
                          ? 'rgba(16, 185, 129, 0.15)'
                          : 'var(--bg-app)',
                        color: isActive
                          ? '#ffffff'
                          : isAnswered
                          ? 'var(--brand-success, #10b981)'
                          : 'var(--text-secondary)',
                        fontWeight: 700,
                        cursor: 'pointer',
                      }}
                    >
                      {idx + 1}
                    </button>
                  );
                })}
              </div>

              {/* Active Question Canvas */}
              {studentAssessment.questions[activeQuestionIdx] && (() => {
                const current = studentAssessment.questions[activeQuestionIdx];
                const q = current.question;
                return (
                  <div
                    style={{
                      backgroundColor: 'var(--bg-app)',
                      borderRadius: 'var(--radius-lg)',
                      padding: '24px',
                      border: '1px solid var(--border-subtle)',
                      marginBottom: '24px',
                    }}
                  >
                    <div
                      style={{
                        display: 'flex',
                        justifyContent: 'space-between',
                        alignItems: 'center',
                        marginBottom: '16px',
                      }}
                    >
                      <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
                        <span style={{ fontWeight: 800, fontSize: '16px', color: 'var(--brand-primary)' }}>
                          Question {activeQuestionIdx + 1} of {studentAssessment.questions.length}
                        </span>
                        <Badge variant="default">{q.question_type}</Badge>
                      </div>
                      <Badge variant="info">{current.points} marks</Badge>
                    </div>

                    <div
                      style={{
                        fontSize: '15px',
                        lineHeight: 1.6,
                        color: 'var(--text-primary)',
                        marginBottom: '20px',
                      }}
                    >
                      {q.prompt_text}
                    </div>

                    {/* Answer Inputs based on Question Type */}
                    {q.question_type === 'MCQ' && (
                      <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
                        {q.options.map((opt) => {
                          const isSelected = studentAnswers[q.id] === opt.id;
                          return (
                            <label
                              key={opt.id}
                              onClick={() => handleAnswerChange(q.id, opt.id)}
                              style={{
                                padding: '12px 16px',
                                borderRadius: 'var(--radius-md)',
                                border: isSelected
                                  ? '2px solid var(--brand-primary)'
                                  : '1px solid var(--border-subtle)',
                                backgroundColor: isSelected
                                  ? 'rgba(59, 130, 246, 0.08)'
                                  : 'var(--bg-surface)',
                                cursor: 'pointer',
                                display: 'flex',
                                alignItems: 'center',
                                gap: '12px',
                                color: 'var(--text-primary)',
                                fontWeight: isSelected ? 600 : 400,
                              }}
                            >
                              <input
                                type="radio"
                                name={`q_${q.id}`}
                                checked={isSelected}
                                onChange={() => {}}
                              />
                              <span>{opt.text}</span>
                            </label>
                          );
                        })}
                      </div>
                    )}

                    {q.question_type === 'MULTI_SELECT' && (
                      <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
                        {q.options.map((opt) => {
                          const currentArr = Array.isArray(studentAnswers[q.id])
                            ? (studentAnswers[q.id] as string[])
                            : [];
                          const isChecked = currentArr.includes(opt.id);
                          return (
                            <label
                              key={opt.id}
                              onClick={() => {
                                const next = isChecked
                                  ? currentArr.filter((x) => x !== opt.id)
                                  : [...currentArr, opt.id];
                                handleAnswerChange(q.id, next);
                              }}
                              style={{
                                padding: '12px 16px',
                                borderRadius: 'var(--radius-md)',
                                border: isChecked
                                  ? '2px solid var(--brand-primary)'
                                  : '1px solid var(--border-subtle)',
                                backgroundColor: isChecked
                                  ? 'rgba(59, 130, 246, 0.08)'
                                  : 'var(--bg-surface)',
                                cursor: 'pointer',
                                display: 'flex',
                                alignItems: 'center',
                                gap: '12px',
                                color: 'var(--text-primary)',
                                fontWeight: isChecked ? 600 : 400,
                              }}
                            >
                              <input
                                type="checkbox"
                                checked={isChecked}
                                onChange={() => {}}
                              />
                              <span>{opt.text}</span>
                            </label>
                          );
                        })}
                      </div>
                    )}

                    {q.question_type === 'NUMERICAL' && (
                      <div style={{ maxWidth: '300px' }}>
                        <Input
                          label="Enter Numeric Solution"
                          type="number"
                          step="any"
                          value={studentAnswers[q.id] !== undefined ? String(studentAnswers[q.id]) : ''}
                          onChange={(e) =>
                            handleAnswerChange(q.id, parseFloat(e.target.value) || 0)
                          }
                          placeholder="0.0"
                        />
                      </div>
                    )}

                    {q.question_type === 'STRUCTURED_TEXT' && (
                      <div>
                        <label
                          style={{
                            display: 'block',
                            fontSize: '13px',
                            fontWeight: 600,
                            marginBottom: '6px',
                            color: 'var(--text-secondary)',
                          }}
                        >
                          Structured Explanation / Code Solution
                        </label>
                        <textarea
                          rows={6}
                          style={{
                            width: '100%',
                            padding: '12px',
                            borderRadius: 'var(--radius-md)',
                            border: '1px solid var(--border-subtle)',
                            backgroundColor: 'var(--bg-surface)',
                            color: 'var(--text-primary)',
                            fontFamily: 'inherit',
                            fontSize: '14px',
                          }}
                          value={String(studentAnswers[q.id] || '')}
                          onChange={(e) => handleAnswerChange(q.id, e.target.value)}
                          placeholder="Provide clear, concise rationale according to the prompt..."
                        />
                      </div>
                    )}
                  </div>
                );
              })()}

              {/* Prev / Next & Submit Toolbar */}
              <div
                style={{
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center',
                }}
              >
                <Button
                  variant="secondary"
                  disabled={activeQuestionIdx === 0}
                  onClick={() => setActiveQuestionIdx((p) => p - 1)}
                >
                  ← Previous Question
                </Button>

                <div style={{ display: 'flex', gap: '12px' }}>
                  {activeQuestionIdx < studentAssessment.questions.length - 1 ? (
                    <Button
                      variant="primary"
                      onClick={() => setActiveQuestionIdx((p) => p + 1)}
                    >
                      Next Question →
                    </Button>
                  ) : (
                    <Button
                      variant="primary"
                      onClick={handleSubmitStudentAssessment}
                      disabled={formSubmitting}
                    >
                      {formSubmitting ? 'Submitting...' : '✓ Finalize & Submit'}
                    </Button>
                  )}
                </div>
              </div>
            </div>
          )}

          {/* Submission Completed: Transparent Deterministic Results View */}
          {submissionCompletedResult && (
            <div
              style={{
                backgroundColor: 'var(--bg-surface)',
                borderRadius: 'var(--radius-lg)',
                border: '1px solid var(--border-subtle)',
                padding: '32px',
              }}
            >
              <div
                style={{
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center',
                  borderBottom: '1px solid var(--border-subtle)',
                  paddingBottom: '20px',
                  marginBottom: '24px',
                }}
              >
                <div>
                  <h2 style={{ margin: 0, fontSize: '24px', color: 'var(--text-primary)' }}>
                    Assessment Performance Report
                  </h2>
                  <div style={{ fontSize: '13px', color: 'var(--text-muted)', marginTop: '4px' }}>
                    Graded deterministically via the Dhruva.AI Assessment Engine with mathematical certainty.
                  </div>
                </div>

                <Badge
                  variant={submissionCompletedResult.is_passed ? 'success' : 'danger'}
                >
                  {submissionCompletedResult.is_passed ? 'PASSED' : 'DID NOT PASS'}
                </Badge>
              </div>

              {/* Score Highlight Banner */}
              <div
                style={{
                  display: 'grid',
                  gridTemplateColumns: 'repeat(4, 1fr)',
                  gap: '16px',
                  marginBottom: '32px',
                }}
              >
                <div
                  style={{
                    padding: '20px',
                    borderRadius: 'var(--radius-md)',
                    backgroundColor: 'var(--bg-app)',
                    textAlign: 'center',
                  }}
                >
                  <div style={{ fontSize: '12px', color: 'var(--text-muted)' }}>Raw Score</div>
                  <div
                    style={{
                      fontSize: '28px',
                      fontWeight: 800,
                      color: 'var(--brand-primary)',
                      marginTop: '4px',
                    }}
                  >
                    {submissionCompletedResult.raw_score}
                  </div>
                </div>
                <div
                  style={{
                    padding: '20px',
                    borderRadius: 'var(--radius-md)',
                    backgroundColor: 'var(--bg-app)',
                    textAlign: 'center',
                  }}
                >
                  <div style={{ fontSize: '12px', color: 'var(--text-muted)' }}>Total Possible</div>
                  <div
                    style={{
                      fontSize: '28px',
                      fontWeight: 800,
                      color: 'var(--text-primary)',
                      marginTop: '4px',
                    }}
                  >
                    {submissionCompletedResult.total_points}
                  </div>
                </div>
                <div
                  style={{
                    padding: '20px',
                    borderRadius: 'var(--radius-md)',
                    backgroundColor: 'var(--bg-app)',
                    textAlign: 'center',
                  }}
                >
                  <div style={{ fontSize: '12px', color: 'var(--text-muted)' }}>Percentage</div>
                  <div
                    style={{
                      fontSize: '28px',
                      fontWeight: 800,
                      color:
                        submissionCompletedResult.percentage >= 40
                          ? 'var(--brand-success, #10b981)'
                          : 'var(--brand-error, #ef4444)',
                      marginTop: '4px',
                    }}
                  >
                    {submissionCompletedResult.percentage}%
                  </div>
                </div>
                <div
                  style={{
                    padding: '20px',
                    borderRadius: 'var(--radius-md)',
                    backgroundColor: 'var(--bg-app)',
                    textAlign: 'center',
                  }}
                >
                  <div style={{ fontSize: '12px', color: 'var(--text-muted)' }}>Grade Assigned</div>
                  <div
                    style={{
                      fontSize: '28px',
                      fontWeight: 800,
                      color: 'var(--text-primary)',
                      marginTop: '4px',
                    }}
                  >
                    {submissionCompletedResult.grade_letter || '—'}
                  </div>
                </div>
              </div>

              {/* Itemized Breakdown Table */}
              <h4 style={{ margin: '0 0 16px 0', color: 'var(--text-primary)' }}>
                Itemized Question Breakdown
              </h4>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
                {submissionCompletedResult.itemized_breakdown.map((item, idx) => (
                  <div
                    key={idx}
                    style={{
                      padding: '14px 18px',
                      borderRadius: 'var(--radius-md)',
                      border: '1px solid var(--border-subtle)',
                      backgroundColor: 'var(--bg-app)',
                      display: 'flex',
                      justifyContent: 'space-between',
                      alignItems: 'center',
                    }}
                  >
                    <div>
                      <div style={{ display: 'flex', gap: '10px', alignItems: 'center' }}>
                        <span style={{ fontWeight: 700, color: 'var(--brand-primary)' }}>
                          Item #{idx + 1}
                        </span>
                        <Badge variant="default">{item.question_type}</Badge>
                        <Badge
                          variant={
                            item.grading_method === 'DETERMINISTIC_AUTOGRADE' ? 'info' : 'warning'
                          }
                        >
                          {item.grading_method}
                        </Badge>
                      </div>
                      {item.feedback && (
                        <div
                          style={{
                            fontSize: '12px',
                            color: 'var(--text-secondary)',
                            marginTop: '4px',
                          }}
                        >
                          Note: {item.feedback}
                        </div>
                      )}
                    </div>
                    <div style={{ textAlign: 'right' }}>
                      <div style={{ fontWeight: 800, fontSize: '15px' }}>
                        {item.awarded_points} / {item.allocated_points} pts
                      </div>
                      <div
                        style={{
                          fontSize: '11px',
                          color:
                            item.awarded_points === item.allocated_points
                              ? 'var(--brand-success, #10b981)'
                              : item.awarded_points > 0
                              ? 'var(--brand-warning, #f59e0b)'
                              : 'var(--brand-error, #ef4444)',
                        }}
                      >
                        {item.awarded_points === item.allocated_points
                          ? 'Full Credit'
                          : item.awarded_points > 0
                          ? 'Partial Credit'
                          : 'No Credit'}
                      </div>
                    </div>
                  </div>
                ))}
              </div>

              <div style={{ marginTop: '24px', textAlign: 'center' }}>
                <Button
                  variant="secondary"
                  onClick={() => {
                    setSubmissionCompletedResult(null);
                    setStudentAssessment(null);
                  }}
                >
                  Return to Assessment Portal
                </Button>
              </div>
            </div>
          )}
        </div>
      )}

      {/* ========================================================================= */}
      {/* MODALS */}
      {/* ========================================================================= */}

      {/* New Bank Modal */}
      <Dialog
        isOpen={isNewBankOpen}
        onClose={() => setIsNewBankOpen(false)}
        title="Create New Question Bank"
      >
        <form onSubmit={handleCreateBank}>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
            <Input
              label="Bank Title"
              required
              value={newBankTitle}
              onChange={(e) => setNewBankTitle(e.target.value)}
              placeholder="e.g. Distributed Systems Midterm Bank"
            />
            <Input
              label="Description"
              value={newBankDesc}
              onChange={(e) => setNewBankDesc(e.target.value)}
              placeholder="Scope, topics, and difficulty spread"
            />
            {courses.length > 0 && (
              <Select
                label="Linked Master Course"
                value={newBankCourseId}
                onChange={(e) => setNewBankCourseId(e.target.value)}
                options={[
                  { value: '', label: 'None (General Institutional Bank)' },
                  ...courses.map((c) => ({ value: c.id, label: `${c.code}: ${c.title}` })),
                ]}
              />
            )}
            <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '8px' }}>
              <Button variant="secondary" onClick={() => setIsNewBankOpen(false)}>
                Cancel
              </Button>
              <Button variant="primary" type="submit" disabled={formSubmitting}>
                {formSubmitting ? 'Creating...' : 'Create Bank'}
              </Button>
            </div>
          </div>
        </form>
      </Dialog>

      {/* Add Question Modal */}
      <Dialog
        isOpen={isNewQuestionOpen}
        onClose={() => setIsNewQuestionOpen(false)}
        title="Author Question with Deterministic Answer Key"
      >
        <form onSubmit={handleCreateQuestion}>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: '12px' }}>
              <Select
                label="Question Type"
                value={qType}
                onChange={(e) => setQType(e.target.value as QuestionType)}
                options={[
                  { value: 'MCQ', label: 'Single-Choice MCQ' },
                  { value: 'MULTI_SELECT', label: 'Multi-Select Choice' },
                  { value: 'NUMERICAL', label: 'Numerical Value' },
                  { value: 'STRUCTURED_TEXT', label: 'Structured Text / Code' },
                ]}
              />
              <Select
                label="Difficulty"
                value={qDifficulty}
                onChange={(e) => setQDifficulty(e.target.value as DifficultyLevel)}
                options={[
                  { value: 'EASY', label: 'Easy' },
                  { value: 'MEDIUM', label: 'Medium' },
                  { value: 'HARD', label: 'Hard' },
                ]}
              />
              <Input
                label="Marks"
                type="number"
                step="0.5"
                min="0.5"
                value={String(qPoints)}
                onChange={(e) => setQPoints(parseFloat(e.target.value) || 1)}
              />
            </div>

            <div>
              <label
                style={{
                  display: 'block',
                  fontSize: '13px',
                  fontWeight: 600,
                  marginBottom: '6px',
                  color: 'var(--text-secondary)',
                }}
              >
                Question Prompt (Markdown supported)
              </label>
              <textarea
                required
                rows={3}
                style={{
                  width: '100%',
                  padding: '10px',
                  borderRadius: 'var(--radius-md)',
                  border: '1px solid var(--border-subtle)',
                  backgroundColor: 'var(--bg-surface)',
                  color: 'var(--text-primary)',
                  fontSize: '14px',
                }}
                value={qPrompt}
                onChange={(e) => setQPrompt(e.target.value)}
                placeholder="State the problem clearly..."
              />
            </div>

            {/* Options configuration for MCQ / Multi-select */}
            {['MCQ', 'MULTI_SELECT'].includes(qType) && (
              <div>
                <label
                  style={{
                    display: 'block',
                    fontSize: '13px',
                    fontWeight: 600,
                    marginBottom: '8px',
                    color: 'var(--text-secondary)',
                  }}
                >
                  Options & Answer Key ({qType === 'MCQ' ? 'Select 1 Correct' : 'Select All Correct'})
                </label>
                <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                  {qOptions.map((opt, idx) => (
                    <div key={opt.id} style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
                      {qType === 'MCQ' ? (
                        <input
                          type="radio"
                          name="correct_opt"
                          checked={mcqCorrectOpt === opt.id}
                          onChange={() => setMcqCorrectOpt(opt.id)}
                        />
                      ) : (
                        <input
                          type="checkbox"
                          checked={multiCorrectOpts.includes(opt.id)}
                          onChange={() => {
                            setMultiCorrectOpts((prev) =>
                              prev.includes(opt.id)
                                ? prev.filter((x) => x !== opt.id)
                                : [...prev, opt.id]
                            );
                          }}
                        />
                      )}
                      <Input
                        placeholder={`Option ${idx + 1}`}
                        value={opt.text}
                        onChange={(e) => {
                          const val = e.target.value;
                          setQOptions((prev) =>
                            prev.map((o) => (o.id === opt.id ? { ...o, text: val } : o))
                          );
                        }}
                      />
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Numerical Configuration */}
            {qType === 'NUMERICAL' && (
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px' }}>
                <Input
                  label="Target Numeric Value"
                  type="number"
                  step="any"
                  value={String(numTarget)}
                  onChange={(e) => setNumTarget(parseFloat(e.target.value) || 0)}
                />
                <Input
                  label="Tolerance (± Allowed)"
                  type="number"
                  step="any"
                  value={String(numTolerance)}
                  onChange={(e) => setNumTolerance(parseFloat(e.target.value) || 0)}
                />
              </div>
            )}

            {/* Structured Text Solution */}
            {qType === 'STRUCTURED_TEXT' && (
              <div>
                <label
                  style={{
                    display: 'block',
                    fontSize: '13px',
                    fontWeight: 600,
                    marginBottom: '6px',
                    color: 'var(--text-secondary)',
                  }}
                >
                  Sample Solution / Grading Rubric
                </label>
                <textarea
                  rows={3}
                  style={{
                    width: '100%',
                    padding: '10px',
                    borderRadius: 'var(--radius-md)',
                    border: '1px solid var(--border-subtle)',
                    backgroundColor: 'var(--bg-surface)',
                    color: 'var(--text-primary)',
                    fontSize: '14px',
                  }}
                  value={sampleSolution}
                  onChange={(e) => setSampleSolution(e.target.value)}
                  placeholder="Expected response, keywords, and rubric points..."
                />
              </div>
            )}

            <Input
              label="Educational Explanation (Post-submission guidance)"
              value={qExplanation}
              onChange={(e) => setQExplanation(e.target.value)}
              placeholder="Why this answer is mathematically / conceptually correct..."
            />

            <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '8px' }}>
              <Button variant="secondary" onClick={() => setIsNewQuestionOpen(false)}>
                Cancel
              </Button>
              <Button variant="primary" type="submit" disabled={formSubmitting}>
                {formSubmitting ? 'Saving...' : 'Author Question'}
              </Button>
            </div>
          </div>
        </form>
      </Dialog>

      {/* New Assessment Modal */}
      <Dialog
        isOpen={isNewAssessmentOpen}
        onClose={() => setIsNewAssessmentOpen(false)}
        title="Create Assessment Configuration"
      >
        <form onSubmit={handleCreateAssessment}>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
            <Input
              label="Assessment Title"
              required
              value={assTitle}
              onChange={(e) => setAssTitle(e.target.value)}
              placeholder="e.g. Operating Systems Final Exam"
            />
            <Input
              label="Course Offering UUID"
              required
              value={assOfferingId}
              onChange={(e) => setAssOfferingId(e.target.value)}
              placeholder="Valid Course Offering ID"
            />
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px' }}>
              <Select
                label="Type"
                value={assType}
                onChange={(e) => setAssType(e.target.value as AssessmentType)}
                options={[
                  { value: 'QUIZ', label: 'Quiz' },
                  { value: 'ASSIGNMENT', label: 'Assignment' },
                  { value: 'MIDTERM', label: 'Midterm Examination' },
                  { value: 'FINAL_EXAM', label: 'Final Examination' },
                ]}
              />
              <Input
                label="Duration (minutes, 0 = untimed)"
                type="number"
                value={String(assDuration)}
                onChange={(e) => setAssDuration(parseInt(e.target.value) || 0)}
              />
            </div>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px' }}>
              <Input
                label="Passing Percentage"
                type="number"
                min="0"
                max="100"
                value={String(assPassingPct)}
                onChange={(e) => setAssPassingPct(parseFloat(e.target.value) || 40)}
              />
              <Input
                label="Max Attempts"
                type="number"
                min="1"
                value={String(assMaxAttempts)}
                onChange={(e) => setAssMaxAttempts(parseInt(e.target.value) || 1)}
              />
            </div>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px' }}>
              <Input
                label="Publish Available From (Local)"
                type="datetime-local"
                value={assPublishAt}
                onChange={(e) => setAssPublishAt(e.target.value)}
              />
              <Input
                label="Due Deadline Cutoff (Local)"
                type="datetime-local"
                value={assDueAt}
                onChange={(e) => setAssDueAt(e.target.value)}
              />
            </div>
            <Input
              label="Exam Instructions"
              value={assInstructions}
              onChange={(e) => setAssInstructions(e.target.value)}
              placeholder="Permitted materials, submission guidelines..."
            />
            <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '8px' }}>
              <Button variant="secondary" onClick={() => setIsNewAssessmentOpen(false)}>
                Cancel
              </Button>
              <Button variant="primary" type="submit" disabled={formSubmitting}>
                {formSubmitting ? 'Creating...' : 'Create Draft'}
              </Button>
            </div>
          </div>
        </form>
      </Dialog>

      {/* Add Question to Assessment Modal */}
      <Dialog
        isOpen={isAddQToAssOpen}
        onClose={() => setIsAddQToAssOpen(false)}
        title="Link Question to Assessment"
      >
        <form onSubmit={handleAddQuestionToAssessment}>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
            <Select
              label="Source Question Bank"
              value={selectedAddBankId}
              onChange={(e) => setSelectedAddBankId(e.target.value)}
              options={questionBanks.map((b) => ({ value: b.id, label: b.title }))}
            />

            {availableQuestionsForAdd.length === 0 ? (
              <div style={{ fontSize: '13px', color: 'var(--text-muted)' }}>
                No questions found in this bank. Author questions in Bank Studio first.
              </div>
            ) : (
              <Select
                label="Select Question"
                value={selectedQToAddId}
                onChange={(e) => {
                  setSelectedQToAddId(e.target.value);
                  const found = availableQuestionsForAdd.find((q) => q.id === e.target.value);
                  if (found) setAddQPoints(found.points);
                }}
                options={availableQuestionsForAdd.map((q) => ({
                  value: q.id,
                  label: `[${q.question_type}] ${q.prompt_text.slice(0, 60)}... (${q.points} pts)`,
                }))}
              />
            )}

            <Input
              label="Allocated Marks for this Assessment"
              type="number"
              step="0.5"
              min="0.5"
              value={String(addQPoints)}
              onChange={(e) => setAddQPoints(parseFloat(e.target.value) || 1)}
            />

            <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '8px' }}>
              <Button variant="secondary" onClick={() => setIsAddQToAssOpen(false)}>
                Cancel
              </Button>
              <Button
                variant="primary"
                type="submit"
                disabled={formSubmitting || !selectedQToAddId}
              >
                {formSubmitting ? 'Linking...' : 'Add to Assessment'}
              </Button>
            </div>
          </div>
        </form>
      </Dialog>

      {/* Manual Grade Modal */}
      <Dialog
        isOpen={manualGradeModalOpen}
        onClose={() => setManualGradeModalOpen(false)}
        title="Subjective Manual Evaluation"
      >
        <form onSubmit={handleManualGradeSubmit}>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
            <Input
              label="Awarded Marks"
              type="number"
              step="0.5"
              min="0"
              value={String(manualGradeAwardedPoints)}
              onChange={(e) => setManualGradeAwardedPoints(parseFloat(e.target.value) || 0)}
            />
            <Input
              label="Evaluator Feedback / Rubric Notes"
              value={manualGradeFeedback}
              onChange={(e) => setManualGradeFeedback(e.target.value)}
              placeholder="Justification for marks awarded..."
            />
            <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '8px' }}>
              <Button variant="secondary" onClick={() => setManualGradeModalOpen(false)}>
                Cancel
              </Button>
              <Button variant="primary" type="submit" disabled={formSubmitting}>
                {formSubmitting ? 'Recording...' : 'Record Grade'}
              </Button>
            </div>
          </div>
        </form>
      </Dialog>
    </div>
  );
}
