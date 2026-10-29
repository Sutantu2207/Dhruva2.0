'use client';

import React, { useEffect, useState, useMemo } from 'react';
import Link from 'next/link';
import { usePathname, useRouter } from 'next/navigation';
import { useAuth } from '@/lib/auth/AuthContext';
import { Badge } from '@/components/ui/Badge';
import { Button } from '@/components/ui/Button';
import { NotificationBell } from '@/components/notifications/NotificationBell';
import {
  Layers,
  BookOpen,
  Server,
  FileCheck2,
  Zap,
  GraduationCap,
  TrendingUp,
  Sparkles,
  LayoutDashboard,
  Menu,
  X,
  LogOut,
  ChevronRight,
  Shield,
  Building,
} from 'lucide-react';

interface NavItem {
  href: string;
  label: string;
  icon: React.ComponentType<{ size?: number; className?: string; color?: string }>;
  badge?: string;
  roles?: string[];
}

export default function WorkspaceLayout({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const pathname = usePathname();
  const { user, isAuthenticated, isLoading, logout } = useAuth();
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);

  useEffect(() => {
    if (!isLoading && !isAuthenticated) {
      router.replace('/login');
    }
  }, [isLoading, isAuthenticated, router]);

  // Close mobile drawer on route transition
  useEffect(() => {
    setIsMobileMenuOpen(false);
  }, [pathname]);

  const primaryRole = user?.roles?.[0] || 'STUDENT';
  const isStudent = primaryRole === 'STUDENT';
  const isFaculty = primaryRole === 'FACULTY';
  const isPlacement = primaryRole === 'PLACEMENT_OFFICER';
  const isHOD = primaryRole === 'HOD';
  const isAdmin = ['SUPER_ADMIN', 'INSTITUTION_ADMIN'].includes(primaryRole);

  // Role-Aware Navigation Mapping
  const filteredNavItems = useMemo<NavItem[]>(() => {
    const allItems: NavItem[] = [
      {
        href: '/workspace',
        label: isStudent
          ? 'Student Dashboard'
          : isFaculty
          ? 'Faculty Hub'
          : isPlacement
          ? 'Placement Hub'
          : isHOD
          ? 'Department Overview'
          : 'Executive Dashboard',
        icon: LayoutDashboard,
      },
      {
        href: '/workspace/curriculum',
        label: isStudent ? 'My Courses & Syllabus' : 'Curriculum & Units',
        icon: BookOpen,
        roles: ['STUDENT', 'FACULTY', 'HOD', 'INSTITUTION_ADMIN', 'SUPER_ADMIN'],
      },
      {
        href: '/workspace/assessments',
        label: isStudent ? 'Exams & Quizzes' : 'Assessments & Grading',
        icon: FileCheck2,
        roles: ['STUDENT', 'FACULTY', 'HOD', 'INSTITUTION_ADMIN', 'SUPER_ADMIN'],
      },
      {
        href: '/workspace/mastery',
        label: isStudent ? 'Mastery & Flashcards' : 'Competency Mastery',
        icon: Zap,
        roles: ['STUDENT', 'FACULTY', 'PLACEMENT_OFFICER', 'HOD', 'INSTITUTION_ADMIN', 'SUPER_ADMIN'],
      },
      {
        href: '/workspace/placement',
        label: isStudent ? 'Projects & Portfolio' : 'Talent & Placement',
        icon: GraduationCap,
        roles: ['STUDENT', 'PLACEMENT_OFFICER', 'HOD', 'INSTITUTION_ADMIN', 'SUPER_ADMIN'],
      },
      {
        href: '/workspace/ai',
        label: isStudent ? 'AI Academic Tutor' : isFaculty ? 'AI Question Authoring' : 'AI Gateway & Logs',
        icon: Sparkles,
        badge: 'Grounded',
        roles: ['STUDENT', 'FACULTY', 'HOD', 'INSTITUTION_ADMIN', 'SUPER_ADMIN'],
      },
      {
        href: '/workspace/academic',
        label: isFaculty ? 'Assigned Classes' : 'Academic Hierarchy',
        icon: Layers,
        roles: ['FACULTY', 'HOD', 'INSTITUTION_ADMIN', 'SUPER_ADMIN'],
      },
      {
        href: '/workspace/analytics',
        label: 'Analytics & Interventions',
        icon: TrendingUp,
        roles: ['FACULTY', 'PLACEMENT_OFFICER', 'HOD', 'INSTITUTION_ADMIN', 'SUPER_ADMIN'],
      },
      {
        href: '/workspace/datacenter',
        label: 'Data Center (ETL Ingest)',
        icon: Server,
        badge: 'Admin',
        roles: ['INSTITUTION_ADMIN', 'SUPER_ADMIN', 'HOD'],
      },
    ];

    if (isAdmin) return allItems;

    return allItems.filter((item) => {
      if (!item.roles) return true;
      return user?.roles?.some((r) => item.roles?.includes(r));
    });
  }, [user?.roles, isStudent, isFaculty, isPlacement, isHOD, isAdmin]);

  // Derive current page title for breadcrumb
  const currentPageTitle = useMemo(() => {
    const match = filteredNavItems.find((item) => item.href === pathname);
    if (match) return match.label;
    if (pathname.startsWith('/workspace/academic')) return 'Academic Structure';
    if (pathname.startsWith('/workspace/curriculum')) return 'Curriculum';
    if (pathname.startsWith('/workspace/assessments')) return 'Assessments';
    if (pathname.startsWith('/workspace/mastery')) return 'Mastery';
    if (pathname.startsWith('/workspace/placement')) return 'Placement';
    if (pathname.startsWith('/workspace/ai')) return 'AI Assistant';
    if (pathname.startsWith('/workspace/analytics')) return 'Analytics';
    if (pathname.startsWith('/workspace/datacenter')) return 'Data Center';
    return 'Workspace';
  }, [pathname, filteredNavItems]);

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
          fontSize: '14px',
        }}
      >
        Initializing secure environment...
      </div>
    );
  }

  if (!user) return null;

  const sidebarContent = (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100%', justifyContent: 'space-between' }}>
      <div>
        {/* Brand Header */}
        <div
          style={{
            padding: '18px 20px',
            borderBottom: '1px solid var(--border-subtle)',
            display: 'flex',
            alignItems: 'center',
            gap: '12px',
          }}
        >
          <div
            style={{
              width: '34px',
              height: '34px',
              borderRadius: 'var(--radius-md)',
              backgroundColor: 'var(--brand-primary)',
              color: '#ffffff',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              fontWeight: 800,
              fontSize: '17px',
              boxShadow: 'var(--shadow-sm)',
            }}
          >
            D
          </div>
          <div style={{ flex: 1, minWidth: 0 }}>
            <div style={{ fontSize: '15px', fontWeight: 700, color: 'var(--text-primary)', letterSpacing: '-0.01em' }}>
              Dhruva.AI
            </div>
            <div style={{ fontSize: '11px', color: 'var(--text-muted)', display: 'flex', alignItems: 'center', gap: '4px' }}>
              <Building size={11} />
              <span style={{ overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                {user.institution_slug?.toUpperCase() || 'INSTITUTE'}
              </span>
            </div>
          </div>
        </div>

        {/* Navigation Items */}
        <nav aria-label="Primary Workspace Navigation" style={{ padding: '16px 12px', display: 'flex', flexDirection: 'column', gap: '4px' }}>
          {filteredNavItems.map((item) => {
            const Icon = item.icon;
            const isActive = pathname === item.href;
            return (
              <Link
                key={item.href}
                href={item.href}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'space-between',
                  padding: '9px 12px',
                  borderRadius: 'var(--radius-md)',
                  backgroundColor: isActive ? 'var(--brand-primary-subtle)' : 'transparent',
                  color: isActive ? 'var(--brand-primary)' : 'var(--text-secondary)',
                  fontWeight: isActive ? 600 : 500,
                  fontSize: '13px',
                  transition: 'background-color 0.15s ease, color 0.15s ease',
                }}
                onMouseEnter={(e) => {
                  if (!isActive) e.currentTarget.style.backgroundColor = 'var(--bg-surface-subtle)';
                }}
                onMouseLeave={(e) => {
                  if (!isActive) e.currentTarget.style.backgroundColor = 'transparent';
                }}
              >
                <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                  <Icon size={16} color={isActive ? 'var(--brand-primary)' : 'var(--text-muted)'} />
                  <span>{item.label}</span>
                </div>
                {item.badge && (
                  <Badge variant={isActive ? 'primary' : 'outline'} size="sm">
                    {item.badge}
                  </Badge>
                )}
              </Link>
            );
          })}
        </nav>
      </div>

      {/* User Session Footer */}
      <div
        style={{
          padding: '16px',
          borderTop: '1px solid var(--border-subtle)',
          backgroundColor: 'var(--bg-surface-subtle)',
          display: 'flex',
          flexDirection: 'column',
          gap: '12px',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          <div
            style={{
              width: '32px',
              height: '32px',
              borderRadius: '50%',
              backgroundColor: '#e0e7ff',
              color: '#3730a3',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              fontWeight: 700,
              fontSize: '13px',
            }}
          >
            {user.full_name?.charAt(0).toUpperCase() || 'U'}
          </div>
          <div style={{ minWidth: 0, flex: 1 }}>
            <div style={{ fontSize: '13px', fontWeight: 600, color: 'var(--text-primary)', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
              {user.full_name}
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '4px', marginTop: '2px' }}>
              <Shield size={10} color="#64748b" />
              <span style={{ fontSize: '11px', color: 'var(--text-muted)', fontWeight: 500 }}>
                {primaryRole.replace('_', ' ')}
              </span>
            </div>
          </div>
        </div>

        <Button
          variant="outline"
          size="sm"
          onClick={async () => {
            await logout();
            router.push('/login');
          }}
          style={{ width: '100%', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '6px' }}
        >
          <LogOut size={13} />
          Sign Out
        </Button>
      </div>
    </div>
  );

  return (
    <div style={{ display: 'flex', minHeight: '100vh', backgroundColor: 'var(--bg-app)' }}>
      {/* Skip to Main Content Link for WCAG Keyboard Nav */}
      <a href="#main-content" className="skip-link">
        Skip to main content
      </a>

      {/* Desktop Permanent Sidebar */}
      <aside
        aria-label="Workspace Sidebar"
        style={{
          width: '260px',
          borderRight: '1px solid var(--border-subtle)',
          backgroundColor: 'var(--bg-surface)',
          display: 'flex',
          flexDirection: 'column',
          position: 'sticky',
          top: 0,
          height: '100vh',
          zIndex: 30,
        }}
        className="hidden-mobile"
      >
        {sidebarContent}
      </aside>

      {/* Mobile Drawer Backdrop & Drawer */}
      {isMobileMenuOpen && (
        <div
          style={{
            position: 'fixed',
            inset: 0,
            backgroundColor: 'rgba(15, 23, 42, 0.5)',
            zIndex: 100,
            display: 'flex',
          }}
          onClick={() => setIsMobileMenuOpen(false)}
        >
          <div
            style={{
              width: '280px',
              maxWidth: '85vw',
              height: '100%',
              backgroundColor: 'var(--bg-surface)',
              boxShadow: 'var(--shadow-lg)',
            }}
            onClick={(e) => e.stopPropagation()}
          >
            {sidebarContent}
          </div>
        </div>
      )}

      {/* Main Content Area */}
      <div style={{ flex: 1, display: 'flex', flexDirection: 'column', minWidth: 0 }}>
        {/* Top Header Bar */}
        <header
          style={{
            height: '60px',
            borderBottom: '1px solid var(--border-subtle)',
            backgroundColor: 'var(--bg-surface)',
            padding: '0 24px',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            position: 'sticky',
            top: 0,
            zIndex: 20,
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
            {/* Mobile Hamburger Button */}
            <button
              onClick={() => setIsMobileMenuOpen((prev) => !prev)}
              style={{
                background: 'none',
                border: '1px solid var(--border-subtle)',
                borderRadius: 'var(--radius-md)',
                padding: '6px',
                cursor: 'pointer',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                color: 'var(--text-secondary)',
              }}
              aria-label="Toggle navigation menu"
              className="visible-mobile"
            >
              {isMobileMenuOpen ? <X size={18} /> : <Menu size={18} />}
            </button>

            {/* Breadcrumb Indicator */}
            <div style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '13px' }}>
              <Link href="/workspace" style={{ color: 'var(--text-muted)', fontWeight: 500 }}>
                Workspace
              </Link>
              <ChevronRight size={14} color="var(--text-muted)" />
              <span style={{ color: 'var(--text-primary)', fontWeight: 600 }}>
                {currentPageTitle}
              </span>
            </div>
          </div>

          {/* Right Header Badges & Notification Hub */}
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
            <Badge variant="outline" size="sm">
              {primaryRole.replace('_', ' ')}
            </Badge>
            <NotificationBell institutionId={user.institution_id} />
          </div>
        </header>

        {/* Main Content Body */}
        <main
          id="main-content"
          tabIndex={-1}
          style={{
            flex: 1,
            padding: '24px 28px',
            maxWidth: '1440px',
            width: '100%',
            margin: '0 auto',
            outline: 'none',
          }}
        >
          {children}
        </main>
      </div>

      <style jsx global>{`
        @media (max-width: 1024px) {
          .hidden-mobile {
            display: none !important;
          }
          .visible-mobile {
            display: flex !important;
          }
        }
        @media (min-width: 1025px) {
          .visible-mobile {
            display: none !important;
          }
        }
      `}</style>
    </div>
  );
}
