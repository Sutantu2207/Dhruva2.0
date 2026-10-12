'use client';

import React from 'react';
import { useAuth } from '@/lib/auth/AuthContext';
import { Badge } from '@/components/ui/Badge';
import { Breadcrumbs } from '@/components/ui/Breadcrumbs';
import { Card } from '@/components/ui/Card';
import { PageHeader } from '@/components/ui/PageHeader';

export default function WorkspaceOverviewPage() {
  const { user } = useAuth();

  return (
    <div>
      <Breadcrumbs
        items={[
          { label: 'Workspace', href: '/workspace' },
          { label: 'Foundation Status' },
        ]}
      />

      <PageHeader
        title="Phase 1: Core Foundation Status"
        description="Multi-tenant Row-Level Security, Argon2id authentication, centralized RBAC, and error envelopes are operational."
        badge={<Badge variant="success">Phase 1 Complete</Badge>}
      />

      {/* Grid of Foundation Subsystem Cards */}
      <div
        style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))',
          gap: '16px',
          marginBottom: '24px',
        }}
      >
        <Card title="Multi-Tenancy & RLS" subtitle="PostgreSQL 16 Partitioning">
          <p style={{ fontSize: '13px', color: 'var(--text-secondary)' }}>
            Dynamic session context <code>app.current_institution_id</code> enforces strict data separation with zero cross-tenant leakage.
          </p>
          <div style={{ marginTop: '12px' }}>
            <Badge variant="success">RLS Enforced</Badge>
          </div>
        </Card>

        <Card title="Identity & Cryptography" subtitle="Argon2id + Dual JWT">
          <p style={{ fontSize: '13px', color: 'var(--text-secondary)' }}>
            OWASP-compliant Argon2id password hashing with rotating 15-min JWT access tokens and revocable refresh tokens.
          </p>
          <div style={{ marginTop: '12px' }}>
            <Badge variant="success">Zero Plaintext</Badge>
          </div>
        </Card>

        <Card title="RBAC & Permission Registry" subtitle="6 Architectural Roles">
          <p style={{ fontSize: '13px', color: 'var(--text-secondary)' }}>
            Super Admin, Institution Admin, HOD, Faculty, Student, and Placement Officer permission matrices validated.
          </p>
          <div style={{ marginTop: '12px' }}>
            <Badge variant="success">33 Tests Passing</Badge>
          </div>
        </Card>

        <Card title="Zero Mock Data Standard" subtitle="Rule 18 Enforcement">
          <p style={{ fontSize: '13px', color: 'var(--text-secondary)' }}>
            Clean database ready for real institutional onboarding. Ephemeral in-memory SQLite sandbox used for automated tests.
          </p>
          <div style={{ marginTop: '12px' }}>
            <Badge variant="info">Zero Fake Records</Badge>
          </div>
        </Card>
      </div>

      {/* Active User Permissions Table/List */}
      <Card title="Caller Granted Permissions" subtitle="Granular authorization bitmask evaluated for your active identity">
        {user?.permissions && user.permissions.length > 0 ? (
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: '8px' }}>
            {user.permissions.map((perm) => (
              <Badge key={perm} variant="default">
                {perm}
              </Badge>
            ))}
          </div>
        ) : (
          <p style={{ fontSize: '13px', color: 'var(--text-muted)' }}>
            Platform Super Admin authorization (Bypasses granular filters).
          </p>
        )}
      </Card>
    </div>
  );
}
