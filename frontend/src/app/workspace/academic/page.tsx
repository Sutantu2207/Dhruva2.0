'use client';

import React, { useEffect, useState, useMemo } from 'react';
import { useAuth } from '@/lib/auth/AuthContext';
import { api, ApiError } from '@/lib/api/client';
import {
  Department,
  Program,
  AcademicYear,
  Semester,
  Batch,
  Section,
  Course,
  CourseOffering,
} from '@/types/academic';
import { PageHeader } from '@/components/ui/PageHeader';
import { Tabs } from '@/components/ui/Tabs';
import { Button } from '@/components/ui/Button';
import { Table, Column } from '@/components/ui/Table';
import { Badge } from '@/components/ui/Badge';
import { EmptyState } from '@/components/ui/EmptyState';
import { ErrorState } from '@/components/ui/ErrorState';
import { Dialog } from '@/components/ui/Dialog';
import { Input } from '@/components/ui/Input';
import { Select } from '@/components/ui/Select';
import { Alert } from '@/components/ui/Alert';

export default function AcademicStructurePage() {
  const { user } = useAuth();
  const [activeTab, setActiveTab] = useState<'departments' | 'calendar' | 'cohorts' | 'courses'>('departments');

  // Tenant slug resolution
  const tenantSlug = user?.institution_slug || '';

  // Role permissions
  const canManage = useMemo(() => {
    if (!user) return false;
    return user.roles.some((r) => ['SUPER_ADMIN', 'INSTITUTION_ADMIN', 'HOD'].includes(r));
  }, [user]);

  // Data states
  const [departments, setDepartments] = useState<Department[]>([]);
  const [programs, setPrograms] = useState<Program[]>([]);
  const [academicYears, setAcademicYears] = useState<AcademicYear[]>([]);
  const [semesters, setSemesters] = useState<Semester[]>([]);
  const [batches, setBatches] = useState<Batch[]>([]);
  const [courses, setCourses] = useState<Course[]>([]);
  const [offerings, setOfferings] = useState<CourseOffering[]>([]);

  // Page state
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [error, setError] = useState<{ message: string; code?: string; requestId?: string } | null>(null);
  const [searchQuery, setSearchQuery] = useState<string>('');

  // Dialog state
  const [modalType, setModalType] = useState<
    'department' | 'program' | 'academicYear' | 'semester' | 'batch' | 'course' | 'offering' | null
  >(null);
  const [formSubmitting, setFormSubmitting] = useState<boolean>(false);
  const [formError, setFormError] = useState<string | null>(null);

  // Form Fields
  const [deptCode, setDeptCode] = useState('');
  const [deptName, setDeptName] = useState('');

  const [progDeptId, setProgDeptId] = useState('');
  const [progCode, setProgCode] = useState('');
  const [progName, setProgName] = useState('');
  const [progDegree, setProgDegree] = useState('UNDERGRADUATE');
  const [progSemesters, setProgSemesters] = useState(8);

  const [ayCode, setAyCode] = useState('');
  const [ayName, setAyName] = useState('');
  const [ayStart, setAyStart] = useState('');
  const [ayEnd, setAyEnd] = useState('');
  const [ayCurrent, setAyCurrent] = useState(false);

  const [semAyId, setSemAyId] = useState('');
  const [semTerm, setSemTerm] = useState(1);
  const [semName, setSemName] = useState('');
  const [semStart, setSemStart] = useState('');
  const [semEnd, setSemEnd] = useState('');

  const [batchProgId, setBatchProgId] = useState('');
  const [batchName, setBatchName] = useState('');
  const [batchAdmission, setBatchAdmission] = useState(2026);
  const [batchGraduation, setBatchGraduation] = useState(2030);

  const [courseDeptId, setCourseDeptId] = useState('');
  const [courseCode, setCourseCode] = useState('');
  const [courseTitle, setCourseTitle] = useState('');
  const [courseCredits, setCourseCredits] = useState(3.0);
  const [courseType, setCourseType] = useState('THEORY');

  const [offCourseId, setOffCourseId] = useState('');
  const [offAyId, setOffAyId] = useState('');
  const [offSemId, setOffSemId] = useState('');

  const loadData = async () => {
    if (!tenantSlug) {
      setIsLoading(false);
      return;
    }
    setIsLoading(true);
    setError(null);
    try {
      const [deptRes, progRes, ayRes, batchRes, courseRes, offRes] = await Promise.all([
        api.get<Department[]>(`/institutions/${tenantSlug}/departments`),
        api.get<Program[]>(`/institutions/${tenantSlug}/programs`),
        api.get<AcademicYear[]>(`/institutions/${tenantSlug}/academic-years`),
        api.get<Batch[]>(`/institutions/${tenantSlug}/batches`),
        api.get<Course[]>(`/institutions/${tenantSlug}/courses`),
        api.get<CourseOffering[]>(`/institutions/${tenantSlug}/offerings`),
      ]);
      setDepartments(deptRes);
      setPrograms(progRes);
      setAcademicYears(ayRes);
      setBatches(batchRes);
      setCourses(courseRes);
      setOfferings(offRes);
    } catch (err) {
      if (err instanceof ApiError) {
        setError({ message: err.message, code: err.code, requestId: err.requestId });
      } else {
        setError({ message: 'Failed to retrieve academic hierarchy data. Please verify connectivity.' });
      }
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, [tenantSlug]);

  const resetForms = () => {
    setModalType(null);
    setFormError(null);
    setFormSubmitting(false);
    setDeptCode('');
    setDeptName('');
    setProgDeptId('');
    setProgCode('');
    setProgName('');
    setProgDegree('UNDERGRADUATE');
    setProgSemesters(8);
    setAyCode('');
    setAyName('');
    setAyStart('');
    setAyEnd('');
    setAyCurrent(false);
    setSemAyId('');
    setSemTerm(1);
    setSemName('');
    setSemStart('');
    setSemEnd('');
    setBatchProgId('');
    setBatchName('');
    setCourseDeptId('');
    setCourseCode('');
    setCourseTitle('');
    setCourseCredits(3.0);
    setCourseType('THEORY');
    setOffCourseId('');
    setOffAyId('');
    setOffSemId('');
  };

  const handleCreateDepartment = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!deptCode.trim() || !deptName.trim()) {
      setFormError('Department code and name are required.');
      return;
    }
    setFormSubmitting(true);
    setFormError(null);
    try {
      await api.post(`/institutions/${tenantSlug}/departments`, {
        code: deptCode.trim().toUpperCase(),
        name: deptName.trim(),
      });
      resetForms();
      await loadData();
    } catch (err: unknown) {
      setFormError(err instanceof ApiError ? err.message : 'Error creating department');
    } finally {
      setFormSubmitting(false);
    }
  };

  const handleCreateProgram = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!progDeptId || !progCode.trim() || !progName.trim()) {
      setFormError('Department, program code, and program name are required.');
      return;
    }
    setFormSubmitting(true);
    setFormError(null);
    try {
      await api.post(`/institutions/${tenantSlug}/programs`, {
        department_id: progDeptId,
        code: progCode.trim().toUpperCase(),
        name: progName.trim(),
        degree_level: progDegree,
        total_semesters: Number(progSemesters),
      });
      resetForms();
      await loadData();
    } catch (err: unknown) {
      setFormError(err instanceof ApiError ? err.message : 'Error creating program');
    } finally {
      setFormSubmitting(false);
    }
  };

  const handleCreateAcademicYear = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!ayCode.trim() || !ayName.trim() || !ayStart || !ayEnd) {
      setFormError('All academic year fields are required.');
      return;
    }
    setFormSubmitting(true);
    setFormError(null);
    try {
      await api.post(`/institutions/${tenantSlug}/academic-years`, {
        code: ayCode.trim().toUpperCase(),
        name: ayName.trim(),
        start_date: ayStart,
        end_date: ayEnd,
        is_current: ayCurrent,
      });
      resetForms();
      await loadData();
    } catch (err: unknown) {
      setFormError(err instanceof ApiError ? err.message : 'Error creating academic year');
    } finally {
      setFormSubmitting(false);
    }
  };

  const handleCreateCourse = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!courseDeptId || !courseCode.trim() || !courseTitle.trim()) {
      setFormError('Department, course code, and title are required.');
      return;
    }
    setFormSubmitting(true);
    setFormError(null);
    try {
      await api.post(`/institutions/${tenantSlug}/courses`, {
        department_id: courseDeptId,
        code: courseCode.trim().toUpperCase(),
        title: courseTitle.trim(),
        credits: Number(courseCredits),
        course_type: courseType,
      });
      resetForms();
      await loadData();
    } catch (err: unknown) {
      setFormError(err instanceof ApiError ? err.message : 'Error creating course');
    } finally {
      setFormSubmitting(false);
    }
  };

  // Table Columns
  const departmentColumns: Column<Department>[] = [
    { key: 'code', header: 'Code', width: '120px', render: (d) => <Badge variant="outline">{d.code}</Badge> },
    { key: 'name', header: 'Department Name' },
    {
      key: 'status',
      header: 'Status',
      width: '120px',
      render: (d) => <Badge variant={d.status === 'ACTIVE' ? 'success' : 'default'}>{d.status}</Badge>,
    },
    { key: 'created_at', header: 'Created', width: '160px', render: (d) => new Date(d.created_at).toLocaleDateString() },
  ];

  const programColumns: Column<Program>[] = [
    { key: 'code', header: 'Code', width: '140px', render: (p) => <Badge variant="outline">{p.code}</Badge> },
    { key: 'name', header: 'Program Name' },
    { key: 'degree_level', header: 'Degree Level', width: '160px' },
    { key: 'total_semesters', header: 'Semesters', width: '100px', render: (p) => `${p.total_semesters} terms` },
    {
      key: 'status',
      header: 'Status',
      width: '120px',
      render: (p) => <Badge variant={p.status === 'ACTIVE' ? 'success' : 'default'}>{p.status}</Badge>,
    },
  ];

  const calendarColumns: Column<AcademicYear>[] = [
    { key: 'code', header: 'Code', width: '140px', render: (y) => <Badge variant="outline">{y.code}</Badge> },
    { key: 'name', header: 'Academic Year' },
    { key: 'start_date', header: 'Start Date', width: '140px' },
    { key: 'end_date', header: 'End Date', width: '140px' },
    {
      key: 'is_current',
      header: 'Current',
      width: '100px',
      render: (y) => (y.is_current ? <Badge variant="info">Active</Badge> : <span style={{ color: 'var(--text-muted)' }}>—</span>),
    },
  ];

  const batchColumns: Column<Batch>[] = [
    { key: 'name', header: 'Cohort Name' },
    { key: 'admission_year', header: 'Admission Year', width: '160px' },
    { key: 'graduation_year', header: 'Graduation Year', width: '160px' },
    { key: 'created_at', header: 'Registered', width: '160px', render: (b) => new Date(b.created_at).toLocaleDateString() },
  ];

  const courseColumns: Column<Course>[] = [
    { key: 'code', header: 'Course Code', width: '120px', render: (c) => <Badge variant="outline">{c.code}</Badge> },
    { key: 'title', header: 'Title' },
    { key: 'credits', header: 'Credits', width: '100px', render: (c) => `${c.credits} cr` },
    { key: 'course_type', header: 'Type', width: '120px' },
    { key: 'created_at', header: 'Added', width: '140px', render: (c) => new Date(c.created_at).toLocaleDateString() },
  ];

  // Filtered Lists
  const filteredDepartments = useMemo(() => {
    return departments.filter(
      (d) =>
        d.code.toLowerCase().includes(searchQuery.toLowerCase()) ||
        d.name.toLowerCase().includes(searchQuery.toLowerCase())
    );
  }, [departments, searchQuery]);

  const filteredPrograms = useMemo(() => {
    return programs.filter(
      (p) =>
        p.code.toLowerCase().includes(searchQuery.toLowerCase()) ||
        p.name.toLowerCase().includes(searchQuery.toLowerCase())
    );
  }, [programs, searchQuery]);

  const filteredYears = useMemo(() => {
    return academicYears.filter(
      (y) =>
        y.code.toLowerCase().includes(searchQuery.toLowerCase()) ||
        y.name.toLowerCase().includes(searchQuery.toLowerCase())
    );
  }, [academicYears, searchQuery]);

  const filteredCourses = useMemo(() => {
    return courses.filter(
      (c) =>
        c.code.toLowerCase().includes(searchQuery.toLowerCase()) ||
        c.title.toLowerCase().includes(searchQuery.toLowerCase())
    );
  }, [courses, searchQuery]);

  if (!tenantSlug) {
    return (
      <div>
        <PageHeader title="Academic Structure" description="Institutional organization and curriculum catalog" />
        <Alert variant="warning" title="No Institution Scope Bound">
          Your current user session is not associated with an institution tenant partition. Super-administrators must select or bind a tenant scope to view academic entities.
        </Alert>
      </div>
    );
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
      <PageHeader
        title="Academic Structure & Catalog"
        description={`Manage departmental hierarchy, degree programs, cohorts, and curriculum for tenant '${tenantSlug}'`}
        action={
          canManage ? (
            <div style={{ display: 'flex', gap: '8px' }}>
              {activeTab === 'departments' && (
                <>
                  <Button variant="primary" size="sm" onClick={() => setModalType('department')}>
                    + Add Department
                  </Button>
                  <Button variant="secondary" size="sm" onClick={() => setModalType('program')}>
                    + Add Program
                  </Button>
                </>
              )}
              {activeTab === 'calendar' && (
                <Button variant="primary" size="sm" onClick={() => setModalType('academicYear')}>
                  + Add Academic Year
                </Button>
              )}
              {activeTab === 'courses' && (
                <Button variant="primary" size="sm" onClick={() => setModalType('course')}>
                  + Add Course
                </Button>
              )}
            </div>
          ) : undefined
        }
      />

      <Tabs
        tabs={[
          { id: 'departments', label: 'Departments & Programs', count: departments.length },
          { id: 'calendar', label: 'Calendar & Terms', count: academicYears.length },
          { id: 'cohorts', label: 'Batches & Cohorts', count: batches.length },
          { id: 'courses', label: 'Course Catalog', count: courses.length },
        ]}
        activeTab={activeTab}
        onChange={(tab) => {
          setActiveTab(tab as typeof activeTab);
          setSearchQuery('');
        }}
      />

      {/* Search / Filter toolbar */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: '16px' }}>
        <div style={{ width: '320px' }}>
          <Input
            placeholder={`Filter ${activeTab}...`}
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
          />
        </div>
        {!canManage && (
          <Badge variant="default">Read-Only Access</Badge>
        )}
      </div>

      {/* Loading & Error States */}
      {isLoading ? (
        <div style={{ padding: '48px', textAlign: 'center', color: 'var(--text-secondary)' }}>
          Loading academic structures...
        </div>
      ) : error ? (
        <ErrorState
          title="Failed to Load Academic Records"
          message={error.message}
          code={error.code}
          requestId={error.requestId}
          onRetry={loadData}
        />
      ) : (
        <>
          {/* TAB: DEPARTMENTS & PROGRAMS */}
          {activeTab === 'departments' && (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '28px' }}>
              <div>
                <h3 style={{ fontSize: '15px', fontWeight: 600, marginBottom: '12px', color: 'var(--text-primary)' }}>
                  Academic Departments
                </h3>
                {filteredDepartments.length === 0 ? (
                  searchQuery ? (
                    <EmptyState
                      title="No matching departments"
                      description={`No department records matched query '${searchQuery}'`}
                    />
                  ) : (
                    <EmptyState
                      title="No departments registered"
                      description="Create academic departments (e.g. Computer Science, Mechanical) to organize programs."
                      actionLabel={canManage ? '+ Add Department' : undefined}
                      onAction={canManage ? () => setModalType('department') : undefined}
                    />
                  )
                ) : (
                  <Table
                    columns={departmentColumns}
                    data={filteredDepartments}
                    keyExtractor={(d) => d.id}
                  />
                )}
              </div>

              <div>
                <h3 style={{ fontSize: '15px', fontWeight: 600, marginBottom: '12px', color: 'var(--text-primary)' }}>
                  Degree Programs
                </h3>
                {filteredPrograms.length === 0 ? (
                  searchQuery ? (
                    <EmptyState
                      title="No matching programs"
                      description={`No degree program records matched query '${searchQuery}'`}
                    />
                  ) : (
                    <EmptyState
                      title="No programs registered"
                      description="Degree programs (e.g. B.Tech, M.Tech) define curriculum structures within departments."
                      actionLabel={canManage ? '+ Add Program' : undefined}
                      onAction={canManage ? () => setModalType('program') : undefined}
                    />
                  )
                ) : (
                  <Table
                    columns={programColumns}
                    data={filteredPrograms}
                    keyExtractor={(p) => p.id}
                  />
                )}
              </div>
            </div>
          )}

          {/* TAB: CALENDAR & TERMS */}
          {activeTab === 'calendar' && (
            <div>
              <h3 style={{ fontSize: '15px', fontWeight: 600, marginBottom: '12px', color: 'var(--text-primary)' }}>
                Academic Calendar Years
              </h3>
              {filteredYears.length === 0 ? (
                searchQuery ? (
                  <EmptyState
                    title="No matching calendar years"
                    description={`No academic year records matched '${searchQuery}'`}
                  />
                ) : (
                  <EmptyState
                    title="No academic years scheduled"
                    description="Configure academic years and terms to schedule courses and student enrollments."
                    actionLabel={canManage ? '+ Add Academic Year' : undefined}
                    onAction={canManage ? () => setModalType('academicYear') : undefined}
                  />
                )
              ) : (
                <Table
                  columns={calendarColumns}
                  data={filteredYears}
                  keyExtractor={(y) => y.id}
                />
              )}
            </div>
          )}

          {/* TAB: BATCHES */}
          {activeTab === 'cohorts' && (
            <div>
              <h3 style={{ fontSize: '15px', fontWeight: 600, marginBottom: '12px', color: 'var(--text-primary)' }}>
                Intake Batches & Cohorts
              </h3>
              {batches.length === 0 ? (
                <EmptyState
                  title="No cohorts registered"
                  description="Batches track student admission cohorts and section divisions."
                />
              ) : (
                <Table
                  columns={batchColumns}
                  data={batches}
                  keyExtractor={(b) => b.id}
                />
              )}
            </div>
          )}

          {/* TAB: COURSES */}
          {activeTab === 'courses' && (
            <div>
              <h3 style={{ fontSize: '15px', fontWeight: 600, marginBottom: '12px', color: 'var(--text-primary)' }}>
                Institutional Course Catalog
              </h3>
              {filteredCourses.length === 0 ? (
                searchQuery ? (
                  <EmptyState
                    title="No matching courses"
                    description={`No catalog courses matched query '${searchQuery}'`}
                  />
                ) : (
                  <EmptyState
                    title="Course catalog is empty"
                    description="Define accredited courses with credit weightings, theory/lab types, and syllabus requirements."
                    actionLabel={canManage ? '+ Add Course' : undefined}
                    onAction={canManage ? () => setModalType('course') : undefined}
                  />
                )
              ) : (
                <Table
                  columns={courseColumns}
                  data={filteredCourses}
                  keyExtractor={(c) => c.id}
                />
              )}
            </div>
          )}
        </>
      )}

      {/* CREATION MODALS */}
      {/* 1. Add Department Modal */}
      <Dialog
        isOpen={modalType === 'department'}
        onClose={resetForms}
        title="Create Academic Department"
      >
        <form onSubmit={handleCreateDepartment} style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
          {formError && <Alert variant="danger">{formError}</Alert>}
          <Input
            label="Department Code"
            placeholder="e.g. CSE, MECH, BIO"
            value={deptCode}
            onChange={(e) => setDeptCode(e.target.value)}
            required
          />
          <Input
            label="Department Name"
            placeholder="e.g. Computer Science and Engineering"
            value={deptName}
            onChange={(e) => setDeptName(e.target.value)}
            required
          />
          <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '8px', marginTop: '12px' }}>
            <Button variant="outline" type="button" onClick={resetForms}>
              Cancel
            </Button>
            <Button variant="primary" type="submit" isLoading={formSubmitting}>
              Create Department
            </Button>
          </div>
        </form>
      </Dialog>

      {/* 2. Add Program Modal */}
      <Dialog
        isOpen={modalType === 'program'}
        onClose={resetForms}
        title="Create Degree Program"
      >
        <form onSubmit={handleCreateProgram} style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
          {formError && <Alert variant="danger">{formError}</Alert>}
          <Select
            label="Department"
            value={progDeptId}
            onChange={(e) => setProgDeptId(e.target.value)}
            options={[
              { value: '', label: 'Select Department...' },
              ...departments.map((d) => ({ value: d.id, label: `${d.code} — ${d.name}` })),
            ]}
            required
          />
          <Input
            label="Program Code"
            placeholder="e.g. BTECH-CSE"
            value={progCode}
            onChange={(e) => setProgCode(e.target.value)}
            required
          />
          <Input
            label="Program Name"
            placeholder="e.g. Bachelor of Technology in Computer Science"
            value={progName}
            onChange={(e) => setProgName(e.target.value)}
            required
          />
          <Select
            label="Degree Level"
            value={progDegree}
            onChange={(e) => setProgDegree(e.target.value)}
            options={[
              { value: 'UNDERGRADUATE', label: 'Undergraduate' },
              { value: 'POSTGRADUATE', label: 'Postgraduate' },
              { value: 'DIPLOMA', label: 'Diploma' },
              { value: 'DOCTORAL', label: 'Doctoral' },
            ]}
          />
          <Input
            label="Total Terms / Semesters"
            type="number"
            min={1}
            max={16}
            value={progSemesters}
            onChange={(e) => setProgSemesters(Number(e.target.value))}
            required
          />
          <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '8px', marginTop: '12px' }}>
            <Button variant="outline" type="button" onClick={resetForms}>
              Cancel
            </Button>
            <Button variant="primary" type="submit" isLoading={formSubmitting}>
              Create Program
            </Button>
          </div>
        </form>
      </Dialog>

      {/* 3. Add Academic Year Modal */}
      <Dialog
        isOpen={modalType === 'academicYear'}
        onClose={resetForms}
        title="Schedule Academic Year"
      >
        <form onSubmit={handleCreateAcademicYear} style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
          {formError && <Alert variant="danger">{formError}</Alert>}
          <Input
            label="Academic Year Code"
            placeholder="e.g. AY-2026-2027"
            value={ayCode}
            onChange={(e) => setAyCode(e.target.value)}
            required
          />
          <Input
            label="Display Name"
            placeholder="e.g. Academic Year 2026-2027"
            value={ayName}
            onChange={(e) => setAyName(e.target.value)}
            required
          />
          <Input
            label="Start Date"
            type="date"
            value={ayStart}
            onChange={(e) => setAyStart(e.target.value)}
            required
          />
          <Input
            label="End Date"
            type="date"
            value={ayEnd}
            onChange={(e) => setAyEnd(e.target.value)}
            required
          />
          <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '8px', marginTop: '12px' }}>
            <Button variant="outline" type="button" onClick={resetForms}>
              Cancel
            </Button>
            <Button variant="primary" type="submit" isLoading={formSubmitting}>
              Schedule Year
            </Button>
          </div>
        </form>
      </Dialog>

      {/* 4. Add Course Modal */}
      <Dialog
        isOpen={modalType === 'course'}
        onClose={resetForms}
        title="Register Catalog Course"
      >
        <form onSubmit={handleCreateCourse} style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
          {formError && <Alert variant="danger">{formError}</Alert>}
          <Select
            label="Offering Department"
            value={courseDeptId}
            onChange={(e) => setCourseDeptId(e.target.value)}
            options={[
              { value: '', label: 'Select Department...' },
              ...departments.map((d) => ({ value: d.id, label: `${d.code} — ${d.name}` })),
            ]}
            required
          />
          <Input
            label="Course Code"
            placeholder="e.g. CS201"
            value={courseCode}
            onChange={(e) => setCourseCode(e.target.value)}
            required
          />
          <Input
            label="Course Title"
            placeholder="e.g. Data Structures and Algorithms"
            value={courseTitle}
            onChange={(e) => setCourseTitle(e.target.value)}
            required
          />
          <Input
            label="Credits"
            type="number"
            step="0.5"
            min={0}
            max={30}
            value={courseCredits}
            onChange={(e) => setCourseCredits(Number(e.target.value))}
            required
          />
          <Select
            label="Course Type"
            value={courseType}
            onChange={(e) => setCourseType(e.target.value)}
            options={[
              { value: 'THEORY', label: 'Theory' },
              { value: 'LAB', label: 'Laboratory' },
              { value: 'SEMINAR', label: 'Seminar' },
              { value: 'PROJECT', label: 'Project' },
              { value: 'ELECTIVE', label: 'Elective' },
            ]}
          />
          <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '8px', marginTop: '12px' }}>
            <Button variant="outline" type="button" onClick={resetForms}>
              Cancel
            </Button>
            <Button variant="primary" type="submit" isLoading={formSubmitting}>
              Register Course
            </Button>
          </div>
        </form>
      </Dialog>
    </div>
  );
}
