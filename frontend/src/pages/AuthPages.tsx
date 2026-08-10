import {
  useEffect,
  useMemo,
  useState,
  type FormEvent,
  type ReactNode,
} from 'react';

import {
  ArrowLeft,
  ArrowRight,
  CheckCircle2,
  LockKeyhole,
  MailCheck,
  RefreshCw,
  ShieldCheck,
} from 'lucide-react';

import {
  Link,
  useLocation,
  useNavigate,
  useSearchParams,
} from 'react-router-dom';

import { Brand } from '../components/Brand';
import { useAuth } from '../context/AuthContext';
import {
  ApiError,
  api,
} from '../lib/api';


type RegistrationLocationState = {
  email?: string;
};


function AuthLayout(
  {
    title,
    subtitle,
    children,
  }: {
    title: string;
    subtitle: string;
    children: ReactNode;
  },
) {
  return (
    <div className="auth-page">
      <div className="auth-art">
        <Link
          to="/"
          className="back-link"
        >
          <ArrowLeft size={16} />
          Back home
        </Link>

        <Brand />

        <div className="auth-art-copy">
          <span className="pill">
            Secure clinical workspace
          </span>

          <h2>
            Human-centred intelligence for continuity of care.
          </h2>

          <p>
            Protected by role-based access, MFA, audit logging,
            and synthetic-data controls.
          </p>
        </div>
      </div>

      <div className="auth-panel">
        <div className="auth-form-wrap">
          <h1>{title}</h1>
          <p>{subtitle}</p>

          {children}
        </div>
      </div>
    </div>
  );
}


/**
 * Login page.
 *
 * A pending/unverified account is intentionally prevented
 * from authenticating by the backend. When the backend
 * returns that state, the UI guides the user to the email
 * verification screen rather than presenting a generic
 * dead end.
 */
export function LoginPage() {
  const {
    login,
    completeMfa,
  } = useAuth();

  const navigate = useNavigate();

  const [email, setEmail] =
    useState('');

  const [password, setPassword] =
    useState('');

  const [challenge, setChallenge] =
    useState('');

  const [code, setCode] =
    useState('');

  const [error, setError] =
    useState('');

  const [needsVerification, setNeedsVerification] =
    useState(false);

  const [busy, setBusy] =
    useState(false);


  async function submit(
    event: FormEvent,
  ) {
    event.preventDefault();

    setError('');
    setNeedsVerification(false);
    setBusy(true);

    try {
      if (challenge) {
        await completeMfa(
          challenge,
          code,
        );

        navigate('/app');
        return;
      }

      const result =
        await login(
          email,
          password,
        );

      if (
        result.mfaRequired &&
        result.challengeToken
      ) {
        setChallenge(
          result.challengeToken,
        );
      } else {
        navigate('/app');
      }
    } catch (errorValue) {
      const message =
        errorValue instanceof Error
          ? errorValue.message
          : 'Unable to sign in.';

      setError(message);

      // The backend currently returns a 403 when an
      // account exists but still requires verification
      // or activation.
      if (
        errorValue instanceof ApiError &&
        errorValue.status === 403
      ) {
        setNeedsVerification(true);
      }
    } finally {
      setBusy(false);
    }
  }


  return (
    <AuthLayout
      title={
        challenge
          ? 'Verify your identity'
          : 'Welcome back'
      }
      subtitle={
        challenge
          ? 'Enter the current code from your authenticator app.'
          : 'Sign in to your MEDISCOPE workspace.'
      }
    >
      <form
        className="auth-form"
        onSubmit={submit}
      >
        {!challenge && (
          <>
            <label>
              Email
              <input
                type="email"
                value={email}
                onChange={
                  (event) =>
                    setEmail(
                      event.target.value,
                    )
                }
                required
                autoComplete="email"
                placeholder="clinician@example.com"
              />
            </label>

            <label>
              Password
              <input
                type="password"
                value={password}
                onChange={
                  (event) =>
                    setPassword(
                      event.target.value,
                    )
                }
                required
                autoComplete="current-password"
                placeholder="••••••••••••"
              />
            </label>

            <div className="form-row">
              <span className="micro-copy">
                Protected sign-in
              </span>

              <Link to="/forgot-password">
                Forgot password?
              </Link>
            </div>
          </>
        )}

        {challenge && (
          <label>
            Authenticator or recovery code
            <input
              value={code}
              onChange={
                (event) =>
                  setCode(
                    event.target.value,
                  )
              }
              required
              maxLength={100}
              autoComplete="one-time-code"
              placeholder="6-digit code"
            />
          </label>
        )}

        {error && (
          <div className="form-error">
            {error}
          </div>
        )}

        {needsVerification && (
          <div className="verification-callout">
            <MailCheck size={20} />

            <div>
              <strong>
                Verification may still be required
              </strong>

              <span>
                Open the email verification page to enter your
                code or request a replacement.
              </span>
            </div>

            <button
              type="button"
              className="button ghost small"
              onClick={
                () =>
                  navigate(
                    `/verify-email?email=${encodeURIComponent(email)}`,
                  )
              }
            >
              Verify
            </button>
          </div>
        )}

        <button
          className="button primary wide"
          disabled={busy}
        >
          {
            busy
              ? 'Please wait…'
              : challenge
                ? 'Verify & continue'
                : 'Sign in'
          }

          <ArrowRight size={18} />
        </button>
      </form>

      {!challenge && (
        <p className="auth-switch">
          New to MEDISCOPE?{' '}
          <Link to="/register">
            Create an account
          </Link>
        </p>
      )}
    </AuthLayout>
  );
}


