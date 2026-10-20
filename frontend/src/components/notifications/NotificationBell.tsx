'use client';

import React, { useState, useEffect, useRef } from 'react';
import { useRouter } from 'next/navigation';
import { Badge } from '@/components/ui/Badge';
import { Button } from '@/components/ui/Button';
import { NotificationItem } from '@/types/analytics';

interface NotificationBellProps {
  institutionId?: string | null;
}

export function NotificationBell({ institutionId }: NotificationBellProps) {
  const router = useRouter();
  const [isOpen, setIsOpen] = useState(false);
  const [unreadCount, setUnreadCount] = useState<number>(3);
  const [notifications, setNotifications] = useState<NotificationItem[]>([
    {
      id: 'notif-1',
      institution_id: institutionId || 'inst-default',
      recipient_user_id: 'user-current',
      notification_type: 'EARLY_WARNING',
      title: 'Academic Alert: Critical Mastery Decay',
      message: 'Student Anita Rao (CS2026-042) flagged for Database Systems & Algorithms intervention.',
      is_read: false,
      link_url: '/workspace/analytics',
      created_at: new Date(Date.now() - 1000 * 60 * 25).toISOString(),
    },
    {
      id: 'notif-2',
      institution_id: institutionId || 'inst-default',
      recipient_user_id: 'user-current',
      notification_type: 'INTERVENTION_ASSIGNED',
      title: 'Intervention Assigned: Academic Tutoring',
      message: 'You have been assigned to supervise study plan revision for Rahul Sharma.',
      is_read: false,
      link_url: '/workspace/analytics',
      created_at: new Date(Date.now() - 1000 * 60 * 120).toISOString(),
    },
    {
      id: 'notif-3',
      institution_id: institutionId || 'inst-default',
      recipient_user_id: 'user-current',
      notification_type: 'ANALYTICS_ROLLUP',
      title: 'Nightly Rollup Generated',
      message: 'Departmental passing rates and competency health rollups successfully cached.',
      is_read: false,
      link_url: '/workspace/analytics',
      created_at: new Date(Date.now() - 1000 * 60 * 360).toISOString(),
    },
  ]);

  const popoverRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (popoverRef.current && !popoverRef.current.contains(event.target as Node)) {
        setIsOpen(false);
      }
    }
    if (isOpen) {
      document.addEventListener('mousedown', handleClickOutside);
    }
    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, [isOpen]);

  const handleMarkAsRead = (id: string, e?: React.MouseEvent) => {
    e?.stopPropagation();
    setNotifications((prev) =>
      prev.map((n) => (n.id === id ? { ...n, is_read: true, read_at: new Date().toISOString() } : n))
    );
    setUnreadCount((prev) => Math.max(0, prev - 1));
  };

  const handleMarkAllRead = () => {
    setNotifications((prev) =>
      prev.map((n) => ({ ...n, is_read: true, read_at: new Date().toISOString() }))
    );
    setUnreadCount(0);
  };

  const formatTimeAgo = (isoString: string) => {
    const diffMs = Date.now() - new Date(isoString).getTime();
    const diffMins = Math.floor(diffMs / (1000 * 60));
    if (diffMins < 60) return `${diffMins}m ago`;
    const diffHours = Math.floor(diffMins / 60);
    if (diffHours < 24) return `${diffHours}h ago`;
    return `${Math.floor(diffHours / 24)}d ago`;
  };

  return (
    <div style={{ position: 'relative' }} ref={popoverRef}>
      {/* Bell Trigger Button */}
      <button
        onClick={() => setIsOpen((prev) => !prev)}
        style={{
          position: 'relative',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          width: '36px',
          height: '36px',
          borderRadius: 'var(--radius-md)',
          backgroundColor: isOpen ? 'var(--bg-surface-elevated)' : 'transparent',
          border: '1px solid var(--border-subtle)',
          color: 'var(--text-primary)',
          cursor: 'pointer',
          transition: 'all 0.15s ease',
        }}
        title="View Notifications"
        aria-label="Notifications"
      >
        <svg
          width="18"
          height="18"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          strokeWidth="2"
          strokeLinecap="round"
          strokeLinejoin="round"
        >
          <path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9" />
          <path d="M13.73 21a2 2 0 0 1-3.46 0" />
        </svg>

        {unreadCount > 0 && (
          <span
            style={{
              position: 'absolute',
              top: '-4px',
              right: '-4px',
              backgroundColor: 'var(--status-danger)',
              color: '#ffffff',
              fontSize: '10px',
              fontWeight: 700,
              minWidth: '18px',
              height: '18px',
              borderRadius: 'var(--radius-full)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              padding: '0 4px',
              boxShadow: '0 0 0 2px var(--bg-surface)',
            }}
          >
            {unreadCount > 9 ? '9+' : unreadCount}
          </span>
        )}
      </button>

      {/* Flyout Popover */}
      {isOpen && (
        <div
          style={{
            position: 'absolute',
            top: '46px',
            right: 0,
            width: '380px',
            maxHeight: '480px',
            backgroundColor: 'var(--bg-surface-elevated)',
            border: '1px solid var(--border-default)',
            borderRadius: 'var(--radius-lg)',
            boxShadow: 'var(--shadow-lg)',
            zIndex: 1000,
            display: 'flex',
            flexDirection: 'column',
            overflow: 'hidden',
          }}
        >
          {/* Header */}
          <div
            style={{
              padding: '12px 16px',
              borderBottom: '1px solid var(--border-subtle)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              backgroundColor: 'var(--bg-surface)',
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <span style={{ fontSize: '14px', fontWeight: 700, color: 'var(--text-primary)' }}>
                Notifications
              </span>
              {unreadCount > 0 && (
                <Badge variant="danger" size="sm">
                  {unreadCount} unread
                </Badge>
              )}
            </div>

            {unreadCount > 0 && (
              <button
                onClick={handleMarkAllRead}
                style={{
                  background: 'none',
                  border: 'none',
                  fontSize: '11px',
                  color: 'var(--brand-accent)',
                  cursor: 'pointer',
                  fontWeight: 600,
                }}
              >
                Mark all read
              </button>
            )}
          </div>

          {/* List */}
          <div style={{ flex: 1, overflowY: 'auto', maxHeight: '360px' }}>
            {notifications.length === 0 ? (
              <div
                style={{
                  padding: '32px 16px',
                  textAlign: 'center',
                  color: 'var(--text-muted)',
                  fontSize: '13px',
                }}
              >
                No notifications right now.
              </div>
            ) : (
              notifications.map((n) => (
                <div
                  key={n.id}
                  onClick={() => {
                    if (!n.is_read) handleMarkAsRead(n.id);
                    if (n.link_url) {
                      setIsOpen(false);
                      router.push(n.link_url);
                    }
                  }}
                  style={{
                    padding: '12px 16px',
                    borderBottom: '1px solid var(--border-subtle)',
                    backgroundColor: n.is_read ? 'transparent' : 'var(--bg-surface-subtle)',
                    cursor: 'pointer',
                    transition: 'background-color 0.15s ease',
                    display: 'flex',
                    flexDirection: 'column',
                    gap: '4px',
                  }}
                >
                  <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                      {!n.is_read && (
                        <span
                          style={{
                            width: '6px',
                            height: '6px',
                            borderRadius: '50%',
                            backgroundColor: 'var(--brand-primary)',
                          }}
                        />
                      )}
                      <span
                        style={{
                          fontSize: '12px',
                          fontWeight: n.is_read ? 500 : 700,
                          color: 'var(--text-primary)',
                        }}
                      >
                        {n.title}
                      </span>
                    </div>
                    <span style={{ fontSize: '11px', color: 'var(--text-muted)' }}>
                      {formatTimeAgo(n.created_at)}
                    </span>
                  </div>

                  <p
                    style={{
                      margin: 0,
                      fontSize: '12px',
                      color: 'var(--text-secondary)',
                      lineHeight: 1.4,
                    }}
                  >
                    {n.message}
                  </p>

                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginTop: '4px' }}>
                    <Badge
                      variant={
                        n.notification_type === 'EARLY_WARNING'
                          ? 'warning'
                          : n.notification_type === 'INTERVENTION_ASSIGNED'
                          ? 'info'
                          : 'default'
                      }
                      size="sm"
                    >
                      {n.notification_type}
                    </Badge>

                    {!n.is_read && (
                      <button
                        onClick={(e) => handleMarkAsRead(n.id, e)}
                        style={{
                          background: 'none',
                          border: 'none',
                          color: 'var(--text-muted)',
                          fontSize: '11px',
                          cursor: 'pointer',
                        }}
                      >
                        Dismiss
                      </button>
                    )}
                  </div>
                </div>
              ))
            )}
          </div>

          {/* Footer */}
          <div
            style={{
              padding: '10px 16px',
              borderTop: '1px solid var(--border-subtle)',
              backgroundColor: 'var(--bg-surface)',
              display: 'flex',
              justifyContent: 'center',
            }}
          >
            <Button
              variant="outline"
              size="sm"
              onClick={() => {
                setIsOpen(false);
                router.push('/workspace/analytics?tab=notifications');
              }}
              style={{ width: '100%', fontSize: '12px' }}
            >
              Open Notification Hub
            </Button>
          </div>
        </div>
      )}
    </div>
  );
}
