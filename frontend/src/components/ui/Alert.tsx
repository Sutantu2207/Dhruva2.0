import React from 'react';

export interface AlertProps {
  title?: string;
  children: React.ReactNode;
  variant?: 'info' | 'success' | 'warning' | 'danger';
}

export const Alert: React.FC<AlertProps> = ({
  title,
  children,
  variant = 'info',
}) => {
  const getStyles = () => {
    switch (variant) {
      case 'info':
        return {
          bg: 'var(--status-info-subtle)',
          border: 'rgba(59, 130, 246, 0.25)',
          color: 'var(--status-info)',
        };
      case 'success':
        return {
          bg: 'var(--status-success-subtle)',
          border: 'rgba(16, 185, 129, 0.25)',
          color: 'var(--status-success)',
        };
      case 'warning':
        return {
          bg: 'var(--status-warning-subtle)',
          border: 'rgba(245, 158, 11, 0.25)',
          color: 'var(--status-warning)',
        };
      case 'danger':
        return {
          bg: 'var(--status-danger-subtle)',
          border: 'rgba(239, 68, 68, 0.25)',
          color: 'var(--status-danger)',
        };
    }
  };

  const current = getStyles();

  return (
    <div
      role="alert"
      style={{
        padding: '12px 16px',
        backgroundColor: current.bg,
        border: `1px solid ${current.border}`,
        borderRadius: 'var(--radius-md)',
        display: 'flex',
        flexDirection: 'column',
        gap: '4px',
      }}
    >
      {title && (
        <span style={{ fontSize: '13px', fontWeight: 600, color: current.color }}>
          {title}
        </span>
      )}
      <div style={{ fontSize: '13px', color: 'var(--text-primary)' }}>
        {children}
      </div>
    </div>
  );
};
