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
          bg: '#ede4ff',
          border: 'rgba(124, 58, 237, 0.25)',
          color: '#7c3aed',
        };
      case 'success':
        return {
          bg: '#ecfdf5',
          border: 'rgba(16, 185, 129, 0.25)',
          color: '#059669',
        };
      case 'warning':
        return {
          bg: '#fffbeb',
          border: 'rgba(245, 158, 11, 0.25)',
          color: '#d97706',
        };
      case 'danger':
        return {
          bg: '#fef2f2',
          border: 'rgba(239, 68, 68, 0.25)',
          color: '#dc2626',
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
