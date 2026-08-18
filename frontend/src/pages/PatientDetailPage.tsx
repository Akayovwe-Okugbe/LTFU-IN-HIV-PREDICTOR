import {
    Activity,
    AlertTriangle,
    ArrowLeft,
    BrainCircuit,
    CalendarDays,
    CheckCircle2,
    Clock3,
    FilePlus2,
    FileText,
    HeartPulse,
    MapPin,
    Pencil,
    Pill,
    ShieldAlert,
    Stethoscope,
    TestTube2,
    TrendingUp,
    UserRound,
} from 'lucide-react';

import {
    useEffect,
    useMemo,
    useState,
} from 'react';

import {
    Link,
    useNavigate,
    useParams,
} from 'react-router-dom';

import {
    PageHeader,
} from '../components/UI';

import {
    ClinicalRecordModal,
} from '../components/clinical/ClinicalRecordModal';

import {
    api,
} from '../lib/api';

import type {
    ClinicalRecord,
    Patient,
    PredictionResponse,
} from '../lib/types';


// =====================================================
// HELPERS
// =====================================================

function formatDate(
    value?: string | null,
): string {
    if (!value) {
        return 'Not recorded';
    }

    return new Date(
        `${value.slice(0, 10)}T00:00:00`,
    ).toLocaleDateString(
        [],
        {
            day: 'numeric',
            month: 'short',
            year: 'numeric',
        },
    );
}


function probability(
    value: number,
): string {
    return `${(
        value
        * 100
    ).toFixed(
        1,
    )}%`;
}


// =====================================================
// PAGE
// =====================================================

