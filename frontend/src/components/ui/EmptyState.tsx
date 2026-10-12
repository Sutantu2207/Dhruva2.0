import React from 'react';
import { Button } from './Button';

export interface EmptyStateProps {
  icon?: React.ReactNode;
  title: string;
  description: string;
  actionLabel?: string;
  onAction?: () => void;
}

export const EmptyState: React.FC<EmptyStateProps> = ({
  icon,
  title,
  description,
  actionLabel,
  onAction,
}) => {
  return (
    <div
      style={{
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        padding: '48px 24px',
        textAlign: 'center',
        border: '1px dashed var(--border-default)',
        borderRadius: 'var(--radius-lg)',
        backgroundColor: 'var(--bg-surface-subtle)',
      }}
    >
      {icon && (
        <div style={{ fontSize: '32px', marginBottom: '16px', color: 'var(--text-muted)' }}>
          {icon}
        </div>
      )}
      <h3 style={{ fontSize: '16px', fontWeight: 600, color: 'var(--text-primary)' }}>
        {title}
      </h3>
      <p
        style={{
          fontSize: '13px',
          color: 'var(--text-muted)',
          maxWidth: '400px',
          marginTop: '6px',
          marginBottom: actionLabel ? '20px' : '0',
        }}
      >
        {description}
      </p>
      {actionLabel && onAction && (
        <Button variant="primary" size="sm" onClick={onAction}>
          {actionLabel}
        </Button>
      )}
    </div>
  );
};
