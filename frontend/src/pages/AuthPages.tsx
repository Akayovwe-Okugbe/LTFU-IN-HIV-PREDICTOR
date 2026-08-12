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
  Copy,
  KeyRound,
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

import {
  QRCodeSVG,
} from 'qrcode.react';

import { Brand } from '../components/Brand';
import { PasswordInput } from '../components/PasswordInput';

import {
  useAuth,
} from '../context/AuthContext';

import {
  ApiError,
  api,
} from '../lib/api';

import type {
  TotpSetupResponse,
} from '../lib/types';


// =====================================================
// NAVIGATION STATE TYPES
// =====================================================

type RegistrationLocationState = {
  email?: string;
};


type RequiredMfaLocationState = {
  setupToken?: string;
};


// =====================================================
// SHARED AUTHENTICATION LAYOUT
// =====================================================

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
            Protected by role-based access, authenticator MFA,
            audit logging and synthetic-data controls.
          </p>
        </div>
      </div>

      <div className="auth-panel">
        <div className="auth-form-wrap">
          <h1>
            {title}
          </h1>

          <p>
            {subtitle}
          </p>

          {children}
        </div>
      </div>
    </div>
  );
}


// =====================================================
// FRONTEND VALIDATION HELPERS
// =====================================================

function isValidName(
  value: string,
): boolean {
  return /^[A-Za-zÀ-ÖØ-öø-ÿ' -]{2,100}$/.test(
    value.trim(),
  );
}


function isValidPhone(
  value: string,
): boolean {
  // Phone is optional.
  if (!value.trim()) {
    return true;
  }

  return /^\+?[0-9 ()-]{7,20}$/.test(
    value.trim(),
  );
}


// =====================================================
// PASSWORD REQUIREMENTS
// =====================================================

/**
 * Return the password-policy checks used by both
 * registration and password reset.
 *
 * Keeping these checks in one place ensures the visual
 * checklist and submit validation always agree.
 */
function getPasswordRequirements(
  value: string,
) {
  return [
    {
      id: 'length',
      label: '12+ characters',
      met:
        value.length >= 12,
    },
    {
      id: 'uppercase',
      label: 'Uppercase letter',
      met:
        /[A-Z]/.test(
          value,
        ),
    },
    {
      id: 'lowercase',
      label: 'Lowercase letter',
      met:
        /[a-z]/.test(
          value,
        ),
    },
    {
      id: 'number',
      label: 'Number',
      met:
        /[0-9]/.test(
          value,
        ),
    },
  ];
}


function passwordMeetsRequirements(
  value: string,
): boolean {
  return getPasswordRequirements(
    value,
  ).every(
    (requirement) =>
      requirement.met,
  );
}


// =====================================================
// LOGIN
// =====================================================