/**
 * Registration page.
 *
 * Security note:
 * The backend deliberately returns the same response for
 * a newly registered address and an address that may
 * already exist. This prevents attackers from testing
 * which email addresses have MEDISCOPE accounts.
 *
 * The UI therefore never displays:
 *     "This email is already registered."
 *
 * Instead, it sends the user to the verification journey
 * with safe sign-in/password-reset alternatives.
 */
export function RegisterPage() {
  const navigate = useNavigate();

  const [error, setError] =
    useState('');

  const [busy, setBusy] =
    useState(false);

  const [form, setForm] =
    useState({
      email: '',
      password: '',
      first_name: '',
      last_name: '',
      phone: '',
      gender: '',
    });


  async function submit(
    event: FormEvent,
  ) {
    event.preventDefault();

    setError('');
    setBusy(true);

    try {
      await api.register(
        form,
      );

      // The user is taken directly to verification.
      // We pass only the email address; no password or
      // sensitive registration data is placed in the URL.
      navigate(
        `/verify-email?email=${encodeURIComponent(form.email.trim().toLowerCase())}`,
        {
          state: {
            email:
              form.email
                .trim()
                .toLowerCase(),
          } satisfies RegistrationLocationState,
        },
      );
    } catch (errorValue) {
      setError(
        errorValue instanceof Error
          ? errorValue.message
          : 'Registration failed.',
      );
    } finally {
      setBusy(false);
    }
  }


  return (
    <AuthLayout
      title="Create your account"
      subtitle="Register securely. Email verification is required before your account can sign in."
    >
      <form
        className="auth-form"
        onSubmit={submit}
      >
        <div className="two-col">
          <label>
            First name
            <input
              required
              value={
                form.first_name
              }
              autoComplete="given-name"
              onChange={
                (event) =>
                  setForm({
                    ...form,
                    first_name:
                      event.target.value,
                  })
              }
            />
          </label>

          <label>
            Last name
            <input
              required
              value={
                form.last_name
              }
              autoComplete="family-name"
              onChange={
                (event) =>
                  setForm({
                    ...form,
                    last_name:
                      event.target.value,
                  })
              }
            />
          </label>
        </div>

        <label>
          Email
          <input
            type="email"
            required
            value={
              form.email
            }
            autoComplete="email"
            onChange={
              (event) =>
                setForm({
                  ...form,
                  email:
                    event.target.value,
                })
            }
          />
        </label>

        <label>
          Password
          <input
            type="password"
            minLength={12}
            required
            value={
              form.password
            }
            autoComplete="new-password"
            onChange={
              (event) =>
                setForm({
                  ...form,
                  password:
                    event.target.value,
                })
            }
          />
        </label>

        <div className="two-col">
          <label>
            Phone
            <input
              value={
                form.phone
              }
              autoComplete="tel"
              onChange={
                (event) =>
                  setForm({
                    ...form,
                    phone:
                      event.target.value,
                  })
              }
            />
          </label>

          <label>
            Gender
            <input
              value={
                form.gender
              }
              onChange={
                (event) =>
                  setForm({
                    ...form,
                    gender:
                      event.target.value,
                  })
              }
            />
          </label>
        </div>

        <div className="security-note">
          <ShieldCheck size={19} />

          <div>
            <strong>
              Privacy-preserving registration
            </strong>

            <span>
              MEDISCOPE does not reveal whether an email is already
              associated with an account.
            </span>
          </div>
        </div>

        {error && (
          <div className="form-error">
            {error}
          </div>
        )}

        <button
          className="button primary wide"
          disabled={busy}
        >
          {
            busy
              ? 'Creating account…'
              : 'Create account'
          }

          <ArrowRight size={18} />
        </button>
      </form>

      <p className="auth-switch">
        Already registered?{' '}
        <Link to="/login">
          Sign in
        </Link>
      </p>
    </AuthLayout>
  );
}


