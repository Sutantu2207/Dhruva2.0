'use client';

import React, { useEffect } from 'react';
import { usePathname, useRouter } from 'next/navigation';
import { useAuth } from '@/lib/auth/AuthContext';
import { Badge } from '@/components/ui/Badge';
import { Button } from '@/components/ui/Button';
import { NotificationBell } from '@/components/notifications/NotificationBell';

export default function WorkspaceLayout({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const pathname = usePathname();
  const { user, isAuthenticated, isLoading, logout } = useAuth();

  useEffect(() => {
    if (!isLoading && !isAuthenticated) {
      router.replace('/login');
    }
  }, [isLoading, isAuthenticated, router]);

  if (isLoading) {
    return (
      <div
        style={{
          minHeight: '100vh',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          backgroundColor: 'var(--bg-app)',
          color: 'var(--text-secondary)',
        }}
      >
        Loading workspace environment...
      </div>
    );
  }

  if (!user) return null;

  const primaryRole = user.roles[0] || 'STUDENT';

  const navItems = [
    { href: '/workspace', label: 'Foundation Overview' },
    { href: '/workspace/academic', label: 'Academic Structure' },
    { href: '/workspace/curriculum', label: 'Curriculum & Syllabus' },
    { href: '/workspace/datacenter', label: 'Data Center & Ingestion' },
    { href: '/workspace/assessments', label: 'Assessments & Grading' },
    { href: '/workspace/mastery', label: 'Mastery & Evidence' },
    { href: '/workspace/placement', label: 'Projects & Placement' },
    { href: '/workspace/analytics', label: 'Analytics & Interventions' },
    { href: '/workspace/ai', label: 'AI Gateway & Tutor' },
  ];

  return (
    <div style={{ display: 'flex', minHeight: '100vh', backgroundColor: 'var(--bg-app)' }}>
      {/* Sidebar Navigation */}
      <aside
        style={{
          width: '240px',
          borderRight: '1px solid var(--border-subtle)',
          backgroundColor: 'var(--bg-surface)',
          display: 'flex',
          flexDirection: 'column',
          justifyContent: 'space-between',
        }}
      >
        <div>
          {/* Brand Banner */}
          <div
            style={{
              padding: '20px 16px',
              borderBottom: '1px solid var(--border-subtle)',
              display: 'flex',
              alignItems: 'center',
              gap: '10px',
            }}
          >
            <div
              style={{
                width: '32px',
                height: '32px',
                borderRadius: 'var(--radius-md)',
                backgroundColor: 'var(--brand-primary)',
                color: '#ffffff',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                fontWeight: 800,
                fontSize: '15px',
              }}
            >
              D
            </div>
            <div>
              <div style={{ fontSize: '15px', fontWeight: 700, color: 'var(--text-primary)' }}>
                Dhruva.AI
              </div>
              <div style={{ fontSize: '11px', color: 'var(--text-muted)' }}>
                V2 Foundation Shell
              </div>
            </div>
          </div>

          {/* Navigation Links */}
          <nav style={{ padding: '16px 8px', display: 'flex', flexDirection: 'column', gap: '4px' }}>
            {navItems.map((item) => {
              const isActive = pathname === item.href;
              return (
                <a
                  key={item.href}
                  href={item.href}
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    padding: '8px 12px',
                    borderRadius: 'var(--radius-md)',
                    backgroundColor: isActive ? 'var(--brand-primary-subtle)' : 'transparent',
                    color: isActive ? 'var(--brand-primary)' : 'var(--text-secondary)',
                    fontWeight: isActive ? 600 : 500,
                    fontSize: '13px',
                    transition: 'all 0.15s ease',
                  }}
                >
                  {item.label}
                </a>
              );
            })}


            {/* Role indicator */}
            <div style={{ padding: '12px 12px 4px', fontSize: '11px', fontWeight: 600, color: 'var(--text-muted)' }}>
              SYSTEM ROLES
            </div>
            <div style={{ padding: '4px 12px', display: 'flex', flexWrap: 'wrap', gap: '4px' }}>
              {user.roles.map((r) => (
                <Badge key={r} variant="outline" size="sm">
                  {r}
                </Badge>
              ))}
            </div>
          </nav>
        </div>

        {/* User Profile Footer */}
        <div
          style={{
            padding: '16px',
            borderTop: '1px solid var(--border-subtle)',
            backgroundColor: 'var(--bg-surface-elevated)',
            display: 'flex',
            flexDirection: 'column',
            gap: '12px',
          }}
        >
          <div>
            <div style={{ fontSize: '13px', fontWeight: 600, color: 'var(--text-primary)' }}>
              {user.full_name}
            </div>
            <div style={{ fontSize: '11px', color: 'var(--text-muted)', overflow: 'hidden', textOverflow: 'ellipsis' }}>
              {user.email}
            </div>
          </div>

          <Button
            variant="outline"
            size="sm"
            onClick={async () => {
              await logout();
              router.push('/login');
            }}
            style={{ width: '100%' }}
          >
            Sign Out
          </Button>
        </div>
      </aside>

      {/* Main Content Shell */}
      <div style={{ flex: 1, display: 'flex', flexDirection: 'column' }}>
        {/* Top Header */}
        <header
          style={{
            height: '56px',
            borderBottom: '1px solid var(--border-subtle)',
            backgroundColor: 'var(--bg-surface)',
            padding: '0 24px',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <Badge variant="info">Tenant Partition</Badge>
            <span style={{ fontSize: '12px', color: 'var(--text-secondary)', fontFamily: 'var(--font-mono)' }}>
              {user.institution_id ? `institution_id: ${user.institution_id}` : 'Global Platform Partition'}
            </span>
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
            <NotificationBell institutionId={user.institution_id} />
            <Badge variant="success">Engine: Active</Badge>
          </div>
        </header>

        {/* Page Content Body */}
        <main style={{ flex: 1, padding: '24px', maxWidth: '1200px', width: '100%', margin: '0 auto' }}>
          {children}
        </main>
      </div>
    </div>
  );
}
