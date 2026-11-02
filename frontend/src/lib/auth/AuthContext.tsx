'use client';

/**
 * Dhruva.AI V2 — Authentication Context & Session Provider
 */

import React, { createContext, useCallback, useContext, useEffect, useState } from 'react';
import { api, ApiError } from '@/lib/api/client';
import { AuthState, Institution, LoginResponseData, RegisterData, User } from '@/types/auth';

interface AuthContextType extends AuthState {
  login: (email: string, password: string) => Promise<void>;
  register: (data: RegisterData) => Promise<void>;
  logout: () => Promise<void>;
  refreshProfile: () => Promise<void>;
  clearError: () => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [institution, setInstitution] = useState<Institution | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  const clearError = useCallback(() => {
    setError(null);
  }, []);

  const refreshProfile = useCallback(async () => {
    const token = api.getToken();
    if (!token) return;
    try {
      const userProfile = await api.get<User>('/auth/me');
      setUser(userProfile);
      if (typeof window !== 'undefined') {
        localStorage.setItem('dhruva_user', JSON.stringify(userProfile));
      }
    } catch {
      api.setToken(null);
      setUser(null);
      if (typeof window !== 'undefined') {
        localStorage.removeItem('dhruva_user');
      }
    }
  }, []);

  useEffect(() => {
    try {
      const stored = localStorage.getItem('dhruva_user');
      if (stored) {
        setUser(JSON.parse(stored));
      }
    } catch {
      // Ignore parse errors
    } finally {
      setIsLoading(false);
    }

    // Refresh profile with backend in background
    refreshProfile();
  }, [refreshProfile]);

  const login = async (email: string, password: string) => {
    setIsLoading(true);
    setError(null);
    try {
      const result = await api.post<LoginResponseData>('/auth/login', { email, password });
      api.setToken(result.access_token);
      setUser(result.user);
      if (typeof window !== 'undefined') {
        localStorage.setItem('dhruva_user', JSON.stringify(result.user));
      }
    } catch (err) {
      if (err instanceof ApiError) {
        setError(err.message);
      } else {
        setError('Authentication failed. Please check your network connection.');
      }
      throw err;
    } finally {
      setIsLoading(false);
    }
  };

  const register = async (data: RegisterData) => {
    setIsLoading(true);
    setError(null);
    try {
      const result = await api.post<LoginResponseData>('/auth/register', data);
      api.setToken(result.access_token);
      setUser(result.user);
      if (typeof window !== 'undefined') {
        localStorage.setItem('dhruva_user', JSON.stringify(result.user));
      }
    } catch (err) {
      if (err instanceof ApiError) {
        setError(err.message);
      } else {
        setError('Registration failed. Please check your network connection.');
      }
      throw err;
    } finally {
      setIsLoading(false);
    }
  };

  const logout = async () => {
    try {
      await api.post('/auth/logout');
    } catch {
      // Ignore network failure on logout
    } finally {
      api.setToken(null);
      setUser(null);
      setInstitution(null);
      if (typeof window !== 'undefined') {
        localStorage.removeItem('dhruva_user');
        localStorage.removeItem('dhruva_token');
        sessionStorage.clear();
      }
    }
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        institution,
        isAuthenticated: !!user,
        isLoading,
        error,
        login,
        register,
        logout,
        refreshProfile,
        clearError,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}
