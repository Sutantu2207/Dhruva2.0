import React from 'react';

export interface InputProps extends React.InputHTMLAttributes<HTMLInputElement> {
  label?: string;
  error?: string;
  helperText?: string;
}

export const Input = React.forwardRef<HTMLInputElement, InputProps>(
  ({ label, error, helperText, id, style, ...props }, ref) => {
    const inputId = id || (label ? label.toLowerCase().replace(/\s+/g, '-') : undefined);

    return (
      <div style={{ display: 'flex', flexDirection: 'column', gap: '6px', width: '100%' }}>
        {label && (
          <label
            htmlFor={inputId}
            style={{
              fontSize: '13px',
              fontWeight: 500,
              color: 'var(--text-secondary)',
            }}
          >
            {label}
          </label>
        )}
        <input
          id={inputId}
          ref={ref}
          style={{
            width: '100%',
            padding: '9px 12px',
            borderRadius: 'var(--radius-md)',
            backgroundColor: 'var(--bg-surface)',
            color: 'var(--text-primary)',
            border: `1px solid ${error ? 'var(--status-danger)' : 'var(--border-default)'}`,
            fontSize: '14px',
            transition: 'border-color 0.15s ease, box-shadow 0.15s ease',
            ...style,
          }}
          {...props}
        />
        {error && (
          <span style={{ fontSize: '12px', color: 'var(--status-danger)', fontWeight: 400 }}>
            {error}
          </span>
        )}
        {helperText && !error && (
          <span style={{ fontSize: '12px', color: 'var(--text-muted)' }}>
            {helperText}
          </span>
        )}
      </div>
    );
  }
);

Input.displayName = 'Input';
