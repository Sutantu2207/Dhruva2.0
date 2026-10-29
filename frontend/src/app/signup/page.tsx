'use client';

import React, { useEffect, useState } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/lib/auth/AuthContext';
import { api } from '@/lib/api/client';
import { Alert } from '@/components/ui/Alert';
import { Button } from '@/components/ui/Button';
import { Card } from '@/components/ui/Card';
import { Input } from '@/components/ui/Input';
import { Select, SelectOption } from '@/components/ui/Select';
import { SystemRole } from '@/types/auth';

interface InstitutionItem {
  id: string;
  slug: string;
  legal_name: string;
}

export default function SignupPage() {
  const router = useRouter();
  const { register, isLoading, error } = useAuth();

  const [firstName, setFirstName] = useState('');
  const [lastName, setLastName] = useState('');
  const [email, setEmail] = useState('');
  const [phone, setPhone] = useState('');
  const [role, setRole] = useState<SystemRole>('STUDENT');
  const [institutionSlug, setInstitutionSlug] = useState('iit-bombay');
  const [institutionOptions, setInstitutionOptions] = useState<SelectOption[]>([
    { value: 'iit-bombay', label: 'IIT Bombay (iitb.ac.in)' },
    { value: 'bits-pilani', label: 'BITS Pilani (bits-pilani.ac.in)' },
  ]);
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [formError, setFormError] = useState<string | null>(null);

  useEffect(() => {
    let isMounted = true;
    api
      .get<InstitutionItem[]>('/auth/institutions')
      .then((items) => {
        if (isMounted && Array.isArray(items) && items.length > 0) {
          const opts = items.map((i) => ({
            value: i.slug,
            label: i.legal_name,
          }));
          setInstitutionOptions(opts);
          setInstitutionSlug(opts[0].value);
        }
      })
      .catch(() => {
        // Fall back to default options
      });
    return () => {
      isMounted = false;
    };
  }, []);

  const roleOptions: SelectOption[] = [
    { value: 'STUDENT', label: 'Student (Learner & Assessment Taker)' },
    { value: 'FACULTY', label: 'Faculty / Professor (Curriculum & Evaluation)' },
  ];

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setFormError(null);

    if (!firstName.trim() || !lastName.trim()) {
      setFormError('Please enter both your first and last name.');
      return;
    }

    if (!email.trim()) {
      setFormError('Please enter your institutional email.');
      return;
    }

    if (password.length < 8) {
      setFormError('Password must be at least 8 characters long.');
      return;
    }

    if (password !== confirmPassword) {
      setFormError('Passwords do not match. Please re-enter your password.');
      return;
    }

    try {
      await register({
        first_name: firstName.trim(),
        last_name: lastName.trim(),
        email: email.trim(),
        phone: phone.trim() || undefined,
        role,
        institution_slug: institutionSlug,
        password,
      });
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
        padding: '32px 16px',
      }}
    >
      <div style={{ width: '100%', maxWidth: '460px', display: 'flex', flexDirection: 'column', gap: '20px' }}>
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
              marginBottom: '10px',
              boxShadow: '0 4px 14px rgba(139, 92, 246, 0.25)',
            }}
          >
            D
          </div>
          <h1 style={{ fontSize: '22px', fontWeight: 700, color: 'var(--text-primary)', letterSpacing: '-0.02em' }}>
            Dhruva.AI
          </h1>
          <p style={{ fontSize: '13px', color: 'var(--text-secondary)', marginTop: '2px' }}>
            Institutional Learning Operating System
          </p>
        </div>

        {/* Signup Card */}
        <Card elevation="raised">
          <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
            <div>
              <h2 style={{ fontSize: '16px', fontWeight: 600, color: 'var(--text-primary)' }}>
                Create Your Account
              </h2>
              <p style={{ fontSize: '12px', color: 'var(--text-muted)', marginTop: '2px' }}>
                Join your institution&apos;s verified operating environment.
              </p>
            </div>

            {(formError || error) && (
              <Alert variant="danger" title="Registration Error">
                {formError || error}
              </Alert>
            )}

            {/* Name Grid */}
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px' }}>
              <Input
                label="First Name"
                placeholder="e.g. Rahul"
                value={firstName}
                onChange={(e) => setFirstName(e.target.value)}
                disabled={isLoading}
                required
                autoFocus
              />
              <Input
                label="Last Name"
                placeholder="e.g. Kumar"
                value={lastName}
                onChange={(e) => setLastName(e.target.value)}
                disabled={isLoading}
                required
              />
            </div>

            <Input
              label="Institutional Email"
              type="email"
              placeholder="e.g. student@iitb.ac.in"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              disabled={isLoading}
              required
            />

            {/* Institution & Role Grid */}
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px' }}>
              <Select
                label="Institution"
                options={institutionOptions}
                value={institutionSlug}
                onChange={(e) => setInstitutionSlug(e.target.value)}
                disabled={isLoading}
              />
              <Select
                label="Role"
                options={roleOptions}
                value={role}
                onChange={(e) => setRole(e.target.value as SystemRole)}
                disabled={isLoading}
              />
            </div>

            <Input
              label="Phone Number (Optional)"
              type="tel"
              placeholder="e.g. +91 98765 43210"
              value={phone}
              onChange={(e) => setPhone(e.target.value)}
              disabled={isLoading}
            />

            <Input
              label="Password"
              type="password"
              placeholder="Minimum 8 characters"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              disabled={isLoading}
              required
            />

            <Input
              label="Confirm Password"
              type="password"
              placeholder="Re-enter your password"
              value={confirmPassword}
              onChange={(e) => setConfirmPassword(e.target.value)}
              disabled={isLoading}
              required
            />

            <Button
              type="submit"
              variant="primary"
              size="md"
              isLoading={isLoading}
              style={{ width: '100%', marginTop: '6px' }}
            >
              Register &amp; Enter Workspace
            </Button>

            <div style={{ textAlign: 'center', marginTop: '6px', fontSize: '13px', color: 'var(--text-secondary)' }}>
              Already have an account?{' '}
              <Link href="/login" style={{ color: 'var(--brand-primary)', fontWeight: 600, textDecoration: 'none' }}>
                Sign In
              </Link>
            </div>
          </form>
        </Card>

        {/* Security Footer Notice */}
        <div style={{ textAlign: 'center', fontSize: '11px', color: 'var(--text-muted)' }}>
          Strict Row-Level Security (RLS) & Multi-Tenant Isolation Enforced.
        </div>
      </div>
    </div>
  );
}
