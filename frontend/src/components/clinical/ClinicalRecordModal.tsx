import {
    Activity,
    CalendarDays,
    FilePlus2,
    HeartPulse,
    NotebookPen,
    Pill,
    Save,
    Stethoscope,
    TestTube2,
    X,
} from 'lucide-react';

import {
    useEffect,
    useState,
    type FormEvent,
} from 'react';

import {
    api,
} from '../../lib/api';

import type {
    ClinicalRecord,
} from '../../lib/types';


// =====================================================
// COMPONENT PROPS
// =====================================================

type Props = {
    patientId: string;

    record?: ClinicalRecord | null;

    onClose: () => void;

    onSaved: (
        record:
            ClinicalRecord,
    ) => void;
};


// =====================================================
// CLINICAL RECORD MODAL
// =====================================================

export function ClinicalRecordModal(
    {
        patientId,
        record,
        onClose,
        onSaved,
    }: Props,
) {
    const editing =
        Boolean(
            record,
        );

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
            art_start_date: '',

            age_at_art_initiation: '',

            last_regimen: '',

            days_of_arv_refill: '',

            current_viral_load: '',

            pregnancy_status: '',

            last_clinic_visit_date: '',

            notes: '',
        });


    // =================================================
    // POPULATE EDIT FORM
    // =================================================

    useEffect(
        () => {
            if (!record) {
                return;
            }

            setForm({
                art_start_date:
                    record.art_start_date
                    ?? '',

                age_at_art_initiation:
                    record.age_at_art_initiation
                        !== null
                        &&
                        record.age_at_art_initiation
                        !== undefined
                        ? String(
                            record.age_at_art_initiation,
                        )
                        : '',

                last_regimen:
                    record.last_regimen
                    ?? '',

                days_of_arv_refill:
                    record.days_of_arv_refill
                        !== null
                        &&
                        record.days_of_arv_refill
                        !== undefined
                        ? String(
                            record.days_of_arv_refill,
                        )
                        : '',

                current_viral_load:
                    record.current_viral_load
                        !== null
                        &&
                        record.current_viral_load
                        !== undefined
                        ? String(
                            record.current_viral_load,
                        )
                        : '',

                pregnancy_status:
                    record.pregnancy_status
                    ?? '',

                last_clinic_visit_date:
                    record.last_clinic_visit_date
                    ?? '',

                notes:
                    record.notes
                    ?? '',
            });
        },
        [
            record,
        ],
    );


    // =================================================
    // SERIALISE FORM VALUES
    // =================================================

    function payload() {
        return {
            art_start_date:
                form.art_start_date
                || null,

            age_at_art_initiation:
                form.age_at_art_initiation
                    ? Number(
                        form.age_at_art_initiation,
                    )
                    : null,

            last_regimen:
                form.last_regimen
                    .trim()
                || null,

            days_of_arv_refill:
                form.days_of_arv_refill
                    ? Number(
                        form.days_of_arv_refill,
                    )
                    : null,

            current_viral_load:
                form.current_viral_load
                    ? Number(
                        form.current_viral_load,
                    )
                    : null,

            pregnancy_status:
                form.pregnancy_status
                || null,

            last_clinic_visit_date:
                form.last_clinic_visit_date
                || null,

            notes:
                form.notes
                    .trim()
                || null,
        };
    }


    // =================================================
    // SAVE RECORD
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
            const saved =
                editing
                    &&
                    record
                    ? await api.updateClinicalRecord(
                        patientId,
                        record.id,
                        payload(),
                    )
                    : await api.createClinicalRecord(
                        patientId,
                        payload(),
                    );

            onSaved(
                saved,
            );

            onClose();
        } catch (
        errorValue
        ) {
            setError(
                errorValue instanceof Error
                    ? errorValue.message
                    : 'Unable to save clinical record.',
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
            className="clinical-modal-backdrop"
            role="presentation"
        >
            <form
                className="clinical-record-create-modal"
                onSubmit={submit}
            >

                {/* =========================================
                    HEADER
                    ========================================= */}

                <header className="clinical-record-modal-header">
                    <div className="clinical-record-modal-title">
                        <div className="clinical-record-modal-icon">
                            <Stethoscope size={21} />
                        </div>

                        <div>
                            <span className="eyebrow">
                                Clinical documentation
                            </span>

                            <h2>
                                {
                                    editing
                                        ? 'Edit latest clinical record'
                                        : 'Add clinical record'
                                }
                            </h2>

                            <p>
                                {
                                    editing
                                        ? (
                                            'Correct the latest stored clinical information. All changes are recorded in the audit trail.'
                                        )
                                        : (
                                            'Add a new longitudinal clinical record for this assigned synthetic patient.'
                                        )
                                }
                            </p>
                        </div>
                    </div>

                    <button
                        type="button"
                        className="clinical-modal-close"
                        aria-label="Close clinical record form"
                        disabled={busy}
                        onClick={onClose}
                    >
                        <X size={19} />
                    </button>
                </header>


                {/* =========================================
                    CLINICAL NOTICE
                    ========================================= */}

                <div className="clinical-record-notice">
                    <HeartPulse size={18} />

                    <div>
                        <strong>
                            Longitudinal clinical documentation
                        </strong>

                        <span>
                            {
                                editing
                                    ? (
                                        'You are correcting an existing clinical record. The original change context remains traceable through the audit log.'
                                    )
                                    : (
                                        'A new record will be added to the patient’s clinical history rather than replacing previous observations.'
                                    )
                            }
                        </span>
                    </div>
                </div>


                {/* =========================================
                    ART HISTORY
                    ========================================= */}

                <section className="clinical-record-form-section">
                    <div className="clinical-record-section-heading">
                        <CalendarDays size={17} />

                        <div>
                            <strong>
                                ART history
                            </strong>

                            <span>
                                Treatment initiation information
                            </span>
                        </div>
                    </div>

                    <div className="clinical-form-two-col">
                        <label className="clinical-form-field">
                            <span>
                                ART start date
                            </span>

                            <input
                                type="date"
                                value={
                                    form.art_start_date
                                }
                                onChange={
                                    (
                                        event,
                                    ) =>
                                        setForm({
                                            ...form,

                                            art_start_date:
                                                event.target.value,
                                        })
                                }
                            />
                        </label>


                        <label className="clinical-form-field">
                            <span>
                                Age at ART initiation
                            </span>

                            <input
                                type="number"
                                min={0}
                                max={120}
                                step="0.1"
                                placeholder="e.g. 31"
                                value={
                                    form.age_at_art_initiation
                                }
                                onChange={
                                    (
                                        event,
                                    ) =>
                                        setForm({
                                            ...form,

                                            age_at_art_initiation:
                                                event.target.value,
                                        })
                                }
                            />
                        </label>
                    </div>
                </section>


                {/* =========================================
                    TREATMENT
                    ========================================= */}

                <section className="clinical-record-form-section">
                    <div className="clinical-record-section-heading">
                        <Pill size={17} />

                        <div>
                            <strong>
                                Treatment
                            </strong>

                            <span>
                                Regimen and refill information
                            </span>
                        </div>
                    </div>

                    <div className="clinical-form-two-col">
                        <label className="clinical-form-field">
                            <span>
                                Last regimen
                            </span>

                            <input
                                maxLength={200}
                                placeholder="e.g. TDF/3TC/DTG"
                                value={
                                    form.last_regimen
                                }
                                onChange={
                                    (
                                        event,
                                    ) =>
                                        setForm({
                                            ...form,

                                            last_regimen:
                                                event.target.value,
                                        })
                                }
                            />
                        </label>


                        <label className="clinical-form-field">
                            <span>
                                ARV refill days
                            </span>

                            <input
                                type="number"
                                min={0}
                                step="1"
                                placeholder="e.g. 90"
                                value={
                                    form.days_of_arv_refill
                                }
                                onChange={
                                    (
                                        event,
                                    ) =>
                                        setForm({
                                            ...form,

                                            days_of_arv_refill:
                                                event.target.value,
                                        })
                                }
                            />
                        </label>
                    </div>
                </section>


                {/* =========================================
                    CURRENT CLINICAL STATE
                    ========================================= */}

                <section className="clinical-record-form-section">
                    <div className="clinical-record-section-heading">
                        <Activity size={17} />

                        <div>
                            <strong>
                                Current clinical state
                            </strong>

                            <span>
                                Latest recorded observations
                            </span>
                        </div>
                    </div>

                    <div className="clinical-form-two-col">
                        <label className="clinical-form-field">
                            <span>
                                Current viral load
                            </span>

                            <div className="clinical-input-with-unit">
                                <TestTube2 size={15} />

                                <input
                                    type="number"
                                    min={0}
                                    step="1"
                                    placeholder="e.g. 420"
                                    value={
                                        form.current_viral_load
                                    }
                                    onChange={
                                        (
                                            event,
                                        ) =>
                                            setForm({
                                                ...form,

                                                current_viral_load:
                                                    event.target.value,
                                            })
                                    }
                                />

                                <small>
                                    copies/mL
                                </small>
                            </div>
                        </label>


                        <label className="clinical-form-field">
                            <span>
                                Pregnancy status
                            </span>

                            <select
                                value={
                                    form.pregnancy_status
                                }
                                onChange={
                                    (
                                        event,
                                    ) =>
                                        setForm({
                                            ...form,

                                            pregnancy_status:
                                                event.target.value,
                                        })
                                }
                            >
                                <option value="">
                                    Not recorded
                                </option>

                                <option value="Not pregnant">
                                    Not pregnant
                                </option>

                                <option value="Pregnant">
                                    Pregnant
                                </option>

                                <option value="Not applicable">
                                    Not applicable
                                </option>
                            </select>
                        </label>
                    </div>


                    <label className="clinical-form-field">
                        <span>
                            Last clinic visit date
                        </span>

                        <input
                            type="date"
                            value={
                                form.last_clinic_visit_date
                            }
                            onChange={
                                (
                                    event,
                                ) =>
                                    setForm({
                                        ...form,

                                        last_clinic_visit_date:
                                            event.target.value,
                                    })
                            }
                        />
                    </label>
                </section>


                {/* =========================================
                    CLINICAL NOTES
                    ========================================= */}

                <section className="clinical-record-form-section">
                    <div className="clinical-record-section-heading">
                        <NotebookPen size={17} />

                        <div>
                            <strong>
                                Clinical notes
                            </strong>

                            <span>
                                Optional contextual information
                            </span>
                        </div>
                    </div>

                    <label className="clinical-form-field">
                        <textarea
                            rows={5}
                            maxLength={5000}
                            placeholder="Add optional clinical context, observations or follow-up notes..."
                            value={
                                form.notes
                            }
                            onChange={
                                (
                                    event,
                                ) =>
                                    setForm({
                                        ...form,

                                        notes:
                                            event.target.value,
                                    })
                            }
                        />

                        <small className="clinical-character-count">
                            {
                                form.notes.length
                            } / 5000
                        </small>
                    </label>
                </section>


                {/* =========================================
                    ERROR
                    ========================================= */}

                {error && (
                    <div className="form-error clinical-record-form-error">
                        {error}
                    </div>
                )}


                {/* =========================================
                    ACTIONS
                    ========================================= */}

                <footer className="clinical-record-modal-actions">
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
                        {
                            editing
                                ? (
                                    <Save size={17} />
                                )
                                : (
                                    <FilePlus2 size={17} />
                                )
                        }

                        {
                            busy
                                ? 'Saving record…'
                                : editing
                                    ? 'Save corrections'
                                    : 'Add clinical record'
                        }
                    </button>
                </footer>
            </form>
        </div>
    );
}
