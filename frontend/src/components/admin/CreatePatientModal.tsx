import {
    CalendarDays,
    MapPin,
    ShieldCheck,
    UserPlus,
    UserRound,
    X,
} from 'lucide-react';

import {
    useState,
    type FormEvent,
} from 'react';

import {
    api,
} from '../../lib/api';

import type {
    AdminPatientSummary,
} from '../../lib/types';


// =====================================================
// COMPONENT PROPS
// =====================================================

type Props = {
    onClose: () => void;

    onCreated: (
        patient:
            AdminPatientSummary,
    ) => void;
};


// =====================================================
// CREATE SYNTHETIC PATIENT MODAL
// =====================================================

export function CreatePatientModal(
    {
        onClose,
        onCreated,
    }: Props,
) {
    const [
        busy,
        setBusy,
    ] =
        useState(false);

    const [
        error,
        setError,
    ] =
        useState('');

    const [
        form,
        setForm,
    ] =
        useState({
            synthetic_patient_number: '',

            first_name: '',

            last_name: '',

            date_of_birth: '',

            sex: '',

            state: '',

            lga: '',

            status: 'ACTIVE',
        });


    // =================================================
    // CREATE PATIENT
    // =================================================

    async function submit(
        event: FormEvent,
    ) {
        event.preventDefault();

        setBusy(
            true,
        );

        setError(
            '',
        );

        try {
            const patient =
                await api.adminCreatePatient({
                    synthetic_patient_number:
                        form
                            .synthetic_patient_number
                            .trim(),

                    first_name:
                        form
                            .first_name
                            .trim(),

                    last_name:
                        form
                            .last_name
                            .trim(),

                    date_of_birth:
                        form.date_of_birth
                        || null,

                    sex:
                        form.sex as
                        'Male'
                        |
                        'Female',

                    state:
                        form
                            .state
                            .trim(),

                    lga:
                        form
                            .lga
                            .trim(),

                    status:
                        form.status,
                });

            onCreated(
                patient,
            );

            onClose();
        } catch (
        errorValue
        ) {
            setError(
                errorValue instanceof Error
                    ? errorValue.message
                    : 'Unable to create synthetic patient.',
            );
        } finally {
            setBusy(
                false,
            );
        }
    }


    // =================================================
    // RENDER
    // =================================================

    return (
        <div
            className="admin-modal-backdrop"
            role="presentation"
        >
            <form
                className="admin-patient-create-modal"
                onSubmit={submit}
            >

                {/* =========================================
                    MODAL HEADER
                    ========================================= */}

                <header className="admin-patient-modal-header">
                    <div className="admin-patient-modal-title">
                        <div className="admin-patient-modal-icon">
                            <UserPlus size={21} />
                        </div>

                        <div>
                            <span className="eyebrow">
                                Patient administration
                            </span>

                            <h2>
                                Create synthetic patient
                            </h2>

                            <p>
                                Create the patient's administrative
                                profile. Clinical information is added
                                later by an assigned clinician.
                            </p>
                        </div>
                    </div>

                    <button
                        type="button"
                        className="admin-modal-close"
                        aria-label="Close create patient form"
                        onClick={onClose}
                    >
                        <X size={19} />
                    </button>
                </header>


                {/* =========================================
                    SYNTHETIC DATA NOTICE
                    ========================================= */}

                <div className="admin-patient-synthetic-note">
                    <ShieldCheck size={18} />

                    <div>
                        <strong>
                            Synthetic records only
                        </strong>

                        <span>
                            MEDISCOPE creates demonstration patient
                            identities only. No real patient data should
                            be entered in this prototype.
                        </span>
                    </div>
                </div>


                {/* =========================================
                    PATIENT IDENTIFIER
                    ========================================= */}

                <section className="admin-patient-form-section">
                    <div className="admin-patient-form-heading">
                        <UserRound size={17} />

                        <div>
                            <strong>
                                Patient identity
                            </strong>

                            <span>
                                Administrative identifiers and names
                            </span>
                        </div>
                    </div>


                    <label className="admin-form-field">
                        <span>
                            Synthetic patient number
                        </span>

                        <input
                            required
                            maxLength={50}
                            autoComplete="off"
                            placeholder="e.g. MED-000123"
                            value={
                                form
                                    .synthetic_patient_number
                            }
                            onChange={
                                (
                                    event,
                                ) =>
                                    setForm({
                                        ...form,

                                        synthetic_patient_number:
                                            event.target.value,
                                    })
                            }
                        />

                        <small>
                            Must be unique within MEDISCOPE.
                        </small>
                    </label>


                    <div className="admin-form-two-col">
                        <label className="admin-form-field">
                            <span>
                                First name
                            </span>

                            <input
                                required
                                maxLength={100}
                                autoComplete="off"
                                placeholder="First name"
                                value={
                                    form.first_name
                                }
                                onChange={
                                    (
                                        event,
                                    ) =>
                                        setForm({
                                            ...form,

                                            first_name:
                                                event.target.value,
                                        })
                                }
                            />
                        </label>


                        <label className="admin-form-field">
                            <span>
                                Last name
                            </span>

                            <input
                                required
                                maxLength={100}
                                autoComplete="off"
                                placeholder="Last name"
                                value={
                                    form.last_name
                                }
                                onChange={
                                    (
                                        event,
                                    ) =>
                                        setForm({
                                            ...form,

                                            last_name:
                                                event.target.value,
                                        })
                                }
                            />
                        </label>
                    </div>
                </section>


                {/* =========================================
                    DEMOGRAPHICS
                    ========================================= */}

                <section className="admin-patient-form-section">
                    <div className="admin-patient-form-heading">
                        <CalendarDays size={17} />

                        <div>
                            <strong>
                                Demographics
                            </strong>

                            <span>
                                Basic demographic information
                            </span>
                        </div>
                    </div>


                    <div className="admin-form-two-col">
                        <label className="admin-form-field">
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
                                    (
                                        event,
                                    ) =>
                                        setForm({
                                            ...form,

                                            date_of_birth:
                                                event.target.value,
                                        })
                                }
                            />
                        </label>


                        <label className="admin-form-field">
                            <span>
                                Sex
                            </span>

                            <select
                                required
                                value={
                                    form.sex
                                }
                                onChange={
                                    (
                                        event,
                                    ) =>
                                        setForm({
                                            ...form,

                                            sex:
                                                event.target.value,
                                        })
                                }
                            >
                                <option value="">
                                    Select sex
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
                </section>


                {/* =========================================
                    LOCATION
                    ========================================= */}

                <section className="admin-patient-form-section">
                    <div className="admin-patient-form-heading">
                        <MapPin size={17} />

                        <div>
                            <strong>
                                Location
                            </strong>

                            <span>
                                State and Local Government Area
                            </span>
                        </div>
                    </div>


                    <div className="admin-form-two-col">
                        <label className="admin-form-field">
                            <span>
                                State
                            </span>

                            <input
                                required
                                maxLength={100}
                                placeholder="e.g. Lagos"
                                value={
                                    form.state
                                }
                                onChange={
                                    (
                                        event,
                                    ) =>
                                        setForm({
                                            ...form,

                                            state:
                                                event.target.value,
                                        })
                                }
                            />
                        </label>


                        <label className="admin-form-field">
                            <span>
                                LGA
                            </span>

                            <input
                                required
                                maxLength={150}
                                placeholder="e.g. Ikeja"
                                value={
                                    form.lga
                                }
                                onChange={
                                    (
                                        event,
                                    ) =>
                                        setForm({
                                            ...form,

                                            lga:
                                                event.target.value,
                                        })
                                }
                            />
                        </label>
                    </div>
                </section>


                {/* =========================================
                    ERROR
                    ========================================= */}

                {error && (
                    <div className="form-error admin-patient-form-error">
                        {error}
                    </div>
                )}


                {/* =========================================
                    ACTIONS
                    ========================================= */}

                <footer className="admin-patient-modal-actions">
                    <button
                        type="button"
                        className="button secondary"
                        disabled={busy}
                        onClick={onClose}
                    >
                        Cancel
                    </button>

                    <button
                        type="submit"
                        className="button primary"
                        disabled={busy}
                    >
                        <UserPlus size={17} />

                        {
                            busy
                                ? 'Creating patient…'
                                : 'Create patient'
                        }
                    </button>
                </footer>
            </form>
        </div>
    );
}