/**
 * Email verification page.
 *
 * The page supports:
 * - an email carried forward from registration;
 * - direct navigation from login;
 * - six-digit OTP verification;
 * - resend verification code;
 * - success navigation to login.
 */
export function VerifyEmailPage() {
  const navigate = useNavigate();
  const location = useLocation();

  const [searchParams] =
    useSearchParams();

  const locationState =
    location.state as RegistrationLocationState | null;

  const initialEmail =
    searchParams.get('email') ??
    locationState?.email ??
    '';

  const [email, setEmail] =
    useState(
      initialEmail,
    );

  const [otp, setOtp] =
    useState('');

  const [message, setMessage] =
    useState('');

  const [error, setError] =
    useState('');

  const [verified, setVerified] =
    useState(false);

  const [busy, setBusy] =
    useState(false);

  const [resending, setResending] =
    useState(false);

  const [resendCooldown, setResendCooldown] =
    useState(0);


  useEffect(
    () => {
      if (
        resendCooldown <= 0
      ) {
        return;
      }

      const timer =
        window.setInterval(
          () => {
            setResendCooldown(
              (current) =>
                Math.max(
                  current - 1,
                  0,
                ),
            );
          },
          1000,
        );

      return () =>
        window.clearInterval(
          timer,
        );
    },
    [resendCooldown],
  );


  async function submit(
    event: FormEvent,
  ) {
    event.preventDefault();

    setMessage('');
    setError('');
    setBusy(true);

    try {
      const response =
        await api.verifyEmail(
          email
            .trim()
            .toLowerCase(),
          otp.trim(),
        );

      setVerified(true);
      setMessage(
        response.message,
      );
    } catch (errorValue) {
      setError(
        errorValue instanceof Error
          ? errorValue.message
          : 'Verification failed.',
      );
    } finally {
      setBusy(false);
    }
  }


  async function resend() {
    if (
      !email.trim() ||
      resendCooldown > 0
    ) {
      return;
    }

    setError('');
    setMessage('');
    setResending(true);

    try {
      const response =
        await api.resendVerification(
          email
            .trim()
            .toLowerCase(),
        );

      setMessage(
        response.message,
      );

      // UX-only cooldown.
      // Backend rate limiting should remain the ultimate
      // protection against abuse.
      setResendCooldown(30);
    } catch (errorValue) {
      setError(
        errorValue instanceof Error
          ? errorValue.message
          : 'Unable to request another code.',
      );
    } finally {
      setResending(false);
    }
  }


  if (verified) {
    return (
      <AuthLayout
        title="Email verified"
        subtitle="Your MEDISCOPE account can now continue to sign-in."
      >
        <div className="verification-success">
          <div className="success-icon">
            <CheckCircle2 size={32} />
          </div>

          <h3>
            Verification complete
          </h3>

          <p>
            Your email address has been verified successfully.
            You can now sign in using your password.
          </p>

          <button
            className="button primary wide"
            onClick={
              () =>
                navigate(
                  `/login`,
                )
            }
          >
            Continue to sign in
            <ArrowRight size={18} />
          </button>
        </div>
      </AuthLayout>
    );
  }


  return (
    <AuthLayout
      title="Verify your email"
      subtitle="Enter the six-digit verification code sent to the email address used during registration."
    >
      <form
        className="auth-form"
        onSubmit={submit}
      >
        <label>
          Email
          <input
            type="email"
            required
            value={email}
            autoComplete="email"
            onChange={
              (event) =>
                setEmail(
                  event.target.value,
                )
            }
          />
        </label>

        <label>
          Verification code
          <input
            className="otp-input"
            required
            inputMode="numeric"
            autoComplete="one-time-code"
            pattern="[0-9]{6}"
            maxLength={6}
            value={otp}
            onChange={
              (event) =>
                setOtp(
                  event.target.value.replace(
                    /\D/g,
                    '',
                  ),
                )
            }
            placeholder="000000"
          />
        </label>

        {message && (
          <div className="form-info">
            {message}
          </div>
        )}

        {error && (
          <div className="form-error">
            {error}
          </div>
        )}

        <button
          className="button primary wide"
          disabled={busy}
        >
          {
            busy
              ? 'Verifying…'
              : 'Verify email'
          }

          <MailCheck size={18} />
        </button>

        <button
          type="button"
          className="button secondary wide"
          onClick={resend}
          disabled={
            resending ||
            resendCooldown > 0 ||
            !email.trim()
          }
        >
          <RefreshCw size={17} />

          {
            resending
              ? 'Sending…'
              : resendCooldown > 0
                ? `Resend available in ${resendCooldown}s`
                : 'Resend verification code'
          }
        </button>
      </form>

      <div className="auth-help-links">
        <Link to="/login">
          Back to sign in
        </Link>

        <Link to="/forgot-password">
          Forgot your password?
        </Link>
      </div>
    </AuthLayout>
  );
}


