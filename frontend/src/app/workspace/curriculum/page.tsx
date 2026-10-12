'use client';

import React, { useEffect, useState, useMemo } from 'react';
import { useAuth } from '@/lib/auth/AuthContext';
import { api, ApiError } from '@/lib/api/client';
import { Course } from '@/types/academic';
import {
  Curriculum,
  Module,
  Lesson,
  LearningResource,
} from '@/types/curriculum';
import { PageHeader } from '@/components/ui/PageHeader';
import { Button } from '@/components/ui/Button';
import { Badge } from '@/components/ui/Badge';
import { EmptyState } from '@/components/ui/EmptyState';
import { ErrorState } from '@/components/ui/ErrorState';
import { Dialog } from '@/components/ui/Dialog';
import { Input } from '@/components/ui/Input';
import { Select } from '@/components/ui/Select';
import { Alert } from '@/components/ui/Alert';

export default function CurriculumManagementPage() {
  const { user } = useAuth();
  const tenantSlug = user?.institution_slug || '';

  // Role permissions
  const canEdit = useMemo(() => {
    if (!user) return false;
    return user.roles.some((r) => ['SUPER_ADMIN', 'INSTITUTION_ADMIN', 'HOD', 'FACULTY'].includes(r));
  }, [user]);

  const canApprove = useMemo(() => {
    if (!user) return false;
    return user.roles.some((r) => ['SUPER_ADMIN', 'INSTITUTION_ADMIN', 'HOD'].includes(r));
  }, [user]);

  // Master catalog courses
  const [courses, setCourses] = useState<Course[]>([]);
  const [selectedCourseId, setSelectedCourseId] = useState<string>('');

  // Curriculums for the selected course
  const [curriculums, setCurriculums] = useState<Curriculum[]>([]);
  const [selectedCurriculumId, setSelectedCurriculumId] = useState<string>('');
  const [selectedCurriculumDetail, setSelectedCurriculumDetail] = useState<Curriculum | null>(null);

  // States
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [isDetailLoading, setIsDetailLoading] = useState<boolean>(false);
  const [error, setError] = useState<{ message: string; code?: string; requestId?: string } | null>(null);

  // Dialog Modals
  const [modalType, setModalType] = useState<
    'curriculum' | 'module' | 'lesson' | 'resource' | null
  >(null);
  const [formSubmitting, setFormSubmitting] = useState<boolean>(false);
  const [formError, setFormError] = useState<string | null>(null);

  // Form inputs
  const [currTitle, setCurrTitle] = useState('');
  const [currDesc, setCurrDesc] = useState('');
  const [currObjectives, setCurrObjectives] = useState('');

  const [modTitle, setModTitle] = useState('');
  const [modSeq, setModSeq] = useState(1);
  const [modHours, setModHours] = useState(10.0);
  const [modDesc, setModDesc] = useState('');

  const [activeModuleId, setActiveModuleId] = useState<string>('');
  const [lesTitle, setLesTitle] = useState('');
  const [lesSeq, setLesSeq] = useState(1);
  const [lesType, setLesType] = useState('THEORY');
  const [lesMinutes, setLesMinutes] = useState(60);
  const [lesMarkdown, setLesMarkdown] = useState('');

  const [activeLessonId, setActiveLessonId] = useState<string>('');
  const [resTitle, setResTitle] = useState('');
  const [resType, setResType] = useState('DOCUMENT');
  const [resUri, setResUri] = useState('');
  const [resUrl, setResUrl] = useState('');

  // 1. Load initial courses
  const loadCourses = async () => {
    if (!tenantSlug) {
      setIsLoading(false);
      return;
    }
    setIsLoading(true);
    setError(null);
    try {
      const courseList = await api.get<Course[]>(`/institutions/${tenantSlug}/courses`);
      setCourses(courseList);
      if (courseList.length > 0) {
        setSelectedCourseId(courseList[0].id);
      }
    } catch (err: unknown) {
      if (err instanceof ApiError) {
        setError({ message: err.message, code: err.code, requestId: err.requestId });
      } else {
        setError({ message: 'Failed to retrieve course catalog. Please check network connectivity.' });
      }
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    loadCourses();
  }, [tenantSlug]);

  // 2. Load curriculums when course changes
  const loadCurriculums = async (courseId: string) => {
    if (!tenantSlug || !courseId) {
      setCurriculums([]);
      setSelectedCurriculumId('');
      setSelectedCurriculumDetail(null);
      return;
    }
    try {
      const list = await api.get<Curriculum[]>(`/institutions/${tenantSlug}/courses/${courseId}/curriculums`);
      setCurriculums(list);
      if (list.length > 0) {
        setSelectedCurriculumId(list[0].id);
      } else {
        setSelectedCurriculumId('');
        setSelectedCurriculumDetail(null);
      }
    } catch (err: unknown) {
      if (err instanceof ApiError) {
        setError({ message: err.message, code: err.code, requestId: err.requestId });
      }
    }
  };

  useEffect(() => {
    if (selectedCourseId) {
      loadCurriculums(selectedCourseId);
    }
  }, [selectedCourseId, tenantSlug]);

  // 3. Load curriculum detail when selected curriculum changes
  const loadCurriculumDetail = async (currId: string) => {
    if (!tenantSlug || !currId) {
      setSelectedCurriculumDetail(null);
      return;
    }
    setIsDetailLoading(true);
    try {
      const detail = await api.get<Curriculum>(`/institutions/${tenantSlug}/curriculums/${currId}`);
      setSelectedCurriculumDetail(detail);
    } catch (err: unknown) {
      if (err instanceof ApiError) {
        setError({ message: err.message, code: err.code, requestId: err.requestId });
      }
    } finally {
      setIsDetailLoading(false);
    }
  };

  useEffect(() => {
    if (selectedCurriculumId) {
      loadCurriculumDetail(selectedCurriculumId);
    }
  }, [selectedCurriculumId, tenantSlug]);

  const resetForms = () => {
    setModalType(null);
    setFormError(null);
    setFormSubmitting(false);
    setCurrTitle('');
    setCurrDesc('');
    setCurrObjectives('');
    setModTitle('');
    setModSeq(1);
    setModHours(10.0);
    setModDesc('');
    setLesTitle('');
    setLesSeq(1);
    setLesType('THEORY');
    setLesMinutes(60);
    setLesMarkdown('');
    setResTitle('');
    setResType('DOCUMENT');
    setResUri('');
    setResUrl('');
  };

  // Form Submissions
  const handleCreateCurriculum = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!currTitle.trim()) {
      setFormError('Curriculum title is required.');
      return;
    }
    setFormSubmitting(true);
    setFormError(null);
    try {
      const objectives = currObjectives
        .split('\n')
        .map((s) => s.trim())
        .filter(Boolean);
      await api.post(`/institutions/${tenantSlug}/courses/${selectedCourseId}/curriculums`, {
        title: currTitle.trim(),
        description: currDesc.trim() || undefined,
        learning_objectives: objectives,
      });
      resetForms();
      await loadCurriculums(selectedCourseId);
    } catch (err: unknown) {
      setFormError(err instanceof ApiError ? err.message : 'Error creating curriculum version');
    } finally {
      setFormSubmitting(false);
    }
  };

  const handleCreateModule = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!modTitle.trim()) {
      setFormError('Module title is required.');
      return;
    }
    setFormSubmitting(true);
    setFormError(null);
    try {
      await api.post(`/institutions/${tenantSlug}/curriculums/${selectedCurriculumId}/modules`, {
        title: modTitle.trim(),
        sequence_order: Number(modSeq),
        estimated_hours: Number(modHours),
        description: modDesc.trim() || undefined,
      });
      resetForms();
      await loadCurriculumDetail(selectedCurriculumId);
    } catch (err: unknown) {
      setFormError(err instanceof ApiError ? err.message : 'Error adding module');
    } finally {
      setFormSubmitting(false);
    }
  };

  const handleCreateLesson = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!lesTitle.trim()) {
      setFormError('Lesson title is required.');
      return;
    }
    setFormSubmitting(true);
    setFormError(null);
    try {
      await api.post(`/institutions/${tenantSlug}/modules/${activeModuleId}/lessons`, {
        title: lesTitle.trim(),
        sequence_order: Number(lesSeq),
        lesson_type: lesType,
        duration_minutes: Number(lesMinutes),
        content_markdown: lesMarkdown.trim() || undefined,
      });
      resetForms();
      await loadCurriculumDetail(selectedCurriculumId);
    } catch (err: unknown) {
      setFormError(err instanceof ApiError ? err.message : 'Error adding lesson');
    } finally {
      setFormSubmitting(false);
    }
  };

  const handleCreateResource = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!resTitle.trim()) {
      setFormError('Resource title is required.');
      return;
    }
    setFormSubmitting(true);
    setFormError(null);
    try {
      await api.post(`/institutions/${tenantSlug}/lessons/${activeLessonId}/resources`, {
        title: resTitle.trim(),
        resource_type: resType,
        storage_uri: resUri.trim() || undefined,
        external_url: resUrl.trim() || undefined,
      });
      resetForms();
      await loadCurriculumDetail(selectedCurriculumId);
    } catch (err: unknown) {
      setFormError(err instanceof ApiError ? err.message : 'Error attaching resource');
    } finally {
      setFormSubmitting(false);
    }
  };

  // Status transitions
  const handleStatusChange = async (targetStatus: string) => {
    try {
      await api.patch(`/institutions/${tenantSlug}/curriculums/${selectedCurriculumId}/status`, {
        status: targetStatus,
      });
      await loadCurriculums(selectedCourseId);
      await loadCurriculumDetail(selectedCurriculumId);
    } catch (err: unknown) {
      alert(err instanceof ApiError ? err.message : 'Failed to update publication status');
    }
  };

  if (!tenantSlug) {
    return (
      <div>
        <PageHeader title="Curriculum & Syllabus Management" description="Course syllabus and content hierarchy" />
        <Alert variant="warning" title="No Institution Scope Bound">
          Your current session is not associated with an institution tenant partition.
        </Alert>
      </div>
    );
  }

  const activeCurriculum = curriculums.find((c) => c.id === selectedCurriculumId);

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
      <PageHeader
        title="Curriculum, Syllabus & Content Management"
        description={`Manage course syllabi, modules, lesson topics, and learning materials for tenant '${tenantSlug}'`}
        action={
          canEdit && selectedCourseId ? (
            <Button variant="primary" size="sm" onClick={() => setModalType('curriculum')}>
              + New Curriculum Version
            </Button>
          ) : undefined
        }
      />

      {/* Course & Curriculum Version Selectors */}
      <div
        style={{
          display: 'flex',
          flexWrap: 'wrap',
          gap: '16px',
          alignItems: 'center',
          backgroundColor: 'var(--bg-surface)',
          padding: '16px',
          borderRadius: 'var(--radius-md)',
          border: '1px solid var(--border-subtle)',
        }}
      >
        <div style={{ minWidth: '280px' }}>
          <Select
            label="Course Catalog"
            value={selectedCourseId}
            onChange={(e) => setSelectedCourseId(e.target.value)}
            options={[
              { value: '', label: 'Select a course...' },
              ...courses.map((c) => ({ value: c.id, label: `${c.code} — ${c.title}` })),
            ]}
          />
        </div>

        {curriculums.length > 0 && (
          <div style={{ minWidth: '220px' }}>
            <Select
              label="Curriculum Version"
              value={selectedCurriculumId}
              onChange={(e) => setSelectedCurriculumId(e.target.value)}
              options={curriculums.map((c) => ({
                value: c.id,
                label: `v${c.version} — ${c.title} (${c.status})`,
              }))}
            />
          </div>
        )}

        {activeCurriculum && (
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginLeft: 'auto', marginTop: '20px' }}>
            <Badge
              variant={
                activeCurriculum.status === 'PUBLISHED'
                  ? 'success'
                  : activeCurriculum.status === 'APPROVED'
                  ? 'info'
                  : activeCurriculum.status === 'IN_REVIEW'
                  ? 'warning'
                  : 'default'
              }
            >
              {activeCurriculum.status}
            </Badge>

            {/* Workflow Actions */}
            {canEdit && activeCurriculum.status === 'DRAFT' && (
              <Button variant="secondary" size="sm" onClick={() => handleStatusChange('IN_REVIEW')}>
                Submit for Review
              </Button>
            )}

            {canApprove && activeCurriculum.status === 'IN_REVIEW' && (
              <>
                <Button variant="outline" size="sm" onClick={() => handleStatusChange('DRAFT')}>
                  Return to Draft
                </Button>
                <Button variant="primary" size="sm" onClick={() => handleStatusChange('APPROVED')}>
                  Approve Curriculum
                </Button>
              </>
            )}

            {canApprove && activeCurriculum.status === 'APPROVED' && (
              <Button variant="primary" size="sm" onClick={() => handleStatusChange('PUBLISHED')}>
                Publish to LMS
              </Button>
            )}

            {canApprove && activeCurriculum.status === 'PUBLISHED' && (
              <Button variant="outline" size="sm" onClick={() => handleStatusChange('ARCHIVED')}>
                Archive Version
              </Button>
            )}
          </div>
        )}
      </div>

      {/* Main Content Area */}
      {isLoading ? (
        <div style={{ padding: '48px', textAlign: 'center', color: 'var(--text-secondary)' }}>
          Loading course catalog...
        </div>
      ) : error ? (
        <ErrorState
          title="Failed to Load Curriculum Records"
          message={error.message}
          code={error.code}
          requestId={error.requestId}
          onRetry={loadCourses}
        />
      ) : courses.length === 0 ? (
        <EmptyState
          title="No courses registered"
          description="Create accredited courses in the Academic Structure workspace before designing curriculums."
        />
      ) : curriculums.length === 0 ? (
        <EmptyState
          title="No curriculum defined for this course"
          description="Establish the syllabus specification, learning objectives, and instructional modules."
          actionLabel={canEdit ? '+ Create Curriculum Specification' : undefined}
          onAction={canEdit ? () => setModalType('curriculum') : undefined}
        />
      ) : isDetailLoading ? (
        <div style={{ padding: '48px', textAlign: 'center', color: 'var(--text-secondary)' }}>
          Loading syllabus tree and instructional units...
        </div>
      ) : selectedCurriculumDetail ? (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
          {/* Header Overview Card */}
          <div
            style={{
              padding: '20px',
              backgroundColor: 'var(--bg-surface)',
              borderRadius: 'var(--radius-md)',
              border: '1px solid var(--border-subtle)',
            }}
          >
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
              <div>
                <h2 style={{ fontSize: '18px', fontWeight: 700, color: 'var(--text-primary)' }}>
                  {selectedCurriculumDetail.title}
                </h2>
                {selectedCurriculumDetail.description && (
                  <p style={{ fontSize: '13px', color: 'var(--text-secondary)', marginTop: '4px' }}>
                    {selectedCurriculumDetail.description}
                  </p>
                )}
              </div>
              {canEdit && ['DRAFT', 'IN_REVIEW'].includes(selectedCurriculumDetail.status) && (
                <Button
                  variant="primary"
                  size="sm"
                  onClick={() => {
                    setModSeq((selectedCurriculumDetail.modules?.length || 0) + 1);
                    setModalType('module');
                  }}
                >
                  + Add Module
                </Button>
              )}
            </div>

            {selectedCurriculumDetail.learning_objectives.length > 0 && (
              <div style={{ marginTop: '16px' }}>
                <div style={{ fontSize: '12px', fontWeight: 600, color: 'var(--text-muted)', marginBottom: '6px' }}>
                  COURSE LEARNING OBJECTIVES & OUTCOMES
                </div>
                <div style={{ display: 'flex', flexWrap: 'wrap', gap: '6px' }}>
                  {selectedCurriculumDetail.learning_objectives.map((obj, i) => (
                    <Badge key={i} variant="outline">
                      {obj}
                    </Badge>
                  ))}
                </div>
              </div>
            )}
          </div>

          {/* Syllabus Modules & Lessons Tree */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
            <h3 style={{ fontSize: '15px', fontWeight: 600, color: 'var(--text-primary)' }}>
              Instructional Units & Syllabus Topics ({selectedCurriculumDetail.modules?.length || 0} Modules)
            </h3>

            {(!selectedCurriculumDetail.modules || selectedCurriculumDetail.modules.length === 0) ? (
              <EmptyState
                title="No modules added"
                description="Add instructional units to structure course lessons, tutorial topics, and learning materials."
                actionLabel={canEdit ? '+ Add Module' : undefined}
                onAction={canEdit ? () => setModalType('module') : undefined}
              />
            ) : (
              selectedCurriculumDetail.modules.map((mod) => (
                <div
                  key={mod.id}
                  style={{
                    backgroundColor: 'var(--bg-surface)',
                    border: '1px solid var(--border-subtle)',
                    borderRadius: 'var(--radius-md)',
                    overflow: 'hidden',
                  }}
                >
                  {/* Module Header */}
                  <div
                    style={{
                      padding: '14px 18px',
                      backgroundColor: 'var(--bg-surface-elevated)',
                      borderBottom: '1px solid var(--border-subtle)',
                      display: 'flex',
                      justifyContent: 'space-between',
                      alignItems: 'center',
                    }}
                  >
                    <div>
                      <span style={{ fontSize: '12px', fontWeight: 700, color: 'var(--brand-primary)', marginRight: '8px' }}>
                        MODULE {mod.sequence_order}
                      </span>
                      <span style={{ fontSize: '14px', fontWeight: 600, color: 'var(--text-primary)' }}>
                        {mod.title}
                      </span>
                      <span style={{ fontSize: '12px', color: 'var(--text-muted)', marginLeft: '12px' }}>
                        ({mod.estimated_hours} hrs)
                      </span>
                    </div>

                    {canEdit && ['DRAFT', 'IN_REVIEW'].includes(selectedCurriculumDetail.status) && (
                      <Button
                        variant="secondary"
                        size="sm"
                        onClick={() => {
                          setActiveModuleId(mod.id);
                          setLesSeq((mod.lessons?.length || 0) + 1);
                          setModalType('lesson');
                        }}
                      >
                        + Add Lesson
                      </Button>
                    )}
                  </div>

                  {/* Lessons List */}
                  <div style={{ padding: '12px 18px' }}>
                    {(!mod.lessons || mod.lessons.length === 0) ? (
                      <div style={{ padding: '12px 0', fontSize: '13px', color: 'var(--text-muted)' }}>
                        No lessons scheduled in this module yet.
                      </div>
                    ) : (
                      <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
                        {mod.lessons.map((les) => (
                          <div
                            key={les.id}
                            style={{
                              padding: '12px 14px',
                              backgroundColor: 'var(--bg-app)',
                              borderRadius: 'var(--radius-sm)',
                              border: '1px solid var(--border-subtle)',
                            }}
                          >
                            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                                <Badge variant="outline">Topic {les.sequence_order}</Badge>
                                <span style={{ fontSize: '13px', fontWeight: 600, color: 'var(--text-primary)' }}>
                                  {les.title}
                                </span>
                                <Badge variant="default">{les.lesson_type}</Badge>
                                <span style={{ fontSize: '11px', color: 'var(--text-muted)' }}>
                                  {les.duration_minutes} min
                                </span>
                              </div>

                              {canEdit && ['DRAFT', 'IN_REVIEW'].includes(selectedCurriculumDetail.status) && (
                                <Button
                                  variant="outline"
                                  size="sm"
                                  onClick={() => {
                                    setActiveLessonId(les.id);
                                    setModalType('resource');
                                  }}
                                >
                                  + Attach Resource
                                </Button>
                              )}
                            </div>

                            {/* Learning Resources */}
                            {les.learning_resources && les.learning_resources.length > 0 && (
                              <div style={{ marginTop: '8px', paddingLeft: '12px', display: 'flex', flexWrap: 'wrap', gap: '6px' }}>
                                {les.learning_resources.map((res) => (
                                  <div
                                    key={res.id}
                                    style={{
                                      display: 'inline-flex',
                                      alignItems: 'center',
                                      gap: '6px',
                                      fontSize: '11px',
                                      padding: '2px 8px',
                                      backgroundColor: 'var(--bg-surface)',
                                      border: '1px solid var(--border-subtle)',
                                      borderRadius: 'var(--radius-sm)',
                                      color: 'var(--text-secondary)',
                                    }}
                                  >
                                    <Badge variant="info">{res.resource_type}</Badge>
                                    <span>{res.title}</span>
                                    {res.storage_uri && <span style={{ color: 'var(--text-muted)' }}>[Storage]</span>}
                                    {res.external_url && (
                                      <a
                                        href={res.external_url}
                                        target="_blank"
                                        rel="noopener noreferrer"
                                        style={{ color: 'var(--brand-primary)', textDecoration: 'underline' }}
                                      >
                                        Link
                                      </a>
                                    )}
                                  </div>
                                ))}
                              </div>
                            )}
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                </div>
              ))
            )}
          </div>
        </div>
      ) : null}

      {/* 1. Add Curriculum Modal */}
      <Dialog isOpen={modalType === 'curriculum'} onClose={resetForms} title="New Curriculum Version">
        <form onSubmit={handleCreateCurriculum} style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
          {formError && <Alert variant="danger">{formError}</Alert>}
          <Input
            label="Curriculum Title"
            placeholder="e.g. Master Syllabus 2026-2027"
            value={currTitle}
            onChange={(e) => setCurrTitle(e.target.value)}
            required
          />
          <Input
            label="Description"
            placeholder="Scope, pedagogical approach, prerequisites..."
            value={currDesc}
            onChange={(e) => setCurrDesc(e.target.value)}
          />
          <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
            <label style={{ fontSize: '13px', fontWeight: 500, color: 'var(--text-primary)' }}>
              Course Learning Objectives (One per line)
            </label>
            <textarea
              style={{
                width: '100%',
                minHeight: '80px',
                padding: '8px 12px',
                fontSize: '13px',
                borderRadius: 'var(--radius-md)',
                border: '1px solid var(--border-default)',
                backgroundColor: 'var(--bg-surface)',
                color: 'var(--text-primary)',
              }}
              placeholder="Analyze fundamental data structures&#10;Implement dynamic programming algorithms"
              value={currObjectives}
              onChange={(e) => setCurrObjectives(e.target.value)}
            />
          </div>
          <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '8px', marginTop: '12px' }}>
            <Button variant="outline" type="button" onClick={resetForms}>
              Cancel
            </Button>
            <Button variant="primary" type="submit" isLoading={formSubmitting}>
              Create Version
            </Button>
          </div>
        </form>
      </Dialog>

      {/* 2. Add Module Modal */}
      <Dialog isOpen={modalType === 'module'} onClose={resetForms} title="Add Instructional Module">
        <form onSubmit={handleCreateModule} style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
          {formError && <Alert variant="danger">{formError}</Alert>}
          <Input
            label="Module Title"
            placeholder="e.g. Unit 1: Graph Theory & Shortest Path Algorithms"
            value={modTitle}
            onChange={(e) => setModTitle(e.target.value)}
            required
          />
          <div style={{ display: 'flex', gap: '12px' }}>
            <div style={{ flex: 1 }}>
              <Input
                label="Sequence Order"
                type="number"
                min={1}
                value={modSeq}
                onChange={(e) => setModSeq(Number(e.target.value))}
                required
              />
            </div>
            <div style={{ flex: 1 }}>
              <Input
                label="Estimated Hours"
                type="number"
                step="0.5"
                min={0}
                value={modHours}
                onChange={(e) => setModHours(Number(e.target.value))}
                required
              />
            </div>
          </div>
          <Input
            label="Module Description"
            placeholder="Brief syllabus overview for this unit..."
            value={modDesc}
            onChange={(e) => setModDesc(e.target.value)}
          />
          <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '8px', marginTop: '12px' }}>
            <Button variant="outline" type="button" onClick={resetForms}>
              Cancel
            </Button>
            <Button variant="primary" type="submit" isLoading={formSubmitting}>
              Add Module
            </Button>
          </div>
        </form>
      </Dialog>

      {/* 3. Add Lesson Modal */}
      <Dialog isOpen={modalType === 'lesson'} onClose={resetForms} title="Add Lesson / Syllabus Topic">
        <form onSubmit={handleCreateLesson} style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
          {formError && <Alert variant="danger">{formError}</Alert>}
          <Input
            label="Lesson Title"
            placeholder="e.g. Dijkstra's Algorithm & Priority Queues"
            value={lesTitle}
            onChange={(e) => setLesTitle(e.target.value)}
            required
          />
          <div style={{ display: 'flex', gap: '12px' }}>
            <div style={{ flex: 1 }}>
              <Input
                label="Sequence Order"
                type="number"
                min={1}
                value={lesSeq}
                onChange={(e) => setLesSeq(Number(e.target.value))}
                required
              />
            </div>
            <div style={{ flex: 1 }}>
              <Select
                label="Lesson Type"
                value={lesType}
                onChange={(e) => setLesType(e.target.value)}
                options={[
                  { value: 'THEORY', label: 'Theory / Lecture' },
                  { value: 'LAB', label: 'Laboratory' },
                  { value: 'TUTORIAL', label: 'Tutorial' },
                  { value: 'WORKSHOP', label: 'Workshop' },
                  { value: 'READING', label: 'Reading' },
                ]}
              />
            </div>
            <div style={{ flex: 1 }}>
              <Input
                label="Duration (min)"
                type="number"
                min={1}
                value={lesMinutes}
                onChange={(e) => setLesMinutes(Number(e.target.value))}
                required
              />
            </div>
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
            <label style={{ fontSize: '13px', fontWeight: 500, color: 'var(--text-primary)' }}>
              Content / Lecture Outline (Markdown)
            </label>
            <textarea
              style={{
                width: '100%',
                minHeight: '80px',
                padding: '8px 12px',
                fontSize: '13px',
                borderRadius: 'var(--radius-md)',
                border: '1px solid var(--border-default)',
                backgroundColor: 'var(--bg-surface)',
                color: 'var(--text-primary)',
              }}
              placeholder="### Overview&#10;- Greedy choice property&#10;- Min-heap time complexity analysis"
              value={lesMarkdown}
              onChange={(e) => setLesMarkdown(e.target.value)}
            />
          </div>
          <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '8px', marginTop: '12px' }}>
            <Button variant="outline" type="button" onClick={resetForms}>
              Cancel
            </Button>
            <Button variant="primary" type="submit" isLoading={formSubmitting}>
              Add Lesson
            </Button>
          </div>
        </form>
      </Dialog>

      {/* 4. Add Learning Resource Modal */}
      <Dialog isOpen={modalType === 'resource'} onClose={resetForms} title="Attach Learning Resource">
        <form onSubmit={handleCreateResource} style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
          {formError && <Alert variant="danger">{formError}</Alert>}
          <Input
            label="Resource Title"
            placeholder="e.g. Graph Algorithms Presentation Slides PDF"
            value={resTitle}
            onChange={(e) => setResTitle(e.target.value)}
            required
          />
          <Select
            label="Resource Type"
            value={resType}
            onChange={(e) => setResType(e.target.value)}
            options={[
              { value: 'DOCUMENT', label: 'Document / PDF' },
              { value: 'SLIDE', label: 'Lecture Slides' },
              { value: 'CODE', label: 'Code Repository' },
              { value: 'VIDEO', label: 'Lecture Video' },
              { value: 'EXTERNAL_LINK', label: 'External Link' },
              { value: 'REFERENCE', label: 'Textbook Reference' },
            ]}
          />
          <Input
            label="Storage URI (Optional)"
            placeholder="s3://curriculum/course-materials/slides.pdf"
            value={resUri}
            onChange={(e) => setResUri(e.target.value)}
          />
          <Input
            label="External URL (Optional)"
            placeholder="https://mit.edu/courses/graphs"
            value={resUrl}
            onChange={(e) => setResUrl(e.target.value)}
          />
          <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '8px', marginTop: '12px' }}>
            <Button variant="outline" type="button" onClick={resetForms}>
              Cancel
            </Button>
            <Button variant="primary" type="submit" isLoading={formSubmitting}>
              Attach Resource
            </Button>
          </div>
        </form>
      </Dialog>
    </div>
  );
}
