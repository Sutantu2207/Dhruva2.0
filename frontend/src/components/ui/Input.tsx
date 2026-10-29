import React, { useState } from 'react';

export interface InputProps extends React.InputHTMLAttributes<HTMLInputElement> {
  label?: string;
  error?: string;
  helperText?: string;
}

export const Input = React.forwardRef<HTMLInputElement, InputProps>(
  ({ label, error, helperText, id, style, onFocus, onBlur, ...props }, ref) => {
    const [isFocused, setIsFocused] = useState(false);
    const inputId = id || (label ? label.toLowerCase().replace(/\s+/g, '-') : undefined);

    const handleFocus = (e: React.FocusEvent<HTMLInputElement>) => {
      setIsFocused(true);
      onFocus?.(e);
    };

    const handleBlur = (e: React.FocusEvent<HTMLInputElement>) => {
      setIsFocused(false);
      onBlur?.(e);
    };

    return (
      <div style={{ display: 'flex', flexDirection: 'column', gap: '6px', width: '100%' }}>
        {label && (
          <label
            htmlFor={inputId}
            style={{
              fontSize: '13px',
              fontWeight: 500,
              color: isFocused ? 'var(--brand-primary)' : 'var(--text-secondary)',
              transition: 'color 0.15s ease',
            }}
          >
            {label}
          </label>
        )}
        <input
          id={inputId}
          ref={ref}
          aria-invalid={Boolean(error)}
          aria-describedby={
            error && inputId
              ? `${inputId}-error`
              : helperText && inputId
              ? `${inputId}-helper`
              : undefined
          }
          onFocus={handleFocus}
          onBlur={handleBlur}
          style={{
            width: '100%',
            padding: '9px 12px',
            borderRadius: 'var(--radius-md)',
            backgroundColor: '#ffffff',
            color: 'var(--text-primary)',
            border: `1px solid ${
              error
                ? 'var(--status-danger)'
                : isFocused
                ? 'var(--brand-primary)'
                : 'var(--border-default)'
            }`,
            fontSize: '14px',
            outline: 'none',
            boxShadow: isFocused
              ? error
                ? '0 0 0 2px var(--bg-app), 0 0 0 4px rgba(220, 38, 38, 0.20)'
                : '0 0 0 2px var(--bg-app), 0 0 0 4px rgba(139, 92, 246, 0.20)'
              : 'none',
            transition: 'border-color 0.15s ease, box-shadow 0.15s ease',
            ...style,
          }}
          {...props}
        />
        {error && (
          <span
            id={inputId ? `${inputId}-error` : undefined}
            role="alert"
            aria-live="polite"
            style={{ fontSize: '12px', color: 'var(--status-danger)', fontWeight: 500 }}
          >
            {error}
          </span>
        )}
        {helperText && !error && (
          <span
            id={inputId ? `${inputId}-helper` : undefined}
            style={{ fontSize: '12px', color: 'var(--text-muted)' }}
          >
            {helperText}
          </span>
        )}
      </div>
    );
  }
);

Input.displayName = 'Input';
