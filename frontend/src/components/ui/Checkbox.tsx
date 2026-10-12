import React from 'react';

export interface CheckboxProps extends Omit<React.InputHTMLAttributes<HTMLInputElement>, 'type'> {
  label?: string;
  description?: string;
}

export const Checkbox: React.FC<CheckboxProps> = ({
  label,
  description,
  id,
  style,
  ...props
}) => {
  const checkboxId = id || (label ? label.toLowerCase().replace(/\s+/g, '-') : undefined);

  return (
    <div style={{ display: 'flex', alignItems: 'flex-start', gap: '8px' }}>
      <input
        type="checkbox"
        id={checkboxId}
        style={{
          width: '16px',
          height: '16px',
          marginTop: '2px',
          accentColor: 'var(--brand-primary)',
          cursor: 'pointer',
          ...style,
        }}
        {...props}
      />
      {(label || description) && (
        <div style={{ display: 'flex', flexDirection: 'column' }}>
          {label && (
            <label
              htmlFor={checkboxId}
              style={{
                fontSize: '13px',
                fontWeight: 500,
                color: 'var(--text-primary)',
                cursor: 'pointer',
              }}
            >
              {label}
            </label>
          )}
          {description && (
            <span style={{ fontSize: '12px', color: 'var(--text-muted)' }}>
              {description}
            </span>
          )}
        </div>
      )}
    </div>
  );
};
