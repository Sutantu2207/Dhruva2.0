'use client';

import React, { useState, useEffect, useMemo, useCallback } from 'react';
import { useAuth } from '@/lib/auth/AuthContext';
import { api, ApiError } from '@/lib/api/client';
import { Badge } from '@/components/ui/Badge';
import { Button } from '@/components/ui/Button';
import { Card } from '@/components/ui/Card';
import { Input } from '@/components/ui/Input';
import { Dialog } from '@/components/ui/Dialog';
import { Select } from '@/components/ui/Select';
import { Alert } from '@/components/ui/Alert';
import { College, CollegeRequest, CollegeCreatePayload } from '@/types/college';
import {
  Building2,
  Search,
  Plus,
  Edit2,
  CheckCircle2,
  XCircle,
  ExternalLink,
  ShieldCheck,
  RefreshCw,
  Clock,
  MapPin,
  GraduationCap,
  FileText,
  Filter,
  Check,
  X,
} from 'lucide-react';

const INSTITUTION_TYPES = [
  'Engineering & Technology',
  'Arts & Science',
  'Medical',
  'Dental',
  'Nursing',
  'Pharmacy',
  'Management',
  'Law',
  'Polytechnic',
  'Architecture',
  'Agriculture',
  'University',
];

const AFFILIATED_UNIVERSITIES = [
  'Anna University',
  'Bharathiar University',
  'The Tamil Nadu Dr. M.G.R. Medical University',
  'Tamil Nadu Agricultural University (TNAU)',
  'Tamil Nadu Dr. Ambedkar Law University',
  'Directorate of Technical Education (DOTE)',
  'Deemed to be University',
  'Private University',
  'Autonomous (UGC Approved)',
];