/**
 * Forgotten-password request page.
 *
 * The backend returns a uniform response whether or not
 * the account exists. The frontend preserves that same
 * privacy-safe behaviour.
 */
export function ForgotPasswordPage() {
  const [email, setEmail] =
    useState('');

  const [message, setMessage] =
    useState('');

  const [error, setError] =
    useState('');

  const [busy, setBusy] =
    useState(false);


  async function submit(
    event: FormEvent,
  ) {
    event.preventDefault();

    setMessage('');
    setError('');
    setBusy(true);

    try {
      const response =
        await api.forgotPassword(
          email
            .trim()
            .toLowerCase(),
        );

      setMessage(
        response.message,
      );
    } catch (errorValue) {
      setError(
        errorValue instanceof Error
          ? errorValue.message
          : 'Request failed.',
      );
    } finally {
      setBusy(false);
    }
  }


  return (
    <AuthLayout
      title="Reset your password"
      subtitle="We'll send reset instructions if the account is eligible."
    >
      <form
        className="auth-form"
        onSubmit={submit}
      >
        <label>
          Email
          <input
            type="email"
            required
            value={email}
            autoComplete="email"
            onChange={
              (event) =>
                setEmail(
                  event.target.value,
                )
            }
          />
        </label>

        {message && (
          <div className="form-info">
            {message}
          </div>
        )}

        {error && (
          <div className="form-error">
            {error}
          </div>
        )}

        <button
          className="button primary wide"
          disabled={busy}
        >
          <LockKeyhole size={17} />

          {
            busy
              ? 'Sending…'
              : 'Send reset instructions'
          }
        </button>
      </form>

      <p className="auth-switch">
        Remembered your password?{' '}
        <Link to="/login">
          Sign in
        </Link>
      </p>
    </AuthLayout>
  );
}