export default function PatientDetailPage() {
    const {
        id = '',
    } =
        useParams();

    const navigate =
        useNavigate();


    // =================================================
    // PATIENT STATE
    // =================================================

    const [
        patient,
        setPatient,
    ] =
        useState<Patient | null>(
            null,
        );


    // =================================================
    // CLINICAL RECORD STATE
    // =================================================

    const [
        records,
        setRecords,
    ] =
        useState<
            ClinicalRecord[]
        >(
            [],
        );


    // =================================================
    // CURRENT-SESSION PREDICTION STATE
    // =================================================

    const [
        prediction,
        setPrediction,
    ] =
        useState<
            PredictionResponse | null
        >(
            null,
        );


    // =================================================
    // PAGE / REQUEST STATE
    // =================================================

    const [
        loading,
        setLoading,
    ] =
        useState(true);

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


    // =================================================
    // CLINICAL RECORD MODAL STATE
    //
    // CREATE:
    //     Adds a new longitudinal clinical record.
    //
    // EDIT:
    //     Updates the current/latest clinical record.
    // =================================================

    const [
        recordModal,
        setRecordModal,
    ] =
        useState<
            'CREATE'
            |
            'EDIT'
            |
            null
        >(
            null,
        );


    // ===================================================
    // LOAD PATIENT + ALL CLINICAL RECORDS
    // ===================================================

    useEffect(
        () => {
            let active =
                true;

            async function load() {
                setLoading(
                    true,
                );

                setError(
                    '',
                );

                try {
                    const [
                        patientList,
                        clinicalRecords,
                    ] =
                        await Promise.all([
                            api.assignedPatients(),

                            api.clinicalRecords(
                                id,
                            ),
                        ]);

                    if (!active) {
                        return;
                    }

                    setPatient(
                        patientList.find(
                            (
                                item,
                            ) =>
                                item.id
                                === id,
                        )
                        ?? null,
                    );

                    setRecords(
                        clinicalRecords,
                    );
                } catch (
                errorValue
                ) {
                    if (active) {
                        setError(
                            errorValue instanceof Error
                                ? errorValue.message
                                : 'Unable to load the patient record.',
                        );
                    }
                } finally {
                    if (active) {
                        setLoading(
                            false,
                        );
                    }
                }
            }

            void load();

            return () => {
                active = false;
            };
        },
        [
            id,
        ],
    );


    // ===================================================
    // DETERMINE LATEST CLINICAL RECORD
    //
    // Do not rely solely on backend list ordering.
    // The most recently updated/created record is selected
    // for the current clinical-state summary and edit flow.
    // ===================================================

    const latestRecord =
        useMemo(
            () => {
                if (
                    records.length
                    === 0
                ) {
                    return null;
                }

                return [...records]
                    .sort(
                        (
                            first,
                            second,
                        ) =>
                            new Date(
                                second.updated_at
                                ??
                                second.created_at
                                ??
                                0,
                            ).getTime()
                            -
                            new Date(
                                first.updated_at
                                ??
                                first.created_at
                                ??
                                0,
                            ).getTime(),
                    )[0];
            },
            [
                records,
            ],
        );


    // ===================================================
    // EXPLICITLY GENERATE NEW PREDICTION
    //
    // A prediction is generated only when the clinician
    // deliberately requests it from this patient record.
    // Simply viewing the patient or intelligence page does
    // not create a new prediction.
    // ===================================================

    async function predict() {
        setBusy(
            true,
        );

        setError(
            '',
        );

        try {
            const response =
                await api.predictPatient(
                    id,
                );

            setPrediction(
                response,
            );
        } catch (
        errorValue
        ) {
            setError(
                errorValue instanceof Error
                    ? errorValue.message
                    : 'Unable to generate the prediction.',
            );
        } finally {
            setBusy(
                false,
            );
        }
    }


    // ===================================================
    // LOADING STATE
    // ===================================================

    if (loading) {
        return (
            <>
                <PageHeader
                    eyebrow="Clinical review"
                    title="Loading patient record…"
                    description="Retrieving assigned synthetic patient and longitudinal clinical information."
                />
            </>
        );
    }


    // ===================================================
    // RENDER
    // ===================================================

    return (
        <>
            {/* =================================================
                BACK NAVIGATION
                ================================================= */}

            <Link
                className="back-link dark"
                to="/app/patients"
            >
                <ArrowLeft size={16} />

                Back to patients
            </Link>


            {/* =================================================
                PAGE HEADER
                ================================================= */}

            <PageHeader
                eyebrow={
                    patient
                        ?.synthetic_patient_number
                    ??
                    'Patient'
                }
                title={
                    patient
                        ? `${patient.first_name} ${patient.last_name}`
                        : 'Patient profile'
                }
                description="Comprehensive synthetic clinical profile with longitudinal health records and model-assisted retention support."
                actions={
                    <div className="patient-header-actions">

                        {/* -------------------------------------
                            OPEN STORED ANALYTICAL INTELLIGENCE
                            ------------------------------------- */}

                        <button
                            type="button"
                            className="button secondary"
                            disabled={
                                !patient
                            }
                            onClick={
                                () =>
                                    navigate(
                                        `/app/patients/${id}/intelligence`,
                                    )
                            }
                        >
                            <TrendingUp size={17} />

                            View intelligence
                        </button>


                        {/* -------------------------------------
                            GENERATE FRESH PATIENT PREDICTION
                            ------------------------------------- */}

                        <button
                            type="button"
                            className="button primary"
                            onClick={predict}
                            disabled={
                                busy
                                ||
                                !patient
                            }
                        >
                            <BrainCircuit size={18} />

                            {
                                busy
                                    ? 'Running models…'
                                    : 'Generate fresh LTFU prediction'
                            }
                        </button>
                    </div>
                }
            />


            {/* =================================================
                PAGE ERROR
                ================================================= */}

            {error && (
                <div className="form-error page-message">
                    {error}
                </div>
            )}


            {/* =================================================
                PATIENT IDENTITY
                ================================================= */}

            {
                patient && (
                    <section className="patient-detail-hero">
                        <div className="patient-detail-avatar">
                            <UserRound size={27} />
                        </div>

                        <div>
                            <span className="eyebrow">
                                Patient identity
                            </span>

                            <h2>
                                {
                                    patient.first_name
                                }{' '}
                                {
                                    patient.last_name
                                }
                            </h2>

                            <strong>
                                {
                                    patient
                                        .synthetic_patient_number
                                }
                            </strong>

                            <div className="patient-detail-meta">
                                <span>
                                    {
                                        patient.sex
                                    }
                                </span>

                                <span>
                                    <MapPin size={13} />

                                    {
                                        patient.lga
                                    },{' '}
                                    {
                                        patient.state
                                    }
                                </span>

                                <span>
                                    Status:{' '}

                                    {
                                        patient.status
                                    }
                                </span>
                            </div>
                        </div>
                    </section>
                )
            }


            {/* =================================================
                PERSONAL + CURRENT CLINICAL SUMMARY
                ================================================= */}

            <div className="detail-grid enhanced-detail-grid">

                {/* ---------------------------------------------
                    DEMOGRAPHIC INFORMATION
                    --------------------------------------------- */}

                <section className="panel patient-detail-section">
                    <div className="panel-heading">
                        <div>
                            <span className="eyebrow">
                                Demographics
                            </span>

                            <h2>
                                Personal information
                            </h2>
                        </div>

                        <UserRound size={20} />
                    </div>


                    <div className="detail-list enhanced">
                        <div>
                            <CalendarDays />

                            <span>
                                Date of birth
                            </span>

                            <strong>
                                {
                                    formatDate(
                                        patient
                                            ?.date_of_birth,
                                    )
                                }
                            </strong>
                        </div>


                        <div>
                            <UserRound />

                            <span>
                                Sex
                            </span>

                            <strong>
                                {
                                    patient
                                        ?.sex
                                    ??
                                    'Not recorded'
                                }
                            </strong>
                        </div>


                        <div>
                            <MapPin />

                            <span>
                                State
                            </span>

                            <strong>
                                {
                                    patient
                                        ?.state
                                    ??
                                    'Not recorded'
                                }
                            </strong>
                        </div>


                        <div>
                            <MapPin />

                            <span>
                                LGA
                            </span>

                            <strong>
                                {
                                    patient
                                        ?.lga
                                    ??
                                    'Not recorded'
                                }
                            </strong>
                        </div>
                    </div>
                </section>


                {/* ---------------------------------------------
                    LATEST CLINICAL STATE
                    --------------------------------------------- */}

                <section className="panel patient-detail-section">
                    <div className="panel-heading">
                        <div>
                            <span className="eyebrow">
                                Latest record
                            </span>

                            <h2>
                                Current clinical state
                            </h2>
                        </div>

                        <HeartPulse size={20} />
                    </div>


                    {
                        latestRecord
                            ? (
                                <div className="detail-list enhanced">

                                    <div>
                                        <Pill />

                                        <span>
                                            Last regimen
                                        </span>

                                        <strong>
                                            {
                                                latestRecord
                                                    .last_regimen
                                                ??
                                                'Not recorded'
                                            }
                                        </strong>
                                    </div>


                                    <div>
                                        <TestTube2 />

                                        <span>
                                            Current viral load
                                        </span>

                                        <strong>
                                            {
                                                latestRecord
                                                    .current_viral_load
                                                    !== null
                                                    &&
                                                    latestRecord
                                                        .current_viral_load
                                                    !== undefined
                                                    ? `${latestRecord.current_viral_load.toLocaleString()} copies/mL`
                                                    : 'Not recorded'
                                            }
                                        </strong>
                                    </div>


                                    <div>
                                        <Clock3 />

                                        <span>
                                            ARV refill
                                        </span>

                                        <strong>
                                            {
                                                latestRecord
                                                    .days_of_arv_refill
                                                    !== null
                                                    &&
                                                    latestRecord
                                                        .days_of_arv_refill
                                                    !== undefined
                                                    ? `${latestRecord.days_of_arv_refill} days`
                                                    : 'Not recorded'
                                            }
                                        </strong>
                                    </div>


                                    <div>
                                        <CalendarDays />

                                        <span>
                                            Last clinic visit
                                        </span>

                                        <strong>
                                            {
                                                formatDate(
                                                    latestRecord
                                                        .last_clinic_visit_date,
                                                )
                                            }
                                        </strong>
                                    </div>


                                    <div>
                                        <Stethoscope />

                                        <span>
                                            ART start date
                                        </span>

                                        <strong>
                                            {
                                                formatDate(
                                                    latestRecord
                                                        .art_start_date,
                                                )
                                            }
                                        </strong>
                                    </div>


                                    <div>
                                        <Activity />

                                        <span>
                                            Pregnancy status
                                        </span>

                                        <strong>
                                            {
                                                latestRecord
                                                    .pregnancy_status
                                                ??
                                                'Not recorded'
                                            }
                                        </strong>
                                    </div>
                                </div>
                            )
                            : (
                                <div className="empty-mini">
                                    <FileText />

                                    <h3>
                                        No clinical record
                                    </h3>

                                    <p>
                                        Clinical information has not yet been
                                        stored for this patient.
                                    </p>
                                </div>
                            )
                    }
                </section>
            </div>


            {/* =================================================
                FRESH PREDICTION
                ================================================= */}

            <section className="panel patient-live-prediction-panel">
                <div className="panel-heading">
                    <div>
                        <span className="eyebrow">
                            Current session
                        </span>

                        <h2>
                            LTFU prediction
                        </h2>

                        <p>
                            A new prediction is only generated when the
                            clinician deliberately requests it.
                        </p>
                    </div>

                    <BrainCircuit size={22} />
                </div>


                {
                    prediction
                        ? (
                            <>
                                {/* -------------------------------------
                                    AGREEMENT STATE
                                    ------------------------------------- */}

                                <div
                                    className="patient-live-agreement"
                                    data-agreement={
                                        prediction
                                            .agreement_status
                                    }
                                >
                                    {
                                        prediction
                                            .agreement_status
                                            === 'AGREE'
                                            ? (
                                                <CheckCircle2 size={22} />
                                            )
                                            : (
                                                <AlertTriangle size={22} />
                                            )
                                    }


                                    <div>
                                        <span>
                                            Model relationship
                                        </span>

                                        <strong>
                                            {
                                                prediction
                                                    .agreement_status
                                                    === 'AGREE'
                                                    ? 'Models agree'
                                                    : 'Models disagree'
                                            }
                                        </strong>

                                        <small>
                                            {
                                                prediction
                                                    .overall_summary
                                            }
                                        </small>
                                    </div>
                                </div>


                                {/* -------------------------------------
                                    MODEL COMPARISON
                                    ------------------------------------- */}

                                <div className="patient-live-model-grid">
                                    <div>
                                        <span>
                                            Logistic Regression
                                        </span>

                                        <strong>
                                            {
                                                probability(
                                                    prediction
                                                        .logistic_regression
                                                        .probability,
                                                )
                                            }
                                        </strong>

                                        <small>
                                            {
                                                prediction
                                                    .logistic_regression
                                                    .classification
                                            }
                                        </small>
                                    </div>


                                    <div>
                                        <span>
                                            XGBoost
                                        </span>

                                        <strong>
                                            {
                                                probability(
                                                    prediction
                                                        .xgboost
                                                        .probability,
                                                )
                                            }
                                        </strong>

                                        <small>
                                            {
                                                prediction
                                                    .xgboost
                                                    .classification
                                            }
                                        </small>
                                    </div>
                                </div>


                                {/* -------------------------------------
                                    CLINICAL DISCLAIMER
                                    ------------------------------------- */}

                                <div className="disclaimer enhanced">
                                    <ShieldAlert size={18} />

                                    <span>
                                        {
                                            prediction
                                                .clinical_disclaimer
                                        }
                                    </span>
                                </div>
                            </>
                        )
                        : (
                            <div className="empty-mini">
                                <BrainCircuit />

                                <h3>
                                    No new prediction in this session
                                </h3>

                                <p>
                                    Generate both model outputs only when
                                    clinical review is appropriate.
                                </p>
                            </div>
                        )
                }
            </section>


            {/* =================================================
                COMPLETE CLINICAL HISTORY
                ================================================= */}

            <section className="panel patient-record-history">
                <div className="panel-heading">

                    {/* -----------------------------------------
                        HISTORY HEADING
                        ----------------------------------------- */}

                    <div>
                        <span className="eyebrow">
                            Longitudinal record
                        </span>

                        <h2>
                            Clinical history
                        </h2>

                        <p>
                            {
                                records.length
                            } clinical record{
                                records.length === 1
                                    ? ''
                                    : 's'
                            } available.
                        </p>
                    </div>


                    {/* -----------------------------------------
                        CLINICAL RECORD ACTIONS
                        ----------------------------------------- */}

                    <div className="patient-record-heading-actions">
                        <FileText size={20} />

                        <div className="patient-record-actions">

                            {/* CREATE A NEW LONGITUDINAL RECORD */}

                            <button
                                type="button"
                                className="button secondary"
                                disabled={
                                    !patient
                                }
                                onClick={
                                    () =>
                                        setRecordModal(
                                            'CREATE',
                                        )
                                }
                            >
                                <FilePlus2 size={16} />

                                Add clinical record
                            </button>


                            {/* EDIT THE CURRENT/LATEST RECORD */}

                            {
                                latestRecord && (
                                    <button
                                        type="button"
                                        className="button secondary"
                                        onClick={
                                            () =>
                                                setRecordModal(
                                                    'EDIT',
                                                )
                                        }
                                    >
                                        <Pencil size={16} />

                                        Edit latest
                                    </button>
                                )
                            }
                        </div>
                    </div>
                </div>


                {/* ---------------------------------------------
                    HISTORY EMPTY STATE
                    --------------------------------------------- */}

                {
                    records.length
                        === 0
                        ? (
                            <div className="empty-mini">
                                <FileText />

                                <h3>
                                    No historical records
                                </h3>

                                <p>
                                    Add the patient's first clinical
                                    record to begin longitudinal
                                    documentation.
                                </p>

                                <button
                                    type="button"
                                    className="button secondary"
                                    disabled={
                                        !patient
                                    }
                                    onClick={
                                        () =>
                                            setRecordModal(
                                                'CREATE',
                                            )
                                    }
                                >
                                    <FilePlus2 size={16} />

                                    Add first clinical record
                                </button>
                            </div>
                        )
                        : (
                            <div className="patient-record-table">

                                {/* ---------------------------------
                                    TABLE HEADER
                                    --------------------------------- */}

                                <div className="patient-record-row header">
                                    <span>
                                        Visit
                                    </span>

                                    <span>
                                        Regimen
                                    </span>

                                    <span>
                                        Refill
                                    </span>

                                    <span>
                                        Viral load
                                    </span>

                                    <span>
                                        Pregnancy
                                    </span>
                                </div>


                                {/* ---------------------------------
                                    CLINICAL HISTORY ROWS
                                    --------------------------------- */}

                                {
                                    records.map(
                                        (
                                            record,
                                        ) => (
                                            <div
                                                className="patient-record-row"
                                                key={
                                                    record.id
                                                }
                                            >
                                                <span>
                                                    {
                                                        formatDate(
                                                            record
                                                                .last_clinic_visit_date,
                                                        )
                                                    }
                                                </span>


                                                <strong>
                                                    {
                                                        record
                                                            .last_regimen
                                                        ??
                                                        '—'
                                                    }
                                                </strong>


                                                <span>
                                                    {
                                                        record
                                                            .days_of_arv_refill
                                                            !== null
                                                            &&
                                                            record
                                                                .days_of_arv_refill
                                                            !== undefined
                                                            ? `${record.days_of_arv_refill} days`
                                                            : '—'
                                                    }
                                                </span>


                                                <span>
                                                    {
                                                        record
                                                            .current_viral_load
                                                            !== null
                                                            &&
                                                            record
                                                                .current_viral_load
                                                            !== undefined
                                                            ? record
                                                                .current_viral_load
                                                                .toLocaleString()
                                                            : '—'
                                                    }
                                                </span>


                                                <span>
                                                    {
                                                        record
                                                            .pregnancy_status
                                                        ??
                                                        '—'
                                                    }
                                                </span>
                                            </div>
                                        ),
                                    )
                                }
                            </div>
                        )
                }
            </section>


            {/* =================================================
                CLINICAL RECORD CREATE / EDIT MODAL

                IMPORTANT:
                This deliberately sits at page level, outside
                the panels above.

                CREATE:
                    Adds the returned record immediately to the
                    local longitudinal record list.

                EDIT:
                    Replaces the edited record in local state so
                    the latest clinical summary and history
                    update immediately without requiring a page
                    refresh.
                ================================================= */}

            {recordModal && (
                <ClinicalRecordModal
                    patientId={
                        id
                    }
                    record={
                        recordModal
                            === 'EDIT'
                            ? latestRecord
                            : null
                    }
                    onClose={
                        () =>
                            setRecordModal(
                                null,
                            )
                    }
                    onSaved={
                        (
                            savedRecord,
                        ) => {
                            setRecords(
                                (
                                    current,
                                ) => {
                                    // ---------------------------------
                                    // UPDATE EXISTING RECORD
                                    // ---------------------------------

                                    if (
                                        recordModal
                                        === 'EDIT'
                                    ) {
                                        return current.map(
                                            (
                                                item,
                                            ) =>
                                                item.id
                                                    === savedRecord.id
                                                    ? savedRecord
                                                    : item,
                                        );
                                    }


                                    // ---------------------------------
                                    // ADD NEW LONGITUDINAL RECORD
                                    // ---------------------------------

                                    return [
                                        savedRecord,
                                        ...current,
                                    ];
                                },
                            );
                        }
                    }
                />
            )}
        </>
    );
}
