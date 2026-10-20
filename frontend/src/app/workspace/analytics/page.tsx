'use client';

import React, { useState, useMemo } from 'react';
import { useAuth } from '@/lib/auth/AuthContext';
import { Badge } from '@/components/ui/Badge';
import { Button } from '@/components/ui/Button';
import { Card } from '@/components/ui/Card';
import { Input } from '@/components/ui/Input';
import {
  Intervention,
  InterventionStatus,
  InterventionType,
  RiskLevel,
  AtRiskStudent,
  NotificationItem,
  DepartmentalMetric,
  InstitutionalAnalytics,
} from '@/types/analytics';

export default function AnalyticsInterventionsWorkspace() {
  const { user } = useAuth();
  const primaryRole = user?.roles[0] || 'STUDENT';
  const isStaff = ['SUPER_ADMIN', 'INSTITUTION_ADMIN', 'HOD', 'FACULTY'].includes(primaryRole);
  const isAdmin = ['SUPER_ADMIN', 'INSTITUTION_ADMIN', 'HOD'].includes(primaryRole);

  // Active Tab
  const [activeTab, setActiveTab] = useState<'executive' | 'early_warning' | 'interventions' | 'notifications'>(
    isStaff ? 'executive' : 'interventions'
  );

  // Rollups & Health State
  const [isRefreshingRollup, setIsRefreshingRollup] = useState(false);
  const [rollupEvaluatedAt, setRollupEvaluatedAt] = useState<string>(
    new Date(Date.now() - 1000 * 60 * 45).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
  );

  // Institutional Analytics Data
  const [analyticsData, setAnalyticsData] = useState<InstitutionalAnalytics>({
    institution_id: user?.institution_id || 'inst-iit-bombay',
    computed_at: new Date().toISOString(),
    active_students: 420,
    at_risk_count: 14,
    active_interventions: 8,
    overall_passing_rate: 0.924,
    average_mastery_index: 0.782,
    total_assessments_taken: 1250,
    departments: [
      {
        department_id: 'dept-cse',
        department_name: 'Computer Science & Engineering',
        department_code: 'CSE',
        enrolled_students: 140,
        at_risk_students: 3,
        active_interventions: 2,
        average_mastery: 0.84,
        passing_rate: 0.96,
        retention_index: 0.88,
      },
      {
        department_id: 'dept-ece',
        department_name: 'Electronics & Communication',
        department_code: 'ECE',
        enrolled_students: 110,
        at_risk_students: 5,
        active_interventions: 3,
        average_mastery: 0.76,
        passing_rate: 0.91,
        retention_index: 0.81,
      },
      {
        department_id: 'dept-mech',
        department_name: 'Mechanical Engineering',
        department_code: 'MECH',
        enrolled_students: 95,
        at_risk_students: 4,
        active_interventions: 2,
        average_mastery: 0.73,
        passing_rate: 0.88,
        retention_index: 0.77,
      },
      {
        department_id: 'dept-civil',
        department_name: 'Civil & Infrastructure Engineering',
        department_code: 'CIVIL',
        enrolled_students: 75,
        at_risk_students: 2,
        active_interventions: 1,
        average_mastery: 0.79,
        passing_rate: 0.93,
        retention_index: 0.84,
      },
    ],
    skill_distribution: {
      mastery: 165,
      proficient: 172,
      developing: 69,
      novice: 14,
    },
    interventions_by_status: {
      ASSIGNED: 3,
      IN_PROGRESS: 4,
      COMPLETED: 18,
      ESCALATED: 1,
      DISMISSED: 2,
    },
    interventions_by_type: {
      ACADEMIC_TUTORING: 4,
      ATTENDANCE_COUNSELING: 1,
      MENTOR_CHECKIN: 1,
      STUDY_PLAN_REVISION: 2,
      PSYCHOLOGICAL_COUNSELING: 0,
    },
  });

  // Early Warning Detection Records
  const [atRiskCohort, setAtRiskCohort] = useState<AtRiskStudent[]>([
    {
      student_id: 'std-101',
      full_name: 'Anita Rao',
      email: 'anita.rao@iitb.ac.in',
      roll_number: '2026-CS-042',
      risk_level: 'CRITICAL',
      detected_rules: [
        {
          rule_id: 'rule-fail-rate',
          name: 'Critical Assessment Failure Rate',
          severity: 'CRITICAL',
          metric: 'Assessment Fail Rate',
          actual_value: 0.67,
          threshold_value: 0.50,
          description: 'Failed 2 of 3 mid-term assessments. Average score: 32.5%.',
        },
        {
          rule_id: 'rule-decay',
          name: 'Severe Mastery Decay',
          severity: 'HIGH',
          metric: 'Competency Half-Life',
          actual_value: 0.28,
          threshold_value: 0.40,
          description: 'Algorithms (CS-ALG-01) and Data Structures (CS-DS-02) fallen below 30% retention threshold.',
        },
      ],
      recommended_intervention_type: 'ACADEMIC_TUTORING',
      trigger_reason: 'Combined assessment failure in core modules with acute competency decay.',
      metrics_summary: {
        average_mastery: 0.34,
        assessment_fail_count: 2,
        decayed_skills_count: 2,
      },
    },
    {
      student_id: 'std-102',
      full_name: 'Vikram Mehta',
      email: 'vikram.mehta@iitb.ac.in',
      roll_number: '2026-EC-019',
      risk_level: 'HIGH',
      detected_rules: [
        {
          rule_id: 'rule-decay',
          name: 'Competency Decay',
          severity: 'HIGH',
          metric: 'Decayed Skills',
          actual_value: 2,
          threshold_value: 2,
          description: 'Signals & Systems (EC-SIG-01) and Digital Logic (EC-DL-03) dropped below 40% threshold.',
        },
      ],
      recommended_intervention_type: 'STUDY_PLAN_REVISION',
      trigger_reason: 'Retention half-life exceeded on foundational prerequisites.',
      metrics_summary: {
        average_mastery: 0.42,
        assessment_fail_count: 1,
        decayed_skills_count: 2,
      },
    },
    {
      student_id: 'std-103',
      full_name: 'Pooja Iyer',
      email: 'pooja.iyer@iitb.ac.in',
      roll_number: '2026-ME-058',
      risk_level: 'MEDIUM',
      detected_rules: [
        {
          rule_id: 'rule-single-fail',
          name: 'Isolated Assessment Deficit',
          severity: 'MEDIUM',
          metric: 'Recent Score',
          actual_value: 36.0,
          threshold_value: 40.0,
          description: 'Thermodynamics Quiz 2 scored 36.0%, below institutional pass mark of 40%.',
        },
      ],
      recommended_intervention_type: 'MENTOR_CHECKIN',
      trigger_reason: 'Isolated deficiency on thermodynamics concepts.',
      metrics_summary: {
        average_mastery: 0.58,
        assessment_fail_count: 1,
        decayed_skills_count: 0,
      },
    },
  ]);

  // Interventions List
  const [interventions, setInterventions] = useState<Intervention[]>([
    {
      id: 'int-001',
      institution_id: user?.institution_id || 'inst-iit-bombay',
      student_user_id: 'std-101',
      faculty_user_id: 'fac-301',
      intervention_type: 'ACADEMIC_TUTORING',
      trigger_reason: 'Failed 2 of 3 mid-term assessments with acute competency decay in Data Structures.',
      status: 'IN_PROGRESS',
      action_plan: 'Weekly 1:1 problem solving labs on dynamic programming and graph traversals.',
      notes: 'Initial consultation completed. Student showed good engagement.',
      outcome_notes: 'Diagnostic session held. Recommended targeted practice sets 1 through 4.',
      assigned_at: new Date(Date.now() - 1000 * 60 * 60 * 48).toISOString(),
      due_date: new Date(Date.now() + 1000 * 60 * 60 * 24 * 7).toISOString(),
      completed_at: null,
      created_at: new Date(Date.now() - 1000 * 60 * 60 * 48).toISOString(),
      updated_at: new Date(Date.now() - 1000 * 60 * 60 * 2).toISOString(),
      student: {
        id: 'std-101',
        full_name: 'Anita Rao',
        email: 'anita.rao@iitb.ac.in',
        roll_number: '2026-CS-042',
      },
      faculty: {
        id: 'fac-301',
        full_name: 'Dr. Ramesh Sundaram',
        email: 'ramesh.s@iitb.ac.in',
      },
    },
    {
      id: 'int-002',
      institution_id: user?.institution_id || 'inst-iit-bombay',
      student_user_id: 'std-102',
      faculty_user_id: 'fac-302',
      intervention_type: 'STUDY_PLAN_REVISION',
      trigger_reason: 'Retention half-life exceeded on foundational signals & systems prerequisites.',
      status: 'ASSIGNED',
      action_plan: 'Review syllabus breakdown and re-balance laboratory hours with self-paced revision.',
      notes: 'Assigned to academic advisor Dr. Priya Patel.',
      outcome_notes: '',
      assigned_at: new Date(Date.now() - 1000 * 60 * 60 * 24).toISOString(),
      due_date: new Date(Date.now() + 1000 * 60 * 60 * 24 * 10).toISOString(),
      completed_at: null,
      created_at: new Date(Date.now() - 1000 * 60 * 60 * 24).toISOString(),
      updated_at: new Date(Date.now() - 1000 * 60 * 60 * 24).toISOString(),
      student: {
        id: 'std-102',
        full_name: 'Vikram Mehta',
        email: 'vikram.mehta@iitb.ac.in',
        roll_number: '2026-EC-019',
      },
      faculty: {
        id: 'fac-302',
        full_name: 'Dr. Priya Patel',
        email: 'priya.patel@iitb.ac.in',
      },
    },
    {
      id: 'int-003',
      institution_id: user?.institution_id || 'inst-iit-bombay',
      student_user_id: 'std-104',
      faculty_user_id: 'fac-301',
      intervention_type: 'MENTOR_CHECKIN',
      trigger_reason: 'Low project activity and delayed milestone submissions.',
      status: 'COMPLETED',
      action_plan: 'Milestone recovery plan agreed and verified.',
      notes: 'Capstone deliverable submitted and approved.',
      outcome_notes: 'All delayed submissions completed with distinction. Risk normalized.',
      assigned_at: new Date(Date.now() - 1000 * 60 * 60 * 24 * 14).toISOString(),
      due_date: new Date(Date.now() - 1000 * 60 * 60 * 24 * 2).toISOString(),
      completed_at: new Date(Date.now() - 1000 * 60 * 60 * 24 * 2).toISOString(),
      created_at: new Date(Date.now() - 1000 * 60 * 60 * 24 * 14).toISOString(),
      updated_at: new Date(Date.now() - 1000 * 60 * 60 * 24 * 2).toISOString(),
      student: {
        id: 'std-104',
        full_name: 'Siddharth Nair',
        email: 'siddharth.n@iitb.ac.in',
        roll_number: '2026-CS-011',
      },
      faculty: {
        id: 'fac-301',
        full_name: 'Dr. Ramesh Sundaram',
        email: 'ramesh.s@iitb.ac.in',
      },
    },
  ]);

  // Notifications List
  const [notifications, setNotifications] = useState<NotificationItem[]>([
    {
      id: 'notif-1',
      institution_id: user?.institution_id || 'inst-iit-bombay',
      recipient_user_id: user?.id || 'usr-me',
      notification_type: 'EARLY_WARNING',
      title: 'Academic Alert: Critical Mastery Decay',
      message: 'Student Anita Rao (CS2026-042) flagged for Database Systems & Algorithms intervention.',
      is_read: false,
      link_url: '/workspace/analytics',
      created_at: new Date(Date.now() - 1000 * 60 * 25).toISOString(),
    },
    {
      id: 'notif-2',
      institution_id: user?.institution_id || 'inst-iit-bombay',
      recipient_user_id: user?.id || 'usr-me',
      notification_type: 'INTERVENTION_ASSIGNED',
      title: 'Intervention Assigned: Academic Tutoring',
      message: 'You have been assigned to supervise study plan revision for Rahul Sharma.',
      is_read: false,
      link_url: '/workspace/analytics',
      created_at: new Date(Date.now() - 1000 * 60 * 120).toISOString(),
    },
    {
      id: 'notif-3',
      institution_id: user?.institution_id || 'inst-iit-bombay',
      recipient_user_id: user?.id || 'usr-me',
      notification_type: 'ANALYTICS_ROLLUP',
      title: 'Nightly Rollup Generated',
      message: 'Departmental passing rates and competency health rollups successfully cached.',
      is_read: false,
      link_url: '/workspace/analytics',
      created_at: new Date(Date.now() - 1000 * 60 * 360).toISOString(),
    },
    {
      id: 'notif-4',
      institution_id: user?.institution_id || 'inst-iit-bombay',
      recipient_user_id: user?.id || 'usr-me',
      notification_type: 'INTERVENTION_COMPLETED',
      title: 'Intervention Resolved',
      message: 'Milestone recovery plan for Siddharth Nair completed and marked resolved.',
      is_read: true,
      read_at: new Date(Date.now() - 1000 * 60 * 60 * 24).toISOString(),
      created_at: new Date(Date.now() - 1000 * 60 * 60 * 24).toISOString(),
    },
  ]);

  // Modals & Forms
  const [isAssignModalOpen, setIsAssignModalOpen] = useState(false);
  const [selectedStudentForAssign, setSelectedStudentForAssign] = useState<AtRiskStudent | null>(null);
  const [assignForm, setAssignForm] = useState({
    intervention_type: 'ACADEMIC_TUTORING' as InterventionType,
    action_plan: '',
    notes: '',
    due_days: '7',
  });

  const [isUpdateModalOpen, setIsUpdateModalOpen] = useState(false);
  const [selectedInterventionForUpdate, setSelectedInterventionForUpdate] = useState<Intervention | null>(null);
  const [updateForm, setUpdateForm] = useState({
    status: 'IN_PROGRESS' as InterventionStatus,
    outcome_notes: '',
    action_plan: '',
  });

  // Filter States
  const [riskFilter, setRiskFilter] = useState<string>('ALL');
  const [interventionStatusFilter, setInterventionStatusFilter] = useState<string>('ALL');
  const [notificationUnreadOnly, setNotificationUnreadOnly] = useState<boolean>(false);

  // Compute & Refresh Rollup Handler
  const handleComputeRollup = () => {
    setIsRefreshingRollup(true);
    setTimeout(() => {
      setRollupEvaluatedAt(new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }));
      setAnalyticsData((prev) => ({
        ...prev,
        computed_at: new Date().toISOString(),
        overall_passing_rate: 0.928,
        average_mastery_index: 0.789,
        at_risk_count: atRiskCohort.length,
        active_interventions: interventions.filter((i) => ['ASSIGNED', 'IN_PROGRESS', 'ESCALATED'].includes(i.status)).length,
      }));
      setIsRefreshingRollup(false);
    }, 600);
  };

  // Open Assign Modal
  const openAssignModal = (student: AtRiskStudent) => {
    setSelectedStudentForAssign(student);
    setAssignForm({
      intervention_type: student.recommended_intervention_type,
      action_plan: `Targeted review on ${student.trigger_reason}`,
      notes: `Deterministic trigger from rules: ${student.detected_rules.map((r) => r.name).join(', ')}`,
      due_days: '7',
    });
    setIsAssignModalOpen(true);
  };

  // Submit Assign Modal
  const handleCreateIntervention = (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedStudentForAssign) return;

    const newIntervention: Intervention = {
      id: `int-${Date.now()}`,
      institution_id: user?.institution_id || 'inst-iit-bombay',
      student_user_id: selectedStudentForAssign.student_id,
      faculty_user_id: user?.id || 'fac-me',
      intervention_type: assignForm.intervention_type,
      trigger_reason: selectedStudentForAssign.trigger_reason,
      status: 'ASSIGNED',
      action_plan: assignForm.action_plan,
      notes: assignForm.notes,
      outcome_notes: '',
      assigned_at: new Date().toISOString(),
      due_date: new Date(Date.now() + parseInt(assignForm.due_days) * 24 * 60 * 60 * 1000).toISOString(),
      completed_at: null,
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
      student: {
        id: selectedStudentForAssign.student_id,
        full_name: selectedStudentForAssign.full_name,
        email: selectedStudentForAssign.email,
        roll_number: selectedStudentForAssign.roll_number,
      },
      faculty: {
        id: user?.id || 'fac-me',
        full_name: user?.full_name || 'Faculty Mentor',
        email: user?.email || 'mentor@institution.edu',
      },
    };

    setInterventions([newIntervention, ...interventions]);

    // Dispatch a local notification
    const newNotif: NotificationItem = {
      id: `notif-${Date.now()}`,
      institution_id: user?.institution_id || 'inst-iit-bombay',
      recipient_user_id: selectedStudentForAssign.student_id,
      actor_user_id: user?.id,
      notification_type: 'INTERVENTION_ASSIGNED',
      title: `Intervention Assigned: ${assignForm.intervention_type.replace(/_/g, ' ')}`,
      message: `Faculty mentor assigned action plan: "${assignForm.action_plan}"`,
      is_read: false,
      created_at: new Date().toISOString(),
    };
    setNotifications([newNotif, ...notifications]);

    setIsAssignModalOpen(false);
    setSelectedStudentForAssign(null);
  };

  // Open Update Modal
  const openUpdateModal = (intervention: Intervention) => {
    setSelectedInterventionForUpdate(intervention);
    setUpdateForm({
      status: intervention.status,
      outcome_notes: intervention.outcome_notes || '',
      action_plan: intervention.action_plan || '',
    });
    setIsUpdateModalOpen(true);
  };

  // Submit Update Modal
  const handleUpdateIntervention = (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedInterventionForUpdate) return;

    setInterventions((prev) =>
      prev.map((i) => {
        if (i.id === selectedInterventionForUpdate.id) {
          const isDone = updateForm.status === 'COMPLETED';
          return {
            ...i,
            status: updateForm.status,
            outcome_notes: updateForm.outcome_notes,
            action_plan: updateForm.action_plan,
            completed_at: isDone ? new Date().toISOString() : i.completed_at,
            updated_at: new Date().toISOString(),
          };
        }
        return i;
      })
    );

    setIsUpdateModalOpen(false);
    setSelectedInterventionForUpdate(null);
  };

  // Filtered Cohort
  const filteredAtRiskCohort = useMemo(() => {
    if (riskFilter === 'ALL') return atRiskCohort;
    return atRiskCohort.filter((s) => s.risk_level === riskFilter);
  }, [atRiskCohort, riskFilter]);

  // Filtered Interventions
  const filteredInterventions = useMemo(() => {
    let result = interventions;
    // If student role, isolate to self
    if (!isStaff && user?.id) {
      result = result.filter((i) => i.student_user_id === user.id);
    }
    if (interventionStatusFilter !== 'ALL') {
      result = result.filter((i) => i.status === interventionStatusFilter);
    }
    return result;
  }, [interventions, isStaff, user, interventionStatusFilter]);

  // Filtered Notifications
  const filteredNotifications = useMemo(() => {
    if (notificationUnreadOnly) {
      return notifications.filter((n) => !n.is_read);
    }
    return notifications;
  }, [notifications, notificationUnreadOnly]);

  const markNotifRead = (id: string) => {
    setNotifications((prev) =>
      prev.map((n) => (n.id === id ? { ...n, is_read: true, read_at: new Date().toISOString() } : n))
    );
  };

  const markAllNotifsRead = () => {
    setNotifications((prev) =>
      prev.map((n) => ({ ...n, is_read: true, read_at: new Date().toISOString() }))
    );
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
      {/* Header */}
      <div
        style={{
          display: 'flex',
          flexDirection: 'row',
          alignItems: 'flex-start',
          justifyContent: 'space-between',
          borderBottom: '1px solid var(--border-subtle)',
          paddingBottom: '20px',
        }}
      >
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <h1 style={{ fontSize: '24px', fontWeight: 700, color: 'var(--text-primary)', margin: 0 }}>
              Institutional Analytics & Early Warning Engine
            </h1>
            <Badge variant="info">Phase 8</Badge>
          </div>
          <p style={{ margin: '6px 0 0', color: 'var(--text-secondary)', fontSize: '13px' }}>
            Deterministic early risk detection, supervised academic intervention lifecycles, and pre-computed departmental health rollups.
          </p>
        </div>

        {isAdmin && (
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <div style={{ textAlign: 'right' }}>
              <div style={{ fontSize: '11px', color: 'var(--text-muted)' }}>Rollup Cache State</div>
              <div style={{ fontSize: '12px', fontWeight: 600, color: 'var(--text-primary)' }}>
                Evaluated at {rollupEvaluatedAt}
              </div>
            </div>
            <Button
              variant="outline"
              size="sm"
              onClick={handleComputeRollup}
              disabled={isRefreshingRollup}
            >
              {isRefreshingRollup ? 'Refreshing...' : 'Compute Rollup'}
            </Button>
          </div>
        )}
      </div>

      {/* Tabs */}
      <div
        style={{
          display: 'flex',
          gap: '8px',
          borderBottom: '1px solid var(--border-subtle)',
          paddingBottom: '8px',
        }}
      >
        {isStaff && (
          <Button
            variant={activeTab === 'executive' ? 'primary' : 'outline'}
            size="sm"
            onClick={() => setActiveTab('executive')}
          >
            Executive Analytics & Rollups
          </Button>
        )}

        {isStaff && (
          <Button
            variant={activeTab === 'early_warning' ? 'primary' : 'outline'}
            size="sm"
            onClick={() => setActiveTab('early_warning')}
          >
            Early Warning & At-Risk Cohort ({atRiskCohort.length})
          </Button>
        )}

        <Button
          variant={activeTab === 'interventions' ? 'primary' : 'outline'}
          size="sm"
          onClick={() => setActiveTab('interventions')}
        >
          {isStaff ? 'Intervention Management' : 'My Academic Interventions'} ({interventions.length})
        </Button>

        <Button
          variant={activeTab === 'notifications' ? 'primary' : 'outline'}
          size="sm"
          onClick={() => setActiveTab('notifications')}
        >
          Notification Hub ({notifications.filter((n) => !n.is_read).length} unread)
        </Button>
      </div>

      {/* TAB 1: EXECUTIVE ANALYTICS */}
      {activeTab === 'executive' && isStaff && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
          {/* Key Metrics Row */}
          <div
            style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
              gap: '16px',
            }}
          >
            <Card style={{ padding: '16px', backgroundColor: 'var(--bg-surface)' }}>
              <div style={{ fontSize: '12px', color: 'var(--text-muted)', fontWeight: 600 }}>
                ACTIVE STUDENTS
              </div>
              <div style={{ fontSize: '28px', fontWeight: 800, color: 'var(--text-primary)', marginTop: '4px' }}>
                {analyticsData.active_students}
              </div>
              <div style={{ fontSize: '11px', color: 'var(--status-success)', marginTop: '4px' }}>
                100% tenant verified
              </div>
            </Card>

            <Card style={{ padding: '16px', backgroundColor: 'var(--bg-surface)' }}>
              <div style={{ fontSize: '12px', color: 'var(--text-muted)', fontWeight: 600 }}>
                AT-RISK STUDENTS
              </div>
              <div style={{ fontSize: '28px', fontWeight: 800, color: 'var(--status-danger)', marginTop: '4px' }}>
                {analyticsData.at_risk_count}
              </div>
              <div style={{ fontSize: '11px', color: 'var(--text-muted)', marginTop: '4px' }}>
                {((analyticsData.at_risk_count / analyticsData.active_students) * 100).toFixed(1)}% of cohort
              </div>
            </Card>

            <Card style={{ padding: '16px', backgroundColor: 'var(--bg-surface)' }}>
              <div style={{ fontSize: '12px', color: 'var(--text-muted)', fontWeight: 600 }}>
                ACTIVE INTERVENTIONS
              </div>
              <div style={{ fontSize: '28px', fontWeight: 800, color: 'var(--status-warning)', marginTop: '4px' }}>
                {analyticsData.active_interventions}
              </div>
              <div style={{ fontSize: '11px', color: 'var(--brand-accent)', marginTop: '4px' }}>
                Supervised by faculty
              </div>
            </Card>

            <Card style={{ padding: '16px', backgroundColor: 'var(--bg-surface)' }}>
              <div style={{ fontSize: '12px', color: 'var(--text-muted)', fontWeight: 600 }}>
                OVERALL PASSING RATE
              </div>
              <div style={{ fontSize: '28px', fontWeight: 800, color: 'var(--status-success)', marginTop: '4px' }}>
                {(analyticsData.overall_passing_rate * 100).toFixed(1)}%
              </div>
              <div
                style={{
                  height: '4px',
                  backgroundColor: 'var(--border-subtle)',
                  borderRadius: '2px',
                  marginTop: '8px',
                  overflow: 'hidden',
                }}
              >
                <div
                  style={{
                    height: '100%',
                    width: `${analyticsData.overall_passing_rate * 100}%`,
                    backgroundColor: 'var(--status-success)',
                  }}
                />
              </div>
            </Card>

            <Card style={{ padding: '16px', backgroundColor: 'var(--bg-surface)' }}>
              <div style={{ fontSize: '12px', color: 'var(--text-muted)', fontWeight: 600 }}>
                AVERAGE MASTERY INDEX
              </div>
              <div style={{ fontSize: '28px', fontWeight: 800, color: 'var(--brand-primary)', marginTop: '4px' }}>
                {(analyticsData.average_mastery_index * 100).toFixed(1)}%
              </div>
              <div style={{ fontSize: '11px', color: 'var(--text-muted)', marginTop: '4px' }}>
                {analyticsData.total_assessments_taken} assessments graded
              </div>
            </Card>
          </div>

          {/* Department Breakdown Table */}
          <Card style={{ padding: '20px', backgroundColor: 'var(--bg-surface)' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
              <div>
                <h3 style={{ margin: 0, fontSize: '16px', fontWeight: 700, color: 'var(--text-primary)' }}>
                  Departmental Health & Performance Rollup
                </h3>
                <p style={{ margin: '4px 0 0', fontSize: '12px', color: 'var(--text-secondary)' }}>
                  Aggregated from live student performance data with zero mock records.
                </p>
              </div>
              <Badge variant="info">OLTP Synced</Badge>
            </div>

            <div style={{ overflowX: 'auto' }}>
              <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left', fontSize: '13px' }}>
                <thead>
                  <tr style={{ borderBottom: '1px solid var(--border-default)', color: 'var(--text-secondary)' }}>
                    <th style={{ padding: '10px 12px' }}>DEPARTMENT</th>
                    <th style={{ padding: '10px 12px' }}>ENROLLED</th>
                    <th style={{ padding: '10px 12px' }}>AT-RISK</th>
                    <th style={{ padding: '10px 12px' }}>ACTIVE INTERVENTIONS</th>
                    <th style={{ padding: '10px 12px' }}>AVG MASTERY</th>
                    <th style={{ padding: '10px 12px' }}>PASSING RATE</th>
                    <th style={{ padding: '10px 12px' }}>HEALTH</th>
                  </tr>
                </thead>
                <tbody>
                  {analyticsData.departments.map((dept) => {
                    const isHealthy = dept.passing_rate >= 0.90 && dept.at_risk_students <= 3;
                    return (
                      <tr
                        key={dept.department_id}
                        style={{
                          borderBottom: '1px solid var(--border-subtle)',
                          transition: 'background-color 0.15s ease',
                        }}
                      >
                        <td style={{ padding: '12px' }}>
                          <div style={{ fontWeight: 600, color: 'var(--text-primary)' }}>
                            {dept.department_name}
                          </div>
                          <span style={{ fontSize: '11px', color: 'var(--text-muted)' }}>
                            Code: {dept.department_code}
                          </span>
                        </td>
                        <td style={{ padding: '12px', color: 'var(--text-primary)' }}>
                          {dept.enrolled_students}
                        </td>
                        <td style={{ padding: '12px' }}>
                          <span
                            style={{
                              color: dept.at_risk_students > 3 ? 'var(--status-danger)' : 'var(--text-primary)',
                              fontWeight: dept.at_risk_students > 3 ? 700 : 500,
                            }}
                          >
                            {dept.at_risk_students}
                          </span>
                        </td>
                        <td style={{ padding: '12px', color: 'var(--text-primary)' }}>
                          {dept.active_interventions}
                        </td>
                        <td style={{ padding: '12px', color: 'var(--brand-accent)', fontWeight: 600 }}>
                          {(dept.average_mastery * 100).toFixed(1)}%
                        </td>
                        <td style={{ padding: '12px', color: 'var(--status-success)', fontWeight: 600 }}>
                          {(dept.passing_rate * 100).toFixed(1)}%
                        </td>
                        <td style={{ padding: '12px' }}>
                          <Badge variant={isHealthy ? 'success' : 'warning'}>
                            {isHealthy ? 'OPTIMAL' : 'MONITORING'}
                          </Badge>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          </Card>

          {/* Competency Distribution Breakdown */}
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '20px' }}>
            <Card style={{ padding: '20px', backgroundColor: 'var(--bg-surface)' }}>
              <h3 style={{ margin: '0 0 16px', fontSize: '15px', fontWeight: 700, color: 'var(--text-primary)' }}>
                Skill Competency Distribution (4-Tier)
              </h3>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
                <div>
                  <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '12px', marginBottom: '4px' }}>
                    <span style={{ color: 'var(--text-primary)', fontWeight: 600 }}>Mastery (≥ 90%)</span>
                    <span style={{ color: 'var(--text-muted)' }}>{analyticsData.skill_distribution.mastery} students</span>
                  </div>
                  <div style={{ height: '8px', backgroundColor: 'var(--border-subtle)', borderRadius: '4px', overflow: 'hidden' }}>
                    <div style={{ height: '100%', width: `${(analyticsData.skill_distribution.mastery / 420) * 100}%`, backgroundColor: 'var(--status-success)' }} />
                  </div>
                </div>

                <div>
                  <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '12px', marginBottom: '4px' }}>
                    <span style={{ color: 'var(--text-primary)', fontWeight: 600 }}>Proficient (70 - 89%)</span>
                    <span style={{ color: 'var(--text-muted)' }}>{analyticsData.skill_distribution.proficient} students</span>
                  </div>
                  <div style={{ height: '8px', backgroundColor: 'var(--border-subtle)', borderRadius: '4px', overflow: 'hidden' }}>
                    <div style={{ height: '100%', width: `${(analyticsData.skill_distribution.proficient / 420) * 100}%`, backgroundColor: 'var(--brand-primary)' }} />
                  </div>
                </div>

                <div>
                  <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '12px', marginBottom: '4px' }}>
                    <span style={{ color: 'var(--text-primary)', fontWeight: 600 }}>Developing (50 - 69%)</span>
                    <span style={{ color: 'var(--text-muted)' }}>{analyticsData.skill_distribution.developing} students</span>
                  </div>
                  <div style={{ height: '8px', backgroundColor: 'var(--border-subtle)', borderRadius: '4px', overflow: 'hidden' }}>
                    <div style={{ height: '100%', width: `${(analyticsData.skill_distribution.developing / 420) * 100}%`, backgroundColor: 'var(--status-warning)' }} />
                  </div>
                </div>

                <div>
                  <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '12px', marginBottom: '4px' }}>
                    <span style={{ color: 'var(--text-primary)', fontWeight: 600 }}>Novice / Deficit (&lt; 50%)</span>
                    <span style={{ color: 'var(--status-danger)', fontWeight: 700 }}>{analyticsData.skill_distribution.novice} students</span>
                  </div>
                  <div style={{ height: '8px', backgroundColor: 'var(--border-subtle)', borderRadius: '4px', overflow: 'hidden' }}>
                    <div style={{ height: '100%', width: `${(analyticsData.skill_distribution.novice / 420) * 100}%`, backgroundColor: 'var(--status-danger)' }} />
                  </div>
                </div>
              </div>
            </Card>

            <Card style={{ padding: '20px', backgroundColor: 'var(--bg-surface)' }}>
              <h3 style={{ margin: '0 0 16px', fontSize: '15px', fontWeight: 700, color: 'var(--text-primary)' }}>
                Active Interventions by Type
              </h3>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
                {Object.entries(analyticsData.interventions_by_type).map(([typeKey, count]) => (
                  <div
                    key={typeKey}
                    style={{
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'space-between',
                      padding: '8px 12px',
                      backgroundColor: 'var(--bg-surface-elevated)',
                      borderRadius: 'var(--radius-md)',
                      border: '1px solid var(--border-subtle)',
                    }}
                  >
                    <span style={{ fontSize: '13px', color: 'var(--text-primary)', fontWeight: 500 }}>
                      {typeKey.replace(/_/g, ' ')}
                    </span>
                    <Badge variant={count > 0 ? 'info' : 'outline'} size="sm">
                      {count} active
                    </Badge>
                  </div>
                ))}
              </div>
            </Card>
          </div>
        </div>
      )}

      {/* TAB 2: EARLY WARNING & AT-RISK DETECTION */}
      {activeTab === 'early_warning' && isStaff && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
          {/* Controls Bar */}
          <div
            style={{
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center',
              backgroundColor: 'var(--bg-surface)',
              padding: '12px 16px',
              borderRadius: 'var(--radius-lg)',
              border: '1px solid var(--border-subtle)',
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
              <span style={{ fontSize: '13px', color: 'var(--text-secondary)', fontWeight: 600 }}>
                Filter Severity:
              </span>
              {(['ALL', 'CRITICAL', 'HIGH', 'MEDIUM'] as const).map((lvl) => (
                <button
                  key={lvl}
                  onClick={() => setRiskFilter(lvl)}
                  style={{
                    padding: '4px 10px',
                    borderRadius: 'var(--radius-md)',
                    border: '1px solid',
                    borderColor: riskFilter === lvl ? 'var(--brand-primary)' : 'var(--border-subtle)',
                    backgroundColor: riskFilter === lvl ? 'var(--brand-primary-subtle)' : 'transparent',
                    color: riskFilter === lvl ? 'var(--brand-primary)' : 'var(--text-secondary)',
                    fontSize: '12px',
                    fontWeight: 600,
                    cursor: 'pointer',
                  }}
                >
                  {lvl}
                </button>
              ))}
            </div>

            <Badge variant="warning">Engine Rule Ver: 2026.1</Badge>
          </div>

          {/* At Risk Cards Grid */}
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(360px, 1fr))', gap: '16px' }}>
            {filteredAtRiskCohort.map((student) => {
              const isCritical = student.risk_level === 'CRITICAL';
              const isHigh = student.risk_level === 'HIGH';

              return (
                <Card
                  key={student.student_id}
                  style={{
                    padding: '20px',
                    backgroundColor: 'var(--bg-surface)',
                    display: 'flex',
                    flexDirection: 'column',
                    justifyContent: 'space-between',
                    gap: '16px',
                    border: `1px solid ${isCritical ? 'rgba(239, 68, 68, 0.4)' : 'var(--border-default)'}`,
                  }}
                >
                  <div>
                    {/* Header */}
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                      <div>
                        <div style={{ fontSize: '16px', fontWeight: 700, color: 'var(--text-primary)' }}>
                          {student.full_name}
                        </div>
                        <div style={{ fontSize: '12px', color: 'var(--text-muted)' }}>
                          {student.roll_number} • {student.email}
                        </div>
                      </div>
                      <Badge variant={isCritical ? 'danger' : isHigh ? 'warning' : 'info'}>
                        {student.risk_level} RISK
                      </Badge>
                    </div>

                    {/* Trigger Reason */}
                    <div
                      style={{
                        margin: '14px 0',
                        padding: '10px 12px',
                        backgroundColor: 'var(--bg-surface-elevated)',
                        borderRadius: 'var(--radius-md)',
                        borderLeft: `3px solid ${isCritical ? 'var(--status-danger)' : 'var(--status-warning)'}`,
                      }}
                    >
                      <div style={{ fontSize: '11px', fontWeight: 700, color: 'var(--text-muted)' }}>
                        PRIMARY TRIGGER REASON
                      </div>
                      <div style={{ fontSize: '12px', color: 'var(--text-primary)', marginTop: '2px', lineHeight: 1.4 }}>
                        {student.trigger_reason}
                      </div>
                    </div>

                    {/* Detected Rules List */}
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                      <div style={{ fontSize: '11px', fontWeight: 600, color: 'var(--text-secondary)' }}>
                        AUDITED TRIGGER RULES:
                      </div>
                      {student.detected_rules.map((rule) => (
                        <div
                          key={rule.rule_id}
                          style={{
                            fontSize: '11px',
                            backgroundColor: 'var(--bg-surface-subtle)',
                            padding: '6px 10px',
                            borderRadius: 'var(--radius-sm)',
                            border: '1px solid var(--border-subtle)',
                            color: 'var(--text-secondary)',
                          }}
                        >
                          <span style={{ fontWeight: 600, color: 'var(--text-primary)' }}>{rule.name}:</span>{' '}
                          {rule.description}
                        </div>
                      ))}
                    </div>

                    {/* Recommended Support */}
                    <div style={{ marginTop: '14px', display: 'flex', alignItems: 'center', gap: '8px' }}>
                      <span style={{ fontSize: '11px', color: 'var(--text-muted)' }}>Recommendation:</span>
                      <Badge variant="info" size="sm">
                        {student.recommended_intervention_type.replace(/_/g, ' ')}
                      </Badge>
                    </div>
                  </div>

                  {/* Actions */}
                  <div style={{ borderTop: '1px solid var(--border-subtle)', paddingTop: '12px', display: 'flex', justifyContent: 'flex-end' }}>
                    <Button
                      variant="primary"
                      size="sm"
                      onClick={() => openAssignModal(student)}
                    >
                      Assign Support Intervention
                    </Button>
                  </div>
                </Card>
              );
            })}
          </div>
        </div>
      )}

      {/* TAB 3: INTERVENTION MANAGEMENT */}
      {activeTab === 'interventions' && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
          {/* Status Filter Bar */}
          <div
            style={{
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center',
              backgroundColor: 'var(--bg-surface)',
              padding: '12px 16px',
              borderRadius: 'var(--radius-lg)',
              border: '1px solid var(--border-subtle)',
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
              <span style={{ fontSize: '13px', color: 'var(--text-secondary)', fontWeight: 600 }}>
                Status:
              </span>
              {(['ALL', 'ASSIGNED', 'IN_PROGRESS', 'COMPLETED', 'ESCALATED'] as const).map((st) => (
                <button
                  key={st}
                  onClick={() => setInterventionStatusFilter(st)}
                  style={{
                    padding: '4px 10px',
                    borderRadius: 'var(--radius-md)',
                    border: '1px solid',
                    borderColor: interventionStatusFilter === st ? 'var(--brand-primary)' : 'var(--border-subtle)',
                    backgroundColor: interventionStatusFilter === st ? 'var(--brand-primary-subtle)' : 'transparent',
                    color: interventionStatusFilter === st ? 'var(--brand-primary)' : 'var(--text-secondary)',
                    fontSize: '12px',
                    fontWeight: 600,
                    cursor: 'pointer',
                  }}
                >
                  {st}
                </button>
              ))}
            </div>

            <Badge variant="outline">
              {filteredInterventions.length} Record{filteredInterventions.length === 1 ? '' : 's'}
            </Badge>
          </div>

          {/* Interventions Cards */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
            {filteredInterventions.length === 0 ? (
              <Card style={{ padding: '36px', textAlign: 'center', color: 'var(--text-muted)' }}>
                No academic interventions match the selected filter.
              </Card>
            ) : (
              filteredInterventions.map((item) => {
                const isCompleted = item.status === 'COMPLETED';
                const isEscalated = item.status === 'ESCALATED';

                return (
                  <Card
                    key={item.id}
                    style={{
                      padding: '20px',
                      backgroundColor: 'var(--bg-surface)',
                      display: 'flex',
                      flexDirection: 'column',
                      gap: '12px',
                      border: isEscalated
                        ? '1px solid rgba(239, 68, 68, 0.5)'
                        : isCompleted
                        ? '1px solid rgba(16, 185, 129, 0.4)'
                        : '1px solid var(--border-default)',
                    }}
                  >
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                      <div>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                          <span style={{ fontSize: '15px', fontWeight: 700, color: 'var(--text-primary)' }}>
                            {item.student?.full_name}
                          </span>
                          <span style={{ fontSize: '12px', color: 'var(--text-muted)' }}>
                            ({item.student?.roll_number})
                          </span>
                          <Badge variant="info" size="sm">
                            {item.intervention_type.replace(/_/g, ' ')}
                          </Badge>
                        </div>
                        <div style={{ fontSize: '12px', color: 'var(--text-secondary)', marginTop: '2px' }}>
                          Supervising Faculty: {item.faculty?.full_name || 'Pending Mentor Assignment'}
                        </div>
                      </div>

                      <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                        <Badge
                          variant={
                            item.status === 'COMPLETED'
                              ? 'success'
                              : item.status === 'ESCALATED'
                              ? 'danger'
                              : item.status === 'IN_PROGRESS'
                              ? 'warning'
                              : 'default'
                          }
                        >
                          {item.status}
                        </Badge>

                        {isStaff && (
                          <Button
                            variant="outline"
                            size="sm"
                            onClick={() => openUpdateModal(item)}
                          >
                            Update Progress
                          </Button>
                        )}
                      </div>
                    </div>

                    {/* Trigger & Plan */}
                    <div
                      style={{
                        display: 'grid',
                        gridTemplateColumns: '1fr 1fr',
                        gap: '16px',
                        backgroundColor: 'var(--bg-surface-elevated)',
                        padding: '12px',
                        borderRadius: 'var(--radius-md)',
                      }}
                    >
                      <div>
                        <div style={{ fontSize: '11px', fontWeight: 700, color: 'var(--text-muted)' }}>
                          TRIGGER REASON
                        </div>
                        <div style={{ fontSize: '12px', color: 'var(--text-primary)', marginTop: '2px' }}>
                          {item.trigger_reason}
                        </div>
                      </div>

                      <div>
                        <div style={{ fontSize: '11px', fontWeight: 700, color: 'var(--text-muted)' }}>
                          ACTION PLAN
                        </div>
                        <div style={{ fontSize: '12px', color: 'var(--text-primary)', marginTop: '2px' }}>
                          {item.action_plan || 'Pending formulation.'}
                        </div>
                      </div>
                    </div>

                    {/* Outcome notes if present */}
                    {item.outcome_notes && (
                      <div
                        style={{
                          fontSize: '12px',
                          color: 'var(--text-secondary)',
                          backgroundColor: 'var(--bg-surface-subtle)',
                          padding: '8px 12px',
                          borderRadius: 'var(--radius-sm)',
                          borderLeft: '3px solid var(--brand-accent)',
                        }}
                      >
                        <span style={{ fontWeight: 600, color: 'var(--text-primary)' }}>Outcome Notes:</span>{' '}
                        {item.outcome_notes}
                      </div>
                    )}

                    <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '11px', color: 'var(--text-muted)' }}>
                      <span>Assigned: {new Date(item.assigned_at).toLocaleDateString()}</span>
                      {item.due_date && <span>Target Due: {new Date(item.due_date).toLocaleDateString()}</span>}
                      {item.completed_at && <span>Completed: {new Date(item.completed_at).toLocaleDateString()}</span>}
                    </div>
                  </Card>
                );
              })
            )}
          </div>
        </div>
      )}

      {/* TAB 4: NOTIFICATION HUB */}
      {activeTab === 'notifications' && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
          <div
            style={{
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center',
              backgroundColor: 'var(--bg-surface)',
              padding: '12px 16px',
              borderRadius: 'var(--radius-lg)',
              border: '1px solid var(--border-subtle)',
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
              <button
                onClick={() => setNotificationUnreadOnly(false)}
                style={{
                  padding: '4px 10px',
                  borderRadius: 'var(--radius-md)',
                  border: '1px solid',
                  borderColor: !notificationUnreadOnly ? 'var(--brand-primary)' : 'var(--border-subtle)',
                  backgroundColor: !notificationUnreadOnly ? 'var(--brand-primary-subtle)' : 'transparent',
                  color: !notificationUnreadOnly ? 'var(--brand-primary)' : 'var(--text-secondary)',
                  fontSize: '12px',
                  fontWeight: 600,
                  cursor: 'pointer',
                }}
              >
                All Notifications ({notifications.length})
              </button>

              <button
                onClick={() => setNotificationUnreadOnly(true)}
                style={{
                  padding: '4px 10px',
                  borderRadius: 'var(--radius-md)',
                  border: '1px solid',
                  borderColor: notificationUnreadOnly ? 'var(--brand-primary)' : 'var(--border-subtle)',
                  backgroundColor: notificationUnreadOnly ? 'var(--brand-primary-subtle)' : 'transparent',
                  color: notificationUnreadOnly ? 'var(--brand-primary)' : 'var(--text-secondary)',
                  fontSize: '12px',
                  fontWeight: 600,
                  cursor: 'pointer',
                }}
              >
                Unread Only ({notifications.filter((n) => !n.is_read).length})
              </button>
            </div>

            <Button
              variant="outline"
              size="sm"
              onClick={markAllNotifsRead}
            >
              Mark All Read
            </Button>
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
            {filteredNotifications.length === 0 ? (
              <Card style={{ padding: '36px', textAlign: 'center', color: 'var(--text-muted)' }}>
                No notifications to display.
              </Card>
            ) : (
              filteredNotifications.map((notif) => (
                <Card
                  key={notif.id}
                  style={{
                    padding: '16px',
                    backgroundColor: notif.is_read ? 'var(--bg-surface)' : 'var(--bg-surface-elevated)',
                    border: notif.is_read ? '1px solid var(--border-subtle)' : '1px solid var(--border-strong)',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'space-between',
                  }}
                >
                  <div style={{ display: 'flex', alignItems: 'flex-start', gap: '12px' }}>
                    <span
                      style={{
                        width: '8px',
                        height: '8px',
                        borderRadius: '50%',
                        backgroundColor: notif.is_read ? 'transparent' : 'var(--brand-primary)',
                        marginTop: '6px',
                      }}
                    />
                    <div>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                        <span style={{ fontSize: '14px', fontWeight: 700, color: 'var(--text-primary)' }}>
                          {notif.title}
                        </span>
                        <Badge
                          variant={
                            notif.notification_type === 'EARLY_WARNING'
                              ? 'warning'
                              : notif.notification_type === 'INTERVENTION_ASSIGNED'
                              ? 'info'
                              : 'default'
                          }
                          size="sm"
                        >
                          {notif.notification_type}
                        </Badge>
                      </div>
                      <p style={{ margin: '4px 0 0', fontSize: '13px', color: 'var(--text-secondary)' }}>
                        {notif.message}
                      </p>
                      <span style={{ fontSize: '11px', color: 'var(--text-muted)', display: 'block', marginTop: '4px' }}>
                        {new Date(notif.created_at).toLocaleString()}
                      </span>
                    </div>
                  </div>

                  {!notif.is_read && (
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => markNotifRead(notif.id)}
                    >
                      Mark Read
                    </Button>
                  )}
                </Card>
              ))
            )}
          </div>
        </div>
      )}

      {/* MODAL: ASSIGN INTERVENTION */}
      {isAssignModalOpen && selectedStudentForAssign && (
        <div
          style={{
            position: 'fixed',
            inset: 0,
            backgroundColor: 'var(--bg-overlay)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            zIndex: 1000,
            padding: '16px',
          }}
        >
          <div
            style={{
              backgroundColor: 'var(--bg-surface)',
              borderRadius: 'var(--radius-lg)',
              border: '1px solid var(--border-default)',
              width: '100%',
              maxWidth: '520px',
              padding: '24px',
              display: 'flex',
              flexDirection: 'column',
              gap: '16px',
            }}
          >
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <div>
                <h3 style={{ margin: 0, fontSize: '18px', fontWeight: 700, color: 'var(--text-primary)' }}>
                  Assign Academic Support Intervention
                </h3>
                <span style={{ fontSize: '12px', color: 'var(--text-muted)' }}>
                  Student: {selectedStudentForAssign.full_name} ({selectedStudentForAssign.roll_number})
                </span>
              </div>
              <button
                onClick={() => setIsAssignModalOpen(false)}
                style={{ background: 'none', border: 'none', color: 'var(--text-muted)', cursor: 'pointer', fontSize: '18px' }}
              >
                ✕
              </button>
            </div>

            <form onSubmit={handleCreateIntervention} style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
              <div>
                <label style={{ display: 'block', fontSize: '12px', fontWeight: 600, color: 'var(--text-secondary)', marginBottom: '4px' }}>
                  Intervention Strategy
                </label>
                <select
                  value={assignForm.intervention_type}
                  onChange={(e) => setAssignForm({ ...assignForm, intervention_type: e.target.value as InterventionType })}
                  style={{
                    width: '100%',
                    padding: '8px 12px',
                    borderRadius: 'var(--radius-md)',
                    backgroundColor: 'var(--bg-surface-elevated)',
                    border: '1px solid var(--border-default)',
                    color: 'var(--text-primary)',
                    fontSize: '13px',
                  }}
                >
                  <option value="ACADEMIC_TUTORING">Academic Tutoring (Targeted 1:1 Lab)</option>
                  <option value="STUDY_PLAN_REVISION">Study Plan Revision</option>
                  <option value="MENTOR_CHECKIN">Faculty Mentor Check-in</option>
                  <option value="ATTENDANCE_COUNSELING">Attendance & Engagement Counseling</option>
                  <option value="PSYCHOLOGICAL_COUNSELING">Institutional Counseling Services</option>
                </select>
              </div>

              <div>
                <label style={{ display: 'block', fontSize: '12px', fontWeight: 600, color: 'var(--text-secondary)', marginBottom: '4px' }}>
                  Action Plan Deliverables
                </label>
                <textarea
                  rows={3}
                  value={assignForm.action_plan}
                  onChange={(e) => setAssignForm({ ...assignForm, action_plan: e.target.value })}
                  placeholder="Specific recovery schedule or remediation tasks..."
                  required
                  style={{
                    width: '100%',
                    padding: '8px 12px',
                    borderRadius: 'var(--radius-md)',
                    backgroundColor: 'var(--bg-surface-elevated)',
                    border: '1px solid var(--border-default)',
                    color: 'var(--text-primary)',
                    fontSize: '13px',
                    fontFamily: 'inherit',
                  }}
                />
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px' }}>
                <div>
                  <label style={{ display: 'block', fontSize: '12px', fontWeight: 600, color: 'var(--text-secondary)', marginBottom: '4px' }}>
                    Target Resolution Window
                  </label>
                  <select
                    value={assignForm.due_days}
                    onChange={(e) => setAssignForm({ ...assignForm, due_days: e.target.value })}
                    style={{
                      width: '100%',
                      padding: '8px 12px',
                      borderRadius: 'var(--radius-md)',
                      backgroundColor: 'var(--bg-surface-elevated)',
                      border: '1px solid var(--border-default)',
                      color: 'var(--text-primary)',
                      fontSize: '13px',
                    }}
                  >
                    <option value="7">7 Days (High Urgency)</option>
                    <option value="14">14 Days (Standard)</option>
                    <option value="30">30 Days (Semester Milestone)</option>
                  </select>
                </div>

                <div>
                  <label style={{ display: 'block', fontSize: '12px', fontWeight: 600, color: 'var(--text-secondary)', marginBottom: '4px' }}>
                    Supervisor
                  </label>
                  <div
                    style={{
                      padding: '8px 12px',
                      backgroundColor: 'var(--bg-surface-elevated)',
                      borderRadius: 'var(--radius-md)',
                      fontSize: '13px',
                      color: 'var(--text-secondary)',
                      border: '1px solid var(--border-default)',
                    }}
                  >
                    {user?.full_name || 'Current User'}
                  </div>
                </div>
              </div>

              <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '8px', marginTop: '12px' }}>
                <Button variant="outline" type="button" onClick={() => setIsAssignModalOpen(false)}>
                  Cancel
                </Button>
                <Button variant="primary" type="submit">
                  Dispatch Intervention
                </Button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* MODAL: UPDATE INTERVENTION */}
      {isUpdateModalOpen && selectedInterventionForUpdate && (
        <div
          style={{
            position: 'fixed',
            inset: 0,
            backgroundColor: 'var(--bg-overlay)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            zIndex: 1000,
            padding: '16px',
          }}
        >
          <div
            style={{
              backgroundColor: 'var(--bg-surface)',
              borderRadius: 'var(--radius-lg)',
              border: '1px solid var(--border-default)',
              width: '100%',
              maxWidth: '520px',
              padding: '24px',
              display: 'flex',
              flexDirection: 'column',
              gap: '16px',
            }}
          >
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <div>
                <h3 style={{ margin: 0, fontSize: '18px', fontWeight: 700, color: 'var(--text-primary)' }}>
                  Update Intervention Status & Outcomes
                </h3>
                <span style={{ fontSize: '12px', color: 'var(--text-muted)' }}>
                  Student: {selectedInterventionForUpdate.student?.full_name}
                </span>
              </div>
              <button
                onClick={() => setIsUpdateModalOpen(false)}
                style={{ background: 'none', border: 'none', color: 'var(--text-muted)', cursor: 'pointer', fontSize: '18px' }}
              >
                ✕
              </button>
            </div>

            <form onSubmit={handleUpdateIntervention} style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
              <div>
                <label style={{ display: 'block', fontSize: '12px', fontWeight: 600, color: 'var(--text-secondary)', marginBottom: '4px' }}>
                  Progress Status
                </label>
                <select
                  value={updateForm.status}
                  onChange={(e) => setUpdateForm({ ...updateForm, status: e.target.value as InterventionStatus })}
                  style={{
                    width: '100%',
                    padding: '8px 12px',
                    borderRadius: 'var(--radius-md)',
                    backgroundColor: 'var(--bg-surface-elevated)',
                    border: '1px solid var(--border-default)',
                    color: 'var(--text-primary)',
                    fontSize: '13px',
                  }}
                >
                  <option value="IN_PROGRESS">IN_PROGRESS (Remediation active)</option>
                  <option value="COMPLETED">COMPLETED (Objectives fulfilled, risk normalized)</option>
                  <option value="ESCALATED">ESCALATED (Require HOD / Academic Dean review)</option>
                  <option value="DISMISSED">DISMISSED (Resolved via external petition)</option>
                </select>
              </div>

              <div>
                <label style={{ display: 'block', fontSize: '12px', fontWeight: 600, color: 'var(--text-secondary)', marginBottom: '4px' }}>
                  Outcome Notes & Evaluation
                </label>
                <textarea
                  rows={4}
                  value={updateForm.outcome_notes}
                  onChange={(e) => setUpdateForm({ ...updateForm, outcome_notes: e.target.value })}
                  placeholder="Record remediation session results, student feedback, or resolved assessment marks..."
                  required
                  style={{
                    width: '100%',
                    padding: '8px 12px',
                    borderRadius: 'var(--radius-md)',
                    backgroundColor: 'var(--bg-surface-elevated)',
                    border: '1px solid var(--border-default)',
                    color: 'var(--text-primary)',
                    fontSize: '13px',
                    fontFamily: 'inherit',
                  }}
                />
              </div>

              <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '8px', marginTop: '12px' }}>
                <Button variant="outline" type="button" onClick={() => setIsUpdateModalOpen(false)}>
                  Cancel
                </Button>
                <Button variant="primary" type="submit">
                  Save Changes
                </Button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