export default function CollegesManagementPage() {
  const { user } = useAuth();
  const primaryRole = user?.roles?.[0] || 'STUDENT';
  const isAdmin = ['SUPER_ADMIN', 'INSTITUTION_ADMIN'].includes(primaryRole);

  const [activeTab, setActiveTab] = useState<'directory' | 'requests'>('directory');

  // Directory State
  const [colleges, setColleges] = useState<College[]>([]);
  const [isLoadingColleges, setIsLoadingColleges] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedType, setSelectedType] = useState('ALL');
  const [statusFilter, setStatusFilter] = useState('ALL');

  // Requests State
  const [requests, setRequests] = useState<CollegeRequest[]>([]);
  const [isLoadingRequests, setIsLoadingRequests] = useState(false);
  const [requestFilter, setRequestFilter] = useState<'ALL' | 'PENDING' | 'APPROVED' | 'REJECTED'>('PENDING');

  // Modal State for Add / Edit College
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [editingCollege, setEditingCollege] = useState<College | null>(null);
  const [modalForm, setModalForm] = useState<CollegeCreatePayload>({
    name: '',
    code: '',
    institution_type: 'Engineering & Technology',
    affiliated_university: 'Anna University',
    location: '',
    district: 'Coimbatore',
    state: 'Tamil Nadu',
    website: '',
    accreditation: '',
    status: 'ACTIVE',
  });
  const [modalError, setModalError] = useState<string | null>(null);
  const [isSubmittingModal, setIsSubmittingModal] = useState(false);

  // Request Action Modal
  const [isRejectModalOpen, setIsRejectModalOpen] = useState(false);
  const [selectedRequestId, setSelectedRequestId] = useState<string | null>(null);
  const [rejectReason, setRejectReason] = useState('');
  const [isProcessingAction, setIsProcessingAction] = useState(false);

  // Global Alert Message
  const [feedback, setFeedback] = useState<{ type: 'success' | 'danger'; message: string } | null>(null);

  const showFeedback = (type: 'success' | 'danger', message: string) => {
    setFeedback({ type, message });
    setTimeout(() => setFeedback(null), 4000);
  };

  // Fetch Colleges Directory
  const fetchColleges = useCallback(async () => {
    setIsLoadingColleges(true);
    try {
      let endpoint = '/colleges?page_size=100';
      if (searchQuery.trim()) {
        endpoint = `/colleges/search?q=${encodeURIComponent(searchQuery.trim())}&limit=50`;
      } else {
        const params = new URLSearchParams({ district: 'Coimbatore', page_size: '100' });
        if (selectedType !== 'ALL') params.set('type', selectedType);
        if (statusFilter !== 'ALL') params.set('status', statusFilter);
        endpoint = `/colleges?${params.toString()}`;
      }
      const data = await api.get<College[]>(endpoint);
      setColleges(data || []);
    } catch (err: any) {
      showFeedback('danger', 'Failed to load colleges: ' + (err.message || 'Server error'));
    } finally {
      setIsLoadingColleges(false);
    }
  }, [searchQuery, selectedType, statusFilter]);

  // Fetch Requests Queue
  const fetchRequests = useCallback(async () => {
    setIsLoadingRequests(true);
    try {
      const endpoint = requestFilter === 'ALL'
        ? '/admin/college-requests'
        : `/admin/college-requests?status=${requestFilter}`;
      const data = await api.get<CollegeRequest[]>(endpoint);
      setRequests(data || []);
    } catch (err: any) {
      showFeedback('danger', 'Failed to load requests: ' + (err.message || 'Server error'));
    } finally {
      setIsLoadingRequests(false);
    }
  }, [requestFilter]);

  useEffect(() => {
    fetchColleges();
  }, [fetchColleges]);

  useEffect(() => {
    if (activeTab === 'requests') {
      fetchRequests();
    }
  }, [activeTab, fetchRequests]);

  // Summary Metrics
  const metrics = useMemo(() => {
    const total = colleges.length;
    const active = colleges.filter((c) => c.status === 'ACTIVE').length;
    const typesCount = new Set(colleges.map((c) => c.institution_type)).size;
    const pendingRequests = requests.filter((r) => r.status === 'PENDING').length;
    return { total, active, typesCount, pendingRequests };
  }, [colleges, requests]);

  // Handle Open Create Modal
  const handleOpenCreateModal = () => {
    setEditingCollege(null);
    setModalForm({
      name: '',
      code: '',
      institution_type: 'Engineering & Technology',
      affiliated_university: 'Anna University',
      location: '',
      district: 'Coimbatore',
      state: 'Tamil Nadu',
      website: '',
      accreditation: '',
      status: 'ACTIVE',
    });
    setModalError(null);
    setIsModalOpen(true);
  };

  // Handle Open Edit Modal
  const handleOpenEditModal = (col: College) => {
    setEditingCollege(col);
    setModalForm({
      name: col.name,
      code: col.code || '',
      institution_type: col.institution_type,
      affiliated_university: col.affiliated_university || '',
      location: col.location,
      district: col.district,
      state: col.state,
      website: col.website || '',
      accreditation: col.accreditation || '',
      status: col.status,
    });
    setModalError(null);
    setIsModalOpen(true);
  };

  // Save (Create or Update) College
  const handleSaveCollege = async (e: React.FormEvent) => {
    e.preventDefault();
    setModalError(null);

    if (!modalForm.name.trim()) {
      setModalError('College name is required.');
      return;
    }
    if (!modalForm.location.trim()) {
      setModalError('Location / Area is required (e.g. Peelamedu, Eachanari).');
      return;
    }

    setIsSubmittingModal(true);
    try {
      if (editingCollege) {
        await api.put(`/colleges/${editingCollege.id}`, modalForm);
        showFeedback('success', `"${modalForm.name}" updated successfully.`);
      } else {
        await api.post('/colleges', modalForm);
        showFeedback('success', `"${modalForm.name}" added to Coimbatore registry.`);
      }
      setIsModalOpen(false);
      fetchColleges();
    } catch (err: any) {
      setModalError(err.message || 'Failed to save college details.');
    } finally {
      setIsSubmittingModal(false);
    }
  };

  // Toggle College Status
  const handleToggleStatus = async (col: College) => {
    const newStatus = col.status === 'ACTIVE' ? 'INACTIVE' : 'ACTIVE';
    try {
      await api.put(`/colleges/${col.id}`, { status: newStatus });
      showFeedback('success', `${col.name} set to ${newStatus}.`);
      fetchColleges();
    } catch (err: any) {
      showFeedback('danger', 'Failed to toggle status: ' + err.message);
    }
  };

  // Approve Request
  const handleApproveRequest = async (requestId: string) => {
    setIsProcessingAction(true);
    try {
      await api.post(`/admin/college-requests/${requestId}/approve`, {});
      showFeedback('success', 'College request approved and added to active directory.');
      fetchRequests();
      fetchColleges();
    } catch (err: any) {
      showFeedback('danger', 'Failed to approve request: ' + err.message);
    } finally {
      setIsProcessingAction(false);
    }
  };

  // Reject Request
  const handleRejectRequest = async () => {
    if (!selectedRequestId) return;
    setIsProcessingAction(true);
    try {
      await api.post(`/admin/college-requests/${selectedRequestId}/reject`, {
        reason: rejectReason.trim() || 'Institution details could not be verified in Coimbatore.',
      });
      showFeedback('success', 'College request rejected.');
      setIsRejectModalOpen(false);
      setSelectedRequestId(null);
      setRejectReason('');
      fetchRequests();
    } catch (err: any) {
      showFeedback('danger', 'Failed to reject request: ' + err.message);
    } finally {
      setIsProcessingAction(false);
    }
  };

  return (
    <div style={{ maxWidth: '1440px', margin: '0 auto', display: 'flex', flexDirection: 'column', gap: '24px' }}>
      
      {/* Page Header */}
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
            <div
              style={{
                width: '38px',
                height: '38px',
                borderRadius: '8px',
                background: 'var(--brand-primary-gradient)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                color: '#fff',
              }}
            >
              <Building2 size={20} />
            </div>
            <div>
              <h1 style={{ fontSize: '22px', fontWeight: 700, color: 'var(--text-primary)', margin: 0, letterSpacing: '-0.02em' }}>
                Coimbatore Higher Education Registry
              </h1>
              <p style={{ margin: '4px 0 0 0', fontSize: '13px', color: 'var(--text-secondary)' }}>
                Comprehensive verified directory of collegiate institutions across Coimbatore district, Tamil Nadu.
              </p>
            </div>
          </div>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          <Button
            variant="outline"
            size="sm"
            onClick={() => {
              if (activeTab === 'directory') fetchColleges();
              else fetchRequests();
            }}
          >
            <RefreshCw size={13} />
            Refresh
          </Button>
          {isAdmin && (
            <Button variant="primary" size="sm" onClick={handleOpenCreateModal}>
              <Plus size={14} />
              Add College
            </Button>
          )}
        </div>
      </div>

      {/* Global Notification Feedback */}
      {feedback && (
        <Alert variant={feedback.type} title={feedback.type === 'success' ? 'Operation Completed' : 'Attention'}>
          {feedback.message}
        </Alert>
      )}

      {/* Quick Metrics Bar */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '16px' }}>
        <Card style={{ padding: '16px' }}>
          <div style={{ fontSize: '12px', fontWeight: 600, color: 'var(--text-muted)' }}>
            Total Coimbatore Institutions
          </div>
          <div style={{ fontSize: '26px', fontWeight: 800, color: 'var(--brand-primary)', marginTop: '4px' }}>
            {metrics.total}
          </div>
          <div style={{ fontSize: '11px', color: 'var(--text-secondary)', marginTop: '4px' }}>
            Accredited & verified records
          </div>
        </Card>

        <Card style={{ padding: '16px' }}>
          <div style={{ fontSize: '12px', fontWeight: 600, color: 'var(--text-muted)' }}>
            Active in Platform
          </div>
          <div style={{ fontSize: '26px', fontWeight: 800, color: 'var(--status-success)', marginTop: '4px' }}>
            {metrics.active}
          </div>
          <div style={{ fontSize: '11px', color: 'var(--text-secondary)', marginTop: '4px' }}>
            Available for student selection
          </div>
        </Card>

        <Card style={{ padding: '16px' }}>
          <div style={{ fontSize: '12px', fontWeight: 600, color: 'var(--text-muted)' }}>
            Academic Verticals
          </div>
          <div style={{ fontSize: '26px', fontWeight: 800, color: '#3b82f6', marginTop: '4px' }}>
            {metrics.typesCount}
          </div>
          <div style={{ fontSize: '11px', color: 'var(--text-secondary)', marginTop: '4px' }}>
            Engineering, Arts, Medical, Polytechnic
          </div>
        </Card>

        <Card style={{ padding: '16px' }}>
          <div style={{ fontSize: '12px', fontWeight: 600, color: 'var(--text-muted)' }}>
            User Requested Submissions
          </div>
          <div style={{ fontSize: '26px', fontWeight: 800, color: metrics.pendingRequests > 0 ? 'var(--status-warning)' : 'var(--text-muted)', marginTop: '4px' }}>
            {metrics.pendingRequests}
          </div>
          <div style={{ fontSize: '11px', color: 'var(--text-secondary)', marginTop: '4px' }}>
            Pending administrative review
          </div>
        </Card>
      </div>

      {/* Tabs Bar */}
      <div style={{ display: 'flex', gap: '12px', borderBottom: '1px solid var(--border-subtle)', paddingBottom: '2px' }}>
        <button
          onClick={() => setActiveTab('directory')}
          style={{
            padding: '10px 16px',
            fontSize: '13px',
            fontWeight: 600,
            border: 'none',
            background: 'transparent',
            color: activeTab === 'directory' ? 'var(--brand-primary)' : 'var(--text-muted)',
            borderBottom: activeTab === 'directory' ? '2px solid var(--brand-primary)' : '2px solid transparent',
            cursor: 'pointer',
            display: 'flex',
            alignItems: 'center',
            gap: '8px',
          }}
        >
          <Building2 size={16} />
          Colleges Directory ({colleges.length})
        </button>

        <button
          onClick={() => setActiveTab('requests')}
          style={{
            padding: '10px 16px',
            fontSize: '13px',
            fontWeight: 600,
            border: 'none',
            background: 'transparent',
            color: activeTab === 'requests' ? 'var(--brand-primary)' : 'var(--text-muted)',
            borderBottom: activeTab === 'requests' ? '2px solid var(--brand-primary)' : '2px solid transparent',
            cursor: 'pointer',
            display: 'flex',
            alignItems: 'center',
            gap: '8px',
          }}
        >
          <FileText size={16} />
          User Requests Queue
          {metrics.pendingRequests > 0 && (
            <Badge variant="warning" size="sm">
              {metrics.pendingRequests}
            </Badge>
          )}
        </button>
      </div>

      {/* TAB 1: COLLEGES DIRECTORY */}
      {activeTab === 'directory' && (
        <Card style={{ padding: '20px', display: 'flex', flexDirection: 'column', gap: '16px' }}>
          
          {/* Search & Filter Bar */}
          <div style={{ display: 'flex', gap: '12px', flexWrap: 'wrap', alignItems: 'center', justifyContent: 'space-between' }}>
            <div style={{ display: 'flex', gap: '10px', flex: 1, minWidth: '280px', maxWidth: '520px', position: 'relative' }}>
              <div style={{ position: 'absolute', left: '12px', top: '50%', transform: 'translateY(-50%)', color: 'var(--text-muted)' }}>
                <Search size={15} />
              </div>
              <input
                type="text"
                placeholder="Search college by name, code, or area (e.g., PSG, CIT, Peelamedu)..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                style={{
                  width: '100%',
                  padding: '9px 12px 9px 36px',
                  borderRadius: 'var(--radius-md)',
                  border: '1px solid var(--border-default)',
                  backgroundColor: 'var(--bg-app)',
                  fontSize: '13px',
                  color: 'var(--text-primary)',
                }}
              />
            </div>

            <div style={{ display: 'flex', gap: '10px', alignItems: 'center', flexWrap: 'wrap' }}>
              <select
                value={selectedType}
                onChange={(e) => setSelectedType(e.target.value)}
                style={{
                  padding: '8px 12px',
                  borderRadius: 'var(--radius-md)',
                  border: '1px solid var(--border-default)',
                  backgroundColor: 'var(--bg-app)',
                  fontSize: '12px',
                  color: 'var(--text-secondary)',
                  cursor: 'pointer',
                }}
              >
                <option value="ALL">All Institution Types</option>
                {INSTITUTION_TYPES.map((t) => (
                  <option key={t} value={t}>
                    {t}
                  </option>
                ))}
              </select>

              <select
                value={statusFilter}
                onChange={(e) => setStatusFilter(e.target.value)}
                style={{
                  padding: '8px 12px',
                  borderRadius: 'var(--radius-md)',
                  border: '1px solid var(--border-default)',
                  backgroundColor: 'var(--bg-app)',
                  fontSize: '12px',
                  color: 'var(--text-secondary)',
                  cursor: 'pointer',
                }}
              >
                <option value="ALL">All Statuses</option>
                <option value="ACTIVE">Active Only</option>
                <option value="INACTIVE">Inactive</option>
              </select>
            </div>
          </div>

          {/* Table Container */}
          <div style={{ overflowX: 'auto', border: '1px solid var(--border-subtle)', borderRadius: 'var(--radius-md)' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left', fontSize: '13px' }}>
              <thead>
                <tr style={{ backgroundColor: 'var(--bg-surface-subtle)', borderBottom: '1px solid var(--border-subtle)' }}>
                  <th style={{ padding: '12px 16px', fontWeight: 600, color: 'var(--text-secondary)' }}>Institution Name</th>
                  <th style={{ padding: '12px 16px', fontWeight: 600, color: 'var(--text-secondary)' }}>Code</th>
                  <th style={{ padding: '12px 16px', fontWeight: 600, color: 'var(--text-secondary)' }}>Vertical</th>
                  <th style={{ padding: '12px 16px', fontWeight: 600, color: 'var(--text-secondary)' }}>Affiliation</th>
                  <th style={{ padding: '12px 16px', fontWeight: 600, color: 'var(--text-secondary)' }}>Location / Area</th>
                  <th style={{ padding: '12px 16px', fontWeight: 600, color: 'var(--text-secondary)' }}>Status</th>
                  <th style={{ padding: '12px 16px', fontWeight: 600, color: 'var(--text-secondary)', textAlign: 'right' }}>Actions</th>
                </tr>
              </thead>
              <tbody>
                {isLoadingColleges ? (
                  <tr>
                    <td colSpan={7} style={{ padding: '36px', textAlign: 'center', color: 'var(--text-muted)' }}>
                      Loading Coimbatore institutions...
                    </td>
                  </tr>
                ) : colleges.length === 0 ? (
                  <tr>
                    <td colSpan={7} style={{ padding: '36px', textAlign: 'center', color: 'var(--text-muted)' }}>
                      No matching colleges found. Try adjusting your search or vertical filter.
                    </td>
                  </tr>
                ) : (
                  colleges.map((col) => (
                    <tr
                      key={col.id}
                      style={{
                        borderBottom: '1px solid var(--border-subtle)',
                        transition: 'background-color 0.15s',
                      }}
                      onMouseEnter={(e) => (e.currentTarget.style.backgroundColor = 'var(--bg-surface-subtle)')}
                      onMouseLeave={(e) => (e.currentTarget.style.backgroundColor = 'transparent')}
                    >
                      <td style={{ padding: '12px 16px', fontWeight: 600, color: 'var(--text-primary)' }}>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                          <span>{col.name}</span>
                          {col.website && (
                            <a
                              href={col.website}
                              target="_blank"
                              rel="noreferrer"
                              style={{ color: 'var(--text-muted)', display: 'inline-flex', alignItems: 'center' }}
                              title="Visit college website"
                            >
                              <ExternalLink size={12} />
                            </a>
                          )}
                        </div>
                        {col.accreditation && (
                          <div style={{ fontSize: '11px', color: 'var(--text-muted)', fontWeight: 400, marginTop: '2px' }}>
                            {col.accreditation}
                          </div>
                        )}
                      </td>
                      <td style={{ padding: '12px 16px', color: 'var(--text-secondary)', fontFamily: 'monospace', fontSize: '12px' }}>
                        {col.code || '—'}
                      </td>
                      <td style={{ padding: '12px 16px' }}>
                        <Badge variant="outline" size="sm">
                          {col.institution_type}
                        </Badge>
                      </td>
                      <td style={{ padding: '12px 16px', color: 'var(--text-secondary)', fontSize: '12px' }}>
                        {col.affiliated_university || '—'}
                      </td>
                      <td style={{ padding: '12px 16px', color: 'var(--text-secondary)', fontSize: '12px' }}>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
                          <MapPin size={11} color="var(--text-muted)" />
                          <span>{col.location}, {col.district}</span>
                        </div>
                      </td>
                      <td style={{ padding: '12px 16px' }}>
                        <span
                          style={{
                            display: 'inline-block',
                            padding: '2px 8px',
                            borderRadius: '999px',
                            fontSize: '11px',
                            fontWeight: 600,
                            backgroundColor: col.status === 'ACTIVE' ? 'var(--status-success-subtle)' : 'var(--bg-surface-subtle)',
                            color: col.status === 'ACTIVE' ? 'var(--status-success)' : 'var(--text-muted)',
                          }}
                        >
                          {col.status}
                        </span>
                      </td>
                      <td style={{ padding: '12px 16px', textAlign: 'right' }}>
                        <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '6px' }}>
                          {isAdmin && (
                            <>
                              <button
                                onClick={() => handleOpenEditModal(col)}
                                style={{
                                  padding: '4px 8px',
                                  borderRadius: '4px',
                                  border: '1px solid var(--border-default)',
                                  backgroundColor: 'var(--bg-surface)',
                                  color: 'var(--text-primary)',
                                  fontSize: '11px',
                                  cursor: 'pointer',
                                  display: 'inline-flex',
                                  alignItems: 'center',
                                  gap: '4px',
                                }}
                                title="Edit College Details"
                              >
                                <Edit2 size={11} />
                                Edit
                              </button>

                              <button
                                onClick={() => handleToggleStatus(col)}
                                style={{
                                  padding: '4px 8px',
                                  borderRadius: '4px',
                                  border: '1px solid var(--border-default)',
                                  backgroundColor: 'var(--bg-surface)',
                                  color: col.status === 'ACTIVE' ? 'var(--status-warning)' : 'var(--status-success)',
                                  fontSize: '11px',
                                  cursor: 'pointer',
                                }}
                                title={col.status === 'ACTIVE' ? 'Deactivate' : 'Activate'}
                              >
                                {col.status === 'ACTIVE' ? 'Deactivate' : 'Activate'}
                              </button>
                            </>
                          )}
                        </div>
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>

          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', fontSize: '12px', color: 'var(--text-muted)' }}>
            <span>Showing {colleges.length} institutions in Coimbatore district</span>
            <span>Accredited via Anna University, Bharathiar University, UGC, and MGR Medical University</span>
          </div>
        </Card>
      )}

      {/* TAB 2: USER REQUESTS QUEUE */}
      {activeTab === 'requests' && (
        <Card style={{ padding: '20px', display: 'flex', flexDirection: 'column', gap: '16px' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '10px' }}>
            <div>
              <h2 style={{ fontSize: '15px', fontWeight: 600, color: 'var(--text-primary)', margin: 0 }}>
                Unlisted College Submissions
              </h2>
              <p style={{ fontSize: '12px', color: 'var(--text-secondary)', margin: '2px 0 0 0' }}>
                Students who did not find their institution in the Coimbatore list submit entries here for validation.
              </p>
            </div>

            <div style={{ display: 'flex', gap: '8px' }}>
              {(['PENDING', 'APPROVED', 'REJECTED', 'ALL'] as const).map((st) => (
                <button
                  key={st}
                  onClick={() => setRequestFilter(st)}
                  style={{
                    padding: '5px 12px',
                    borderRadius: 'var(--radius-sm)',
                    border: '1px solid var(--border-default)',
                    backgroundColor: requestFilter === st ? 'var(--brand-primary)' : 'var(--bg-surface)',
                    color: requestFilter === st ? '#fff' : 'var(--text-secondary)',
                    fontSize: '11px',
                    fontWeight: 600,
                    cursor: 'pointer',
                  }}
                >
                  {st}
                </button>
              ))}
            </div>
          </div>

          <div style={{ overflowX: 'auto', border: '1px solid var(--border-subtle)', borderRadius: 'var(--radius-md)' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left', fontSize: '13px' }}>
              <thead>
                <tr style={{ backgroundColor: 'var(--bg-surface-subtle)', borderBottom: '1px solid var(--border-subtle)' }}>
                  <th style={{ padding: '12px 16px', fontWeight: 600, color: 'var(--text-secondary)' }}>Requested College Name</th>
                  <th style={{ padding: '12px 16px', fontWeight: 600, color: 'var(--text-secondary)' }}>Submitted By</th>
                  <th style={{ padding: '12px 16px', fontWeight: 600, color: 'var(--text-secondary)' }}>Location</th>
                  <th style={{ padding: '12px 16px', fontWeight: 600, color: 'var(--text-secondary)' }}>Vertical</th>
                  <th style={{ padding: '12px 16px', fontWeight: 600, color: 'var(--text-secondary)' }}>Status</th>
                  <th style={{ padding: '12px 16px', fontWeight: 600, color: 'var(--text-secondary)' }}>Submitted Date</th>
                  <th style={{ padding: '12px 16px', fontWeight: 600, color: 'var(--text-secondary)', textAlign: 'right' }}>Actions</th>
                </tr>
              </thead>
              <tbody>
                {isLoadingRequests ? (
                  <tr>
                    <td colSpan={7} style={{ padding: '36px', textAlign: 'center', color: 'var(--text-muted)' }}>
                      Loading submission requests...
                    </td>
                  </tr>
                ) : requests.length === 0 ? (
                  <tr>
                    <td colSpan={7} style={{ padding: '36px', textAlign: 'center', color: 'var(--text-muted)' }}>
                      No requests found with status &quot;{requestFilter}&quot;.
                    </td>
                  </tr>
                ) : (
                  requests.map((req) => (
                    <tr
                      key={req.id}
                      style={{
                        borderBottom: '1px solid var(--border-subtle)',
                        transition: 'background-color 0.15s',
                      }}
                    >
                      <td style={{ padding: '12px 16px', fontWeight: 600, color: 'var(--text-primary)' }}>
                        {req.college_name}
                      </td>
                      <td style={{ padding: '12px 16px', color: 'var(--text-secondary)', fontSize: '12px' }}>
                        <div>{req.requester_name}</div>
                        <div style={{ color: 'var(--text-muted)', fontSize: '11px' }}>{req.requester_email}</div>
                      </td>
                      <td style={{ padding: '12px 16px', color: 'var(--text-secondary)', fontSize: '12px' }}>
                        {req.location || 'Coimbatore'}
                      </td>
                      <td style={{ padding: '12px 16px' }}>
                        <Badge variant="outline" size="sm">
                          {req.institution_type || 'General'}
                        </Badge>
                      </td>
                      <td style={{ padding: '12px 16px' }}>
                        <Badge
                          variant={
                            req.status === 'APPROVED' ? 'success' : req.status === 'REJECTED' ? 'danger' : 'warning'
                          }
                          size="sm"
                        >
                          {req.status}
                        </Badge>
                      </td>
                      <td style={{ padding: '12px 16px', color: 'var(--text-muted)', fontSize: '11px' }}>
                        {new Date(req.created_at).toLocaleDateString()}
                      </td>
                      <td style={{ padding: '12px 16px', textAlign: 'right' }}>
                        {req.status === 'PENDING' && isAdmin ? (
                          <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '6px' }}>
                            <Button
                              variant="primary"
                              size="sm"
                              onClick={() => handleApproveRequest(req.id)}
                              disabled={isProcessingAction}
                            >
                              <Check size={12} />
                              Approve
                            </Button>
                            <Button
                              variant="outline"
                              size="sm"
                              onClick={() => {
                                setSelectedRequestId(req.id);
                                setIsRejectModalOpen(true);
                              }}
                              disabled={isProcessingAction}
                            >
                              <X size={12} />
                              Reject
                            </Button>
                          </div>
                        ) : (
                          <span style={{ fontSize: '11px', color: 'var(--text-muted)' }}>
                            {req.admin_notes || 'Handled'}
                          </span>
                        )}
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </Card>
      )}

      {/* ADD / EDIT COLLEGE MODAL DIALOG */}
      <Dialog
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        title={editingCollege ? 'Edit Coimbatore Institution' : 'Add New Coimbatore Institution'}
        description="Ensure details correspond with verified Anna University, UGC, or Tamil Nadu government college registers."
        footer={
          <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '8px' }}>
            <Button variant="outline" size="sm" onClick={() => setIsModalOpen(false)} disabled={isSubmittingModal}>
              Cancel
            </Button>
            <Button variant="primary" size="sm" onClick={handleSaveCollege} isLoading={isSubmittingModal}>
              {editingCollege ? 'Update College' : 'Add to Directory'}
            </Button>
          </div>
        }
      >
        <form onSubmit={handleSaveCollege} style={{ display: 'flex', flexDirection: 'column', gap: '14px', padding: '6px 0' }}>
          {modalError && (
            <Alert variant="danger" title="Validation Error">
              {modalError}
            </Alert>
          )}

          <Input
            label="College / Institution Name *"
            placeholder="e.g. Coimbatore Institute of Technology (CIT)"
            value={modalForm.name}
            onChange={(e) => setModalForm((prev) => ({ ...prev, name: e.target.value }))}
            required
          />

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px' }}>
            <Input
              label="Counseling / College Code"
              placeholder="e.g. 7176 or CAS-001"
              value={modalForm.code || ''}
              onChange={(e) => setModalForm((prev) => ({ ...prev, code: e.target.value }))}
            />

            <div>
              <label style={{ display: 'block', fontSize: '13px', fontWeight: 600, color: 'var(--text-primary)', marginBottom: '4px' }}>
                Institution Vertical *
              </label>
              <select
                value={modalForm.institution_type}
                onChange={(e) => setModalForm((prev) => ({ ...prev, institution_type: e.target.value }))}
                style={{
                  width: '100%',
                  padding: '9px 12px',
                  borderRadius: 'var(--radius-md)',
                  border: '1px solid var(--border-default)',
                  backgroundColor: 'var(--bg-app)',
                  fontSize: '13px',
                }}
              >
                {INSTITUTION_TYPES.map((t) => (
                  <option key={t} value={t}>
                    {t}
                  </option>
                ))}
              </select>
            </div>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px' }}>
            <div>
              <label style={{ display: 'block', fontSize: '13px', fontWeight: 600, color: 'var(--text-primary)', marginBottom: '4px' }}>
                Affiliated University
              </label>
              <select
                value={modalForm.affiliated_university || ''}
                onChange={(e) => setModalForm((prev) => ({ ...prev, affiliated_university: e.target.value }))}
                style={{
                  width: '100%',
                  padding: '9px 12px',
                  borderRadius: 'var(--radius-md)',
                  border: '1px solid var(--border-default)',
                  backgroundColor: 'var(--bg-app)',
                  fontSize: '13px',
                }}
              >
                {AFFILIATED_UNIVERSITIES.map((u) => (
                  <option key={u} value={u}>
                    {u}
                  </option>
                ))}
              </select>
            </div>

            <Input
              label="Location / Area in Coimbatore *"
              placeholder="e.g. Peelamedu, Saravanampatti"
              value={modalForm.location}
              onChange={(e) => setModalForm((prev) => ({ ...prev, location: e.target.value }))}
              required
            />
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px' }}>
            <Input
              label="District"
              value={modalForm.district || 'Coimbatore'}
              disabled
            />
            <Input
              label="State"
              value={modalForm.state || 'Tamil Nadu'}
              disabled
            />
          </div>

          <Input
            label="Official Website URL"
            type="url"
            placeholder="https://www.college.edu.in"
            value={modalForm.website || ''}
            onChange={(e) => setModalForm((prev) => ({ ...prev, website: e.target.value }))}
          />

          <Input
            label="Accreditation & Approvals"
            placeholder="e.g. Autonomous | NAAC A++ (CGPA 3.65) | NBA Accredited"
            value={modalForm.accreditation || ''}
            onChange={(e) => setModalForm((prev) => ({ ...prev, accreditation: e.target.value }))}
          />
        </form>
      </Dialog>

      {/* REJECT REQUEST MODAL DIALOG */}
      <Dialog
        isOpen={isRejectModalOpen}
        onClose={() => setIsRejectModalOpen(false)}
        title="Reject College Submission Request"
        description="Provide a reason for rejection. This note will be recorded for audit and feedback to the student."
        footer={
          <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '8px' }}>
            <Button variant="outline" size="sm" onClick={() => setIsRejectModalOpen(false)}>
              Cancel
            </Button>
            <Button variant="primary" size="sm" onClick={handleRejectRequest} isLoading={isProcessingAction}>
              Confirm Rejection
            </Button>
          </div>
        }
      >
        <div style={{ padding: '8px 0', display: 'flex', flexDirection: 'column', gap: '12px' }}>
          <Input
            label="Rejection Reason / Notes"
            placeholder="e.g. Institution location is not within Coimbatore district, or already exists under alternate name."
            value={rejectReason}
            onChange={(e) => setRejectReason(e.target.value)}
            autoFocus
          />
        </div>
      </Dialog>

    </div>
  );
}

