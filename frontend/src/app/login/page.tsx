'use client';

import React, { useEffect, useState } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/lib/auth/AuthContext';
import { Alert } from '@/components/ui/Alert';
import { Button } from '@/components/ui/Button';
import { Card } from '@/components/ui/Card';
import { Input } from '@/components/ui/Input';

export default function LoginPage() {
  const router = useRouter();
  const { login, error, clearError } = useAuth();

  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [formError, setFormError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setFormError(null);
    clearError();

    const cleanEmail = email.trim();
    const cleanPassword = password.trim();

    if (!cleanEmail || !cleanPassword) {
      setFormError('Please enter both your institutional email and password.');
      return;
    }

    try {
      setIsSubmitting(true);
      await login(cleanEmail, cleanPassword);
      window.location.href = '/workspace';
    } catch (err: any) {
      console.error('Sign-in error:', err);
      const msg = err?.message || 'Authentication failed. Please check your credentials or network connection.';
      setFormError(msg);
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div
      style={{
        minHeight: '100vh',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        backgroundColor: 'transparent',
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
              disabled={isSubmitting}
              required
              autoFocus
            />

            <Input
              label="Password"
              type="password"
              placeholder="••••••••••••"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              disabled={isSubmitting}
              required
            />

            <Button
              type="submit"
              variant="primary"
              size="md"
              isLoading={isSubmitting}
              disabled={isSubmitting}
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
            padding: '16px',
            borderRadius: 'var(--radius-md)',
            backgroundColor: 'var(--bg-surface)',
            border: '1px solid var(--border-subtle)',
            boxShadow: 'var(--shadow-sm)',
            fontSize: '12px',
          }}
        >
          <div style={{ color: 'var(--text-secondary)', marginBottom: '10px', fontWeight: 600, fontSize: '12px' }}>
            Quick Role-Segregated Sign-In:
          </div>
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: '8px' }}>
            <button
              type="button"
              onClick={() => {
                setEmail('rahul.k@iitb.ac.in');
                setPassword('SecurePass123!');
              }}
              style={{
                background: email === 'rahul.k@iitb.ac.in' ? 'var(--brand-primary-subtle)' : 'var(--bg-surface-subtle)',
                border: email === 'rahul.k@iitb.ac.in' ? '1px solid var(--brand-primary)' : '1px solid var(--border-subtle)',
                borderRadius: '6px',
                padding: '6px 10px',
                fontSize: '12px',
                fontWeight: 500,
                color: email === 'rahul.k@iitb.ac.in' ? 'var(--brand-primary)' : 'var(--text-primary)',
                cursor: 'pointer',
                display: 'inline-flex',
                alignItems: 'center',
                gap: '6px',
              }}
            >
              🎓 Student (Rahul K.)
            </button>
            <button
              type="button"
              onClick={() => {
                setEmail('prof.verma@iitb.ac.in');
                setPassword('SecurePass123!');
              }}
              style={{
                background: email === 'prof.verma@iitb.ac.in' ? 'var(--brand-primary-subtle)' : 'var(--bg-surface-subtle)',
                border: email === 'prof.verma@iitb.ac.in' ? '1px solid var(--brand-primary)' : '1px solid var(--border-subtle)',
                borderRadius: '6px',
                padding: '6px 10px',
                fontSize: '12px',
                fontWeight: 500,
                color: email === 'prof.verma@iitb.ac.in' ? 'var(--brand-primary)' : 'var(--text-primary)',
                cursor: 'pointer',
                display: 'inline-flex',
                alignItems: 'center',
                gap: '6px',
              }}
            >
              👨‍🏫 Faculty (Prof. Verma)
            </button>
            <button
              type="button"
              onClick={() => {
                setEmail('hod.cse@iitb.ac.in');
                setPassword('SecurePass123!');
              }}
              style={{
                background: email === 'hod.cse@iitb.ac.in' ? 'var(--brand-primary-subtle)' : 'var(--bg-surface-subtle)',
                border: email === 'hod.cse@iitb.ac.in' ? '1px solid var(--brand-primary)' : '1px solid var(--border-subtle)',
                borderRadius: '6px',
                padding: '6px 10px',
                fontSize: '12px',
                fontWeight: 500,
                color: email === 'hod.cse@iitb.ac.in' ? 'var(--brand-primary)' : 'var(--text-primary)',
                cursor: 'pointer',
                display: 'inline-flex',
                alignItems: 'center',
                gap: '6px',
              }}
            >
              🏛️ HOD (Anita Desai)
            </button>
            <button
              type="button"
              onClick={() => {
                setEmail('placement@iitb.ac.in');
                setPassword('SecurePass123!');
              }}
              style={{
                background: email === 'placement@iitb.ac.in' ? 'var(--brand-primary-subtle)' : 'var(--bg-surface-subtle)',
                border: email === 'placement@iitb.ac.in' ? '1px solid var(--brand-primary)' : '1px solid var(--border-subtle)',
                borderRadius: '6px',
                padding: '6px 10px',
                fontSize: '12px',
                fontWeight: 500,
                color: email === 'placement@iitb.ac.in' ? 'var(--brand-primary)' : 'var(--text-primary)',
                cursor: 'pointer',
                display: 'inline-flex',
                alignItems: 'center',
                gap: '6px',
              }}
            >
              💼 Placement (Sneha K.)
            </button>
            <button
              type="button"
              onClick={() => {
                setEmail('admin@iitb.ac.in');
                setPassword('SecurePass123!');
              }}
              style={{
                background: email === 'admin@iitb.ac.in' ? 'var(--brand-primary-subtle)' : 'var(--bg-surface-subtle)',
                border: email === 'admin@iitb.ac.in' ? '1px solid var(--brand-primary)' : '1px solid var(--border-subtle)',
                borderRadius: '6px',
                padding: '6px 10px',
                fontSize: '12px',
                fontWeight: 500,
                color: email === 'admin@iitb.ac.in' ? 'var(--brand-primary)' : 'var(--text-primary)',
                cursor: 'pointer',
                display: 'inline-flex',
                alignItems: 'center',
                gap: '6px',
              }}
            >
              🏢 Admin (IITB)
            </button>
            <button
              type="button"
              onClick={() => {
                setEmail('superadmin@dhruva.ai');
                setPassword('SecurePass123!');
              }}
              style={{
                background: email === 'superadmin@dhruva.ai' ? 'var(--brand-primary-subtle)' : 'var(--bg-surface-subtle)',
                border: email === 'superadmin@dhruva.ai' ? '1px solid var(--brand-primary)' : '1px solid var(--border-subtle)',
                borderRadius: '6px',
                padding: '6px 10px',
                fontSize: '12px',
                fontWeight: 500,
                color: email === 'superadmin@dhruva.ai' ? 'var(--brand-primary)' : 'var(--text-primary)',
                cursor: 'pointer',
                display: 'inline-flex',
                alignItems: 'center',
                gap: '6px',
              }}
            >
              ⚡ Super Admin
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
