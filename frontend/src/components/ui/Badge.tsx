import React from 'react';

export interface BadgeProps {
  children: React.ReactNode;
  variant?: 'default' | 'primary' | 'success' | 'warning' | 'danger' | 'info' | 'outline';
  size?: 'sm' | 'md';
}

export const Badge: React.FC<BadgeProps> = ({
  children,
  variant = 'default',
  size = 'md',
}) => {
  const getVariantStyles = (): React.CSSProperties => {
    switch (variant) {
      case 'primary':
      case 'default':
        return {
          backgroundColor: '#eef2ff',
          color: '#4338ca',
          border: '1px solid rgba(79, 70, 229, 0.25)',
        };
      case 'success':
        return {
          backgroundColor: '#ecfdf5',
          color: '#059669',
          border: '1px solid rgba(16, 185, 129, 0.25)',
        };
      case 'warning':
        return {
          backgroundColor: '#fffbeb',
          color: '#d97706',
          border: '1px solid rgba(245, 158, 11, 0.25)',
        };
      case 'danger':
        return {
          backgroundColor: '#fef2f2',
          color: '#dc2626',
          border: '1px solid rgba(239, 68, 68, 0.25)',
        };
      case 'info':
        return {
          backgroundColor: '#eff6ff',
          color: '#2563eb',
          border: '1px solid rgba(37, 99, 235, 0.25)',
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
        fontWeight: 600,
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