export function LoginPage() {
  const {
    login,
    completeMfa,
  } = useAuth();

  const navigate =
    useNavigate();

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

  const [
    needsVerification,
    setNeedsVerification,
  ] = useState(false);

  const [busy, setBusy] =
    useState(false);

  const [
    mfaMethod,
    setMfaMethod,
  ] =
    useState<
      'AUTHENTICATOR'
      | 'RECOVERY'
    >(
      'AUTHENTICATOR',
    );

  async function submit(
    event: FormEvent,
  ) {
    event.preventDefault();

    setError('');
    setNeedsVerification(false);
    setBusy(true);

    try {
      // -------------------------------------------------
      // SECOND-FACTOR LOGIN
      // -------------------------------------------------

      if (challenge) {
        await completeMfa(
          challenge,
          code.trim(),
        );

        navigate(
          '/app',
          {
            replace: true,
          },
        );

        return;
      }

      // -------------------------------------------------
      // PASSWORD LOGIN
      // -------------------------------------------------

      const result =
        await login(
          email
            .trim()
            .toLowerCase(),
          password,
        );

      // -------------------------------------------------
      // ACCOUNT ALREADY HAS MFA
      // -------------------------------------------------

      if (
        result.status
        === 'mfa_required'
      ) {
        setChallenge(
          result.challengeToken,
        );

        setCode('');

        // Always begin with the normal authenticator flow.
        // The user may explicitly switch to a recovery code.
        setMfaMethod(
          'AUTHENTICATOR',
        );

        return;
      }

      // -------------------------------------------------
      // CLINICIAN / ADMINISTRATOR WITHOUT MFA
      //
      // The backend does not issue normal access tokens.
      // The user must enrol TOTP first.
      // -------------------------------------------------

      if (
        result.status
        === 'mfa_setup_required'
      ) {
        navigate(
          '/mfa-required-setup',
          {
            replace: true,

            state: {
              setupToken:
                result.setupToken,
            } satisfies RequiredMfaLocationState,
          },
        );

        return;
      }

      // -------------------------------------------------
      // STANDARD USER WITHOUT MFA
      // -------------------------------------------------

      navigate(
        '/app',
        {
          replace: true,
        },
      );
    } catch (errorValue) {
      const message =
        errorValue instanceof Error
          ? errorValue.message
          : 'Unable to sign in.';

      setError(
        message,
      );

      // Existing backend behaviour uses 403 for accounts
      // that cannot yet authenticate because verification
      // or activation remains outstanding.
      if (
        errorValue instanceof ApiError
        &&
        errorValue.status === 403
      ) {
        setNeedsVerification(
          true,
        );
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
          ? 'Enter your current authenticator code or a one-time recovery code.'
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
                required
                maxLength={320}
                autoComplete="email"
                value={email}
                placeholder="you@example.com"
                onChange={
                  (event) =>
                    setEmail(
                      event.target.value,
                    )
                }
              />
            </label>

            <label>
              Password

              <PasswordInput
                required
                autoComplete="current-password"
                value={password}
                placeholder="Enter your password"
                onChange={
                  (event) =>
                    setPassword(
                      event.target.value,
                    )
                }
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
          <div className="mfa-login-panel">

            {/* ===============================================
                MFA METHOD SWITCH
                =============================================== */}

            <div className="mfa-method-tabs">
              <button
                type="button"
                className={
                  mfaMethod
                    === 'AUTHENTICATOR'
                    ? 'active'
                    : ''
                }
                onClick={
                  () => {
                    setMfaMethod(
                      'AUTHENTICATOR',
                    );

                    setCode('');
                    setError('');
                  }
                }
              >
                <ShieldCheck size={16} />

                Authenticator
              </button>

              <button
                type="button"
                className={
                  mfaMethod
                    === 'RECOVERY'
                    ? 'active'
                    : ''
                }
                onClick={
                  () => {
                    setMfaMethod(
                      'RECOVERY',
                    );

                    setCode('');
                    setError('');
                  }
                }
              >
                <KeyRound size={16} />

                Recovery code
              </button>
            </div>


            {/* ===============================================
                AUTHENTICATOR CODE
                =============================================== */}

            {
              mfaMethod
              === 'AUTHENTICATOR'
              && (
                <>
                  <label>
                    Authenticator code

                    <input
                      className="otp-input"
                      required
                      inputMode="numeric"
                      autoComplete="one-time-code"
                      pattern="[0-9]{6}"
                      maxLength={6}
                      value={code}
                      placeholder="000000"
                      onChange={
                        (
                          event,
                        ) =>
                          setCode(
                            event.target.value.replace(
                              /\D/g,
                              '',
                            ),
                          )
                      }
                    />
                  </label>

                  <div className="mfa-method-help">
                    <ShieldCheck size={17} />

                    <div>
                      <strong>
                        Use your authenticator app
                      </strong>

                      <span>
                        Enter the current six-digit code generated
                        for your MEDISCOPE account.
                      </span>
                    </div>
                  </div>
                </>
              )
            }


            {/* ===============================================
                RECOVERY CODE
                =============================================== */}

            {
              mfaMethod
              === 'RECOVERY'
              && (
                <>
                  <label>
                    Recovery code

                    <input
                      required
                      maxLength={100}
                      autoComplete="off"
                      value={code}
                      placeholder="Enter one of your saved recovery codes"
                      onChange={
                        (
                          event,
                        ) =>
                          setCode(
                            event.target.value.replace(
                              /\s/g,
                              '',
                            ),
                          )
                      }
                    />
                  </label>

                  <div className="mfa-recovery-note">
                    <KeyRound size={17} />

                    <div>
                      <strong>
                        One-time recovery code
                      </strong>

                      <span>
                        Use one of the recovery codes shown when MFA
                        was enabled. A recovery code can only be used
                        once.
                      </span>
                    </div>
                  </div>
                </>
              )
            }
          </div>
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
                Enter or resend your email verification code
                before attempting to sign in again.
              </span>
            </div>

            <button
              type="button"
              className="button ghost small"
              onClick={
                () =>
                  navigate(
                    `/verify-email?email=${encodeURIComponent(
                      email.trim().toLowerCase(),
                    )}`,
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


// =====================================================
// REGISTRATION
// =====================================================

export function RegisterPage() {
  const navigate =
    useNavigate();

  const [error, setError] =
    useState('');

  const [busy, setBusy] =
    useState(false);

  const [
    confirmation,
    setConfirmation,
  ] = useState('');

  const [form, setForm] =
    useState({
      email: '',
      password: '',
      first_name: '',
      last_name: '',
      phone: '',
      gender: '',
      date_of_birth: '',
    });


  const passwordRequirements =
    getPasswordRequirements(
      form.password,
    );

  const passwordValid =
    passwordRequirements.every(
      (requirement) =>
        requirement.met,
    );


  async function submit(
    event: FormEvent,
  ) {
    event.preventDefault();

    setError('');

    // -------------------------------------------------
    // NAME VALIDATION
    // -------------------------------------------------

    if (
      !isValidName(
        form.first_name,
      )
      ||
      !isValidName(
        form.last_name,
      )
    ) {
      setError(
        'Please enter valid first and last names.',
      );

      return;
    }

    // -------------------------------------------------
    // PHONE VALIDATION
    // -------------------------------------------------

    if (
      !isValidPhone(
        form.phone,
      )
    ) {
      setError(
        'Please enter a valid phone number.',
      );

      return;
    }

    // -------------------------------------------------
    // GENDER VALIDATION
    // -------------------------------------------------

    if (
      ![
        'Male',
        'Female',
      ].includes(
        form.gender,
      )
    ) {
      setError(
        'Please select Male or Female.',
      );

      return;
    }

    // -------------------------------------------------
    // DATE-OF-BIRTH VALIDATION
    // -------------------------------------------------

    if (
      !form.date_of_birth
    ) {
      setError(
        'Please provide your date of birth.',
      );

      return;
    }

    const dob =
      new Date(
        `${form.date_of_birth}T00:00:00`,
      );

    const today =
      new Date();

    if (
      Number.isNaN(
        dob.getTime(),
      )
      ||
      dob > today
    ) {
      setError(
        'Please provide a valid date of birth.',
      );

      return;
    }

    // -------------------------------------------------
    // PASSWORD VALIDATION
    // -------------------------------------------------

    if (!passwordValid) {
      setError(
        'Please complete all password requirements.',
      );

      return;
    }

    if (
      form.password
      !== confirmation
    ) {
      setError(
        'The passwords do not match.',
      );

      return;
    }

    setBusy(true);

    try {
      await api.register({
        ...form,

        email:
          form.email
            .trim()
            .toLowerCase(),

        first_name:
          form.first_name
            .trim(),

        last_name:
          form.last_name
            .trim(),

        phone:
          form.phone.trim()
          || null,
      });

      // Registration remains account-enumeration safe:
      // regardless of whether the address already exists,
      // continue to verification guidance.

      navigate(
        `/verify-email?email=${encodeURIComponent(
          form.email
            .trim()
            .toLowerCase(),
        )}`,
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
      subtitle="Register securely. Email verification is required before sign-in."
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
              minLength={2}
              maxLength={100}
              autoComplete="given-name"
              value={
                form.first_name
              }
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
              minLength={2}
              maxLength={100}
              autoComplete="family-name"
              value={
                form.last_name
              }
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
            maxLength={320}
            autoComplete="email"
            placeholder="you@example.com"
            value={
              form.email
            }
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

        <div className="two-col">
          <label>
            Date of birth

            <input
              type="date"
              required
              max={
                new Date()
                  .toISOString()
                  .slice(
                    0,
                    10,
                  )
              }
              value={
                form.date_of_birth
              }
              onChange={
                (event) =>
                  setForm({
                    ...form,

                    date_of_birth:
                      event.target.value,
                  })
              }
            />
          </label>

          <label>
            Gender

            <select
              className="auth-select"
              required
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
            >
              <option value="">
                Select gender
              </option>

              <option value="Male">
                Male
              </option>

              <option value="Female">
                Female
              </option>
            </select>
          </label>
        </div>

        <label>
          Phone

          <input
            type="tel"
            maxLength={40}
            autoComplete="tel"
            placeholder="08012345678 or +2348012345678"
            value={
              form.phone
            }
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
          Password

          <PasswordInput
            required
            minLength={12}
            maxLength={200}
            autoComplete="new-password"
            placeholder="Create a strong password"
            value={
              form.password
            }
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

        <div
          className="password-strength-panel"
          aria-live="polite"
        >
          <div className="password-strength-heading">
            <span>
              Password strength
            </span>

            <strong
              className={
                passwordValid
                  ? 'complete'
                  : ''
              }
            >
              {
                passwordValid
                  ? 'Ready'
                  : `${passwordRequirements.filter(
                    (item) =>
                      item.met,
                  ).length}/4`
              }
            </strong>
          </div>

          <div className="password-requirement-grid">
            {
              passwordRequirements.map(
                (
                  requirement,
                ) => (
                  <span
                    key={
                      requirement.id
                    }
                    className={
                      requirement.met
                        ? 'password-requirement met'
                        : 'password-requirement'
                    }
                  >
                    <CheckCircle2
                      size={14}
                    />

                    {
                      requirement.label
                    }
                  </span>
                ),
              )
            }
          </div>
        </div>

        <label>
          Confirm password

          <PasswordInput
            required
            minLength={12}
            maxLength={200}
            autoComplete="new-password"
            placeholder="Repeat your password"
            value={confirmation}
            onChange={
              (event) =>
                setConfirmation(
                  event.target.value,
                )
            }
          />
        </label>

        {
          confirmation.length > 0 && (
            <div
              className={
                form.password === confirmation
                  ? 'password-match-status matched'
                  : 'password-match-status'
              }
            >
              <CheckCircle2 size={14} />

              {
                form.password === confirmation
                  ? 'Passwords match'
                  : 'Passwords do not match'
              }
            </div>
          )
        }

        <div className="security-note">
          <ShieldCheck size={19} />

          <div>
            <strong>
              Privacy-preserving registration
            </strong>

            <span>
              MEDISCOPE does not reveal whether an email
              address is already associated with an account.
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


// =====================================================
// MANDATORY PRIVILEGED-ROLE MFA ENROLMENT
// =====================================================

export function RequiredMfaSetupPage() {
  const location =
    useLocation();

  const navigate =
    useNavigate();

  const {
    completeRequiredMfaSetup,
  } = useAuth();

  const locationState =
    location.state as RequiredMfaLocationState | null;

  const setupToken =
    locationState?.setupToken ?? '';

  const [setup, setSetup] =
    useState<TotpSetupResponse | null>(
      null,
    );

  const [code, setCode] =
    useState('');

  const [error, setError] =
    useState('');

  const [busy, setBusy] =
    useState(false);

  const [
    recoveryCodes,
    setRecoveryCodes,
  ] = useState<string[]>([]);


  useEffect(
    () => {
      if (!setupToken) {
        setError(
          'The MFA setup session is missing or has expired. Please sign in again.',
        );

        return;
      }

      api.beginRequiredMfaSetup(
        setupToken,
      )
        .then(
          setSetup,
        )
        .catch(
          (errorValue) =>
            setError(
              errorValue instanceof Error
                ? errorValue.message
                : 'Unable to start MFA setup.',
            ),
        );
    },
    [
      setupToken,
    ],
  );


  async function submit(
    event: FormEvent,
  ) {
    event.preventDefault();

    setError('');
    setBusy(true);

    try {
      const codes =
        await completeRequiredMfaSetup(
          setupToken,
          code,
        );

      setRecoveryCodes(
        codes,
      );
    } catch (errorValue) {
      setError(
        errorValue instanceof Error
          ? errorValue.message
          : 'Unable to complete MFA setup.',
      );
    } finally {
      setBusy(false);
    }
  }


  // -------------------------------------------------
  // RECOVERY CODES — DISPLAYED ONCE
  // -------------------------------------------------

  if (
    recoveryCodes.length > 0
  ) {
    return (
      <AuthLayout
        title="Save your recovery codes"
        subtitle="MFA is enabled. Store these codes securely before continuing."
      >
        <div className="recovery-panel">
          <div className="recovery-grid">
            {
              recoveryCodes.map(
                (
                  recoveryCode,
                ) => (
                  <code
                    key={
                      recoveryCode
                    }
                  >
                    {recoveryCode}
                  </code>
                ),
              )
            }
          </div>

          <button
            className="button primary wide"
            onClick={
              () =>
                navigate(
                  '/app',
                  {
                    replace: true,
                  },
                )
            }
          >
            I have saved them

            <ArrowRight size={18} />
          </button>
        </div>
      </AuthLayout>
    );
  }


  return (
    <AuthLayout
      title="Multi-factor authentication required"
      subtitle="Clinician and administrator accounts must configure an authenticator before entering MEDISCOPE."
    >
      {setup && (
        <div className="totp-enrolment">
          <div className="qr-card">
            <QRCodeSVG
              value={
                setup.provisioning_uri
              }
              size={196}
              marginSize={2}
            />
          </div>

          <div>
            <span className="eyebrow">
              Authenticator setup
            </span>

            <h3>
              Scan the QR code
            </h3>

            <p>
              Open Microsoft Authenticator or another
              TOTP-compatible application and scan this code.
            </p>

            <div className="secret-box">
              <code>
                {
                  setup.manual_secret
                }
              </code>

              <button
                type="button"
                className="icon-button"
                title="Copy manual secret"
                onClick={
                  () =>
                    navigator.clipboard.writeText(
                      setup.manual_secret,
                    )
                }
              >
                <Copy size={17} />
              </button>
            </div>
          </div>
        </div>
      )}

      <form
        className="auth-form"
        onSubmit={submit}
      >
        <label>
          Current authenticator code

          <input
            className="otp-input"
            required
            inputMode="numeric"
            autoComplete="one-time-code"
            pattern="[0-9]{6}"
            maxLength={6}
            value={code}
            placeholder="000000"
            onChange={
              (event) =>
                setCode(
                  event.target.value.replace(
                    /\D/g,
                    '',
                  ),
                )
            }
          />
        </label>

        {error && (
          <div className="form-error">
            {error}
          </div>
        )}

        <button
          className="button primary wide"
          disabled={
            busy ||
            !setup
          }
        >
          <KeyRound size={18} />

          {
            busy
              ? 'Securing account…'
              : 'Enable MFA & continue'
          }
        </button>
      </form>
    </AuthLayout>
  );
}


// =====================================================
// EMAIL VERIFICATION
// =====================================================

export function VerifyEmailPage() {
  const navigate =
    useNavigate();

  const location =
    useLocation();

  const [searchParams] =
    useSearchParams();

  const locationState =
    location.state as RegistrationLocationState | null;

  const initialEmail =
    searchParams.get(
      'email',
    )
    ??
    locationState?.email
    ??
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

  const [
    resending,
    setResending,
  ] = useState(false);

  const [
    resendCooldown,
    setResendCooldown,
  ] = useState(0);


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
    [
      resendCooldown,
    ],
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

      setVerified(
        true,
      );

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
      !email.trim()
      ||
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

      // This cooldown improves UX only.
      // Backend rate limiting remains authoritative.
      setResendCooldown(
        30,
      );
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
        subtitle="Your MEDISCOPE account is ready for sign-in."
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
      title="Verify your email"
      subtitle="Enter the six-digit verification code sent to your registration email."
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
            placeholder="000000"
            onChange={
              (event) =>
                setOtp(
                  event.target.value.replace(
                    /\D/g,
                    '',
                  ),
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
            resending
            ||
            resendCooldown > 0
            ||
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


// =====================================================
// FORGOTTEN PASSWORD
// =====================================================

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


// =====================================================
// PASSWORD RESET
// =====================================================

export function ResetPasswordPage() {
  const navigate =
    useNavigate();

  const [searchParams] =
    useSearchParams();

  const token =
    useMemo(
      () =>
        searchParams.get(
          'token',
        ) ?? '',
      [
        searchParams,
      ],
    );

  const [
    password,
    setPassword,
  ] = useState('');

  const [
    confirmation,
    setConfirmation,
  ] = useState('');

  const [error, setError] =
    useState('');

  const [busy, setBusy] =
    useState(false);

  const [done, setDone] =
    useState(false);

  const passwordRequirements =
    getPasswordRequirements(
      password,
    );

  const passwordValid =
    passwordMeetsRequirements(
      password,
    );


  async function submit(
    event: FormEvent,
  ) {
    event.preventDefault();

    setError('');

    if (!token) {
      setError(
        'This password-reset link does not contain a valid token.',
      );

      return;
    }

    if (!passwordValid) {
      setError(
        'Please complete all password requirements.',
      );

      return;
    }

    if (
      password
      !== confirmation
    ) {
      setError(
        'The passwords do not match.',
      );

      return;
    }

    setBusy(true);

    try {
      await api.resetPassword(
        token,
        password,
      );

      setDone(
        true,
      );
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
        subtitle="Your previous refresh-token sessions have been revoked for security."
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

          <PasswordInput
            required
            minLength={12}
            maxLength={200}
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

        <div
          className="password-strength-panel"
          aria-live="polite"
        >
          <div className="password-strength-heading">
            <span>
              Password strength
            </span>

            <strong
              className={
                passwordValid
                  ? 'complete'
                  : ''
              }
            >
              {
                passwordValid
                  ? 'Ready'
                  : `${passwordRequirements.filter(
                    (item) =>
                      item.met,
                  ).length}/4`
              }
            </strong>
          </div>

          <div className="password-requirement-grid">
            {
              passwordRequirements.map(
                (
                  requirement,
                ) => (
                  <span
                    key={
                      requirement.id
                    }
                    className={
                      requirement.met
                        ? 'password-requirement met'
                        : 'password-requirement'
                    }
                  >
                    <CheckCircle2
                      size={14}
                    />

                    {
                      requirement.label
                    }
                  </span>
                ),
              )
            }
          </div>
        </div>

        <label>
          Confirm new password

          <PasswordInput
            required
            minLength={12}
            maxLength={200}
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

        {error && (
          <div className="form-error">
            {error}
          </div>
        )}

        <button
          className="button primary wide"
          disabled={
            busy
            ||
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
