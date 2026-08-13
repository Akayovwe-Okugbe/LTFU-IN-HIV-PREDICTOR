import {
    Activity,
    AlertTriangle,
    ArrowLeft,
    BrainCircuit,
    CalendarDays,
    CheckCircle2,
    Clock3,
    FileText,
    HeartPulse,
    MapPin,
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

    const [
        patient,
        setPatient,
    ] =
        useState<Patient | null>(
            null,
        );

    const [
        records,
        setRecords,
    ] =
        useState<
            ClinicalRecord[]
        >(
            [],
        );

    const [
        prediction,
        setPrediction,
    ] =
        useState<
            PredictionResponse | null
        >(
            null,
        );

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

                setError('');

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


    const latestRecord =
        useMemo(
            () =>
                records[0]
                ?? null,
            [
                records,
            ],
        );


    // ===================================================
    // EXPLICITLY GENERATE NEW PREDICTION
    // ===================================================

    async function predict() {
        setBusy(
            true,
        );

        setError('');

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


    return (
        <>
            <Link
                className="back-link dark"
                to="/app/patients"
            >
                <ArrowLeft size={16} />

                Back to patients
            </Link>


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

                    <FileText size={20} />
                </div>


                {
                    records.length
                        === 0
                        ? (
                            <div className="empty-mini">
                                <FileText />

                                <h3>
                                    No historical records
                                </h3>
                            </div>
                        )
                        : (
                            <div className="patient-record-table">
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
        </>
    );
}
