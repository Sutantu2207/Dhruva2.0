'use client';

import React from 'react';

export interface ToastProps {
  id: string;
  title: string;
  message?: string;
  variant?: 'info' | 'success' | 'warning' | 'danger';
  onDismiss: (id: string) => void;
}

export const Toast: React.FC<ToastProps> = ({
  id,
  title,
  message,
  variant = 'info',
  onDismiss,
}) => {
  const getBorderColor = () => {
    switch (variant) {
      case 'success':
        return 'var(--status-success)';
      case 'warning':
        return 'var(--status-warning)';
      case 'danger':
        return 'var(--status-danger)';
      default:
        return 'var(--status-info)';
    }
  };

  return (
    <div
      role="status"
      style={{
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'flex-start',
        gap: '12px',
        padding: '12px 16px',
        backgroundColor: 'var(--bg-surface-elevated)',
        borderLeft: `3px solid ${getBorderColor()}`,
        borderRadius: 'var(--radius-md)',
        boxShadow: 'var(--shadow-lg)',
        border: '1px solid var(--border-default)',
        minWidth: '280px',
        maxWidth: '420px',
      }}
    >
      <div>
        <div style={{ fontSize: '13px', fontWeight: 600, color: 'var(--text-primary)' }}>
          {title}
        </div>
        {message && (
          <div style={{ fontSize: '12px', color: 'var(--text-secondary)', marginTop: '2px' }}>
            {message}
          </div>
        )}
      </div>
      <button
        onClick={() => onDismiss(id)}
        style={{
          background: 'none',
          border: 'none',
          color: 'var(--text-muted)',
          cursor: 'pointer',
          fontSize: '14px',
          padding: '2px',
        }}
        aria-label="Dismiss toast"
      >
        ✕
      </button>
    </div>
  );
};
