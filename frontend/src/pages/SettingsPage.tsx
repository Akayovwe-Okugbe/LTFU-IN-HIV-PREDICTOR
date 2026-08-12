import {
    CheckCircle2,
    Copy,
    KeyRound,
    LockKeyhole,
    ShieldCheck,
    Smartphone,
} from 'lucide-react';

import {
    useState,
    type FormEvent,
} from 'react';

import {
    QRCodeSVG,
} from 'qrcode.react';

import {
    PageHeader,
} from '../components/UI';

import {
    PasswordInput,
} from '../components/PasswordInput';

import {
    useAuth,
} from '../context/AuthContext';

import {
    api,
} from '../lib/api';

import type {
    TotpSetupResponse,
} from '../lib/types';


// =====================================================
// SECURITY SETTINGS PAGE
// =====================================================

export default function SettingsPage() {
    const {
        user,
        refreshProfile,
    } = useAuth();

    const [
        setup,
        setSetup,
    ] =
        useState<TotpSetupResponse | null>(
            null,
        );

    const [
        confirmationCode,
        setConfirmationCode,
    ] =
        useState('');

    const [
        recoveryCodes,
        setRecoveryCodes,
    ] =
        useState<string[]>(
            [],
        );

    const [
        password,
        setPassword,
    ] =
        useState('');

    const [
        disableCode,
        setDisableCode,
    ] =
        useState('');

    const [
        message,
        setMessage,
    ] =
        useState('');

    const [
        error,
        setError,
    ] =
        useState('');

    const [
        busy,
        setBusy,
    ] =
        useState(false);


    const privilegedRole =
        user?.role === 'CLINICIAN'
        ||
        user?.role === 'ADMINISTRATOR';


    // ===================================================
    // START MFA SETUP
    // ===================================================

    async function startMfaSetup() {
        setError('');
        setMessage('');
        setRecoveryCodes(
            [],
        );

        try {
            const response =
                await api.beginTotpSetup();

            setSetup(
                response,
            );
        } catch (
        errorValue
        ) {
            setError(
                errorValue instanceof Error
                    ? errorValue.message
                    : 'Unable to start MFA setup.',
            );
        }
    }


    // ===================================================
    // CONFIRM MFA SETUP
    // ===================================================

    async function confirmMfaSetup(
        event: FormEvent,
    ) {
        event.preventDefault();

        setError('');
        setMessage('');
        setBusy(true);

        try {
            const response =
                await api.confirmTotpSetup(
                    confirmationCode,
                );

            setRecoveryCodes(
                response.recovery_codes,
            );

            setSetup(
                null,
            );

            setConfirmationCode(
                '',
            );

            await refreshProfile();

            setMessage(
                'Multi-factor authentication is now enabled.',
            );
        } catch (
        errorValue
        ) {
            setError(
                errorValue instanceof Error
                    ? errorValue.message
                    : 'Unable to confirm MFA setup.',
            );
        } finally {
            setBusy(
                false,
            );
        }
    }


    // ===================================================
    // DISABLE MFA
    //
    // Only standard USER accounts may disable MFA.
    // Clinicians and administrators are protected by the
    // backend mandatory-MFA policy.
    // ===================================================

    async function disableMfa(
        event: FormEvent,
    ) {
        event.preventDefault();

        setError('');
        setMessage('');
        setBusy(true);

        try {
            const response =
                await api.disableTotp(
                    password,
                    disableCode,
                );

            setPassword(
                '',
            );

            setDisableCode(
                '',
            );

            await refreshProfile();

            setMessage(
                response.message,
            );
        } catch (
        errorValue
        ) {
            setError(
                errorValue instanceof Error
                    ? errorValue.message
                    : 'Unable to disable MFA.',
            );
        } finally {
            setBusy(
                false,
            );
        }
    }


    // ===================================================
    // RENDER
    // ===================================================

    return (
        <>
            <PageHeader
                eyebrow="Account security"
                title="Security"
                description="Manage sign-in protection for your MEDISCOPE account."
            />


            {/* =================================================
          STATUS MESSAGES
          ================================================= */}

            {message && (
                <div className="form-info security-page-message">
                    {message}
                </div>
            )}

            {error && (
                <div className="form-error security-page-message">
                    {error}
                </div>
            )}


            {/* =================================================
          SECURITY STATUS
          ================================================= */}

            <section className="security-overview-card">
                <div
                    className={
                        user?.mfa_enabled
                            ? 'security-overview-icon protected'
                            : 'security-overview-icon'
                    }
                >
                    <ShieldCheck size={25} />
                </div>

                <div className="security-overview-copy">
                    <span className="eyebrow">
                        Multi-factor authentication
                    </span>

                    <h2>
                        {
                            user?.mfa_enabled
                                ? 'Your account has additional protection'
                                : 'Add another layer of sign-in protection'
                        }
                    </h2>

                    <p>
                        {
                            privilegedRole
                                ? (
                                    'Authenticator-based MFA is mandatory for your MEDISCOPE role.'
                                )
                                : (
                                    'MFA is optional for standard users, but strongly recommended.'
                                )
                        }
                    </p>
                </div>

                <span
                    className={
                        user?.mfa_enabled
                            ? 'mfa-status-badge enabled'
                            : 'mfa-status-badge'
                    }
                >
                    {
                        user?.mfa_enabled
                            ? 'Enabled'
                            : 'Not enabled'
                    }
                </span>
            </section>


            {/* =================================================
          MFA NOT YET ENABLED
          ================================================= */}

            {!user?.mfa_enabled && (
                <section className="panel security-action-panel">

                    {!setup && (
                        <div className="security-setup-intro">
                            <div className="security-method-icon">
                                <Smartphone size={23} />
                            </div>

                            <div className="security-method-copy">
                                <h3>
                                    Authenticator application
                                </h3>

                                <p>
                                    Use Microsoft Authenticator, Google Authenticator,
                                    Authy or another TOTP-compatible application.
                                </p>

                                <div className="security-benefits">
                                    <span>
                                        <CheckCircle2 size={14} />
                                        No SMS required
                                    </span>

                                    <span>
                                        <CheckCircle2 size={14} />
                                        Works offline
                                    </span>

                                    <span>
                                        <CheckCircle2 size={14} />
                                        Recovery codes included
                                    </span>
                                </div>
                            </div>

                            <button
                                type="button"
                                className="button primary"
                                onClick={
                                    startMfaSetup
                                }
                            >
                                <KeyRound size={17} />

                                Set up authenticator
                            </button>
                        </div>
                    )}


                    {/* ---------------------------------------------
              TOTP ENROLMENT
              --------------------------------------------- */}

                    {setup && (
                        <form
                            className="security-enrolment"
                            onSubmit={
                                confirmMfaSetup
                            }
                        >
                            <div className="security-enrolment-grid">

                                {/* QR CODE */}

                                <div className="security-qr-section">
                                    <span className="security-step">
                                        Step 1
                                    </span>

                                    <div className="security-qr-card">
                                        <QRCodeSVG
                                            value={
                                                setup.provisioning_uri
                                            }
                                            size={190}
                                            marginSize={2}
                                        />
                                    </div>

                                    <span className="security-qr-caption">
                                        Scan with your authenticator app
                                    </span>
                                </div>


                                {/* MANUAL SETUP */}

                                <div className="security-enrolment-details">
                                    <span className="security-step">
                                        Step 2
                                    </span>

                                    <h3>
                                        Connect your authenticator
                                    </h3>

                                    <p>
                                        Scan the QR code or manually enter the secret
                                        below into your authenticator application.
                                    </p>

                                    <div className="security-secret">
                                        <code>
                                            {
                                                setup.manual_secret
                                            }
                                        </code>

                                        <button
                                            type="button"
                                            className="icon-button"
                                            title="Copy secret"
                                            aria-label="Copy secret"
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

                                    <label>
                                        <span>
                                            Step 3 — Enter the six-digit code
                                        </span>

                                        <input
                                            className="otp-input"
                                            required
                                            inputMode="numeric"
                                            autoComplete="one-time-code"
                                            maxLength={6}
                                            pattern="[0-9]{6}"
                                            placeholder="000000"
                                            value={
                                                confirmationCode
                                            }
                                            onChange={
                                                (event) =>
                                                    setConfirmationCode(
                                                        event.target.value.replace(
                                                            /\D/g,
                                                            '',
                                                        ),
                                                    )
                                            }
                                        />
                                    </label>

                                    <div className="security-enrolment-actions">
                                        <button
                                            type="button"
                                            className="button secondary"
                                            onClick={
                                                () => {
                                                    setSetup(
                                                        null,
                                                    );

                                                    setConfirmationCode(
                                                        '',
                                                    );
                                                }
                                            }
                                        >
                                            Cancel
                                        </button>

                                        <button
                                            type="submit"
                                            className="button primary"
                                            disabled={
                                                busy
                                                ||
                                                confirmationCode.length
                                                !== 6
                                            }
                                        >
                                            {
                                                busy
                                                    ? 'Confirming…'
                                                    : 'Enable MFA'
                                            }
                                        </button>
                                    </div>
                                </div>
                            </div>
                        </form>
                    )}
                </section>
            )}


            {/* =================================================
          RECOVERY CODES
          ================================================= */}

            {recoveryCodes.length > 0 && (
                <section className="panel security-recovery-panel">
                    <div className="security-recovery-heading">
                        <div className="security-method-icon">
                            <KeyRound size={22} />
                        </div>

                        <div>
                            <span className="eyebrow">
                                Important
                            </span>

                            <h3>
                                Save your recovery codes
                            </h3>

                            <p>
                                Each code can be used once if you lose access to
                                your authenticator. MEDISCOPE will not display
                                this set again.
                            </p>
                        </div>
                    </div>

                    <div className="security-recovery-grid">
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
                </section>
            )}


            {/* =================================================
          MFA ENABLED
          ================================================= */}

            {user?.mfa_enabled && (
                <section className="panel security-enabled-panel">
                    <div className="security-enabled-summary">
                        <div className="security-method-icon enabled">
                            <LockKeyhole size={23} />
                        </div>

                        <div>
                            <h3>
                                Authenticator protection is active
                            </h3>

                            <p>
                                A valid authenticator or recovery code will be
                                required after password verification.
                            </p>
                        </div>
                    </div>


                    {/* ---------------------------------------------
              STANDARD USER MAY DISABLE MFA
              --------------------------------------------- */}

                    {!privilegedRole && (
                        <details className="security-danger-zone">
                            <summary>
                                Disable multi-factor authentication
                            </summary>

                            <div className="security-danger-content">
                                <p>
                                    Confirm your password and current authenticator
                                    or recovery code before removing MFA.
                                </p>

                                <form
                                    onSubmit={
                                        disableMfa
                                    }
                                >
                                    <label>
                                        Password

                                        <PasswordInput
                                            required
                                            value={
                                                password
                                            }
                                            autoComplete="current-password"
                                            onChange={
                                                (event) =>
                                                    setPassword(
                                                        event.target.value,
                                                    )
                                            }
                                        />
                                    </label>

                                    <label>
                                        Authenticator or recovery code

                                        <input
                                            required
                                            maxLength={100}
                                            value={
                                                disableCode
                                            }
                                            onChange={
                                                (event) =>
                                                    setDisableCode(
                                                        event.target.value,
                                                    )
                                            }
                                        />
                                    </label>

                                    <button
                                        type="submit"
                                        className="button danger-button"
                                        disabled={busy}
                                    >
                                        Disable MFA
                                    </button>
                                </form>
                            </div>
                        </details>
                    )}


                    {/* ---------------------------------------------
              PRIVILEGED ROLE
              --------------------------------------------- */}

                    {privilegedRole && (
                        <div className="privileged-security-note">
                            <ShieldCheck size={18} />

                            <span>
                                MFA cannot be disabled while this account has the
                                {` ${user?.role}`} role.
                            </span>
                        </div>
                    )}
                </section>
            )}
        </>
    );
}
