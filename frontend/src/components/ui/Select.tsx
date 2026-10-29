import React, { useState } from 'react';

export interface SelectOption {
  value: string;
  label: string;
  disabled?: boolean;
}

export interface SelectProps extends React.SelectHTMLAttributes<HTMLSelectElement> {
  label?: string;
  error?: string;
  options: SelectOption[];
}

export const Select: React.FC<SelectProps> = ({
  label,
  error,
  options,
  id,
  style,
  onFocus,
  onBlur,
  ...props
}) => {
  const [isFocused, setIsFocused] = useState(false);
  const selectId = id || (label ? label.toLowerCase().replace(/\s+/g, '-') : undefined);

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '6px', width: '100%' }}>
      {label && (
        <label
          htmlFor={selectId}
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
      <select
        id={selectId}
        onFocus={(e) => {
          setIsFocused(true);
          onFocus?.(e);
        }}
        onBlur={(e) => {
          setIsFocused(false);
          onBlur?.(e);
        }}
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
      >
        {options.map((opt) => (
          <option
            key={opt.value}
            value={opt.value}
            disabled={opt.disabled}
            style={{ backgroundColor: '#ffffff', color: '#1e1135' }}
          >
            {opt.label}
          </option>
        ))}
      </select>
      {error && (
        <span style={{ fontSize: '12px', color: 'var(--status-danger)', fontWeight: 500 }}>
          {error}
        </span>
      )}
    </div>
  );
};
