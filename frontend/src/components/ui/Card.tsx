import React from 'react';

export interface CardProps extends React.HTMLAttributes<HTMLDivElement> {
  children: React.ReactNode;
  title?: string;
  subtitle?: string;
  action?: React.ReactNode;
  elevation?: 'flat' | 'raised';
}

export const Card: React.FC<CardProps> = ({
  children,
  title,
  subtitle,
  action,
  elevation = 'flat',
  style,
  ...props
}) => {
  return (
    <div
      style={{
        backgroundColor: elevation === 'raised' ? 'var(--bg-surface-elevated)' : 'var(--bg-surface)',
        border: '1px solid var(--border-subtle)',
        borderRadius: 'var(--radius-lg)',
        boxShadow: elevation === 'raised' ? 'var(--shadow-md)' : 'var(--shadow-sm)',
        padding: '20px',
        display: 'flex',
        flexDirection: 'column',
        gap: '16px',
        ...style,
      }}
      {...props}
    >
      {(title || subtitle || action) && (
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
          <div>
            {title && (
              <h3 style={{ fontSize: '15px', fontWeight: 600, color: 'var(--text-primary)' }}>
                {title}
              </h3>
            )}
            {subtitle && (
              <p style={{ fontSize: '12px', color: 'var(--text-muted)', marginTop: '2px' }}>
                {subtitle}
              </p>
            )}
          </div>
          {action && <div>{action}</div>}
        </div>
      )}
      <div>{children}</div>
    </div>
  );
};
