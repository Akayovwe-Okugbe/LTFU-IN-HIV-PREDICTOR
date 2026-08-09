import { createContext, useContext, useEffect, useMemo, useState, type ReactNode } from 'react';
import { api } from '../lib/api';
import type { UserProfile } from '../lib/types';

type LoginResult = { mfaRequired: boolean; challengeToken?: string };

interface AuthContextValue {
  user: UserProfile | null;
  loading: boolean;
  login(email: string, password: string): Promise<LoginResult>;
  completeMfa(challengeToken: string, code: string): Promise<void>;
  logout(): void;
  refreshProfile(): Promise<void>;
}

const AuthContext = createContext<AuthContextValue | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<UserProfile | null>(null);
  const [loading, setLoading] = useState(true);

  async function refreshProfile() {
    try {
      setUser(await api.currentUser());
    } catch {
      sessionStorage.removeItem('mediscope_access_token');
      sessionStorage.removeItem('mediscope_refresh_token');
      setUser(null);
    }
  }

  useEffect(() => {
    const token = sessionStorage.getItem('mediscope_access_token');
    if (!token) { setLoading(false); return; }
    refreshProfile().finally(() => setLoading(false));
  }, []);

  async function login(email: string, password: string): Promise<LoginResult> {
    const response = await api.login(email, password);
    if (response.mfa_required === true) {
      return { mfaRequired: true, challengeToken: String(response.mfa_challenge_token) };
    }
    sessionStorage.setItem('mediscope_access_token', String(response.access_token));
    if (response.refresh_token) sessionStorage.setItem('mediscope_refresh_token', String(response.refresh_token));
    await refreshProfile();
    return { mfaRequired: false };
  }

  async function completeMfa(challengeToken: string, code: string) {
    const response = await api.completeMfa(challengeToken, code);
    sessionStorage.setItem('mediscope_access_token', response.access_token);
    sessionStorage.setItem('mediscope_refresh_token', response.refresh_token);
    await refreshProfile();
  }

  function logout() {
    sessionStorage.removeItem('mediscope_access_token');
    sessionStorage.removeItem('mediscope_refresh_token');
    setUser(null);
  }

  const value = useMemo(() => ({ user, loading, login, completeMfa, logout, refreshProfile }), [user, loading]);
  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) throw new Error('useAuth must be used within AuthProvider.');
  return context;
}
