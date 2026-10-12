'use client';

import React, { useState } from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/lib/auth/AuthContext';
import { Alert } from '@/components/ui/Alert';
import { Button } from '@/components/ui/Button';
import { Card } from '@/components/ui/Card';
import { Input } from '@/components/ui/Input';

export default function LoginPage() {
  const router = useRouter();
  const { login, isLoading, error } = useAuth();

  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [formError, setFormError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setFormError(null);

    if (!email.trim() || !password.trim()) {
      setFormError('Please enter both your institutional email and password.');
      return;
    }

    try {
      await login(email, password);
      router.push('/workspace');
    } catch {
      // Error handled in AuthContext
    }
  };

  return (
    <div
      style={{
        minHeight: '100vh',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        backgroundColor: 'var(--bg-app)',
        padding: '24px',
      }}
    >
      <div style={{ width: '100%', maxWidth: '420px', display: 'flex', flexDirection: 'column', gap: '24px' }}>
        {/* Brand Header */}
        <div style={{ textAlign: 'center' }}>
          <div
            style={{
              display: 'inline-flex',
              alignItems: 'center',
              justifyContent: 'center',
              width: '44px',
              height: '44px',
              borderRadius: 'var(--radius-md)',
              backgroundColor: 'var(--brand-primary)',
              color: '#ffffff',
              fontSize: '20px',
              fontWeight: 800,
              marginBottom: '12px',
              boxShadow: 'var(--shadow-glow)',
            }}
          >
            D
          </div>
          <h1 style={{ fontSize: '22px', fontWeight: 700, color: 'var(--text-primary)', letterSpacing: '-0.02em' }}>
            Dhruva.AI
          </h1>
          <p style={{ fontSize: '13px', color: 'var(--text-secondary)', marginTop: '4px' }}>
            Institutional Learning Operating System
          </p>
        </div>

        {/* Login Card */}
        <Card elevation="raised">
          <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
            <div>
              <h2 style={{ fontSize: '16px', fontWeight: 600, color: 'var(--text-primary)' }}>
                Sign In
              </h2>
              <p style={{ fontSize: '12px', color: 'var(--text-muted)', marginTop: '2px' }}>
                Enter your institutional credentials to access your workspace.
              </p>
            </div>

            {(formError || error) && (
              <Alert variant="danger" title="Authentication Error">
                {formError || error}
              </Alert>
            )}

            <Input
              label="Institutional Email"
              type="email"
              placeholder="e.g. user@institution.edu"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              disabled={isLoading}
              required
              autoFocus
            />

            <Input
              label="Password"
              type="password"
              placeholder="••••••••••••"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              disabled={isLoading}
              required
            />

            <Button
              type="submit"
              variant="primary"
              size="md"
              isLoading={isLoading}
              style={{ width: '100%', marginTop: '8px' }}
            >
              Sign In to Workspace
            </Button>
          </form>
        </Card>

        {/* Security Footer Notice */}
        <div style={{ textAlign: 'center', fontSize: '11px', color: 'var(--text-muted)' }}>
          Strict Row-Level Security (RLS) & Multi-Tenant Isolation Enforced.
          <br />
          Unauthorized access attempts are monitored and recorded in the audit log.
        </div>
      </div>
    </div>
  );
}