/**
 * Password reset confirmation page.
 *
 * The password-reset email should point to:
 *
 *   http://localhost:5173/reset-password?token=...
 *
 * during local development.
 */
export function ResetPasswordPage() {
  const navigate = useNavigate();

  const [searchParams] =
    useSearchParams();

  const token =
    useMemo(
      () =>
        searchParams.get(
          'token',
        ) ?? '',
      [searchParams],
    );

  const [password, setPassword] =
    useState('');

  const [confirmation, setConfirmation] =
    useState('');

  const [message, setMessage] =
    useState('');

  const [error, setError] =
    useState('');

  const [busy, setBusy] =
    useState(false);

  const [done, setDone] =
    useState(false);


  async function submit(
    event: FormEvent,
  ) {
    event.preventDefault();

    setMessage('');
    setError('');

    if (!token) {
      setError(
        'This password-reset link does not contain a reset token.',
      );
      return;
    }

    if (
      password !== confirmation
    ) {
      setError(
        'The passwords do not match.',
      );
      return;
    }

    if (
      password.length < 12
    ) {
      setError(
        'Password must contain at least 12 characters.',
      );
      return;
    }

    setBusy(true);

    try {
      const response =
        await api.resetPassword(
          token,
          password,
        );

      setMessage(
        response.message,
      );

      setDone(true);
    } catch (errorValue) {
      setError(
        errorValue instanceof Error
          ? errorValue.message
          : 'Password reset failed.',
      );
    } finally {
      setBusy(false);
    }
  }


  if (done) {
    return (
      <AuthLayout
        title="Password updated"
        subtitle="Your existing refresh-token sessions have been revoked for security."
      >
        <div className="verification-success">
          <div className="success-icon">
            <CheckCircle2 size={32} />
          </div>

          <h3>
            New password saved
          </h3>

          <p>
            Sign in again using your new password.
          </p>

          <button
            className="button primary wide"
            onClick={
              () =>
                navigate(
                  '/login',
                )
            }
          >
            Continue to sign in
            <ArrowRight size={18} />
          </button>
        </div>
      </AuthLayout>
    );
  }


  return (
    <AuthLayout
      title="Choose a new password"
      subtitle="Create a strong replacement password for your MEDISCOPE account."
    >
      <form
        className="auth-form"
        onSubmit={submit}
      >
        {!token && (
          <div className="form-error">
            Invalid password-reset link. Request a new reset email.
          </div>
        )}

        <label>
          New password
          <input
            type="password"
            required
            minLength={12}
            autoComplete="new-password"
            value={password}
            onChange={
              (event) =>
                setPassword(
                  event.target.value,
                )
            }
          />
        </label>

        <label>
          Confirm new password
          <input
            type="password"
            required
            minLength={12}
            autoComplete="new-password"
            value={confirmation}
            onChange={
              (event) =>
                setConfirmation(
                  event.target.value,
                )
            }
          />
        </label>

        {message && (
          <div className="form-info">
            {message}
          </div>
        )}

        {error && (
          <div className="form-error">
            {error}
          </div>
        )}

        <button
          className="button primary wide"
          disabled={
            busy ||
            !token
          }
        >
          <LockKeyhole size={17} />

          {
            busy
              ? 'Updating…'
              : 'Update password'
          }
        </button>
      </form>

      <p className="auth-switch">
        Need a new link?{' '}
        <Link to="/forgot-password">
          Request another reset email
        </Link>
      </p>
    </AuthLayout>
  );
}
