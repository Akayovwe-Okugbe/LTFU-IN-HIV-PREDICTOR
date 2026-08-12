import {
    ArrowRight,
    CheckCircle2,
    Clock3,
    Edit3,
    HeartPulse,
    Mail,
    MapPin,
    Phone,
    ShieldCheck,
    UserRound,
    X,
} from 'lucide-react';

import {
    useEffect,
    useMemo,
    useState,
    type FormEvent,
} from 'react';

import {
    PageHeader,
} from '../components/UI';

import {
    useAuth,
} from '../context/AuthContext';

import {
    api,
} from '../lib/api';

import type {
    HealthRecordChangeRequest,
    Patient,
} from '../lib/types';


// =====================================================
// HEALTH-RECORD FIELD CONFIGURATION
// =====================================================

/**
 * These are the synthetic patient fields that a standard
 * USER may request to have corrected.
 *
 * The user does not directly modify the underlying health
 * record. A change request is created and reviewed through
 * the existing clinician approval workflow.
 */
const healthRecordFields = [
    {
        key: 'first_name',
        label: 'First name',
    },
    {
        key: 'last_name',
        label: 'Last name',
    },
    {
        key: 'date_of_birth',
        label: 'Date of birth',
    },
    {
        key: 'sex',
        label: 'Sex',
    },
    {
        key: 'state',
        label: 'State',
    },
    {
        key: 'lga',
        label: 'LGA',
    },
] as const;


type HealthRecordFieldKey =
    typeof healthRecordFields[number]['key'];


// =====================================================
// FORM TYPE
// =====================================================

type ProfileForm = {
    first_name: string;
    last_name: string;
    phone: string;
    gender: string;
    date_of_birth: string;
};


// =====================================================
// DATE FORMATTER
// =====================================================

function formatDate(
    value?: string | null,
): string {
    if (!value) {
        return 'Not recorded';
    }

    const date =
        new Date(
            `${value}T00:00:00`,
        );

    if (
        Number.isNaN(
            date.getTime(),
        )
    ) {
        return value;
    }

    return date.toLocaleDateString(
        [],
        {
            day: 'numeric',
            month: 'short',
            year: 'numeric',
        },
    );
}


// =====================================================
// REQUEST STATUS LABEL
// =====================================================

function requestStatusLabel(
    status: string,
): string {
    switch (
    status.toUpperCase()
    ) {
        case 'APPROVED':
            return 'Approved';

        case 'REJECTED':
            return 'Rejected';

        case 'PENDING':
            return 'Pending review';

        default:
            return status;
    }
}


// =====================================================
// PROFILE PAGE
// =====================================================

