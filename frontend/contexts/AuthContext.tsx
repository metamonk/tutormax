'use client';

import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import { apiClient } from '@/lib/api';
import type { User, LoginRequest, UserRole } from '@/lib/types';

interface AuthContextType {
  user: User | null;
  loading: boolean;
  error: string | null;
  isAuthenticated: boolean;
  login: (credentials: LoginRequest) => Promise<void>;
  logout: () => Promise<void>;
  refreshUser: () => Promise<void>;
  hasRole: (role: UserRole) => boolean;
  hasAnyRole: (roles: UserRole[]) => boolean;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

interface AuthProviderProps {
  children: ReactNode;
}

export const AuthProvider: React.FC<AuthProviderProps> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  // Load user on mount if token exists
  useEffect(() => {
    const initAuth = async () => {
      if (apiClient.isAuthenticated()) {
        try {
          const currentUser = await apiClient.getCurrentUser();
          setUser(currentUser);
        } catch (err) {
          console.error('Failed to load user:', err);
          apiClient.clearAuth();
        }
      }
      setLoading(false);
    };

    initAuth();
  }, []);

  const login = async (credentials: LoginRequest) => {
    try {
      setLoading(true);
      setError(null);
      await apiClient.login(credentials);
      const currentUser = await apiClient.getCurrentUser();
      setUser(currentUser);
    } catch (err: any) {
      const errorMessage = err.response?.data?.detail || 'Login failed';
      setError(errorMessage);
      throw new Error(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  const logout = async () => {
    try {
      setLoading(true);
      await apiClient.logout();
      setUser(null);
    } catch (err) {
      console.error('Logout error:', err);
    } finally {
      setLoading(false);
    }
  };

  const refreshUser = async () => {
    try {
      setLoading(true);
      const currentUser = await apiClient.getCurrentUser();
      setUser(currentUser);
    } catch (err) {
      console.error('Failed to refresh user:', err);
      setError('Failed to refresh user data');
    } finally {
      setLoading(false);
    }
  };

  const hasRole = (role: UserRole): boolean => {
    if (!user) return false;
    return user.roles.includes(role) || user.is_superuser;
  };

  const hasAnyRole = (roles: UserRole[]): boolean => {
    if (!user) return false;
    if (user.is_superuser) return true;
    return roles.some(role => user.roles.includes(role));
  };

  const value: AuthContextType = {
    user,
    loading,
    error,
    isAuthenticated: !!user,
    login,
    logout,
    refreshUser,
    hasRole,
    hasAnyRole,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};

// Custom hook to use auth context
export const useAuth = (): AuthContextType => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

// HOC for protecting routes based on roles
interface RequireRoleProps {
  roles: UserRole[];
  children: ReactNode;
  fallback?: ReactNode;
}

export const RequireRole: React.FC<RequireRoleProps> = ({
  roles,
  children,
  fallback = <div>Access denied. You don&apos;t have permission to view this content.</div>
}) => {
  const { hasAnyRole, loading } = useAuth();

  if (loading) {
    return <div>Loading...</div>;
  }

  if (!hasAnyRole(roles)) {
    return <>{fallback}</>;
  }

  return <>{children}</>;
};
