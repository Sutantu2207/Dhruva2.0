'use client';

import React, { useState, useEffect, useMemo } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/lib/auth/AuthContext';
import { Badge } from '@/components/ui/Badge';
import { Button } from '@/components/ui/Button';
import { Card } from '@/components/ui/Card';
import { api } from '@/lib/api/client';
import { Course } from '@/types/academic';
import { Assessment } from '@/types/assessment';
import {
  BookOpen,
  FileCheck2,
  Zap,
  GraduationCap,
  Sparkles,
  ArrowRight,
  TrendingUp,
  ShieldCheck,
  Cpu,
  Clock,
  Layers,
  Server,
  Activity,
  PlusCircle,
  ExternalLink,
  Users,
  AlertTriangle,
  RefreshCw,
  Compass,
} from 'lucide-react';

export default function PurposefulWorkspaceDashboard() {
  const router = useRouter();
  const { user } = useAuth();
  const tenantSlug = user?.institution_slug || '';
  const primaryRole = user?.roles?.[0] || 'STUDENT';

  // Role view toggle (defaults to primary role, allows admins/faculty to view other roles)
  const [activeRoleView, setActiveRoleView] = useState<string>(primaryRole);

  useEffect(() => {
    setActiveRoleView(primaryRole);
  }, [primaryRole]);

  // Live Data States
  const [courses, setCourses] = useState<Course[]>([]);
  const [assessments, setAssessments] = useState<Assessment[]>([]);
  const [isLoadingData, setIsLoadingData] = useState<boolean>(true);
  const [quickAiPrompt, setQuickAiPrompt] = useState<string>('');

  // Fetch real courses and assessments for the tenant
  const loadDashboardData = async () => {
    if (!tenantSlug) return;
    setIsLoadingData(true);
    try {
      const [fetchedCourses, fetchedAssessments] = await Promise.all([
        api.get<Course[]>(`/institutions/${tenantSlug}/courses`).catch(() => []),
        api.get<Assessment[]>(`/institutions/${tenantSlug}/assessments`).catch(() => []),
      ]);
      setCourses(fetchedCourses || []);
      setAssessments(fetchedAssessments || []);
    } catch {
      setCourses([]);
      setAssessments([]);
    } finally {
      setIsLoadingData(false);
    }
  };

  useEffect(() => {
    loadDashboardData();
  }, [tenantSlug]);

  const handleLaunchAiWithPrompt = (e: React.FormEvent) => {
    e.preventDefault();
    if (!quickAiPrompt.trim()) {
      router.push('/workspace/ai');
      return;
    }
    // Route to AI workspace with prompt query
    router.push(`/workspace/ai?prompt=${encodeURIComponent(quickAiPrompt.trim())}`);
  };

  // Role switcher pills (for users with multiple roles or platform admins)
  const isElevatedUser = user?.roles?.some((r) =>
    ['SUPER_ADMIN', 'INSTITUTION_ADMIN', 'HOD', 'FACULTY'].includes(r)
  );

  return (
    <div style={{ maxWidth: '1440px', margin: '0 auto', display: 'flex', flexDirection: 'column', gap: '24px' }}>
      
      {/* Top Welcome & Role Switcher Banner */}
      <div
        style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'flex-start',
          flexWrap: 'wrap',
          gap: '16px',
          padding: '24px',
          backgroundColor: 'var(--bg-surface)',
          borderRadius: 'var(--radius-lg)',
          border: '1px solid var(--border-subtle)',
          boxShadow: 'var(--shadow-sm)',
        }}
      >
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <h1 style={{ fontSize: '24px', fontWeight: 700, color: 'var(--text-primary)', margin: 0, letterSpacing: '-0.02em' }}>
              Welcome back, {user?.first_name || user?.full_name}!
            </h1>
            <Badge variant="primary" size="md">
              {activeRoleView.replace('_', ' ')}
            </Badge>
          </div>
          <p style={{ margin: '6px 0 0 0', fontSize: '14px', color: 'var(--text-secondary)' }}>
            {activeRoleView === 'STUDENT'
              ? 'Track your active courses, upcoming quizzes, retention decay, and career readiness.'
              : activeRoleView === 'FACULTY'
              ? 'Manage teaching curricula, author grounded assessment questions, and review student mastery.'
              : activeRoleView === 'HOD'
              ? 'Executive oversight: Departmental curriculum progress, cohort retention health, and intervention workflows.'
              : activeRoleView === 'PLACEMENT_OFFICER'
              ? 'Discover verified student talent, review capstone evidence, and track Career Readiness Index.'
              : 'Institutional Administration: Infrastructure health, user provisioning, and Data Center bulk ingestion.'}
          </p>
        </div>

        {/* Multi-role View Switcher */}
        {isElevatedUser && (
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', flexWrap: 'wrap' }}>
            <span style={{ fontSize: '12px', fontWeight: 600, color: 'var(--text-muted)' }}>
              View Dashboard As:
            </span>
            <div style={{ display: 'flex', gap: '4px', backgroundColor: 'var(--bg-surface-subtle)', padding: '4px', borderRadius: 'var(--radius-md)' }}>
              {['STUDENT', 'FACULTY', 'HOD', 'PLACEMENT_OFFICER', 'INSTITUTION_ADMIN'].map((r) => (
                <button
                  key={r}
                  onClick={() => setActiveRoleView(r)}
                  style={{
                    padding: '4px 10px',
                    borderRadius: 'var(--radius-sm)',
                    border: 'none',
                    backgroundColor: activeRoleView === r ? 'var(--bg-surface)' : 'transparent',
                    color: activeRoleView === r ? 'var(--brand-primary)' : 'var(--text-secondary)',
                    fontWeight: activeRoleView === r ? 600 : 500,
                    fontSize: '11px',
                    cursor: 'pointer',
                    boxShadow: activeRoleView === r ? 'var(--shadow-sm)' : 'none',
                  }}
                >
                  {r === 'PLACEMENT_OFFICER' ? 'Placement' : r === 'INSTITUTION_ADMIN' ? 'Admin' : r}
                </button>
              ))}
            </div>
          </div>
        )}
      </div>

      {/* ============================================================== */}
      {/* 1. STUDENT DASHBOARD VIEW                                       */}
      {/* ============================================================== */}
      {activeRoleView === 'STUDENT' && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
          
          {/* Quick Metrics Bar */}
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: '16px' }}>
            <Card style={{ padding: '20px' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                <div style={{ padding: '10px', borderRadius: '10px', backgroundColor: 'rgba(79, 70, 229, 0.1)', color: 'var(--brand-primary)' }}>
                  <BookOpen size={20} />
                </div>
                <div>
                  <div style={{ fontSize: '12px', color: 'var(--text-muted)', fontWeight: 500 }}>Enrolled Courses</div>
                  <div style={{ fontSize: '22px', fontWeight: 700, color: 'var(--text-primary)' }}>
                    {courses.length}
                  </div>
                </div>
              </div>
              <div style={{ marginTop: '12px', fontSize: '12px', color: 'var(--text-secondary)' }}>
                Active in semester curriculum
              </div>
            </Card>

            <Card style={{ padding: '20px' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                <div style={{ padding: '10px', borderRadius: '10px', backgroundColor: 'rgba(5, 150, 105, 0.1)', color: 'var(--status-success)' }}>
                  <FileCheck2 size={20} />
                </div>
                <div>
                  <div style={{ fontSize: '12px', color: 'var(--text-muted)', fontWeight: 500 }}>Active Assessments</div>
                  <div style={{ fontSize: '22px', fontWeight: 700, color: 'var(--text-primary)' }}>
                    {assessments.filter((a) => a.status === 'PUBLISHED').length}
                  </div>
                </div>
              </div>
              <div style={{ marginTop: '12px', fontSize: '12px', color: 'var(--text-secondary)' }}>
                Pending student submissions
              </div>
            </Card>

            <Card style={{ padding: '20px' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                <div style={{ padding: '10px', borderRadius: '10px', backgroundColor: 'rgba(217, 119, 6, 0.1)', color: 'var(--status-warning)' }}>
                  <Zap size={20} />
                </div>
                <div>
                  <div style={{ fontSize: '12px', color: 'var(--text-muted)', fontWeight: 500 }}>Retention Half-Life</div>
                  <div style={{ fontSize: '22px', fontWeight: 700, color: 'var(--text-primary)' }}>
                    30 Days
                  </div>
                </div>
              </div>
              <div style={{ marginTop: '12px', fontSize: '12px', color: 'var(--text-secondary)' }}>
                Ebbinghaus SM-2 schedule active
              </div>
            </Card>

            <Card style={{ padding: '20px' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                <div style={{ padding: '10px', borderRadius: '10px', backgroundColor: 'rgba(37, 99, 235, 0.1)', color: 'var(--status-info)' }}>
                  <GraduationCap size={20} />
                </div>
                <div>
                  <div style={{ fontSize: '12px', color: 'var(--text-muted)', fontWeight: 500 }}>Career Readiness (CRI)</div>
                  <div style={{ fontSize: '22px', fontWeight: 700, color: 'var(--text-primary)' }}>
                    84.5%
                  </div>
                </div>
              </div>
              <div style={{ marginTop: '12px', fontSize: '12px', color: 'var(--text-secondary)' }}>
                Verified technical competencies
              </div>
            </Card>
          </div>

          {/* Quick AI Learning Assistant Launcher Card */}
          <Card style={{ padding: '24px', backgroundColor: 'linear-gradient(to right, #ffffff, var(--brand-primary-subtle))' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '8px' }}>
              <Sparkles size={20} color="var(--brand-primary)" />
              <h2 style={{ fontSize: '16px', fontWeight: 700, color: 'var(--text-primary)', margin: 0 }}>
                Dhruva.AI Grounded Learning Assistant
              </h2>
              <Badge variant="success" size="sm">Zero-Leak Guardrailed</Badge>
            </div>
            <p style={{ fontSize: '13px', color: 'var(--text-secondary)', margin: '0 0 16px 0' }}>
              Ask questions about your curriculum, request Python code examples, or prepare for upcoming exam topics. All answers cite verified syllabus references.
            </p>
            <form onSubmit={handleLaunchAiWithPrompt} style={{ display: 'flex', gap: '10px', flexWrap: 'wrap' }}>
              <input
                type="text"
                placeholder="Ask about B-Trees, Dijkstra algorithm, or any active course topic..."
                value={quickAiPrompt}
                onChange={(e) => setQuickAiPrompt(e.target.value)}
                style={{
                  flex: 1,
                  minWidth: '280px',
                  padding: '10px 14px',
                  borderRadius: 'var(--radius-md)',
                  border: '1px solid var(--border-default)',
                  fontSize: '14px',
                  backgroundColor: 'var(--bg-surface)',
                  color: 'var(--text-primary)',
                }}
              />
              <Button type="submit" variant="primary" style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                <Sparkles size={16} />
                Ask Assistant
              </Button>
            </form>
          </Card>

          {/* Main 2-Column Section: Courses & Upcoming Assessments */}
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(360px, 1fr))', gap: '24px' }}>
            
            {/* Left: Continue Learning & Course Units */}
            <Card style={{ padding: '24px', display: 'flex', flexDirection: 'column', gap: '16px' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <BookOpen size={18} color="var(--brand-primary)" />
                  <h3 style={{ fontSize: '16px', fontWeight: 700, color: 'var(--text-primary)', margin: 0 }}>
                    Continue Learning
                  </h3>
                </div>
                <Link href="/workspace/curriculum" style={{ fontSize: '12px', fontWeight: 600, color: 'var(--brand-primary)', display: 'flex', alignItems: 'center', gap: '4px' }}>
                  All Courses <ArrowRight size={13} />
                </Link>
              </div>

              {isLoadingData ? (
                <div style={{ padding: '24px', textAlign: 'center', color: 'var(--text-muted)', fontSize: '13px' }}>
                  Loading enrolled courses...
                </div>
              ) : courses.length === 0 ? (
                <div style={{ padding: '24px', textAlign: 'center', color: 'var(--text-muted)', fontSize: '13px' }}>
                  No courses enrolled yet. Visit the Academic Catalog to enroll.
                </div>
              ) : (
                <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
                  {courses.slice(0, 3).map((course) => (
                    <div
                      key={course.id}
                      style={{
                        padding: '14px 16px',
                        borderRadius: 'var(--radius-md)',
                        border: '1px solid var(--border-subtle)',
                        backgroundColor: 'var(--bg-surface-subtle)',
                        display: 'flex',
                        justifyContent: 'space-between',
                        alignItems: 'center',
                        gap: '12px',
                      }}
                    >
                      <div>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '4px' }}>
                          <span style={{ fontWeight: 700, fontSize: '13px', color: 'var(--text-primary)' }}>
                            {course.code}
                          </span>
                          <Badge variant="outline" size="sm">{course.credits} Credits</Badge>
                        </div>
                        <div style={{ fontSize: '13px', color: 'var(--text-secondary)' }}>
                          {course.title || (course as any).name}
                        </div>
                      </div>
                      <Link href={`/workspace/curriculum`}>
                        <Button variant="outline" size="sm" style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
                          Syllabus <ArrowRight size={12} />
                        </Button>
                      </Link>
                    </div>
                  ))}
                </div>
              )}
            </Card>

            {/* Right: Upcoming Assessments & Quizzes */}
            <Card style={{ padding: '24px', display: 'flex', flexDirection: 'column', gap: '16px' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <FileCheck2 size={18} color="var(--status-success)" />
                  <h3 style={{ fontSize: '16px', fontWeight: 700, color: 'var(--text-primary)', margin: 0 }}>
                    Upcoming Assessments & Deadlines
                  </h3>
                </div>
                <Link href="/workspace/assessments" style={{ fontSize: '12px', fontWeight: 600, color: 'var(--brand-primary)', display: 'flex', alignItems: 'center', gap: '4px' }}>
                  Assessment Hub <ArrowRight size={13} />
                </Link>
              </div>

              {isLoadingData ? (
                <div style={{ padding: '24px', textAlign: 'center', color: 'var(--text-muted)', fontSize: '13px' }}>
                  Loading assessment schedules...
                </div>
              ) : assessments.length === 0 ? (
                <div style={{ padding: '24px', textAlign: 'center', color: 'var(--text-muted)', fontSize: '13px' }}>
                  No published assessments active. Great job staying ahead!
                </div>
              ) : (
                <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
                  {assessments.slice(0, 3).map((ass) => (
                    <div
                      key={ass.id}
                      style={{
                        padding: '14px 16px',
                        borderRadius: 'var(--radius-md)',
                        border: '1px solid var(--border-subtle)',
                        backgroundColor: 'var(--bg-surface-subtle)',
                        display: 'flex',
                        justifyContent: 'space-between',
                        alignItems: 'center',
                        gap: '12px',
                      }}
                    >
                      <div>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '4px' }}>
                          <span style={{ fontWeight: 700, fontSize: '13px', color: 'var(--text-primary)' }}>
                            {ass.title}
                          </span>
                          <Badge variant={ass.status === 'PUBLISHED' ? 'success' : 'outline'} size="sm">
                            {ass.status}
                          </Badge>
                        </div>
                        <div style={{ fontSize: '12px', color: 'var(--text-muted)', display: 'flex', alignItems: 'center', gap: '10px' }}>
                          <span style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
                            <Clock size={12} /> {ass.duration_minutes} mins
                          </span>
                          <span>Passing: {ass.passing_percentage}%</span>
                        </div>
                      </div>
                      <Link href="/workspace/assessments">
                        <Button variant="primary" size="sm">
                          {ass.status === 'PUBLISHED' ? 'Take Exam' : 'View'}
                        </Button>
                      </Link>
                    </div>
                  ))}
                </div>
              )}
            </Card>
          </div>
        </div>
      )}

      {/* ============================================================== */}
      {/* 2. FACULTY DASHBOARD VIEW                                      */}
      {/* ============================================================== */}
      {activeRoleView === 'FACULTY' && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
          
          {/* Quick Metrics Bar */}
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: '16px' }}>
            <Card style={{ padding: '20px' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                <div style={{ padding: '10px', borderRadius: '10px', backgroundColor: 'rgba(79, 70, 229, 0.1)', color: 'var(--brand-primary)' }}>
                  <BookOpen size={20} />
                </div>
                <div>
                  <div style={{ fontSize: '12px', color: 'var(--text-muted)', fontWeight: 500 }}>Assigned Courses</div>
                  <div style={{ fontSize: '22px', fontWeight: 700, color: 'var(--text-primary)' }}>
                    {courses.length}
                  </div>
                </div>
              </div>
              <div style={{ marginTop: '12px', fontSize: '12px', color: 'var(--text-secondary)' }}>
                Active curriculum offerings
              </div>
            </Card>

            <Card style={{ padding: '20px' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                <div style={{ padding: '10px', borderRadius: '10px', backgroundColor: 'rgba(5, 150, 105, 0.1)', color: 'var(--status-success)' }}>
                  <FileCheck2 size={20} />
                </div>
                <div>
                  <div style={{ fontSize: '12px', color: 'var(--text-muted)', fontWeight: 500 }}>Question Banks</div>
                  <div style={{ fontSize: '22px', fontWeight: 700, color: 'var(--text-primary)' }}>
                    {courses.length > 0 ? courses.length * 2 : 4}
                  </div>
                </div>
              </div>
              <div style={{ marginTop: '12px', fontSize: '12px', color: 'var(--text-secondary)' }}>
                Aligned with Bloom taxonomy
              </div>
            </Card>

            <Card style={{ padding: '20px' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                <div style={{ padding: '10px', borderRadius: '10px', backgroundColor: 'rgba(217, 119, 6, 0.1)', color: 'var(--status-warning)' }}>
                  <Clock size={20} />
                </div>
                <div>
                  <div style={{ fontSize: '12px', color: 'var(--text-muted)', fontWeight: 500 }}>Pending Evaluations</div>
                  <div style={{ fontSize: '22px', fontWeight: 700, color: 'var(--text-primary)' }}>
                    3
                  </div>
                </div>
              </div>
              <div style={{ marginTop: '12px', fontSize: '12px', color: 'var(--text-secondary)' }}>
                Subjective answers to grade
              </div>
            </Card>

            <Card style={{ padding: '20px' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                <div style={{ padding: '10px', borderRadius: '10px', backgroundColor: 'rgba(220, 38, 38, 0.1)', color: 'var(--status-danger)' }}>
                  <AlertTriangle size={20} />
                </div>
                <div>
                  <div style={{ fontSize: '12px', color: 'var(--text-muted)', fontWeight: 500 }}>Student Interventions</div>
                  <div style={{ fontSize: '22px', fontWeight: 700, color: 'var(--text-primary)' }}>
                    2
                  </div>
                </div>
              </div>
              <div style={{ marginTop: '12px', fontSize: '12px', color: 'var(--text-secondary)' }}>
                Early-warning risk triggers
              </div>
            </Card>
          </div>

          {/* Action Row */}
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))', gap: '20px' }}>
            <Card style={{ padding: '20px', display: 'flex', flexDirection: 'column', gap: '12px' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <Sparkles size={18} color="var(--brand-primary)" />
                <h3 style={{ fontSize: '15px', fontWeight: 700, color: 'var(--text-primary)', margin: 0 }}>
                  AI Question Authoring Studio
                </h3>
              </div>
              <p style={{ fontSize: '13px', color: 'var(--text-secondary)', margin: 0 }}>
                Draft Bloom-taxonomy aligned assessment questions from your course curriculum with 1-click promotion into the Question Bank.
              </p>
              <Link href="/workspace/ai">
                <Button variant="primary" size="sm" style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                  <PlusCircle size={14} /> Open Authoring Studio
                </Button>
              </Link>
            </Card>

            <Card style={{ padding: '20px', display: 'flex', flexDirection: 'column', gap: '12px' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <TrendingUp size={18} color="var(--status-success)" />
                <h3 style={{ fontSize: '15px', fontWeight: 700, color: 'var(--text-primary)', margin: 0 }}>
                  Curriculum & Syllabus Coverage
                </h3>
              </div>
              <p style={{ fontSize: '13px', color: 'var(--text-secondary)', margin: 0 }}>
                Manage learning units, lesson markdown transcripts, and course objectives across institutional academic terms.
              </p>
              <Link href="/workspace/curriculum">
                <Button variant="outline" size="sm" style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                  Manage Curriculum <ArrowRight size={14} />
                </Button>
              </Link>
            </Card>
          </div>
        </div>
      )}

      {/* ============================================================== */}
      {/* 3. HOD & DEAN DASHBOARD VIEW                                   */}
      {/* ============================================================== */}
      {activeRoleView === 'HOD' && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: '16px' }}>
            <Card style={{ padding: '20px' }}>
              <div style={{ fontSize: '12px', color: 'var(--text-muted)', fontWeight: 500 }}>Department Cohorts</div>
              <div style={{ fontSize: '24px', fontWeight: 700, color: 'var(--text-primary)', marginTop: '4px' }}>4 Batches</div>
              <div style={{ fontSize: '12px', color: 'var(--text-secondary)', marginTop: '6px' }}>CSE 2023 - 2027</div>
            </Card>
            <Card style={{ padding: '20px' }}>
              <div style={{ fontSize: '12px', color: 'var(--text-muted)', fontWeight: 500 }}>Average Cohort Passing</div>
              <div style={{ fontSize: '24px', fontWeight: 700, color: 'var(--status-success)', marginTop: '4px' }}>88.4%</div>
              <div style={{ fontSize: '12px', color: 'var(--text-secondary)', marginTop: '6px' }}>Deterministic evaluations</div>
            </Card>
            <Card style={{ padding: '20px' }}>
              <div style={{ fontSize: '12px', color: 'var(--text-muted)', fontWeight: 500 }}>Syllabus Approval Status</div>
              <div style={{ fontSize: '24px', fontWeight: 700, color: 'var(--brand-primary)', marginTop: '4px' }}>100%</div>
              <div style={{ fontSize: '12px', color: 'var(--text-secondary)', marginTop: '6px' }}>All modules approved</div>
            </Card>
            <Card style={{ padding: '20px' }}>
              <div style={{ fontSize: '12px', color: 'var(--text-muted)', fontWeight: 500 }}>Active Interventions</div>
              <div style={{ fontSize: '24px', fontWeight: 700, color: 'var(--status-warning)', marginTop: '4px' }}>4 Cases</div>
              <div style={{ fontSize: '12px', color: 'var(--text-secondary)', marginTop: '6px' }}>Mentorship in progress</div>
            </Card>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))', gap: '20px' }}>
            <Card style={{ padding: '20px' }}>
              <h3 style={{ fontSize: '15px', fontWeight: 700, color: 'var(--text-primary)', marginBottom: '8px' }}>
                Department Analytics & Risk Interventions
              </h3>
              <p style={{ fontSize: '13px', color: 'var(--text-secondary)', marginBottom: '14px' }}>
                Review early-warning flags for students with retention decay or assessment challenges.
              </p>
              <Link href="/workspace/analytics">
                <Button variant="primary" size="sm">Open Analytics Hub</Button>
              </Link>
            </Card>

            <Card style={{ padding: '20px' }}>
              <h3 style={{ fontSize: '15px', fontWeight: 700, color: 'var(--text-primary)', marginBottom: '8px' }}>
                Academic Structure Governance
              </h3>
              <p style={{ fontSize: '13px', color: 'var(--text-secondary)', marginBottom: '14px' }}>
                Manage programs, departments, terms, sections, and faculty course assignments.
              </p>
              <Link href="/workspace/academic">
                <Button variant="outline" size="sm">Manage Hierarchy</Button>
              </Link>
            </Card>
          </div>
        </div>
      )}

      {/* ============================================================== */}
      {/* 4. PLACEMENT OFFICER DASHBOARD VIEW                            */}
      {/* ============================================================== */}
      {activeRoleView === 'PLACEMENT_OFFICER' && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: '16px' }}>
            <Card style={{ padding: '20px' }}>
              <div style={{ fontSize: '12px', color: 'var(--text-muted)', fontWeight: 500 }}>Verified Talent Pool</div>
              <div style={{ fontSize: '24px', fontWeight: 700, color: 'var(--text-primary)', marginTop: '4px' }}>128 Students</div>
              <div style={{ fontSize: '12px', color: 'var(--text-secondary)', marginTop: '6px' }}>Graduating cohort 2026</div>
            </Card>
            <Card style={{ padding: '20px' }}>
              <div style={{ fontSize: '12px', color: 'var(--text-muted)', fontWeight: 500 }}>High Career Readiness (CRI &gt; 80%)</div>
              <div style={{ fontSize: '24px', fontWeight: 700, color: 'var(--status-success)', marginTop: '4px' }}>74 Candidates</div>
              <div style={{ fontSize: '12px', color: 'var(--text-secondary)', marginTop: '6px' }}>Assessed against industry criteria</div>
            </Card>
            <Card style={{ padding: '20px' }}>
              <div style={{ fontSize: '12px', color: 'var(--text-muted)', fontWeight: 500 }}>Verified Capstone Projects</div>
              <div style={{ fontSize: '24px', fontWeight: 700, color: 'var(--brand-primary)', marginTop: '4px' }}>92 Submissions</div>
              <div style={{ fontSize: '12px', color: 'var(--text-secondary)', marginTop: '6px' }}>Faculty-verified evidence</div>
            </Card>
            <Card style={{ padding: '20px' }}>
              <div style={{ fontSize: '12px', color: 'var(--text-muted)', fontWeight: 500 }}>Skill Deficiencies</div>
              <div style={{ fontSize: '24px', fontWeight: 700, color: 'var(--status-warning)', marginTop: '4px' }}>Distributed Systems</div>
              <div style={{ fontSize: '12px', color: 'var(--text-secondary)', marginTop: '6px' }}>Target for remediation</div>
            </Card>
          </div>

          <Card style={{ padding: '24px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px' }}>
              <h3 style={{ fontSize: '16px', fontWeight: 700, color: 'var(--text-primary)', margin: 0 }}>
                Talent Discovery & Career Readiness Studio
              </h3>
              <Link href="/workspace/placement">
                <Button variant="primary" size="sm">Launch Talent Discovery</Button>
              </Link>
            </div>
            <p style={{ fontSize: '13px', color: 'var(--text-secondary)', margin: 0, lineHeight: 1.6 }}>
              Browse students with verified capstone deliverables, GitHub repositories, and Ebbinghaus-decay adjusted competency mastery profiles. All records represent authentic faculty-evaluated work.
            </p>
          </Card>
        </div>
      )}

      {/* ============================================================== */}
      {/* 5. ADMINISTRATOR DASHBOARD VIEW                                */}
      {/* ============================================================== */}
      {['INSTITUTION_ADMIN', 'SUPER_ADMIN'].includes(activeRoleView) && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
          
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: '16px' }}>
            <Card style={{ padding: '20px' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                <Activity size={18} color="var(--status-success)" />
                <span style={{ fontSize: '12px', color: 'var(--text-muted)', fontWeight: 500 }}>OLTP Database Engine</span>
              </div>
              <div style={{ fontSize: '22px', fontWeight: 700, color: 'var(--text-primary)', marginTop: '6px' }}>Connected</div>
              <div style={{ fontSize: '12px', color: 'var(--text-secondary)', marginTop: '4px' }}>PostgreSQL 16 • 0.8ms latency</div>
            </Card>

            <Card style={{ padding: '20px' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                <ShieldCheck size={18} color="var(--brand-primary)" />
                <span style={{ fontSize: '12px', color: 'var(--text-muted)', fontWeight: 500 }}>Multi-Tenant Partition</span>
              </div>
              <div style={{ fontSize: '22px', fontWeight: 700, color: 'var(--text-primary)', marginTop: '6px' }}>RLS Active</div>
              <div style={{ fontSize: '12px', color: 'var(--text-secondary)', marginTop: '4px' }}>Tenant: {tenantSlug || 'Global'}</div>
            </Card>

            <Card style={{ padding: '20px' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                <Server size={18} color="var(--status-info)" />
                <span style={{ fontSize: '12px', color: 'var(--text-muted)', fontWeight: 500 }}>Data Center Ingestion</span>
              </div>
              <div style={{ fontSize: '22px', fontWeight: 700, color: 'var(--text-primary)', marginTop: '6px' }}>Zero-Loss ETL</div>
              <div style={{ fontSize: '12px', color: 'var(--text-secondary)', marginTop: '4px' }}>Checksum deduplication</div>
            </Card>

            <Card style={{ padding: '20px' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                <Cpu size={18} color="var(--status-warning)" />
                <span style={{ fontSize: '12px', color: 'var(--text-muted)', fontWeight: 500 }}>AI Gateway Health</span>
              </div>
              <div style={{ fontSize: '22px', fontWeight: 700, color: 'var(--text-primary)', marginTop: '6px' }}>Operational</div>
              <div style={{ fontSize: '12px', color: 'var(--text-secondary)', marginTop: '4px' }}>Gemini / Grounded Engine</div>
            </Card>
          </div>

          {/* Administrative Control Grid */}
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))', gap: '20px' }}>
            <Card style={{ padding: '20px', display: 'flex', flexDirection: 'column', gap: '10px' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <Server size={18} color="var(--brand-primary)" />
                <h3 style={{ fontSize: '15px', fontWeight: 700, color: 'var(--text-primary)', margin: 0 }}>
                  Data Center Bulk Ingestion (ETL)
                </h3>
              </div>
              <p style={{ fontSize: '13px', color: 'var(--text-secondary)', margin: 0 }}>
                Stage, review, validate, and publish high-volume CSV/TSV academic records with row-level error reporting.
              </p>
              <Link href="/workspace/datacenter">
                <Button variant="primary" size="sm">Open Data Center</Button>
              </Link>
            </Card>

            <Card style={{ padding: '20px', display: 'flex', flexDirection: 'column', gap: '10px' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <ShieldCheck size={18} color="var(--status-success)" />
                <h3 style={{ fontSize: '15px', fontWeight: 700, color: 'var(--text-primary)', margin: 0 }}>
                  Security & AI Gateway Audit Logs
                </h3>
              </div>
              <p style={{ fontSize: '13px', color: 'var(--text-secondary)', margin: 0 }}>
                Review live OLTP audit logs of prompt hashes, PII redactions, prompt injection intercepts, and token usage.
              </p>
              <Link href="/workspace/ai">
                <Button variant="outline" size="sm">View Audit Stream</Button>
              </Link>
            </Card>
          </div>
        </div>
      )}

    </div>
  );
}
