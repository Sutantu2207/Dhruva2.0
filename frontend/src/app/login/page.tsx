'use client';

import React, { useState } from 'react';
import Link from 'next/link';
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
      <div style={{ width: '100%', maxWidth: '400px', display: 'flex', flexDirection: 'column', gap: '24px' }}>
        {/* Brand Header */}
        <div style={{ textAlign: 'center' }}>
          <div
            style={{
              display: 'inline-flex',
              alignItems: 'center',
              justifyContent: 'center',
              width: '46px',
              height: '46px',
              borderRadius: 'var(--radius-md)',
              background: 'var(--brand-primary-gradient)',
              color: '#ffffff',
              fontSize: '22px',
              fontWeight: 800,
              marginBottom: '12px',
              boxShadow: '0 4px 14px rgba(139, 92, 246, 0.25)',
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
              style={{ width: '100%', marginTop: '4px' }}
            >
              Sign In to Workspace
            </Button>

            <div style={{ textAlign: 'center', marginTop: '6px', fontSize: '13px', color: 'var(--text-secondary)' }}>
              Don&apos;t have an account?{' '}
              <Link href="/signup" style={{ color: 'var(--brand-primary)', fontWeight: 600, textDecoration: 'none' }}>
                Sign Up
              </Link>
            </div>
          </form>
        </Card>

        {/* Quick Institutional Sign-In Shortcuts */}
        <div
          style={{
            padding: '12px 16px',
            borderRadius: 'var(--radius-md)',
            background: 'rgba(255, 255, 255, 0.04)',
            border: '1px solid var(--border-subtle)',
            fontSize: '12px',
          }}
        >
          <div style={{ color: 'var(--text-secondary)', marginBottom: '8px', fontWeight: 500 }}>
            Quick Institutional Sign-In:
          </div>
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: '6px' }}>
            <button
              type="button"
              onClick={() => {
                setEmail('admin@iitb.ac.in');
                setPassword('SecurePass123!');
              }}
              style={{
                background: 'rgba(255, 255, 255, 0.08)',
                border: '1px solid var(--border-subtle)',
                borderRadius: '6px',
                padding: '4px 8px',
                fontSize: '11px',
                color: 'var(--text-primary)',
                cursor: 'pointer',
              }}
            >
              Admin (IITB)
            </button>
            <button
              type="button"
              onClick={() => {
                setEmail('hod.cse@iitb.ac.in');
                setPassword('SecurePass123!');
              }}
              style={{
                background: 'rgba(255, 255, 255, 0.08)',
                border: '1px solid var(--border-subtle)',
                borderRadius: '6px',
                padding: '4px 8px',
                fontSize: '11px',
                color: 'var(--text-primary)',
                cursor: 'pointer',
              }}
            >
              HOD (Anita Desai)
            </button>
            <button
              type="button"
              onClick={() => {
                setEmail('prof.verma@iitb.ac.in');
                setPassword('SecurePass123!');
              }}
              style={{
                background: 'rgba(255, 255, 255, 0.08)',
                border: '1px solid var(--border-subtle)',
                borderRadius: '6px',
                padding: '4px 8px',
                fontSize: '11px',
                color: 'var(--text-primary)',
                cursor: 'pointer',
              }}
            >
              Faculty (Prof. Verma)
            </button>
            <button
              type="button"
              onClick={() => {
                setEmail('rahul.k@iitb.ac.in');
                setPassword('SecurePass123!');
              }}
              style={{
                background: 'rgba(255, 255, 255, 0.08)',
                border: '1px solid var(--border-subtle)',
                borderRadius: '6px',
                padding: '4px 8px',
                fontSize: '11px',
                color: 'var(--text-primary)',
                cursor: 'pointer',
              }}
            >
              Student (Rahul K.)
            </button>
            <button
              type="button"
              onClick={() => {
                setEmail('placement@iitb.ac.in');
                setPassword('SecurePass123!');
              }}
              style={{
                background: 'rgba(255, 255, 255, 0.08)',
                border: '1px solid var(--border-subtle)',
                borderRadius: '6px',
                padding: '4px 8px',
                fontSize: '11px',
                color: 'var(--text-primary)',
                cursor: 'pointer',
              }}
            >
              Placement (Sneha K.)
            </button>
            <button
              type="button"
              onClick={() => {
                setEmail('superadmin@dhruva.ai');
                setPassword('SecurePass123!');
              }}
              style={{
                background: 'rgba(255, 255, 255, 0.08)',
                border: '1px solid var(--border-subtle)',
                borderRadius: '6px',
                padding: '4px 8px',
                fontSize: '11px',
                color: 'var(--text-primary)',
                cursor: 'pointer',
              }}
            >
              Super Admin
            </button>
          </div>
        </div>

        {/* Security Footer Notice */}
        <div style={{ textAlign: 'center', fontSize: '11px', color: 'var(--text-muted)' }}>
          Strict Row-Level Security (RLS) & Multi-Tenant Isolation Enforced.
        </div>
      </div>
    </div>
  );
}
