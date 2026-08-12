import {
  createContext,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from 'react';

import {
  api,
} from '../lib/api';

import type {
  UserProfile,
} from '../lib/types';


// =====================================================
// LOGIN RESULT
// =====================================================

/**
 * The login function has three possible successful
 * outcomes.
 *
 * authenticated:
 *     Standard USER without MFA, or any fully
 *     authenticated account.
 *
 * mfa_required:
 *     Account already has MFA enabled and must provide
 *     TOTP/recovery code.
 *
 * mfa_setup_required:
 *     CLINICIAN or ADMINISTRATOR has correct password but
 *     has not yet configured mandatory MFA.
 */
export type LoginResult =
  | {
    status:
    'authenticated';
  }

  | {
    status:
    'mfa_required';

    challengeToken:
    string;
  }

  | {
    status:
    'mfa_setup_required';

    setupToken:
    string;
  };


// =====================================================
// CONTEXT INTERFACE
// =====================================================

interface AuthContextValue {
  user:
  UserProfile | null;

  loading:
  boolean;


  login(
    email: string,
    password: string,
  ): Promise<LoginResult>;


  completeMfa(
    challengeToken: string,
    code: string,
  ): Promise<void>;


  completeRequiredMfaSetup(
    setupToken: string,
    code: string,
  ): Promise<string[]>;


  refreshProfile():
    Promise<void>;


  logout():
    void;
}


// =====================================================
// CONTEXT
// =====================================================

const AuthContext =
  createContext<
    AuthContextValue
    | undefined
  >(
    undefined,
  );


// =====================================================
// PROVIDER
// =====================================================

export function AuthProvider(
  {
    children,
  }: {
    children: ReactNode;
  },
) {
  const [
    user,
    setUser,
  ] =
    useState<
      UserProfile | null
    >(
      null,
    );


  const [
    loading,
    setLoading,
  ] =
    useState(
      true,
    );


  // ===================================================
  // LOAD CURRENT USER
  // ===================================================

  async function refreshProfile():
    Promise<void> {
    try {
      const profile =
        await api.currentUser();

      setUser(
        profile,
      );
    } catch {
      // Invalid/expired local access token.
      sessionStorage.removeItem(
        'mediscope_access_token',
      );

      sessionStorage.removeItem(
        'mediscope_refresh_token',
      );

      setUser(
        null,
      );
    }
  }


  // ===================================================
  // INITIAL SESSION RESTORATION
  // ===================================================

  useEffect(
    () => {
      const token =
        sessionStorage.getItem(
          'mediscope_access_token',
        );

      if (!token) {
        setLoading(
          false,
        );

        return;
      }

      refreshProfile()
        .finally(
          () =>
            setLoading(
              false,
            ),
        );
    },
    [],
  );


  // ===================================================
  // PASSWORD LOGIN
  // ===================================================

  async function login(
    email: string,
    password: string,
  ): Promise<LoginResult> {
    const response =
      await api.login(
        email,
        password,
      );


    // -------------------------------------------------
    // PRIVILEGED ROLE REQUIRES FIRST-TIME MFA SETUP
    // -------------------------------------------------

    if (
      response.mfa_setup_required
      === true
    ) {
      const setupToken =
        response.mfa_setup_token;

      if (
        typeof setupToken
        !== 'string'
        ||
        !setupToken
      ) {
        throw new Error(
          'The backend requested MFA setup but did not return a setup token.',
        );
      }

      return {
        status:
          'mfa_setup_required',

        setupToken,
      };
    }


    // -------------------------------------------------
    // ACCOUNT ALREADY HAS MFA ENABLED
    // -------------------------------------------------

    if (
      response.mfa_required
      === true
    ) {
      const challengeToken =
        response.mfa_challenge_token;

      if (
        typeof challengeToken
        !== 'string'
        ||
        !challengeToken
      ) {
        throw new Error(
          'The backend requested MFA but did not return a challenge token.',
        );
      }

      return {
        status:
          'mfa_required',

        challengeToken,
      };
    }


    // -------------------------------------------------
    // NORMAL TOKEN RESPONSE
    // -------------------------------------------------

    const accessToken =
      response.access_token;

    const refreshToken =
      response.refresh_token;


    if (
      typeof accessToken
      !== 'string'
      ||
      !accessToken
    ) {
      throw new Error(
        'Authentication succeeded but no access token was returned.',
      );
    }


    sessionStorage.setItem(
      'mediscope_access_token',
      accessToken,
    );


    if (
      typeof refreshToken
      === 'string'
      &&
      refreshToken
    ) {
      sessionStorage.setItem(
        'mediscope_refresh_token',
        refreshToken,
      );
    }


    await refreshProfile();


    return {
      status:
        'authenticated',
    };
  }


  // ===================================================
  // COMPLETE EXISTING MFA LOGIN
  // ===================================================

  async function completeMfa(
    challengeToken: string,
    code: string,
  ): Promise<void> {
    const response =
      await api.completeMfa(
        challengeToken,
        code,
      );


    sessionStorage.setItem(
      'mediscope_access_token',
      response.access_token,
    );


    sessionStorage.setItem(
      'mediscope_refresh_token',
      response.refresh_token,
    );


    await refreshProfile();
  }


  // ===================================================
  // COMPLETE PRIVILEGED MFA ENROLMENT
  // ===================================================

  async function completeRequiredMfaSetup(
    setupToken: string,
    code: string,
  ): Promise<string[]> {
    const response =
      await api.confirmRequiredMfaSetup(
        setupToken,
        code,
      );


    sessionStorage.setItem(
      'mediscope_access_token',
      response.access_token,
    );


    sessionStorage.setItem(
      'mediscope_refresh_token',
      response.refresh_token,
    );


    await refreshProfile();


    return (
      response.recovery_codes
    );
  }


  // ===================================================
  // LOGOUT
  // ===================================================

  function logout():
    void {
    sessionStorage.removeItem(
      'mediscope_access_token',
    );

    sessionStorage.removeItem(
      'mediscope_refresh_token',
    );

    setUser(
      null,
    );
  }


  // ===================================================
  // CONTEXT VALUE
  // ===================================================

  const value =
    useMemo<
      AuthContextValue
    >(
      () => ({
        user,

        loading,

        login,

        completeMfa,

        completeRequiredMfaSetup,

        refreshProfile,

        logout,
      }),
      [
        user,
        loading,
      ],
    );


  return (
    <AuthContext.Provider
      value={value}
    >
      {children}
    </AuthContext.Provider>
  );
}


// =====================================================
// AUTH CONTEXT HOOK
// =====================================================

export function useAuth():
  AuthContextValue {
  const context =
    useContext(
      AuthContext,
    );

  if (!context) {
    throw new Error(
      'useAuth must be used within AuthProvider.',
    );
  }

  return context;
}
