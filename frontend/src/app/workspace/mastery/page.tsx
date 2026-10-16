'use client';

import React, { useEffect, useState, useMemo } from 'react';
import { useAuth } from '@/lib/auth/AuthContext';
import { api, ApiError } from '@/lib/api/client';
import {
  Concept,
  ConceptPrerequisite,
  LearningOutcome,
  Skill,
  LearningEvidence,
  MasteryRecord,
  ReviewSchedule,
  BloomLevel,
  EvidenceType,
  VerificationStatus,
  CompetencyLevel,
  QualityRating,
} from '@/types/mastery';
import { PageHeader } from '@/components/ui/PageHeader';
import { Button } from '@/components/ui/Button';
import { Badge } from '@/components/ui/Badge';
import { EmptyState } from '@/components/ui/EmptyState';
import { ErrorState } from '@/components/ui/ErrorState';
import { Dialog } from '@/components/ui/Dialog';
import { Input } from '@/components/ui/Input';
import { Select } from '@/components/ui/Select';
import { Alert } from '@/components/ui/Alert';

export default function MasteryAndEvidencePage() {
  const { user } = useAuth();
  const tenantSlug = user?.institution_slug || '';

  const isStaff = useMemo(() => {
    if (!user) return false;
    return user.roles.some((r) =>
      ['SUPER_ADMIN', 'INSTITUTION_ADMIN', 'HOD', 'FACULTY'].includes(r)
    );
  }, [user]);

  // Main navigation tabs
  const [activeTab, setActiveTab] = useState<'concepts' | 'mastery' | 'evidence' | 'reviews'>('concepts');

  // Shared state
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [error, setError] = useState<{ message: string; code?: string; requestId?: string } | null>(null);

  // =========================================================================
  // TAB 1: CONCEPTS & KNOWLEDGE GRAPH
  // =========================================================================
  const [concepts, setConcepts] = useState<Concept[]>([]);
  const [conceptPrereqs, setConceptPrereqs] = useState<ConceptPrerequisite[]>([]);
  const [learningOutcomes, setLearningOutcomes] = useState<LearningOutcome[]>([]);
  const [conceptSearch, setConceptSearch] = useState('');
  const [bloomFilter, setBloomFilter] = useState<string>('ALL');

  // Modals for Concepts
  const [isNewConceptOpen, setIsNewConceptOpen] = useState(false);
  const [newConceptCode, setNewConceptCode] = useState('');
  const [newConceptName, setNewConceptName] = useState('');
  const [newConceptDesc, setNewConceptDesc] = useState('');
  const [newConceptBloom, setNewConceptBloom] = useState<BloomLevel>('UNDERSTAND');

  const [isLinkPrereqOpen, setIsLinkPrereqOpen] = useState(false);
  const [selectedConceptForPrereq, setSelectedConceptForPrereq] = useState('');
  const [selectedPrereqTarget, setSelectedPrereqTarget] = useState('');

  const [isLinkSkillOpen, setIsLinkSkillOpen] = useState(false);
  const [linkSkillConceptId, setLinkSkillConceptId] = useState('');
  const [linkSkillId, setLinkSkillId] = useState('');
  const [linkSkillWeight, setLinkSkillWeight] = useState<number>(1.0);

  // =========================================================================
  // TAB 2: SKILLS & MASTERY PROFILES
  // =========================================================================
  const [skills, setSkills] = useState<Skill[]>([]);
  const [masteryRecords, setMasteryRecords] = useState<MasteryRecord[]>([]);
  const [targetStudentId, setTargetStudentId] = useState<string>(user?.id || '');
  const [selectedProvenanceRecord, setSelectedProvenanceRecord] = useState<MasteryRecord | null>(null);

  // New Skill Modal
  const [isNewSkillOpen, setIsNewSkillOpen] = useState(false);
  const [newSkillCode, setNewSkillCode] = useState('');
  const [newSkillName, setNewSkillName] = useState('');
  const [newSkillCategory, setNewSkillCategory] = useState('DATABASES');
  const [newSkillDesc, setNewSkillDesc] = useState('');

  // =========================================================================
  // TAB 3: LEARNING EVIDENCE & VERIFICATION
  // =========================================================================
  const [evidenceList, setEvidenceList] = useState<LearningEvidence[]>([]);
  const [evidenceStatusFilter, setEvidenceStatusFilter] = useState<string>('ALL');

  // Submit Evidence Modal
  const [isSubmitEvidenceOpen, setIsSubmitEvidenceOpen] = useState(false);
  const [evSkillId, setEvSkillId] = useState('');
  const [evType, setEvType] = useState<EvidenceType>('PROJECT_DELIVERABLE');
  const [evTitle, setEvTitle] = useState('');
  const [evDesc, setEvDesc] = useState('');
  const [evArtifactUrl, setEvArtifactUrl] = useState('');
  const [evFileSizeBytes, setEvFileSizeBytes] = useState<number>(1048576);

  // Verify Evidence Modal
  const [isVerifyModalOpen, setIsVerifyModalOpen] = useState(false);
  const [verifyingEvidence, setVerifyingEvidence] = useState<LearningEvidence | null>(null);
  const [verifyApproved, setVerifyApproved] = useState<boolean>(true);
  const [verifyNotes, setVerifyNotes] = useState('');

  // =========================================================================
  // TAB 4: DAILY SPACED REVIEW QUEUE (SM-2)
  // =========================================================================
  const [reviewSchedules, setReviewSchedules] = useState<ReviewSchedule[]>([]);
  const [isScheduleReviewOpen, setIsScheduleReviewOpen] = useState(false);
  const [schedConceptId, setSchedConceptId] = useState('');
  const [completingReviewId, setCompletingReviewId] = useState<string | null>(null);
  const [selectedQualityRating, setSelectedQualityRating] = useState<QualityRating>(4);

  // =========================================================================
  // DATA LOADING
  // =========================================================================
  const loadInitialData = async () => {
    if (!tenantSlug) return;
    setIsLoading(true);
    setError(null);
    try {
      // 1. Load concepts
      const cRes = await api.get<{ data: Concept[] }>(
        `/api/v1/institutions/${tenantSlug}/concepts?page_size=100`
      );
      setConcepts(cRes.data || []);

      // 2. Load skills
      const sRes = await api.get<{ data: Skill[] }>(
        `/api/v1/institutions/${tenantSlug}/skills?page_size=100`
      );
      setSkills(sRes.data || []);

      // 3. Load learning outcomes
      const loRes = await api.get<{ data: LearningOutcome[] }>(
        `/api/v1/institutions/${tenantSlug}/learning-outcomes`
      );
      setLearningOutcomes(loRes.data || []);

      // 4. Load mastery records for current/target student
      const studentIdToLoad = targetStudentId || user?.id;
      if (studentIdToLoad) {
        try {
          const mRes = await api.get<{ data: MasteryRecord[] }>(
            `/api/v1/institutions/${tenantSlug}/students/${studentIdToLoad}/mastery`
          );
          setMasteryRecords(mRes.data || []);
        } catch {
          setMasteryRecords([]);
        }

        // 5. Load student evidence history
        try {
          const eRes = await api.get<{ data: LearningEvidence[] }>(
            `/api/v1/institutions/${tenantSlug}/students/${studentIdToLoad}/evidence?page_size=100`
          );
          setEvidenceList(eRes.data || []);
        } catch {
          setEvidenceList([]);
        }
      }

      // 6. Load daily pending spaced reviews
      try {
        const rRes = await api.get<{ data: ReviewSchedule[] }>(
          `/api/v1/institutions/${tenantSlug}/reviews/me`
        );
        setReviewSchedules(rRes.data || []);
      } catch {
        setReviewSchedules([]);
      }
    } catch (err: unknown) {
      const apiErr = err as ApiError;
      setError({
        message: apiErr.message || 'Failed to load mastery data.',
        code: apiErr.code,
        requestId: apiErr.requestId,
      });
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    loadInitialData();
  }, [tenantSlug, targetStudentId]);

  // =========================================================================
  // ACTIONS: CONCEPTS & GRAPH
  // =========================================================================
  const handleCreateConcept = async () => {
    if (!newConceptCode || !newConceptName) return;
    try {
      const res = await api.post<{ data: Concept }>(
        `/api/v1/institutions/${tenantSlug}/concepts`,
        {
          code: newConceptCode.trim(),
          name: newConceptName.trim(),
          description: newConceptDesc.trim(),
          bloom_level: newConceptBloom,
        }
      );
      setConcepts((prev) => [...prev, res.data]);
      setIsNewConceptOpen(false);
      setNewConceptCode('');
      setNewConceptName('');
      setNewConceptDesc('');
    } catch (err: unknown) {
      const apiErr = err as ApiError;
      alert(`Error creating concept: ${apiErr.message}`);
    }
  };

  const handleLinkPrerequisite = async () => {
    if (!selectedConceptForPrereq || !selectedPrereqTarget) return;
    try {
      const res = await api.post<{ data: ConceptPrerequisite }>(
        `/api/v1/institutions/${tenantSlug}/concepts/prerequisites`,
        {
          concept_id: selectedConceptForPrereq,
          prerequisite_concept_id: selectedPrereqTarget,
        }
      );
      setConceptPrereqs((prev) => [...prev, res.data]);
      setIsLinkPrereqOpen(false);
      alert('Prerequisite linked successfully.');
    } catch (err: unknown) {
      const apiErr = err as ApiError;
      alert(`Error linking prerequisite: ${apiErr.message}`);
    }
  };

  const handleLinkSkill = async () => {
    if (!linkSkillConceptId || !linkSkillId) return;
    try {
      await api.post(`/api/v1/institutions/${tenantSlug}/concepts/link-skill`, {
        concept_id: linkSkillConceptId,
        skill_id: linkSkillId,
        weight: linkSkillWeight,
      });
      setIsLinkSkillOpen(false);
      alert('Concept linked to Skill competency model.');
    } catch (err: unknown) {
      const apiErr = err as ApiError;
      alert(`Error linking skill: ${apiErr.message}`);
    }
  };

  // =========================================================================
  // ACTIONS: SKILLS & MASTERY
  // =========================================================================
  const handleCreateSkill = async () => {
    if (!newSkillCode || !newSkillName) return;
    try {
      const res = await api.post<{ data: Skill }>(
        `/api/v1/institutions/${tenantSlug}/skills`,
        {
          code: newSkillCode.trim(),
          name: newSkillName.trim(),
          category: newSkillCategory.trim(),
          description: newSkillDesc.trim(),
        }
      );
      setSkills((prev) => [...prev, res.data]);
      setIsNewSkillOpen(false);
      setNewSkillCode('');
      setNewSkillName('');
      setNewSkillDesc('');
    } catch (err: unknown) {
      const apiErr = err as ApiError;
      alert(`Error creating skill: ${apiErr.message}`);
    }
  };

  // =========================================================================
  // ACTIONS: LEARNING EVIDENCE
  // =========================================================================
  const handleSubmitEvidence = async () => {
    if (!evSkillId || !evTitle || !evArtifactUrl) {
      alert('Please select a skill, title, and valid artifact URL.');
      return;
    }
    try {
      const res = await api.post<{ data: LearningEvidence }>(
        `/api/v1/institutions/${tenantSlug}/evidence/submit`,
        {
          skill_id: evSkillId,
          evidence_type: evType,
          title: evTitle.trim(),
          description: evDesc.trim(),
          artifact_url: evArtifactUrl.trim(),
          file_size_bytes: evFileSizeBytes,
        }
      );
      setEvidenceList((prev) => [res.data, ...prev]);
      setIsSubmitEvidenceOpen(false);
      setEvTitle('');
      setEvDesc('');
      setEvArtifactUrl('');
      // Refresh mastery profile immediately
      const mRes = await api.get<{ data: MasteryRecord[] }>(
        `/api/v1/institutions/${tenantSlug}/students/${user?.id}/mastery`
      );
      setMasteryRecords(mRes.data || []);
      alert('Learning evidence submitted successfully.');
    } catch (err: unknown) {
      const apiErr = err as ApiError;
      alert(`Error submitting evidence: ${apiErr.message}`);
    }
  };

  const handleVerifyEvidence = async () => {
    if (!verifyingEvidence) return;
    try {
      const res = await api.post<{ data: LearningEvidence }>(
        `/api/v1/institutions/${tenantSlug}/evidence/${verifyingEvidence.id}/verify`,
        {
          is_verified: verifyApproved,
          verification_notes: verifyNotes.trim(),
        }
      );
      setEvidenceList((prev) =>
        prev.map((e) => (e.id === verifyingEvidence.id ? res.data : e))
      );
      setIsVerifyModalOpen(false);
      setVerifyingEvidence(null);
      setVerifyNotes('');

      // Refresh target student's mastery profile
      const studentId = verifyingEvidence.student_user_id;
      const mRes = await api.get<{ data: MasteryRecord[] }>(
        `/api/v1/institutions/${tenantSlug}/students/${studentId}/mastery`
      );
      setMasteryRecords(mRes.data || []);
      alert(`Evidence ${verifyApproved ? 'VERIFIED' : 'REJECTED'}. Mastery scores recalculated.`);
    } catch (err: unknown) {
      const apiErr = err as ApiError;
      alert(`Error verifying evidence: ${apiErr.message}`);
    }
  };

  // =========================================================================
  // ACTIONS: SPACED REVIEWS (SM-2)
  // =========================================================================
  const handleScheduleReview = async () => {
    if (!schedConceptId) return;
    try {
      const res = await api.post<{ data: ReviewSchedule }>(
        `/api/v1/institutions/${tenantSlug}/reviews/schedule?concept_id=${schedConceptId}`,
        {}
      );
      setReviewSchedules((prev) => [...prev, res.data]);
      setIsScheduleReviewOpen(false);
      alert('Review scheduled with initial 1-day interval.');
    } catch (err: unknown) {
      const apiErr = err as ApiError;
      alert(`Error scheduling review: ${apiErr.message}`);
    }
  };

  const handleCompleteReview = async (scheduleId: string) => {
    try {
      const res = await api.post<{ data: ReviewSchedule }>(
        `/api/v1/institutions/${tenantSlug}/reviews/${scheduleId}/complete`,
        {
          quality_rating: selectedQualityRating,
        }
      );
      // Remove from pending reviews or update
      setReviewSchedules((prev) => prev.filter((s) => s.id !== scheduleId));
      setCompletingReviewId(null);
      alert(
        `Review completed! Quality score: ${selectedQualityRating}/5. Next review scheduled in ${res.data.interval_days} days (Ease factor: ${res.data.ease_factor.toFixed(2)}).`
      );
    } catch (err: unknown) {
      const apiErr = err as ApiError;
      alert(`Error completing review: ${apiErr.message}`);
    }
  };

  // Filtering helpers
  const filteredConcepts = useMemo(() => {
    return concepts.filter((c) => {
      const matchSearch =
        c.code.toLowerCase().includes(conceptSearch.toLowerCase()) ||
        c.name.toLowerCase().includes(conceptSearch.toLowerCase());
      const matchBloom = bloomFilter === 'ALL' || c.bloom_level === bloomFilter;
      return matchSearch && matchBloom;
    });
  }, [concepts, conceptSearch, bloomFilter]);

  const filteredEvidence = useMemo(() => {
    return evidenceList.filter((e) => {
      if (evidenceStatusFilter === 'ALL') return true;
      return e.verification_status === evidenceStatusFilter;
    });
  }, [evidenceList, evidenceStatusFilter]);

  // Color helpers
  const getCompetencyBadge = (level: CompetencyLevel) => {
    switch (level) {
      case 'MASTERY':
        return <Badge variant="success">MASTERY (90%+)</Badge>;
      case 'PROFICIENT':
        return <Badge variant="info">PROFICIENT (70-89%)</Badge>;
      case 'DEVELOPING':
        return <Badge variant="warning">DEVELOPING (50-69%)</Badge>;
      case 'NOVICE':
      default:
        return <Badge variant="danger">NOVICE (&lt;50%)</Badge>;
    }
  };

  const getBloomBadge = (level: BloomLevel) => {
    switch (level) {
      case 'CREATE':
        return <Badge variant="success">CREATE (L6)</Badge>;
      case 'EVALUATE':
        return <Badge variant="info">EVALUATE (L5)</Badge>;
      case 'ANALYZE':
        return <Badge variant="info">ANALYZE (L4)</Badge>;
      case 'APPLY':
        return <Badge variant="warning">APPLY (L3)</Badge>;
      case 'UNDERSTAND':
        return <Badge variant="default">UNDERSTAND (L2)</Badge>;
      case 'REMEMBER':
      default:
        return <Badge variant="default">REMEMBER (L1)</Badge>;
    }
  };

  const getStatusBadge = (status: VerificationStatus) => {
    switch (status) {
      case 'VERIFIED':
        return <Badge variant="success">VERIFIED</Badge>;
      case 'REJECTED':
        return <Badge variant="danger">REJECTED</Badge>;
      case 'SUBMITTED':
      default:
        return <Badge variant="warning">SUBMITTED</Badge>;
    }
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '24px', paddingBottom: '60px' }}>
      <PageHeader
        title="Mastery, Skills & Learning Evidence Engine"
        description="Institutional knowledge graph, deterministic skill mastery decay tracking, learning evidence verification, and SuperMemo SM-2 spaced repetition."
      />

      {error && (
        <ErrorState
          title="Engine Service Unavailable"
          message={error.message}
          code={error.code}
          requestId={error.requestId}
          onRetry={loadInitialData}
        />
      )}

      {/* Main Tab Switcher */}
      <div
        style={{
          display: 'flex',
          gap: '8px',
          borderBottom: '1px solid var(--border-subtle)',
          paddingBottom: '8px',
        }}
      >
        <Button
          variant={activeTab === 'concepts' ? 'primary' : 'ghost'}
          onClick={() => setActiveTab('concepts')}
        >
          Knowledge Graph & Concepts ({concepts.length})
        </Button>
        <Button
          variant={activeTab === 'mastery' ? 'primary' : 'ghost'}
          onClick={() => setActiveTab('mastery')}
        >
          Skills & Mastery Profiles ({skills.length})
        </Button>
        <Button
          variant={activeTab === 'evidence' ? 'primary' : 'ghost'}
          onClick={() => setActiveTab('evidence')}
        >
          Learning Evidence & Review ({evidenceList.length})
        </Button>
        <Button
          variant={activeTab === 'reviews' ? 'primary' : 'ghost'}
          onClick={() => setActiveTab('reviews')}
        >
          Spaced Review Queue (SM-2) ({reviewSchedules.length})
        </Button>
      </div>

      {isLoading && (
        <div style={{ padding: '40px', textAlign: 'center', color: 'var(--text-secondary)' }}>
          Computing knowledge graph & mastery scores...
        </div>
      )}

      {/* =====================================================================
          TAB 1: KNOWLEDGE GRAPH & CONCEPTS
         ===================================================================== */}
      {!isLoading && activeTab === 'concepts' && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
          {/* Action & Filter Toolbar */}
          <div
            style={{
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center',
              flexWrap: 'wrap',
              gap: '12px',
            }}
          >
            <div style={{ display: 'flex', gap: '12px', alignItems: 'center' }}>
              <div style={{ width: '260px' }}>
                <Input
                  value={conceptSearch}
                  onChange={(e) => setConceptSearch(e.target.value)}
                  placeholder="Search code or concept name..."
                />
              </div>
              <div style={{ width: '180px' }}>
                <Select
                  value={bloomFilter}
                  onChange={(e) => setBloomFilter(e.target.value)}
                  options={[
                    { value: 'ALL', label: "All Bloom's Levels" },
                    { value: 'REMEMBER', label: 'L1: Remember' },
                    { value: 'UNDERSTAND', label: 'L2: Understand' },
                    { value: 'APPLY', label: 'L3: Apply' },
                    { value: 'ANALYZE', label: 'L4: Analyze' },
                    { value: 'EVALUATE', label: 'L5: Evaluate' },
                    { value: 'CREATE', label: 'L6: Create' },
                  ]}
                />
              </div>
            </div>

            {isStaff && (
              <div style={{ display: 'flex', gap: '8px' }}>
                <Button variant="secondary" onClick={() => setIsLinkPrereqOpen(true)}>
                  Link Prerequisite
                </Button>
                <Button variant="secondary" onClick={() => setIsLinkSkillOpen(true)}>
                  Link to Skill
                </Button>
                <Button variant="primary" onClick={() => setIsNewConceptOpen(true)}>
                  + New Concept
                </Button>
              </div>
            )}
          </div>

          {/* Concepts Grid */}
          {filteredConcepts.length === 0 ? (
            <EmptyState
              title="No Concepts Found"
              description="Create foundational concepts to establish your institution's academic knowledge graph."
            />
          ) : (
            <div
              style={{
                display: 'grid',
                gridTemplateColumns: 'repeat(auto-fill, minmax(320px, 1fr))',
                gap: '16px',
              }}
            >
              {filteredConcepts.map((concept) => (
                <div
                  key={concept.id}
                  style={{
                    backgroundColor: 'var(--bg-surface)',
                    border: '1px solid var(--border-subtle)',
                    borderRadius: 'var(--radius-lg)',
                    padding: '20px',
                    display: 'flex',
                    flexDirection: 'column',
                    justifyContent: 'space-between',
                    gap: '12px',
                    boxShadow: 'var(--shadow-sm)',
                  }}
                >
                  <div>
                    <div
                      style={{
                        display: 'flex',
                        justifyContent: 'space-between',
                        alignItems: 'flex-start',
                        marginBottom: '8px',
                      }}
                    >
                      <span
                        style={{
                          fontSize: '11px',
                          fontWeight: 700,
                          color: 'var(--brand-accent)',
                          fontFamily: 'var(--font-mono)',
                        }}
                      >
                        {concept.code}
                      </span>
                      {getBloomBadge(concept.bloom_level)}
                    </div>
                    <h3
                      style={{
                        fontSize: '16px',
                        fontWeight: 600,
                        color: 'var(--text-primary)',
                        marginBottom: '6px',
                      }}
                    >
                      {concept.name}
                    </h3>
                    <p
                      style={{
                        fontSize: '13px',
                        color: 'var(--text-secondary)',
                        lineHeight: '1.4',
                      }}
                    >
                      {concept.description || 'No detailed syllabus descriptor provided.'}
                    </p>
                  </div>

                  <div
                    style={{
                      borderTop: '1px solid var(--border-subtle)',
                      paddingTop: '12px',
                      display: 'flex',
                      justifyContent: 'space-between',
                      alignItems: 'center',
                      fontSize: '12px',
                      color: 'var(--text-muted)',
                    }}
                  >
                    <span>Created: {new Date(concept.created_at).toLocaleDateString()}</span>
                    <Button
                      variant="ghost"
                      onClick={() => {
                        setSchedConceptId(concept.id);
                        setIsScheduleReviewOpen(true);
                      }}
                    >
                      Queue for Review
                    </Button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* =====================================================================
          TAB 2: SKILLS & MASTERY PROFILES
         ===================================================================== */}
      {!isLoading && activeTab === 'mastery' && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
          {/* Header & Target Student Selector */}
          <div
            style={{
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center',
              flexWrap: 'wrap',
              gap: '12px',
            }}
          >
            <div>
              <h2 style={{ fontSize: '18px', fontWeight: 600, color: 'var(--text-primary)' }}>
                Deterministic Competency & Retention Dashboard
              </h2>
              <p style={{ fontSize: '13px', color: 'var(--text-secondary)' }}>
                Mastery blends 70% assessment scores and 30% verified evidence, decayed via Ebbinghaus exponential retention (half-life: 30 days).
              </p>
            </div>

            {isStaff && (
              <Button variant="primary" onClick={() => setIsNewSkillOpen(true)}>
                + New Skill Definition
              </Button>
            )}
          </div>

          {/* Mastery Cards List */}
          {skills.length === 0 ? (
            <EmptyState
              title="No Skills Defined"
              description="Define skills and competencies to track student learning trajectories."
            />
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
              {skills.map((skill) => {
                const record = masteryRecords.find((r) => r.skill_id === skill.id);
                const score = record ? record.mastery_score : 0.0;
                const scorePct = Math.round(score * 100);
                const level: CompetencyLevel = record ? record.competency_level : 'NOVICE';
                const confidence = record ? Math.round(record.confidence_score * 100) : 0;

                // Color gradient based on score
                let barColor = 'var(--status-danger)';
                if (scorePct >= 90) barColor = 'var(--status-success)';
                else if (scorePct >= 70) barColor = 'var(--brand-accent)';
                else if (scorePct >= 50) barColor = 'var(--status-warning)';

                return (
                  <div
                    key={skill.id}
                    style={{
                      backgroundColor: 'var(--bg-surface)',
                      border: '1px solid var(--border-subtle)',
                      borderRadius: 'var(--radius-lg)',
                      padding: '20px',
                      display: 'flex',
                      flexDirection: 'column',
                      gap: '16px',
                    }}
                  >
                    <div
                      style={{
                        display: 'flex',
                        justifyContent: 'space-between',
                        alignItems: 'flex-start',
                        flexWrap: 'wrap',
                        gap: '8px',
                      }}
                    >
                      <div>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '4px' }}>
                          <span
                            style={{
                              fontSize: '12px',
                              fontWeight: 700,
                              color: 'var(--brand-primary)',
                              fontFamily: 'var(--font-mono)',
                            }}
                          >
                            {skill.code}
                          </span>
                          <Badge variant="default">{skill.category}</Badge>
                        </div>
                        <h3 style={{ fontSize: '16px', fontWeight: 600, color: 'var(--text-primary)' }}>
                          {skill.name}
                        </h3>
                        <p style={{ fontSize: '13px', color: 'var(--text-secondary)' }}>
                          {skill.description || 'Standard institutional competency item.'}
                        </p>
                      </div>

                      <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                        {getCompetencyBadge(level)}
                        {record && (
                          <Button
                            variant="secondary"
                            onClick={() => setSelectedProvenanceRecord(record)}
                          >
                            Inspect Provenance
                          </Button>
                        )}
                      </div>
                    </div>

                    {/* Progress Bar & Scores */}
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
                      <div
                        style={{
                          display: 'flex',
                          justifyContent: 'space-between',
                          fontSize: '13px',
                          fontWeight: 600,
                        }}
                      >
                        <span style={{ color: 'var(--text-primary)' }}>
                          Mastery Level: {scorePct}%
                        </span>
                        <span style={{ color: 'var(--text-muted)' }}>
                          Confidence: {confidence}% (Assessments: {record?.assessment_count || 0}, Evidence: {record?.evidence_count || 0})
                        </span>
                      </div>

                      <div
                        style={{
                          width: '100%',
                          height: '8px',
                          backgroundColor: 'var(--bg-surface-elevated)',
                          borderRadius: 'var(--radius-full)',
                          overflow: 'hidden',
                        }}
                      >
                        <div
                          style={{
                            width: `${scorePct}%`,
                            height: '100%',
                            backgroundColor: barColor,
                            transition: 'width 0.4s ease',
                          }}
                        />
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>
      )}

      {/* =====================================================================
          TAB 3: LEARNING EVIDENCE & VERIFICATION
         ===================================================================== */}
      {!isLoading && activeTab === 'evidence' && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
          <div
            style={{
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center',
              flexWrap: 'wrap',
              gap: '12px',
            }}
          >
            <div style={{ width: '220px' }}>
              <Select
                value={evidenceStatusFilter}
                onChange={(e) => setEvidenceStatusFilter(e.target.value)}
                options={[
                  { value: 'ALL', label: 'All Verification Statuses' },
                  { value: 'SUBMITTED', label: 'Pending Review (Submitted)' },
                  { value: 'VERIFIED', label: 'Faculty Verified' },
                  { value: 'REJECTED', label: 'Rejected' },
                ]}
              />
            </div>

            <Button variant="primary" onClick={() => setIsSubmitEvidenceOpen(true)}>
              + Submit Learning Evidence
            </Button>
          </div>

          {filteredEvidence.length === 0 ? (
            <EmptyState
              title="No Learning Evidence Found"
              description="Students can upload project deliverables, certificates, lab reports, or code repositories to earn verified competency credit."
            />
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
              {filteredEvidence.map((ev) => {
                const targetSkill = skills.find((s) => s.id === ev.skill_id);

                return (
                  <div
                    key={ev.id}
                    style={{
                      backgroundColor: 'var(--bg-surface)',
                      border: '1px solid var(--border-subtle)',
                      borderRadius: 'var(--radius-lg)',
                      padding: '16px 20px',
                      display: 'flex',
                      justifyContent: 'space-between',
                      alignItems: 'center',
                      flexWrap: 'wrap',
                      gap: '16px',
                    }}
                  >
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '4px', maxWidth: '650px' }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                        <span style={{ fontWeight: 600, color: 'var(--text-primary)', fontSize: '15px' }}>
                          {ev.title}
                        </span>
                        <Badge variant="default">{ev.evidence_type.replace('_', ' ')}</Badge>
                        {targetSkill && (
                          <span
                            style={{
                              fontSize: '11px',
                              fontFamily: 'var(--font-mono)',
                              color: 'var(--brand-accent)',
                            }}
                          >
                            [{targetSkill.code}]
                          </span>
                        )}
                      </div>

                      <p style={{ fontSize: '13px', color: 'var(--text-secondary)' }}>
                        {ev.description || 'No supplementary submission note provided.'}
                      </p>

                      <div style={{ display: 'flex', gap: '16px', fontSize: '12px', color: 'var(--text-muted)' }}>
                        <span>
                          Artifact:{' '}
                          <a
                            href={ev.artifact_url}
                            target="_blank"
                            rel="noopener noreferrer"
                            style={{ color: 'var(--brand-primary)', textDecoration: 'underline' }}
                          >
                            {ev.artifact_url.length > 45
                              ? ev.artifact_url.slice(0, 45) + '...'
                              : ev.artifact_url}
                          </a>
                        </span>
                        <span>Submitted: {new Date(ev.created_at).toLocaleDateString()}</span>
                        {ev.verified_at && (
                          <span>Verified: {new Date(ev.verified_at).toLocaleDateString()}</span>
                        )}
                      </div>

                      {ev.verification_notes && (
                        <div
                          style={{
                            marginTop: '4px',
                            padding: '6px 10px',
                            backgroundColor: 'var(--bg-surface-elevated)',
                            borderRadius: 'var(--radius-sm)',
                            fontSize: '12px',
                            color: 'var(--text-primary)',
                          }}
                        >
                          <strong>Evaluator Feedback:</strong> {ev.verification_notes}
                        </div>
                      )}
                    </div>

                    <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                      {getStatusBadge(ev.verification_status)}
                      {isStaff && ev.verification_status === 'SUBMITTED' && (
                        <Button
                          variant="secondary"
                          onClick={() => {
                            setVerifyingEvidence(ev);
                            setIsVerifyModalOpen(true);
                          }}
                        >
                          Evaluate & Verify
                        </Button>
                      )}
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>
      )}

      {/* =====================================================================
          TAB 4: DAILY SPACED REVIEW QUEUE (SM-2)
         ===================================================================== */}
      {!isLoading && activeTab === 'reviews' && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
          <div
            style={{
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center',
              flexWrap: 'wrap',
              gap: '12px',
            }}
          >
            <div>
              <h2 style={{ fontSize: '18px', fontWeight: 600, color: 'var(--text-primary)' }}>
                SuperMemo SM-2 Spaced Recall Queue
              </h2>
              <p style={{ fontSize: '13px', color: 'var(--text-secondary)' }}>
                Daily active recall items designed to counteract the Ebbinghaus forgetting curve with personalized interval progression.
              </p>
            </div>

            <Button variant="secondary" onClick={() => setIsScheduleReviewOpen(true)}>
              + Schedule Concept Review
            </Button>
          </div>

          {reviewSchedules.length === 0 ? (
            <EmptyState
              title="All Caught Up!"
              description="No concept reviews due today. Excellent work maintaining retention!"
            />
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
              {reviewSchedules.map((sched) => {
                const targetConcept = concepts.find((c) => c.id === sched.concept_id);
                const isSelectedForGrading = completingReviewId === sched.id;

                return (
                  <div
                    key={sched.id}
                    style={{
                      backgroundColor: 'var(--bg-surface)',
                      border: '1px solid var(--border-subtle)',
                      borderRadius: 'var(--radius-lg)',
                      padding: '20px',
                      display: 'flex',
                      flexDirection: 'column',
                      gap: '14px',
                    }}
                  >
                    <div
                      style={{
                        display: 'flex',
                        justifyContent: 'space-between',
                        alignItems: 'flex-start',
                      }}
                    >
                      <div>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '4px' }}>
                          <span
                            style={{
                              fontSize: '11px',
                              fontFamily: 'var(--font-mono)',
                              color: 'var(--brand-accent)',
                              fontWeight: 700,
                            }}
                          >
                            {targetConcept?.code || 'CONCEPT'}
                          </span>
                          <Badge variant="default">Repetition #{sched.repetition_number}</Badge>
                          <Badge variant="info">Interval: {sched.interval_days}d</Badge>
                          <Badge variant="default">Ease Factor: {sched.ease_factor.toFixed(2)}</Badge>
                        </div>
                        <h3 style={{ fontSize: '16px', fontWeight: 600, color: 'var(--text-primary)' }}>
                          {targetConcept?.name || 'Academic Concept'}
                        </h3>
                        <p style={{ fontSize: '13px', color: 'var(--text-secondary)' }}>
                          {targetConcept?.description || 'Active recall prompt based on course curriculum syllabus.'}
                        </p>
                      </div>

                      <Button
                        variant={isSelectedForGrading ? 'secondary' : 'primary'}
                        onClick={() =>
                          setCompletingReviewId(isSelectedForGrading ? null : sched.id)
                        }
                      >
                        {isSelectedForGrading ? 'Cancel' : 'Rate Recall Quality'}
                      </Button>
                    </div>

                    {/* Interactive Quality Rating Selection */}
                    {isSelectedForGrading && (
                      <div
                        style={{
                          backgroundColor: 'var(--bg-surface-elevated)',
                          padding: '16px',
                          borderRadius: 'var(--radius-md)',
                          display: 'flex',
                          flexDirection: 'column',
                          gap: '12px',
                        }}
                      >
                        <span style={{ fontSize: '13px', fontWeight: 600, color: 'var(--text-primary)' }}>
                          Select SuperMemo Recall Score:
                        </span>
                        <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap' }}>
                          {[
                            { val: 5, label: '5 - Perfect Recall' },
                            { val: 4, label: '4 - Good Recall' },
                            { val: 3, label: '3 - Serious Difficulty' },
                            { val: 2, label: '2 - Incorrect / Easy to Recall' },
                            { val: 1, label: '1 - Incorrect / Remembered' },
                            { val: 0, label: '0 - Complete Blackout' },
                          ].map((item) => (
                            <Button
                              key={item.val}
                              variant={selectedQualityRating === item.val ? 'primary' : 'ghost'}
                              onClick={() => setSelectedQualityRating(item.val as QualityRating)}
                            >
                              {item.label}
                            </Button>
                          ))}
                        </div>

                        <div style={{ display: 'flex', justifyContent: 'flex-end', marginTop: '8px' }}>
                          <Button
                            variant="primary"
                            onClick={() => handleCompleteReview(sched.id)}
                          >
                            Submit Rating & Advance SM-2 Interval
                          </Button>
                        </div>
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          )}
        </div>
      )}

      {/* =====================================================================
          MODAL: NEW CONCEPT
         ===================================================================== */}
      <Dialog
        isOpen={isNewConceptOpen}
        onClose={() => setIsNewConceptOpen(false)}
        title="Create Academic Concept"
      >
        <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
          <div>
            <label style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>Concept Code</label>
            <Input
              value={newConceptCode}
              onChange={(e) => setNewConceptCode(e.target.value)}
              placeholder="e.g. CON-DB-INDEX-01"
            />
          </div>

          <div>
            <label style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>Concept Name</label>
            <Input
              value={newConceptName}
              onChange={(e) => setNewConceptName(e.target.value)}
              placeholder="e.g. B-Tree Clustered Indexing"
            />
          </div>

          <div>
            <label style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>Bloom's Taxonomy Level</label>
            <Select
              value={newConceptBloom}
              onChange={(e) => setNewConceptBloom(e.target.value as BloomLevel)}
              options={[
                { value: 'REMEMBER', label: 'REMEMBER (Level 1)' },
                { value: 'UNDERSTAND', label: 'UNDERSTAND (Level 2)' },
                { value: 'APPLY', label: 'APPLY (Level 3)' },
                { value: 'ANALYZE', label: 'ANALYZE (Level 4)' },
                { value: 'EVALUATE', label: 'EVALUATE (Level 5)' },
                { value: 'CREATE', label: 'CREATE (Level 6)' },
              ]}
            />
          </div>

          <div>
            <label style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>Description & Syllabus Context</label>
            <Input
              value={newConceptDesc}
              onChange={(e) => setNewConceptDesc(e.target.value)}
              placeholder="Formal specification and learning scope..."
            />
          </div>

          <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '8px', marginTop: '12px' }}>
            <Button variant="ghost" onClick={() => setIsNewConceptOpen(false)}>
              Cancel
            </Button>
            <Button variant="primary" onClick={handleCreateConcept}>
              Save Concept
            </Button>
          </div>
        </div>
      </Dialog>

      {/* =====================================================================
          MODAL: LINK PREREQUISITE
         ===================================================================== */}
      <Dialog
        isOpen={isLinkPrereqOpen}
        onClose={() => setIsLinkPrereqOpen(false)}
        title="Link Prerequisite Concept"
      >
        <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
          <div>
            <label style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>Target Concept</label>
            <Select
              value={selectedConceptForPrereq}
              onChange={(e) => setSelectedConceptForPrereq(e.target.value)}
              options={[
                { value: '', label: 'Select Target Concept...' },
                ...concepts.map((c) => ({ value: c.id, label: `${c.code}: ${c.name}` })),
              ]}
            />
          </div>

          <div>
            <label style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>Required Prerequisite Concept</label>
            <Select
              value={selectedPrereqTarget}
              onChange={(e) => setSelectedPrereqTarget(e.target.value)}
              options={[
                { value: '', label: 'Select Prerequisite Concept...' },
                ...concepts
                  .filter((c) => c.id !== selectedConceptForPrereq)
                  .map((c) => ({ value: c.id, label: `${c.code}: ${c.name}` })),
              ]}
            />
          </div>

          <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '8px', marginTop: '12px' }}>
            <Button variant="ghost" onClick={() => setIsLinkPrereqOpen(false)}>
              Cancel
            </Button>
            <Button variant="primary" onClick={handleLinkPrerequisite}>
              Link Prerequisite
            </Button>
          </div>
        </div>
      </Dialog>

      {/* =====================================================================
          MODAL: LINK CONCEPT TO SKILL
         ===================================================================== */}
      <Dialog
        isOpen={isLinkSkillOpen}
        onClose={() => setIsLinkSkillOpen(false)}
        title="Link Concept to Skill Competency"
      >
        <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
          <div>
            <label style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>Concept</label>
            <Select
              value={linkSkillConceptId}
              onChange={(e) => setLinkSkillConceptId(e.target.value)}
              options={[
                { value: '', label: 'Select Concept...' },
                ...concepts.map((c) => ({ value: c.id, label: `${c.code}: ${c.name}` })),
              ]}
            />
          </div>

          <div>
            <label style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>Competency Skill</label>
            <Select
              value={linkSkillId}
              onChange={(e) => setLinkSkillId(e.target.value)}
              options={[
                { value: '', label: 'Select Skill...' },
                ...skills.map((s) => ({ value: s.id, label: `${s.code}: ${s.name}` })),
              ]}
            />
          </div>

          <div>
            <label style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>Weight Contribution</label>
            <Input
              type="number"
              value={linkSkillWeight.toString()}
              onChange={(e) => setLinkSkillWeight(parseFloat(e.target.value) || 1.0)}
              placeholder="1.0"
            />
          </div>

          <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '8px', marginTop: '12px' }}>
            <Button variant="ghost" onClick={() => setIsLinkSkillOpen(false)}>
              Cancel
            </Button>
            <Button variant="primary" onClick={handleLinkSkill}>
              Create Link
            </Button>
          </div>
        </div>
      </Dialog>

      {/* =====================================================================
          MODAL: NEW SKILL
         ===================================================================== */}
      <Dialog
        isOpen={isNewSkillOpen}
        onClose={() => setIsNewSkillOpen(false)}
        title="Create Skill Competency Item"
      >
        <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
          <div>
            <label style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>Skill Code</label>
            <Input
              value={newSkillCode}
              onChange={(e) => setNewSkillCode(e.target.value)}
              placeholder="e.g. SKILL-SQL-OPT"
            />
          </div>

          <div>
            <label style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>Skill Name</label>
            <Input
              value={newSkillName}
              onChange={(e) => setNewSkillName(e.target.value)}
              placeholder="e.g. Query Plan Optimization & Index Selection"
            />
          </div>

          <div>
            <label style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>Taxonomy Category</label>
            <Input
              value={newSkillCategory}
              onChange={(e) => setNewSkillCategory(e.target.value)}
              placeholder="e.g. DATABASES | ALGORITHMS | NETWORKS"
            />
          </div>

          <div>
            <label style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>Criteria & Description</label>
            <Input
              value={newSkillDesc}
              onChange={(e) => setNewSkillDesc(e.target.value)}
              placeholder="Description of observable competency mastery..."
            />
          </div>

          <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '8px', marginTop: '12px' }}>
            <Button variant="ghost" onClick={() => setIsNewSkillOpen(false)}>
              Cancel
            </Button>
            <Button variant="primary" onClick={handleCreateSkill}>
              Save Skill
            </Button>
          </div>
        </div>
      </Dialog>

      {/* =====================================================================
          MODAL: SUBMIT LEARNING EVIDENCE
         ===================================================================== */}
      <Dialog
        isOpen={isSubmitEvidenceOpen}
        onClose={() => setIsSubmitEvidenceOpen(false)}
        title="Submit Learning Evidence Artifact"
      >
        <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
          <div>
            <label style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>Target Skill</label>
            <Select
              value={evSkillId}
              onChange={(e) => setEvSkillId(e.target.value)}
              options={[
                { value: '', label: 'Select Target Skill...' },
                ...skills.map((s) => ({ value: s.id, label: `${s.code}: ${s.name}` })),
              ]}
            />
          </div>

          <div>
            <label style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>Evidence Artifact Type</label>
            <Select
              value={evType}
              onChange={(e) => setEvType(e.target.value as EvidenceType)}
              options={[
                { value: 'PROJECT_DELIVERABLE', label: 'Project Deliverable' },
                { value: 'CERTIFICATE', label: 'Industry Certificate' },
                { value: 'LAB_REPORT', label: 'Laboratory / Benchmarking Report' },
                { value: 'CODE_REPOSITORY', label: 'Git Code Repository' },
                { value: 'RESEARCH_NOTE', label: 'Research Note / Paper' },
              ]}
            />
          </div>

          <div>
            <label style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>Artifact Title</label>
            <Input
              value={evTitle}
              onChange={(e) => setEvTitle(e.target.value)}
              placeholder="e.g. Distributed Consensus Engine Implementation in Rust"
            />
          </div>

          <div>
            <label style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>Artifact URL (Public Repository or Storage Link)</label>
            <Input
              value={evArtifactUrl}
              onChange={(e) => setEvArtifactUrl(e.target.value)}
              placeholder="https://github.com/student/consensus-raft"
            />
          </div>

          <div>
            <label style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>Submission Summary</label>
            <Input
              value={evDesc}
              onChange={(e) => setEvDesc(e.target.value)}
              placeholder="Brief summary of work and key learning outcomes demonstrated..."
            />
          </div>

          <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '8px', marginTop: '12px' }}>
            <Button variant="ghost" onClick={() => setIsSubmitEvidenceOpen(false)}>
              Cancel
            </Button>
            <Button variant="primary" onClick={handleSubmitEvidence}>
              Submit Evidence
            </Button>
          </div>
        </div>
      </Dialog>

      {/* =====================================================================
          MODAL: VERIFY EVIDENCE (STAFF)
         ===================================================================== */}
      <Dialog
        isOpen={isVerifyModalOpen}
        onClose={() => setIsVerifyModalOpen(false)}
        title="Faculty Evidence Verification Gate"
      >
        <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
          {verifyingEvidence && (
            <div
              style={{
                backgroundColor: 'var(--bg-surface-elevated)',
                padding: '12px',
                borderRadius: 'var(--radius-sm)',
                fontSize: '13px',
              }}
            >
              <div><strong>Title:</strong> {verifyingEvidence.title}</div>
              <div>
                <strong>Artifact:</strong>{' '}
                <a
                  href={verifyingEvidence.artifact_url}
                  target="_blank"
                  rel="noopener noreferrer"
                  style={{ color: 'var(--brand-primary)', textDecoration: 'underline' }}
                >
                  {verifyingEvidence.artifact_url}
                </a>
              </div>
            </div>
          )}

          <div>
            <label style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>Decision</label>
            <div style={{ display: 'flex', gap: '12px', marginTop: '6px' }}>
              <Button
                variant={verifyApproved ? 'primary' : 'ghost'}
                onClick={() => setVerifyApproved(true)}
              >
                Approve (Verified)
              </Button>
              <Button
                variant={!verifyApproved ? 'primary' : 'ghost'}
                onClick={() => setVerifyApproved(false)}
              >
                Reject
              </Button>
            </div>
          </div>

          <div>
            <label style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>Verification Notes / Feedback</label>
            <Input
              value={verifyNotes}
              onChange={(e) => setVerifyNotes(e.target.value)}
              placeholder="Evaluator feedback explaining mark allocation or rejection reason..."
            />
          </div>

          <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '8px', marginTop: '12px' }}>
            <Button variant="ghost" onClick={() => setIsVerifyModalOpen(false)}>
              Cancel
            </Button>
            <Button variant="primary" onClick={handleVerifyEvidence}>
              Confirm Verification
            </Button>
          </div>
        </div>
      </Dialog>

      {/* =====================================================================
          MODAL: SCHEDULE REVIEW
         ===================================================================== */}
      <Dialog
        isOpen={isScheduleReviewOpen}
        onClose={() => setIsScheduleReviewOpen(false)}
        title="Schedule Spaced Concept Review"
      >
        <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
          <div>
            <label style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>Target Concept</label>
            <Select
              value={schedConceptId}
              onChange={(e) => setSchedConceptId(e.target.value)}
              options={[
                { value: '', label: 'Select Concept to Review...' },
                ...concepts.map((c) => ({ value: c.id, label: `${c.code}: ${c.name}` })),
              ]}
            />
          </div>

          <Alert
            variant="info"
            title="SuperMemo SM-2 Interval Calculation"
          >
            Review schedule will initialize at 1 day. Subsequent intervals will advance to 6 days and scale dynamically based on your recall quality score (0-5).
          </Alert>

          <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '8px', marginTop: '12px' }}>
            <Button variant="ghost" onClick={() => setIsScheduleReviewOpen(false)}>
              Cancel
            </Button>
            <Button variant="primary" onClick={handleScheduleReview}>
              Confirm Schedule
            </Button>
          </div>
        </div>
      </Dialog>

      {/* =====================================================================
          MODAL: INSPECT PROVENANCE
         ===================================================================== */}
      <Dialog
        isOpen={Boolean(selectedProvenanceRecord)}
        onClose={() => setSelectedProvenanceRecord(null)}
        title="Deterministic Mastery Calculation Provenance"
      >
        {selectedProvenanceRecord && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
            <div
              style={{
                display: 'grid',
                gridTemplateColumns: '1fr 1fr',
                gap: '12px',
                backgroundColor: 'var(--bg-surface-elevated)',
                padding: '16px',
                borderRadius: 'var(--radius-md)',
                fontSize: '13px',
              }}
            >
              <div>
                <span style={{ color: 'var(--text-muted)' }}>Final Mastery Score:</span>
                <div style={{ fontSize: '18px', fontWeight: 700, color: 'var(--status-success)' }}>
                  {(selectedProvenanceRecord.mastery_score * 100).toFixed(1)}%
                </div>
              </div>

              <div>
                <span style={{ color: 'var(--text-muted)' }}>Competency Level:</span>
                <div>{getCompetencyBadge(selectedProvenanceRecord.competency_level)}</div>
              </div>

              <div>
                <span style={{ color: 'var(--text-muted)' }}>Confidence Rating:</span>
                <div style={{ fontSize: '15px', fontWeight: 600, color: 'var(--text-primary)' }}>
                  {(selectedProvenanceRecord.confidence_score * 100).toFixed(1)}%
                </div>
              </div>

              <div>
                <span style={{ color: 'var(--text-muted)' }}>Retention Decay Factor:</span>
                <div style={{ fontSize: '15px', fontWeight: 600, color: 'var(--text-primary)' }}>
                  {selectedProvenanceRecord.decay_factor.toFixed(3)}
                </div>
              </div>
            </div>

            <div
              style={{
                backgroundColor: 'var(--bg-surface-subtle)',
                padding: '14px',
                borderRadius: 'var(--radius-md)',
                fontFamily: 'var(--font-mono)',
                fontSize: '12px',
                color: 'var(--text-secondary)',
                maxHeight: '200px',
                overflowY: 'auto',
              }}
            >
              <pre>{JSON.stringify(selectedProvenanceRecord.calculation_provenance, null, 2)}</pre>
            </div>

            <div style={{ display: 'flex', justifyContent: 'flex-end', marginTop: '8px' }}>
              <Button variant="secondary" onClick={() => setSelectedProvenanceRecord(null)}>
                Close
              </Button>
            </div>
          </div>
        )}
      </Dialog>
    </div>
  );
}