export default function ProfilePage() {
    const {
        user,
        refreshProfile,
    } = useAuth();

    const [
        patient,
        setPatient,
    ] =
        useState<Patient | null>(
            null,
        );

    const [
        requests,
        setRequests,
    ] =
        useState<
            HealthRecordChangeRequest[]
        >(
            [],
        );

    const [
        loadingHealthData,
        setLoadingHealthData,
    ] =
        useState(
            false,
        );

    const [
        savingProfile,
        setSavingProfile,
    ] =
        useState(
            false,
        );

    const [
        submittingRequest,
        setSubmittingRequest,
    ] =
        useState(
            false,
        );

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
        editingField,
        setEditingField,
    ] =
        useState<
            HealthRecordFieldKey | ''
        >(
            '',
        );

    const [
        proposedValue,
        setProposedValue,
    ] =
        useState('');

    const [
        reason,
        setReason,
    ] =
        useState('');

    const [
        form,
        setForm,
    ] =
        useState<ProfileForm>({
            first_name:
                user?.first_name ?? '',

            last_name:
                user?.last_name ?? '',

            phone:
                user?.phone ?? '',

            gender:
                user?.gender ?? '',

            date_of_birth:
                user?.date_of_birth ?? '',
        });


    // ===================================================
    // KEEP ACCOUNT FORM SYNCHRONISED WITH AUTH CONTEXT
    // ===================================================

    useEffect(
        () => {
            setForm({
                first_name:
                    user?.first_name ?? '',

                last_name:
                    user?.last_name ?? '',

                phone:
                    user?.phone ?? '',

                gender:
                    user?.gender ?? '',

                date_of_birth:
                    user?.date_of_birth ?? '',
            });
        },
        [
            user,
        ],
    );


    // ===================================================
    // LOAD STANDARD USER HEALTH INFORMATION
    // ===================================================

    useEffect(
        () => {
            if (
                user?.role !== 'USER'
            ) {
                return;
            }

            let active =
                true;

            async function loadHealthData() {
                setLoadingHealthData(
                    true,
                );

                const [
                    patientResult,
                    requestResult,
                ] =
                    await Promise.allSettled([
                        api.linkedPatient(),
                        api.myChangeRequests(),
                    ]);

                if (!active) {
                    return;
                }

                if (
                    patientResult.status
                    === 'fulfilled'
                ) {
                    setPatient(
                        patientResult.value,
                    );
                }

                if (
                    requestResult.status
                    === 'fulfilled'
                ) {
                    setRequests(
                        requestResult.value,
                    );
                }

                setLoadingHealthData(
                    false,
                );
            }

            void loadHealthData();

            return () => {
                active = false;
            };
        },
        [
            user?.role,
        ],
    );


    // ===================================================
    // USER INITIALS
    // ===================================================

    const initials =
        `${user?.first_name?.[0] ?? ''}${user?.last_name?.[0] ?? ''}`;


    // ===================================================
    // PENDING REQUEST COUNT
    // ===================================================

    const pendingRequestCount =
        useMemo(
            () =>
                requests.filter(
                    (request) =>
                        request.status.toUpperCase()
                        === 'PENDING',
                ).length,
            [
                requests,
            ],
        );


    // ===================================================
    // SAVE ACCOUNT PROFILE
    // ===================================================

    async function saveProfile(
        event: FormEvent,
    ) {
        event.preventDefault();

        setError('');
        setMessage('');
        setSavingProfile(
            true,
        );

        try {
            await api.updateCurrentUser({
                first_name:
                    form.first_name.trim(),

                last_name:
                    form.last_name.trim(),

                phone:
                    form.phone.trim()
                    || null,

                gender:
                    form.gender
                    || null,

                date_of_birth:
                    form.date_of_birth
                    || null,
            });

            await refreshProfile();

            setMessage(
                'Your account profile was updated successfully.',
            );
        } catch (
        errorValue
        ) {
            setError(
                errorValue instanceof Error
                    ? errorValue.message
                    : 'Unable to update your profile.',
            );
        } finally {
            setSavingProfile(
                false,
            );
        }
    }


    // ===================================================
    // OPEN HEALTH-RECORD CHANGE REQUEST
    // ===================================================

    function beginChangeRequest(
        field:
            HealthRecordFieldKey,
        currentValue: string,
    ) {
        setEditingField(
            field,
        );

        setProposedValue(
            currentValue
                === 'Not recorded'
                ? ''
                : currentValue,
        );

        setReason('');

        setError('');
        setMessage('');
    }


    // ===================================================
    // CLOSE CHANGE REQUEST
    // ===================================================

    function cancelChangeRequest() {
        setEditingField('');
        setProposedValue('');
        setReason('');
    }


    // ===================================================
    // SUBMIT HEALTH-RECORD CHANGE REQUEST
    // ===================================================

    async function submitChangeRequest(
        event: FormEvent,
    ) {
        event.preventDefault();

        if (!editingField) {
            return;
        }

        setError('');
        setMessage('');
        setSubmittingRequest(
            true,
        );

        try {
            const response =
                await api.submitChangeRequest({
                    field_name:
                        editingField,

                    proposed_value:
                        proposedValue.trim(),

                    reason:
                        reason.trim()
                        || undefined,
                });

            setRequests(
                (current) => [
                    response,
                    ...current,
                ],
            );

            cancelChangeRequest();

            setMessage(
                'Your health-record change request was submitted for clinician review.',
            );
        } catch (
        errorValue
        ) {
            setError(
                errorValue instanceof Error
                    ? errorValue.message
                    : 'Unable to submit your change request.',
            );
        } finally {
            setSubmittingRequest(
                false,
            );
        }
    }


    // ===================================================
    // HEALTH FIELD DISPLAY VALUE
    // ===================================================

    function getPatientFieldValue(
        field:
            HealthRecordFieldKey,
    ): string {
        if (!patient) {
            return 'Not recorded';
        }

        const rawValue =
            patient[
            field as keyof Patient
            ];

        if (
            rawValue === null
            ||
            rawValue === undefined
            ||
            rawValue === ''
        ) {
            return 'Not recorded';
        }

        if (
            field === 'date_of_birth'
        ) {
            return formatDate(
                String(
                    rawValue,
                ),
            );
        }

        return String(
            rawValue,
        );
    }


    // ===================================================
    // CURRENT CHANGE REQUEST FIELD LABEL
    // ===================================================

    const editingLabel =
        healthRecordFields.find(
            (field) =>
                field.key
                === editingField,
        )?.label;


    // ===================================================
    // RENDER
    // ===================================================

    return (
        <>
            <PageHeader
                eyebrow="Your account"
                title="Profile"
                description="Manage your personal account details and review your linked synthetic health information."
            />


            {/* =================================================
          PAGE MESSAGES
          ================================================= */}

            {message && (
                <div className="form-info page-message">
                    {message}
                </div>
            )}

            {error && (
                <div className="form-error page-message">
                    {error}
                </div>
            )}


            {/* =================================================
          ACCOUNT PROFILE
          ================================================= */}

            <section className="profile-account-card">

                {/* -----------------------------------------------
            PROFILE SUMMARY
            ----------------------------------------------- */}

                <header className="profile-account-header">
                    <div className="profile-identity">
                        <div className="profile-avatar-modern">
                            {
                                initials
                                    ? initials
                                    : <UserRound size={24} />
                            }
                        </div>

                        <div>
                            <span className="eyebrow">
                                Personal information
                            </span>

                            <h2>
                                {user?.first_name}{' '}
                                {user?.last_name}
                            </h2>

                            <div className="profile-meta">
                                <span>
                                    <Mail size={14} />
                                    {user?.email}
                                </span>

                                {
                                    user?.phone && (
                                        <span>
                                            <Phone size={14} />
                                            {user.phone}
                                        </span>
                                    )
                                }
                            </div>
                        </div>
                    </div>

                    <div className="profile-account-badge">
                        <ShieldCheck size={15} />

                        <span>
                            {user?.role}
                        </span>
                    </div>
                </header>


                {/* -----------------------------------------------
            EDITABLE PROFILE FORM
            ----------------------------------------------- */}

                <form
                    className="profile-modern-form"
                    onSubmit={
                        saveProfile
                    }
                >
                    <div className="profile-form-section-heading">
                        <div>
                            <h3>
                                Account details
                            </h3>

                            <p>
                                These details belong to your MEDISCOPE account
                                and can be updated directly.
                            </p>
                        </div>
                    </div>


                    <div className="profile-form-grid">
                        <label>
                            <span>
                                First name
                            </span>

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
                            <span>
                                Last name
                            </span>

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


                        <label className="profile-form-wide">
                            <span>
                                Email address
                            </span>

                            <input
                                value={
                                    user?.email
                                    ?? ''
                                }
                                disabled
                            />

                            <small>
                                Email changes require a separate verification
                                workflow and cannot be made here.
                            </small>
                        </label>


                        <label>
                            <span>
                                Date of birth
                            </span>

                            <input
                                type="date"
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
                            <span>
                                Gender
                            </span>

                            <select
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
                                    Not specified
                                </option>

                                <option value="Male">
                                    Male
                                </option>

                                <option value="Female">
                                    Female
                                </option>
                            </select>
                        </label>


                        <label className="profile-form-wide">
                            <span>
                                Phone number
                            </span>

                            <input
                                type="tel"
                                maxLength={40}
                                autoComplete="tel"
                                placeholder="+44..."
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
                    </div>


                    <div className="profile-form-actions">
                        <button
                            type="submit"
                            className="button primary"
                            disabled={
                                savingProfile
                            }
                        >
                            {
                                savingProfile
                                    ? 'Saving…'
                                    : 'Save changes'
                            }
                        </button>
                    </div>
                </form>
            </section>


            {/* =================================================
          STANDARD USER HEALTH RECORD
          ================================================= */}

            {user?.role === 'USER' && (
                <section className="profile-health-section">

                    {/* ---------------------------------------------
              HEALTH PROFILE HEADER
              --------------------------------------------- */}

                    <header className="profile-health-header">
                        <div className="profile-health-heading">
                            <div className="profile-health-icon">
                                <HeartPulse size={23} />
                            </div>

                            <div>
                                <span className="eyebrow">
                                    Linked synthetic health profile
                                </span>

                                <h2>
                                    My health record
                                </h2>

                                <p>
                                    Review linked information and request corrections
                                    where necessary.
                                </p>
                            </div>
                        </div>

                        {
                            patient && (
                                <div className="profile-health-status">
                                    <CheckCircle2 size={15} />

                                    Linked
                                </div>
                            )
                        }
                    </header>


                    {/* ---------------------------------------------
              LOADING STATE
              --------------------------------------------- */}

                    {loadingHealthData && (
                        <div className="profile-health-empty">
                            <HeartPulse size={24} />

                            <strong>
                                Loading health profile
                            </strong>

                            <span>
                                Retrieving your linked synthetic record.
                            </span>
                        </div>
                    )}


                    {/* ---------------------------------------------
              NO LINKED PROFILE
              --------------------------------------------- */}

                    {!loadingHealthData &&
                        !patient && (
                            <div className="profile-health-empty">
                                <HeartPulse size={24} />

                                <strong>
                                    No linked health profile
                                </strong>

                                <span>
                                    An administrator must link your account to a
                                    synthetic patient record before health information
                                    can appear here.
                                </span>
                            </div>
                        )}


                    {/* ---------------------------------------------
              LINKED HEALTH PROFILE
              --------------------------------------------- */}

                    {!loadingHealthData &&
                        patient && (
                            <>
                                <div className="profile-patient-summary">
                                    <div>
                                        <span>
                                            Synthetic patient number
                                        </span>

                                        <strong>
                                            {
                                                patient.synthetic_patient_number
                                            }
                                        </strong>
                                    </div>

                                    <div>
                                        <span>
                                            Record status
                                        </span>

                                        <strong>
                                            {
                                                patient.status
                                            }
                                        </strong>
                                    </div>

                                    <div>
                                        <span>
                                            Location
                                        </span>

                                        <strong>
                                            <MapPin size={14} />

                                            {
                                                patient.lga
                                            },{' '}
                                            {
                                                patient.state
                                            }
                                        </strong>
                                    </div>

                                    <div>
                                        <span>
                                            Pending requests
                                        </span>

                                        <strong>
                                            {
                                                pendingRequestCount
                                            }
                                        </strong>
                                    </div>
                                </div>


                                {/* ---------------------------------------
                    HEALTH RECORD FIELDS
                    --------------------------------------- */}

                                <div className="profile-health-fields">
                                    {
                                        healthRecordFields.map(
                                            (
                                                field,
                                            ) => {
                                                const value =
                                                    getPatientFieldValue(
                                                        field.key,
                                                    );

                                                return (
                                                    <article
                                                        className="profile-health-field"
                                                        key={
                                                            field.key
                                                        }
                                                    >
                                                        <div>
                                                            <span>
                                                                {
                                                                    field.label
                                                                }
                                                            </span>

                                                            <strong>
                                                                {value}
                                                            </strong>
                                                        </div>

                                                        <button
                                                            type="button"
                                                            className="profile-change-button"
                                                            onClick={
                                                                () =>
                                                                    beginChangeRequest(
                                                                        field.key,
                                                                        value,
                                                                    )
                                                            }
                                                        >
                                                            <Edit3 size={14} />

                                                            Request change
                                                        </button>
                                                    </article>
                                                );
                                            },
                                        )
                                    }
                                </div>


                                {/* ---------------------------------------
                    CHANGE REQUEST HISTORY
                    --------------------------------------- */}

                                <section className="profile-request-history">
                                    <header className="profile-request-history-header">
                                        <div>
                                            <span className="eyebrow">
                                                Review workflow
                                            </span>

                                            <h3>
                                                Change requests
                                            </h3>
                                        </div>

                                        {
                                            pendingRequestCount > 0 && (
                                                <span className="profile-pending-badge">
                                                    <Clock3 size={14} />

                                                    {
                                                        pendingRequestCount
                                                    } pending
                                                </span>
                                            )
                                        }
                                    </header>


                                    {
                                        requests.length === 0
                                            ? (
                                                <div className="profile-request-empty">
                                                    No health-record change requests have been submitted.
                                                </div>
                                            )
                                            : (
                                                <div className="profile-request-list">
                                                    {
                                                        requests.map(
                                                            (
                                                                request,
                                                            ) => (
                                                                <article
                                                                    className="profile-request-row"
                                                                    key={
                                                                        request.id
                                                                    }
                                                                >
                                                                    <div className="profile-request-status-icon">
                                                                        {
                                                                            request.status
                                                                                .toUpperCase()
                                                                                === 'PENDING'
                                                                                ? (
                                                                                    <Clock3 size={17} />
                                                                                )
                                                                                : (
                                                                                    <CheckCircle2 size={17} />
                                                                                )
                                                                        }
                                                                    </div>

                                                                    <div className="profile-request-copy">
                                                                        <strong>
                                                                            {
                                                                                request.field_name
                                                                            }
                                                                        </strong>

                                                                        <span>
                                                                            Proposed:{' '}
                                                                            {
                                                                                request.proposed_value
                                                                            }
                                                                        </span>

                                                                        {
                                                                            request.reason && (
                                                                                <small>
                                                                                    {
                                                                                        request.reason
                                                                                    }
                                                                                </small>
                                                                            )
                                                                        }
                                                                    </div>

                                                                    <span
                                                                        className="profile-request-status"
                                                                        data-status={
                                                                            request.status
                                                                        }
                                                                    >
                                                                        {
                                                                            requestStatusLabel(
                                                                                request.status,
                                                                            )
                                                                        }
                                                                    </span>
                                                                </article>
                                                            ),
                                                        )
                                                    }
                                                </div>
                                            )
                                    }
                                </section>
                            </>
                        )}
                </section>
            )}


            {/* =================================================
          CHANGE REQUEST MODAL
          ================================================= */}

            {editingField && (
                <div
                    className="profile-modal-backdrop"
                    role="presentation"
                    onMouseDown={
                        (event) => {
                            if (
                                event.target
                                === event.currentTarget
                            ) {
                                cancelChangeRequest();
                            }
                        }
                    }
                >
                    <form
                        className="profile-change-modal"
                        onSubmit={
                            submitChangeRequest
                        }
                    >
                        <header className="profile-change-modal-header">
                            <div>
                                <span className="eyebrow">
                                    Health record correction
                                </span>

                                <h2>
                                    Request a change
                                </h2>

                                <p>
                                    Your request will be reviewed by an assigned
                                    clinician before the health record is updated.
                                </p>
                            </div>

                            <button
                                type="button"
                                className="icon-button"
                                title="Close"
                                aria-label="Close change request"
                                onClick={
                                    cancelChangeRequest
                                }
                            >
                                <X size={18} />
                            </button>
                        </header>


                        <div className="profile-change-modal-body">
                            <div className="profile-change-field-summary">
                                <span>
                                    Field
                                </span>

                                <strong>
                                    {
                                        editingLabel
                                        ?? editingField
                                    }
                                </strong>
                            </div>

                            <label>
                                <span>
                                    Proposed value
                                </span>

                                <input
                                    required
                                    maxLength={500}
                                    value={
                                        proposedValue
                                    }
                                    onChange={
                                        (event) =>
                                            setProposedValue(
                                                event.target.value,
                                            )
                                    }
                                />
                            </label>

                            <label>
                                <span>
                                    Reason
                                    <small>
                                        Optional
                                    </small>
                                </span>

                                <textarea
                                    rows={4}
                                    maxLength={2000}
                                    placeholder="Briefly explain why this information should be reviewed."
                                    value={
                                        reason
                                    }
                                    onChange={
                                        (event) =>
                                            setReason(
                                                event.target.value,
                                            )
                                    }
                                />
                            </label>
                        </div>


                        <footer className="profile-change-modal-footer">
                            <button
                                type="button"
                                className="button secondary"
                                onClick={
                                    cancelChangeRequest
                                }
                            >
                                Cancel
                            </button>

                            <button
                                type="submit"
                                className="button primary"
                                disabled={
                                    submittingRequest
                                    ||
                                    !proposedValue.trim()
                                }
                            >
                                {
                                    submittingRequest
                                        ? 'Submitting…'
                                        : 'Submit for review'
                                }

                                <ArrowRight size={16} />
                            </button>
                        </footer>
                    </form>
                </div>
            )}
        </>
    );
}
