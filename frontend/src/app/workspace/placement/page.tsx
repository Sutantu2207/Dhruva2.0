'use client';

import React, { useEffect, useState, useMemo } from 'react';
import { useAuth } from '@/lib/auth/AuthContext';
import { api, ApiError } from '@/lib/api/client';
import {
  Project,
  ProjectType,
  ProjectStatus,
  Portfolio,
  PortfolioVisibility,
  PublicPortfolio,
  CareerGoal,
  CareerReadiness,
  TalentCandidate,
  PlacementAnalytics,
} from '@/types/placement';
import { Skill } from '@/types/mastery';
import { PageHeader } from '@/components/ui/PageHeader';
import { Button } from '@/components/ui/Button';
import { Badge } from '@/components/ui/Badge';
import { EmptyState } from '@/components/ui/EmptyState';
import { ErrorState } from '@/components/ui/ErrorState';
import { Dialog } from '@/components/ui/Dialog';
import { Input } from '@/components/ui/Input';
import { Select } from '@/components/ui/Select';
import { Alert } from '@/components/ui/Alert';

export default function PlacementAndPortfoliosPage() {
  const { user } = useAuth();
  const tenantSlug = user?.institution_slug || '';

  const isStaff = useMemo(() => {
    if (!user) return false;
    return user.roles.some((r) =>
      ['SUPER_ADMIN', 'INSTITUTION_ADMIN', 'HOD', 'FACULTY', 'PLACEMENT_OFFICER'].includes(r)
    );
  }, [user]);

  const isPlacementOfficer = useMemo(() => {
    if (!user) return false;
    return user.roles.some((r) =>
      ['SUPER_ADMIN', 'INSTITUTION_ADMIN', 'HOD', 'PLACEMENT_OFFICER'].includes(r)
    );
  }, [user]);

  // Main tabs
  const [activeTab, setActiveTab] = useState<'projects' | 'portfolio' | 'readiness' | 'talent'>(
    isPlacementOfficer ? 'talent' : 'projects'
  );

  // Common loading & error states
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [error, setError] = useState<{ message: string; code?: string; requestId?: string } | null>(null);

  // Skills library for linking
  const [skills, setSkills] = useState<Skill[]>([]);

  // =========================================================================
  // TAB 1: STUDENT PROJECT STUDIO
  // =========================================================================
  const [projects, setProjects] = useState<Project[]>([]);
  const [projectStatusFilter, setProjectStatusFilter] = useState<string>('ALL');

  // New Project Dialog
  const [isNewProjectOpen, setIsNewProjectOpen] = useState(false);
  const [newProjTitle, setNewProjTitle] = useState('');
  const [newProjDesc, setNewProjDesc] = useState('');
  const [newProjType, setNewProjType] = useState<ProjectType>('COURSE_PROJECT');
  const [newProjRepoUrl, setNewProjRepoUrl] = useState('');
  const [newProjDemoUrl, setNewProjDemoUrl] = useState('');
  const [newProjContribution, setNewProjContribution] = useState('');
  const [newProjSkillIds, setNewProjSkillIds] = useState<string[]>([]);

  // Verify / Revoke Dialogs (Staff)
  const [verifyingProject, setVerifyingProject] = useState<Project | null>(null);
  const [verifyApproved, setVerifyApproved] = useState<boolean>(true);
  const [verifyNotes, setVerifyNotes] = useState('');
  const [isVerifyModalOpen, setIsVerifyModalOpen] = useState(false);

  const [revokingProject, setRevokingProject] = useState<Project | null>(null);
  const [revocationReason, setRevocationReason] = useState('');
  const [isRevokeModalOpen, setIsRevokeModalOpen] = useState(false);

  // =========================================================================
  // TAB 2: PORTFOLIO BUILDER
  // =========================================================================
  const [portfolio, setPortfolio] = useState<Portfolio | null>(null);
  const [portHeadline, setPortHeadline] = useState('');
  const [portBio, setPortBio] = useState('');
  const [portVisibility, setPortVisibility] = useState<PortfolioVisibility>('PRIVATE');
  const [portCuratedProjects, setPortCuratedProjects] = useState<string[]>([]);
  const [portGithub, setPortGithub] = useState('');
  const [portLinkedin, setPortLinkedin] = useState('');
  const [portWebsite, setPortWebsite] = useState('');
  const [isSavingPortfolio, setIsSavingPortfolio] = useState(false);

  // =========================================================================
  // TAB 3: CAREER GOALS & DETERMINISTIC READINESS
  // =========================================================================
  const [careerGoal, setCareerGoal] = useState<CareerGoal | null>(null);
  const [careerReadiness, setCareerReadiness] = useState<CareerReadiness | null>(null);
  const [isGoalModalOpen, setIsGoalModalOpen] = useState(false);
  const [targetRoleInput, setTargetRoleInput] = useState('');
  const [targetIndustryInput, setTargetIndustryInput] = useState('');
  const [targetCompaniesInput, setTargetCompaniesInput] = useState('');
  const [selectedRequiredSkills, setSelectedRequiredSkills] = useState<string[]>([]);
  const [isCalculatingReadiness, setIsCalculatingReadiness] = useState(false);

  // =========================================================================
  // TAB 4: PLACEMENT TALENT DISCOVERY & ANALYTICS
  // =========================================================================
  const [talentCandidates, setTalentCandidates] = useState<TalentCandidate[]>([]);
  const [placementAnalytics, setPlacementAnalytics] = useState<PlacementAnalytics | null>(null);
  const [minReadinessFilter, setMinReadinessFilter] = useState<string>('0.0');
  const [roleSearchFilter, setRoleSearchFilter] = useState<string>('');

  // =========================================================================
  // DATA LOADING
  // =========================================================================
  const loadData = async () => {
    if (!tenantSlug) return;
    setIsLoading(true);
    setError(null);
    try {
      // 1. Load institutional skills library
      const sRes = await api.get<{ data: Skill[] }>(
        `/api/v1/institutions/${tenantSlug}/skills?page_size=100`
      );
      setSkills(sRes.data || []);

      // 2. Load student projects
      const pRes = await api.get<{ data: Project[] }>(
        `/api/v1/institutions/${tenantSlug}/projects?page_size=100`
      );
      setProjects(pRes.data || []);

      // 3. Load portfolio
      try {
        const portRes = await api.get<{ data: Portfolio }>(
          `/api/v1/institutions/${tenantSlug}/portfolios/me`
        );
        if (portRes.data) {
          setPortfolio(portRes.data);
          setPortHeadline(portRes.data.headline || '');
          setPortBio(portRes.data.bio || '');
          setPortVisibility(portRes.data.visibility || 'PRIVATE');
          setPortCuratedProjects(portRes.data.curated_project_ids || []);
          setPortGithub(portRes.data.social_links?.github || '');
          setPortLinkedin(portRes.data.social_links?.linkedin || '');
          setPortWebsite(portRes.data.social_links?.website || '');
        }
      } catch {
        // Portfolio not yet initialized
      }

      // 4. Load career goal & readiness
      try {
        const gRes = await api.get<{ data: CareerGoal | null }>(
          `/api/v1/institutions/${tenantSlug}/career-goals/me`
        );
        if (gRes.data) {
          setCareerGoal(gRes.data);
          setTargetRoleInput(gRes.data.target_role);
          setTargetIndustryInput(gRes.data.target_industry);
          setTargetCompaniesInput(gRes.data.target_companies?.join(', ') || '');
          setSelectedRequiredSkills(gRes.data.required_skill_ids || []);
        }
      } catch {
        // No active goal
      }

      // 5. If Placement Officer or Staff, load talent pool & analytics
      if (isPlacementOfficer) {
        try {
          const tRes = await api.get<{ data: TalentCandidate[] }>(
            `/api/v1/institutions/${tenantSlug}/placement/talent-pool`
          );
          setTalentCandidates(tRes.data || []);

          const aRes = await api.get<{ data: PlacementAnalytics }>(
            `/api/v1/institutions/${tenantSlug}/placement/readiness-analytics`
          );
          setPlacementAnalytics(aRes.data || null);
        } catch {
          // Handled gracefully
        }
      }
    } catch (err: unknown) {
      const apiErr = err as ApiError;
      setError({
        message: apiErr.message || 'Failed to load projects and placement data.',
        code: apiErr.code,
        requestId: apiErr.requestId,
      });
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, [tenantSlug]);

  // =========================================================================
  // ACTIONS: PROJECT STUDIO
  // =========================================================================
  const handleCreateProject = async () => {
    if (!newProjTitle.trim()) {
      alert('Please enter a project title.');
      return;
    }
    try {
      const res = await api.post<{ data: Project }>(
        `/api/v1/institutions/${tenantSlug}/projects`,
        {
          title: newProjTitle.trim(),
          description: newProjDesc.trim(),
          project_type: newProjType,
          repository_url: newProjRepoUrl.trim(),
          deployment_url: newProjDemoUrl.trim(),
          contribution_details: newProjContribution.trim(),
          skill_ids: newProjSkillIds,
        }
      );
      setProjects((prev) => [res.data, ...prev]);
      setIsNewProjectOpen(false);
      setNewProjTitle('');
      setNewProjDesc('');
      setNewProjRepoUrl('');
      setNewProjDemoUrl('');
      setNewProjContribution('');
      setNewProjSkillIds([]);
      alert('Project deliverable saved in DRAFT status.');
    } catch (err: unknown) {
      const apiErr = err as ApiError;
      alert(`Error creating project: ${apiErr.message}`);
    }
  };

  const handleSubmitProject = async (projectId: string) => {
    try {
      const res = await api.post<{ data: Project }>(
        `/api/v1/institutions/${tenantSlug}/projects/${projectId}/submit`,
        {}
      );
      setProjects((prev) => prev.map((p) => (p.id === projectId ? res.data : p)));
      alert('Project submitted for faculty verification.');
    } catch (err: unknown) {
      const apiErr = err as ApiError;
      alert(`Error submitting project: ${apiErr.message}`);
    }
  };

  const handleVerifyProject = async () => {
    if (!verifyingProject) return;
    try {
      const res = await api.post<{ data: Project }>(
        `/api/v1/institutions/${tenantSlug}/projects/${verifyingProject.id}/verify`,
        {
          is_verified: verifyApproved,
          verification_notes: verifyNotes.trim(),
        }
      );
      setProjects((prev) => prev.map((p) => (p.id === verifyingProject.id ? res.data : p)));
      setIsVerifyModalOpen(false);
      setVerifyingProject(null);
      setVerifyNotes('');
      alert(`Project ${verifyApproved ? 'VERIFIED' : 'REJECTED'} successfully.`);
    } catch (err: unknown) {
      const apiErr = err as ApiError;
      alert(`Error verifying project: ${apiErr.message}`);
    }
  };

  const handleRevokeProject = async () => {
    if (!revokingProject) return;
    if (!revocationReason.trim() || revocationReason.trim().length < 5) {
      alert('Please enter a clear revocation reason (minimum 5 characters).');
      return;
    }
    try {
      const res = await api.post<{ data: Project }>(
        `/api/v1/institutions/${tenantSlug}/projects/${revokingProject.id}/revoke`,
        {
          revocation_reason: revocationReason.trim(),
        }
      );
      setProjects((prev) => prev.map((p) => (p.id === revokingProject.id ? res.data : p)));
      setIsRevokeModalOpen(false);
      setRevokingProject(null);
      setRevocationReason('');
      alert('Project verification revoked.');
    } catch (err: unknown) {
      const apiErr = err as ApiError;
      alert(`Error revoking verification: ${apiErr.message}`);
    }
  };

  // =========================================================================
  // ACTIONS: PORTFOLIO BUILDER
  // =========================================================================
  const handleSavePortfolio = async () => {
    setIsSavingPortfolio(true);
    try {
      const res = await api.put<{ data: Portfolio }>(
        `/api/v1/institutions/${tenantSlug}/portfolios/me`,
        {
          headline: portHeadline.trim(),
          bio: portBio.trim(),
          visibility: portVisibility,
          curated_project_ids: portCuratedProjects,
          social_links: {
            github: portGithub.trim(),
            linkedin: portLinkedin.trim(),
            website: portWebsite.trim(),
          },
        }
      );
      setPortfolio(res.data);
      alert('Portfolio settings updated successfully.');
    } catch (err: unknown) {
      const apiErr = err as ApiError;
      alert(`Error updating portfolio: ${apiErr.message}`);
    } finally {
      setIsSavingPortfolio(false);
    }
  };

  const handleTogglePublish = async () => {
    if (!portfolio) return;
    const nextState = !portfolio.is_published;
    try {
      const res = await api.post<{ data: Portfolio }>(
        `/api/v1/institutions/${tenantSlug}/portfolios/me/publish`,
        { is_published: nextState }
      );
      setPortfolio(res.data);
      alert(`Portfolio ${nextState ? 'PUBLISHED' : 'UNPUBLISHED'}.`);
    } catch (err: unknown) {
      const apiErr = err as ApiError;
      alert(`Error updating publication status: ${apiErr.message}`);
    }
  };

  // =========================================================================
  // ACTIONS: CAREER GOALS & DETERMINISTIC READINESS
  // =========================================================================
  const handleSaveCareerGoal = async () => {
    if (!targetRoleInput.trim()) {
      alert('Please specify a target role.');
      return;
    }
    const companies = targetCompaniesInput
      .split(',')
      .map((c) => c.trim())
      .filter(Boolean);

    try {
      const res = await api.post<{ data: CareerGoal }>(
        `/api/v1/institutions/${tenantSlug}/career-goals/me`,
        {
          target_role: targetRoleInput.trim(),
          target_industry: targetIndustryInput.trim(),
          target_companies: companies,
          required_skill_ids: selectedRequiredSkills,
        }
      );
      setCareerGoal(res.data);
      setIsGoalModalOpen(false);
      // Immediately calculate readiness
      await handleCalculateReadiness(res.data.id);
    } catch (err: unknown) {
      const apiErr = err as ApiError;
      alert(`Error saving career goal: ${apiErr.message}`);
    }
  };

  const handleCalculateReadiness = async (goalId?: string) => {
    setIsCalculatingReadiness(true);
    try {
      const gId = goalId || careerGoal?.id;
      const url = gId
        ? `/api/v1/institutions/${tenantSlug}/career-readiness/calculate?career_goal_id=${gId}`
        : `/api/v1/institutions/${tenantSlug}/career-readiness/calculate`;

      const res = await api.post<{ data: CareerReadiness }>(url, {});
      setCareerReadiness(res.data);
      alert(`Career Readiness calculated: ${(res.data.readiness_score * 100).toFixed(1)}% match.`);
    } catch (err: unknown) {
      const apiErr = err as ApiError;
      alert(`Error calculating career readiness: ${apiErr.message}`);
    } finally {
      setIsCalculatingReadiness(false);
    }
  };

  // =========================================================================
  // ACTIONS: TALENT POOL SEARCH (STAFF)
  // =========================================================================
  const handleSearchTalent = async () => {
    setIsLoading(true);
    try {
      const minScore = parseFloat(minReadinessFilter) || 0.0;
      let url = `/api/v1/institutions/${tenantSlug}/placement/talent-pool?min_readiness=${minScore}`;
      if (roleSearchFilter.trim()) {
        url += `&target_role=${encodeURIComponent(roleSearchFilter.trim())}`;
      }
      const res = await api.get<{ data: TalentCandidate[] }>(url);
      setTalentCandidates(res.data || []);
    } catch (err: unknown) {
      const apiErr = err as ApiError;
      alert(`Error searching talent pool: ${apiErr.message}`);
    } finally {
      setIsLoading(false);
    }
  };

  // Status badge helper
  const getStatusBadge = (status: ProjectStatus) => {
    switch (status) {
      case 'VERIFIED':
        return <Badge variant="success">VERIFIED</Badge>;
      case 'SUBMITTED':
        return <Badge variant="warning">SUBMITTED</Badge>;
      case 'REJECTED':
        return <Badge variant="danger">REJECTED</Badge>;
      case 'REVOKED':
        return <Badge variant="danger">REVOKED</Badge>;
      case 'DRAFT':
      default:
        return <Badge variant="default">DRAFT</Badge>;
    }
  };

  // Filtered projects
  const filteredProjects = useMemo(() => {
    return projects.filter((p) => {
      if (projectStatusFilter === 'ALL') return true;
      return p.status === projectStatusFilter;
    });
  }, [projects, projectStatusFilter]);

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '24px', paddingBottom: '60px' }}>
      <PageHeader
        title="Student Projects, Portfolios & Placement Engine"
        description="Verified capstone project studio, public & institutional portfolio publishing, explainable career readiness matching, and restricted placement talent discovery."
      />

      {error && (
        <ErrorState
          title="Placement Engine Unavailable"
          message={error.message}
          code={error.code}
          requestId={error.requestId}
          onRetry={loadData}
        />
      )}

      {/* Main Tab Switcher */}
      <div
        style={{
          display: 'flex',
          gap: '8px',
          borderBottom: '1px solid var(--border-subtle)',
          paddingBottom: '8px',
          flexWrap: 'wrap',
        }}
      >
        <Button
          variant={activeTab === 'projects' ? 'primary' : 'ghost'}
          onClick={() => setActiveTab('projects')}
        >
          Project Studio ({projects.length})
        </Button>
        <Button
          variant={activeTab === 'portfolio' ? 'primary' : 'ghost'}
          onClick={() => setActiveTab('portfolio')}
        >
          Portfolio Builder {portfolio?.is_published ? '(Live)' : '(Draft)'}
        </Button>
        <Button
          variant={activeTab === 'readiness' ? 'primary' : 'ghost'}
          onClick={() => setActiveTab('readiness')}
        >
          Career Goals & Readiness
        </Button>
        {isPlacementOfficer && (
          <Button
            variant={activeTab === 'talent' ? 'primary' : 'ghost'}
            onClick={() => setActiveTab('talent')}
          >
            Placement Talent Discovery ({talentCandidates.length})
          </Button>
        )}
      </div>

      {isLoading && (
        <div style={{ padding: '40px', textAlign: 'center', color: 'var(--text-secondary)' }}>
          Loading projects and talent analytics...
        </div>
      )}

      {/* =====================================================================
          TAB 1: STUDENT PROJECT STUDIO
         ===================================================================== */}
      {!isLoading && activeTab === 'projects' && (
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
                value={projectStatusFilter}
                onChange={(e) => setProjectStatusFilter(e.target.value)}
                options={[
                  { value: 'ALL', label: 'All Project Statuses' },
                  { value: 'DRAFT', label: 'Drafts' },
                  { value: 'SUBMITTED', label: 'Pending Verification' },
                  { value: 'VERIFIED', label: 'Verified Deliverables' },
                  { value: 'REJECTED', label: 'Rejected' },
                  { value: 'REVOKED', label: 'Revoked' },
                ]}
              />
            </div>

            <Button variant="primary" onClick={() => setIsNewProjectOpen(true)}>
              + New Project Deliverable
            </Button>
          </div>

          {filteredProjects.length === 0 ? (
            <EmptyState
              title="No Projects Found"
              description="Author capstone, course, or research projects to demonstrate applied engineering competencies."
            />
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
              {filteredProjects.map((proj) => (
                <div
                  key={proj.id}
                  style={{
                    backgroundColor: 'var(--bg-surface)',
                    border: '1px solid var(--border-subtle)',
                    borderRadius: 'var(--radius-lg)',
                    padding: '20px',
                    display: 'flex',
                    flexDirection: 'column',
                    gap: '14px',
                    boxShadow: 'var(--shadow-sm)',
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
                        <span style={{ fontSize: '16px', fontWeight: 700, color: 'var(--text-primary)' }}>
                          {proj.title}
                        </span>
                        <Badge variant="default">{proj.project_type.replace('_', ' ')}</Badge>
                        {getStatusBadge(proj.status)}
                      </div>
                      <p style={{ fontSize: '13px', color: 'var(--text-secondary)' }}>
                        {proj.description || 'No detailed abstract provided.'}
                      </p>
                    </div>

                    <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
                      {proj.status === 'DRAFT' && (
                        <Button
                          variant="secondary"
                          onClick={() => handleSubmitProject(proj.id)}
                        >
                          Submit for Review
                        </Button>
                      )}

                      {isStaff && proj.status === 'SUBMITTED' && (
                        <Button
                          variant="primary"
                          onClick={() => {
                            setVerifyingProject(proj);
                            setIsVerifyModalOpen(true);
                          }}
                        >
                          Evaluate & Verify
                        </Button>
                      )}

                      {isStaff && proj.status === 'VERIFIED' && (
                        <Button
                          variant="secondary"
                          onClick={() => {
                            setRevokingProject(proj);
                            setIsRevokeModalOpen(true);
                          }}
                        >
                          Revoke Verification
                        </Button>
                      )}
                    </div>
                  </div>

                  {/* Links & Metadata */}
                  <div style={{ display: 'flex', gap: '20px', fontSize: '12px', color: 'var(--text-muted)', flexWrap: 'wrap' }}>
                    {proj.repository_url && (
                      <span>
                        Repository:{' '}
                        <a
                          href={proj.repository_url}
                          target="_blank"
                          rel="noopener noreferrer"
                          style={{ color: 'var(--brand-primary)', textDecoration: 'underline' }}
                        >
                          {proj.repository_url}
                        </a>
                      </span>
                    )}
                    {proj.deployment_url && (
                      <span>
                        Live Demo:{' '}
                        <a
                          href={proj.deployment_url}
                          target="_blank"
                          rel="noopener noreferrer"
                          style={{ color: 'var(--brand-accent)', textDecoration: 'underline' }}
                        >
                          {proj.deployment_url}
                        </a>
                      </span>
                    )}
                    <span>Created: {new Date(proj.created_at).toLocaleDateString()}</span>
                  </div>

                  {/* Verification / Revocation Feedback */}
                  {proj.verification_notes && (
                    <div
                      style={{
                        padding: '8px 12px',
                        backgroundColor: 'var(--bg-surface-elevated)',
                        borderRadius: 'var(--radius-sm)',
                        fontSize: '12px',
                        color: 'var(--text-primary)',
                      }}
                    >
                      <strong>Faculty Review:</strong> {proj.verification_notes}
                    </div>
                  )}

                  {proj.revocation_reason && (
                    <div
                      style={{
                        padding: '8px 12px',
                        backgroundColor: 'var(--status-danger-subtle)',
                        border: '1px solid var(--status-danger)',
                        borderRadius: 'var(--radius-sm)',
                        fontSize: '12px',
                        color: 'var(--status-danger)',
                      }}
                    >
                      <strong>Revocation Notice:</strong> {proj.revocation_reason}
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* =====================================================================
          TAB 2: PORTFOLIO BUILDER
         ===================================================================== */}
      {!isLoading && activeTab === 'portfolio' && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
          <div
            style={{
              backgroundColor: 'var(--bg-surface)',
              border: '1px solid var(--border-subtle)',
              borderRadius: 'var(--radius-lg)',
              padding: '24px',
              display: 'flex',
              flexDirection: 'column',
              gap: '20px',
            }}
          >
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <div>
                <h3 style={{ fontSize: '18px', fontWeight: 600, color: 'var(--text-primary)' }}>
                  Institutional Portfolio Settings
                </h3>
                <p style={{ fontSize: '13px', color: 'var(--text-secondary)' }}>
                  Publish verified engineering artifacts and competencies directly to prospective employers and institutional reviews.
                </p>
              </div>

              <div style={{ display: 'flex', gap: '12px', alignItems: 'center' }}>
                <Button
                  variant={portfolio?.is_published ? 'secondary' : 'primary'}
                  onClick={handleTogglePublish}
                >
                  {portfolio?.is_published ? 'Unpublish Portfolio' : 'Publish Portfolio'}
                </Button>
                <Button
                  variant="primary"
                  onClick={handleSavePortfolio}
                  disabled={isSavingPortfolio}
                >
                  {isSavingPortfolio ? 'Saving...' : 'Save Settings'}
                </Button>
              </div>
            </div>

            {/* Form Fields */}
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px' }}>
              <div>
                <label style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>Headline</label>
                <Input
                  value={portHeadline}
                  onChange={(e) => setPortHeadline(e.target.value)}
                  placeholder="e.g. Distributed Systems Researcher & Backend Engineer"
                />
              </div>

              <div>
                <label style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>Visibility Mode</label>
                <Select
                  value={portVisibility}
                  onChange={(e) => setPortVisibility(e.target.value as PortfolioVisibility)}
                  options={[
                    { value: 'PRIVATE', label: 'PRIVATE (Owner & Faculty Only)' },
                    { value: 'INSTITUTION', label: 'INSTITUTION (Campus Wide)' },
                    { value: 'PUBLIC', label: 'PUBLIC (Recruiters & World)' },
                  ]}
                />
              </div>
            </div>

            <div>
              <label style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>Bio / Professional Summary</label>
              <Input
                value={portBio}
                onChange={(e) => setPortBio(e.target.value)}
                placeholder="Highlight academic background, research interests, and core strengths..."
              />
            </div>

            {/* Social Links */}
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: '12px' }}>
              <div>
                <label style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>GitHub Profile</label>
                <Input
                  value={portGithub}
                  onChange={(e) => setPortGithub(e.target.value)}
                  placeholder="https://github.com/username"
                />
              </div>
              <div>
                <label style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>LinkedIn Profile</label>
                <Input
                  value={portLinkedin}
                  onChange={(e) => setPortLinkedin(e.target.value)}
                  placeholder="https://linkedin.com/in/username"
                />
              </div>
              <div>
                <label style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>Personal Website</label>
                <Input
                  value={portWebsite}
                  onChange={(e) => setPortWebsite(e.target.value)}
                  placeholder="https://myportfolio.dev"
                />
              </div>
            </div>

            {/* Curated Projects Selection */}
            <div>
              <label style={{ fontSize: '12px', fontWeight: 600, color: 'var(--text-primary)', marginBottom: '8px', display: 'block' }}>
                Select Curated Projects to Showcase:
              </label>
              {projects.length === 0 ? (
                <p style={{ fontSize: '13px', color: 'var(--text-muted)' }}>
                  No projects available yet. Author projects in the Project Studio.
                </p>
              ) : (
                <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                  {projects.map((p) => {
                    const isChecked = portCuratedProjects.includes(p.id);
                    return (
                      <div
                        key={p.id}
                        style={{
                          display: 'flex',
                          alignItems: 'center',
                          gap: '12px',
                          padding: '10px 14px',
                          backgroundColor: 'var(--bg-surface-elevated)',
                          borderRadius: 'var(--radius-sm)',
                        }}
                      >
                        <input
                          type="checkbox"
                          checked={isChecked}
                          onChange={(e) => {
                            if (e.target.checked) {
                              setPortCuratedProjects((prev) => [...prev, p.id]);
                            } else {
                              setPortCuratedProjects((prev) => prev.filter((id) => id !== p.id));
                            }
                          }}
                        />
                        <span style={{ fontWeight: 600, color: 'var(--text-primary)' }}>{p.title}</span>
                        {getStatusBadge(p.status)}
                        {p.status !== 'VERIFIED' && (
                          <span style={{ fontSize: '11px', color: 'var(--text-muted)' }}>
                            (Note: Draft/unverified projects are hidden from public viewers)
                          </span>
                        )}
                      </div>
                    );
                  })}
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      {/* =====================================================================
          TAB 3: CAREER GOALS & DETERMINISTIC READINESS
         ===================================================================== */}
      {!isLoading && activeTab === 'readiness' && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
          {/* Active Goal Card */}
          <div
            style={{
              backgroundColor: 'var(--bg-surface)',
              border: '1px solid var(--border-subtle)',
              borderRadius: 'var(--radius-lg)',
              padding: '20px',
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center',
              flexWrap: 'wrap',
              gap: '12px',
            }}
          >
            <div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '4px' }}>
                <span style={{ fontSize: '18px', fontWeight: 700, color: 'var(--text-primary)' }}>
                  Target Role: {careerGoal?.target_role || 'Not Set'}
                </span>
                {careerGoal && <Badge variant="success">ACTIVE GOAL</Badge>}
              </div>
              <p style={{ fontSize: '13px', color: 'var(--text-secondary)' }}>
                Industry: {careerGoal?.target_industry || 'General Engineering'} | Required Skills:{' '}
                {careerGoal?.required_skill_ids?.length || 0}
              </p>
            </div>

            <div style={{ display: 'flex', gap: '8px' }}>
              <Button variant="secondary" onClick={() => setIsGoalModalOpen(true)}>
                {careerGoal ? 'Edit Career Goal' : 'Set Career Goal'}
              </Button>
              <Button
                variant="primary"
                onClick={() => handleCalculateReadiness()}
                disabled={isCalculatingReadiness || !careerGoal}
              >
                {isCalculatingReadiness ? 'Evaluating...' : 'Recalculate Readiness Index'}
              </Button>
            </div>
          </div>

          {/* Readiness Dashboard Score & Gap Analysis */}
          {careerReadiness ? (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
              {/* Score Header */}
              <div
                style={{
                  display: 'grid',
                  gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))',
                  gap: '16px',
                }}
              >
                <div
                  style={{
                    backgroundColor: 'var(--bg-surface)',
                    border: '1px solid var(--border-subtle)',
                    borderRadius: 'var(--radius-lg)',
                    padding: '20px',
                  }}
                >
                  <span style={{ fontSize: '12px', color: 'var(--text-muted)' }}>Readiness Index</span>
                  <div style={{ fontSize: '28px', fontWeight: 800, color: 'var(--status-success)' }}>
                    {(careerReadiness.readiness_score * 100).toFixed(1)}%
                  </div>
                  <span style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>
                    Verified match across target role requirements
                  </span>
                </div>

                <div
                  style={{
                    backgroundColor: 'var(--bg-surface)',
                    border: '1px solid var(--border-subtle)',
                    borderRadius: 'var(--radius-lg)',
                    padding: '20px',
                  }}
                >
                  <span style={{ fontSize: '12px', color: 'var(--text-muted)' }}>Matching Competencies</span>
                  <div style={{ fontSize: '28px', fontWeight: 800, color: 'var(--brand-accent)' }}>
                    {careerReadiness.matching_skills_count} / {careerReadiness.total_required_skills}
                  </div>
                  <span style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>
                    Verified at Proficient (70%+) or Mastery (90%+)
                  </span>
                </div>

                <div
                  style={{
                    backgroundColor: 'var(--bg-surface)',
                    border: '1px solid var(--border-subtle)',
                    borderRadius: 'var(--radius-lg)',
                    padding: '20px',
                  }}
                >
                  <span style={{ fontSize: '12px', color: 'var(--text-muted)' }}>Deficit Skills</span>
                  <div style={{ fontSize: '28px', fontWeight: 800, color: 'var(--status-danger)' }}>
                    {careerReadiness.target_gap_analysis.deficit_count}
                  </div>
                  <span style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>
                    Missing evidence or score under 40% threshold
                  </span>
                </div>
              </div>

              {/* Itemized Gap Analysis Breakdown */}
              <div
                style={{
                  backgroundColor: 'var(--bg-surface)',
                  border: '1px solid var(--border-subtle)',
                  borderRadius: 'var(--radius-lg)',
                  padding: '20px',
                  display: 'flex',
                  flexDirection: 'column',
                  gap: '12px',
                }}
              >
                <h4 style={{ fontSize: '16px', fontWeight: 600, color: 'var(--text-primary)' }}>
                  Deterministic Competency Gap Analysis
                </h4>

                <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                  {careerReadiness.target_gap_analysis.skills_breakdown.map((item) => {
                    let badgeVariant: 'success' | 'warning' | 'danger' = 'danger';
                    if (item.status === 'MET') badgeVariant = 'success';
                    else if (item.status === 'PARTIAL') badgeVariant = 'warning';

                    return (
                      <div
                        key={item.skill_id}
                        style={{
                          backgroundColor: 'var(--bg-surface-elevated)',
                          padding: '12px 16px',
                          borderRadius: 'var(--radius-md)',
                          display: 'flex',
                          justifyContent: 'space-between',
                          alignItems: 'center',
                          flexWrap: 'wrap',
                          gap: '12px',
                        }}
                      >
                        <div>
                          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                            <span style={{ fontWeight: 600, color: 'var(--text-primary)' }}>
                              {item.code}: {item.name}
                            </span>
                            <Badge variant="default">{item.category}</Badge>
                            <Badge variant={badgeVariant}>{item.status}</Badge>
                            {item.has_verified_project && (
                              <Badge variant="success">Verified Project Deliverable</Badge>
                            )}
                          </div>
                          <p style={{ fontSize: '12px', color: 'var(--text-secondary)', marginTop: '4px' }}>
                            {item.gap_note}
                          </p>
                        </div>

                        <div style={{ textAlign: 'right' }}>
                          <div style={{ fontSize: '15px', fontWeight: 700, color: 'var(--text-primary)' }}>
                            Score: {(item.score * 100).toFixed(1)}%
                          </div>
                          <span style={{ fontSize: '11px', color: 'var(--text-muted)' }}>
                            Decay: {item.decay_factor.toFixed(2)}x
                          </span>
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>
            </div>
          ) : (
            <EmptyState
              title="No Readiness Record Computed"
              description="Configure an active career goal and click 'Recalculate Readiness Index' to evaluate alignment."
            />
          )}
        </div>
      )}

      {/* =====================================================================
          TAB 4: PLACEMENT TALENT DISCOVERY (STAFF ONLY)
         ===================================================================== */}
      {!isLoading && activeTab === 'talent' && isPlacementOfficer && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
          {/* Analytics Summary */}
          {placementAnalytics && (
            <div
              style={{
                display: 'grid',
                gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
                gap: '16px',
              }}
            >
              <div
                style={{
                  backgroundColor: 'var(--bg-surface)',
                  border: '1px solid var(--border-subtle)',
                  borderRadius: 'var(--radius-lg)',
                  padding: '16px',
                }}
              >
                <span style={{ fontSize: '12px', color: 'var(--text-muted)' }}>Evaluated Students</span>
                <div style={{ fontSize: '24px', fontWeight: 700, color: 'var(--text-primary)' }}>
                  {placementAnalytics.total_evaluated_students}
                </div>
              </div>

              <div
                style={{
                  backgroundColor: 'var(--bg-surface)',
                  border: '1px solid var(--border-subtle)',
                  borderRadius: 'var(--radius-lg)',
                  padding: '16px',
                }}
              >
                <span style={{ fontSize: '12px', color: 'var(--text-muted)' }}>Avg Readiness Score</span>
                <div style={{ fontSize: '24px', fontWeight: 700, color: 'var(--status-success)' }}>
                  {(placementAnalytics.average_readiness_score * 100).toFixed(1)}%
                </div>
              </div>

              <div
                style={{
                  backgroundColor: 'var(--bg-surface)',
                  border: '1px solid var(--border-subtle)',
                  borderRadius: 'var(--radius-lg)',
                  padding: '16px',
                }}
              >
                <span style={{ fontSize: '12px', color: 'var(--text-muted)' }}>Job-Ready Candidates (70%+)</span>
                <div style={{ fontSize: '24px', fontWeight: 700, color: 'var(--brand-accent)' }}>
                  {placementAnalytics.distribution.high_readiness_90_plus +
                    placementAnalytics.distribution.proficient_70_89}
                </div>
              </div>
            </div>
          )}

          {/* Search Toolbar */}
          <div
            style={{
              display: 'flex',
              gap: '12px',
              alignItems: 'center',
              flexWrap: 'wrap',
              backgroundColor: 'var(--bg-surface)',
              padding: '16px',
              borderRadius: 'var(--radius-lg)',
              border: '1px solid var(--border-subtle)',
            }}
          >
            <div style={{ width: '220px' }}>
              <label style={{ fontSize: '11px', color: 'var(--text-secondary)' }}>Minimum Readiness</label>
              <Select
                value={minReadinessFilter}
                onChange={(e) => setMinReadinessFilter(e.target.value)}
                options={[
                  { value: '0.0', label: 'All Candidates (0%+)' },
                  { value: '0.50', label: 'Developing (50%+)' },
                  { value: '0.70', label: 'Job Ready (70%+)' },
                  { value: '0.90', label: 'High Mastery (90%+)' },
                ]}
              />
            </div>

            <div style={{ width: '260px' }}>
              <label style={{ fontSize: '11px', color: 'var(--text-secondary)' }}>Target Role Filter</label>
              <Input
                value={roleSearchFilter}
                onChange={(e) => setRoleSearchFilter(e.target.value)}
                placeholder="e.g. Systems Engineer..."
              />
            </div>

            <div style={{ alignSelf: 'flex-end' }}>
              <Button variant="primary" onClick={handleSearchTalent}>
                Filter Candidates
              </Button>
            </div>
          </div>

          {/* Candidates List */}
          {talentCandidates.length === 0 ? (
            <EmptyState
              title="No Candidates Found"
              description="Adjust search filters or ensure students have computed active career readiness records."
            />
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
              {talentCandidates.map((c) => (
                <div
                  key={c.student_id}
                  style={{
                    backgroundColor: 'var(--bg-surface)',
                    border: '1px solid var(--border-subtle)',
                    borderRadius: 'var(--radius-lg)',
                    padding: '16px 20px',
                    display: 'flex',
                    justifyContent: 'space-between',
                    alignItems: 'center',
                    flexWrap: 'wrap',
                    gap: '12px',
                  }}
                >
                  <div>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                      <span style={{ fontWeight: 700, fontSize: '15px', color: 'var(--text-primary)' }}>
                        {c.full_name}
                      </span>
                      <span style={{ fontSize: '12px', color: 'var(--text-muted)' }}>({c.email})</span>
                      {c.portfolio_accessible && (
                        <Badge variant="success">Portfolio Published</Badge>
                      )}
                    </div>
                    <p style={{ fontSize: '13px', color: 'var(--text-secondary)', marginTop: '2px' }}>
                      Target Role: <strong>{c.target_role}</strong> | Verified Skills:{' '}
                      {c.matching_skills_count} / {c.total_required_skills}
                    </p>
                  </div>

                  <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
                    <div style={{ textAlign: 'right' }}>
                      <div style={{ fontSize: '18px', fontWeight: 800, color: 'var(--status-success)' }}>
                        {(c.readiness_score * 100).toFixed(1)}%
                      </div>
                      <span style={{ fontSize: '11px', color: 'var(--text-muted)' }}>Readiness Index</span>
                    </div>

                    {c.portfolio_slug && c.portfolio_accessible && (
                      <Button
                        variant="secondary"
                        onClick={() =>
                          window.open(
                            `/api/v1/institutions/${tenantSlug}/portfolios/${c.portfolio_slug}`,
                            '_blank'
                          )
                        }
                      >
                        View Portfolio
                      </Button>
                    )}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* =====================================================================
          MODAL: NEW PROJECT DELIVERABLE
         ===================================================================== */}
      <Dialog
        isOpen={isNewProjectOpen}
        onClose={() => setIsNewProjectOpen(false)}
        title="Author Project Deliverable"
      >
        <div style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
          <div>
            <label style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>Project Title</label>
            <Input
              value={newProjTitle}
              onChange={(e) => setNewProjTitle(e.target.value)}
              placeholder="e.g. Distributed Consensus Engine (Raft)"
            />
          </div>

          <div>
            <label style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>Project Type</label>
            <Select
              value={newProjType}
              onChange={(e) => setNewProjType(e.target.value as ProjectType)}
              options={[
                { value: 'CAPSTONE', label: 'Senior Capstone Project' },
                { value: 'COURSE_PROJECT', label: 'Course Lab Project' },
                { value: 'RESEARCH', label: 'Faculty Research Project' },
                { value: 'HACKATHON', label: 'Hackathon Submission' },
                { value: 'OPEN_SOURCE', label: 'Open Source Contribution' },
              ]}
            />
          </div>

          <div>
            <label style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>Abstract & Scope</label>
            <Input
              value={newProjDesc}
              onChange={(e) => setNewProjDesc(e.target.value)}
              placeholder="High-level description of problem, solution, and architecture..."
            />
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px' }}>
            <div>
              <label style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>Repository URL</label>
              <Input
                value={newProjRepoUrl}
                onChange={(e) => setNewProjRepoUrl(e.target.value)}
                placeholder="https://github.com/..."
              />
            </div>
            <div>
              <label style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>Deployment / Demo URL</label>
              <Input
                value={newProjDemoUrl}
                onChange={(e) => setNewProjDemoUrl(e.target.value)}
                placeholder="https://demo.app/..."
              />
            </div>
          </div>

          <div>
            <label style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>My Individual Contribution</label>
            <Input
              value={newProjContribution}
              onChange={(e) => setNewProjContribution(e.target.value)}
              placeholder="Specific modules, algorithms, or benchmarks authored..."
            />
          </div>

          <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '8px', marginTop: '12px' }}>
            <Button variant="ghost" onClick={() => setIsNewProjectOpen(false)}>
              Cancel
            </Button>
            <Button variant="primary" onClick={handleCreateProject}>
              Save Draft Deliverable
            </Button>
          </div>
        </div>
      </Dialog>

      {/* =====================================================================
          MODAL: VERIFY PROJECT (STAFF)
         ===================================================================== */}
      <Dialog
        isOpen={isVerifyModalOpen}
        onClose={() => setIsVerifyModalOpen(false)}
        title="Faculty Project Verification Gate"
      >
        <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
          {verifyingProject && (
            <div
              style={{
                backgroundColor: 'var(--bg-surface-elevated)',
                padding: '12px',
                borderRadius: 'var(--radius-sm)',
                fontSize: '13px',
              }}
            >
              <div><strong>Project:</strong> {verifyingProject.title}</div>
              <div><strong>Type:</strong> {verifyingProject.project_type}</div>
              {verifyingProject.repository_url && (
                <div><strong>Repo:</strong> {verifyingProject.repository_url}</div>
              )}
            </div>
          )}

          <div>
            <label style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>Evaluation Decision</label>
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
                Reject Project
              </Button>
            </div>
          </div>

          <div>
            <label style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>Reviewer Remarks</label>
            <Input
              value={verifyNotes}
              onChange={(e) => setVerifyNotes(e.target.value)}
              placeholder="Explain verification feedback or required revisions..."
            />
          </div>

          <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '8px', marginTop: '12px' }}>
            <Button variant="ghost" onClick={() => setIsVerifyModalOpen(false)}>
              Cancel
            </Button>
            <Button variant="primary" onClick={handleVerifyProject}>
              Confirm Decision
            </Button>
          </div>
        </div>
      </Dialog>

      {/* =====================================================================
          MODAL: REVOKE PROJECT (STAFF)
         ===================================================================== */}
      <Dialog
        isOpen={isRevokeModalOpen}
        onClose={() => setIsRevokeModalOpen(false)}
        title="Revoke Project Verification"
      >
        <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
          <Alert variant="danger" title="Academic Integrity Warning">
            Revoking verification will permanently remove this project from verified portfolios and career readiness calculations.
          </Alert>

          <div>
            <label style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>Mandatory Revocation Reason</label>
            <Input
              value={revocationReason}
              onChange={(e) => setRevocationReason(e.target.value)}
              placeholder="e.g. Verified code deliverable failed reproducibility audit..."
            />
          </div>

          <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '8px', marginTop: '12px' }}>
            <Button variant="ghost" onClick={() => setIsRevokeModalOpen(false)}>
              Cancel
            </Button>
            <Button variant="danger" onClick={handleRevokeProject}>
              Confirm Revocation
            </Button>
          </div>
        </div>
      </Dialog>

      {/* =====================================================================
          MODAL: SET CAREER GOAL
         ===================================================================== */}
      <Dialog
        isOpen={isGoalModalOpen}
        onClose={() => setIsGoalModalOpen(false)}
        title="Configure Career Goal"
      >
        <div style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
          <div>
            <label style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>Target Career Role</label>
            <Input
              value={targetRoleInput}
              onChange={(e) => setTargetRoleInput(e.target.value)}
              placeholder="e.g. Systems Software Engineer"
            />
          </div>

          <div>
            <label style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>Target Industry</label>
            <Input
              value={targetIndustryInput}
              onChange={(e) => setTargetIndustryInput(e.target.value)}
              placeholder="e.g. Cloud Infrastructure / Database Systems"
            />
          </div>

          <div>
            <label style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>Target Companies (comma-separated)</label>
            <Input
              value={targetCompaniesInput}
              onChange={(e) => setTargetCompaniesInput(e.target.value)}
              placeholder="e.g. Google, Cloudflare, Databricks"
            />
          </div>

          <div>
            <label style={{ fontSize: '12px', fontWeight: 600, color: 'var(--text-primary)', marginBottom: '8px', display: 'block' }}>
              Required Competencies from Institutional Library:
            </label>
            <div style={{ maxHeight: '180px', overflowY: 'auto', display: 'flex', flexDirection: 'column', gap: '6px' }}>
              {skills.map((s) => {
                const isChecked = selectedRequiredSkills.includes(s.id);
                return (
                  <div
                    key={s.id}
                    style={{
                      display: 'flex',
                      alignItems: 'center',
                      gap: '8px',
                      fontSize: '13px',
                      padding: '4px 8px',
                      backgroundColor: 'var(--bg-surface-elevated)',
                      borderRadius: 'var(--radius-sm)',
                    }}
                  >
                    <input
                      type="checkbox"
                      checked={isChecked}
                      onChange={(e) => {
                        if (e.target.checked) {
                          setSelectedRequiredSkills((prev) => [...prev, s.id]);
                        } else {
                          setSelectedRequiredSkills((prev) => prev.filter((id) => id !== s.id));
                        }
                      }}
                    />
                    <span style={{ fontWeight: 600, color: 'var(--text-primary)' }}>{s.code}</span>
                    <span style={{ color: 'var(--text-secondary)' }}>{s.name}</span>
                  </div>
                );
              })}
            </div>
          </div>

          <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '8px', marginTop: '12px' }}>
            <Button variant="ghost" onClick={() => setIsGoalModalOpen(false)}>
              Cancel
            </Button>
            <Button variant="primary" onClick={handleSaveCareerGoal}>
              Save Career Goal
            </Button>
          </div>
        </div>
      </Dialog>
    </div>
  );
}
