import React from 'react';

export interface BadgeProps {
  children: React.ReactNode;
  variant?: 'default' | 'success' | 'warning' | 'danger' | 'info' | 'outline';
  size?: 'sm' | 'md';
}

export const Badge: React.FC<BadgeProps> = ({
  children,
  variant = 'default',
  size = 'md',
}) => {
  const getVariantStyles = (): React.CSSProperties => {
    switch (variant) {
      case 'default':
        return {
          backgroundColor: 'var(--bg-surface-elevated)',
          color: 'var(--text-secondary)',
          border: '1px solid var(--border-subtle)',
        };
      case 'success':
        return {
          backgroundColor: 'var(--status-success-subtle)',
          color: 'var(--status-success)',
          border: '1px solid rgba(16, 185, 129, 0.2)',
        };
      case 'warning':
        return {
          backgroundColor: 'var(--status-warning-subtle)',
          color: 'var(--status-warning)',
          border: '1px solid rgba(245, 158, 11, 0.2)',
        };
      case 'danger':
        return {
          backgroundColor: 'var(--status-danger-subtle)',
          color: 'var(--status-danger)',
          border: '1px solid rgba(239, 68, 68, 0.2)',
        };
      case 'info':
        return {
          backgroundColor: 'var(--status-info-subtle)',
          color: 'var(--status-info)',
          border: '1px solid rgba(59, 130, 246, 0.2)',
        };
      case 'outline':
        return {
          backgroundColor: 'transparent',
          color: 'var(--text-secondary)',
          border: '1px solid var(--border-default)',
        };
    }
  };

  return (
    <span
      style={{
        display: 'inline-flex',
        alignItems: 'center',
        gap: '4px',
        borderRadius: 'var(--radius-full)',
        fontWeight: 500,
        fontSize: size === 'sm' ? '11px' : '12px',
        padding: size === 'sm' ? '1px 8px' : '2px 10px',
        lineHeight: 1.4,
        ...getVariantStyles(),
      }}
    >
      {children}
    </span>
  );
};
