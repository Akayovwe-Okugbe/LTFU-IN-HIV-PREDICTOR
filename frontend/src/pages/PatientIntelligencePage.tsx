import {
    Activity,
    AlertTriangle,
    ArrowLeft,
    BrainCircuit,
    CalendarDays,
    CheckCircle2,
    Clock3,
    Database,
    FileText,
    HeartPulse,
    MapPin,
    Pill,
    ShieldCheck,
    Stethoscope,
    TrendingUp,
    UserRound,
} from 'lucide-react';

import {
    useEffect,
    useMemo,
    useState,
} from 'react';

import {
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
    ClinicianPatientIntelligence,
} from '../lib/types';


// =====================================================
// PRESENTATION HELPERS
// =====================================================

function humaniseValue(
    value: string,
): string {
    return value
        .replaceAll(
            '_',
            ' ',
        )
        .toLowerCase()
        .replace(
            /\b\w/g,
            (
                character,
            ) =>
                character.toUpperCase(),
        );
}


function formatDate(
    value?: string | null,
): string {
    if (!value) {
        return 'Not recorded';
    }

    const date =
        new Date(
            `${value.slice(0, 10)}T00:00:00`,
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


function formatDateTime(
    value?: string | null,
): string {
    if (!value) {
        return 'Not recorded';
    }

    const date =
        new Date(
            value,
        );

    if (
        Number.isNaN(
            date.getTime(),
        )
    ) {
        return value;
    }

    return date.toLocaleString(
        [],
        {
            day: 'numeric',
            month: 'short',
            year: 'numeric',
            hour: '2-digit',
            minute: '2-digit',
        },
    );
}


function formatProbability(
    value?: number | null,
): string {
    if (
        value === null
        ||
        value === undefined
    ) {
        return '—';
    }

    return `${Math.round(
        value
        * 100,
    )}%`;
}


function formatNumber(
    value?: number | null,
): string {
    if (
        value === null
        ||
        value === undefined
    ) {
        return 'Not recorded';
    }

    return new Intl.NumberFormat().format(
        value,
    );
}


/**
 * Calculate patient age for display only.
 *
 * This derived value is not persisted and is not used by
 * the MEDISCOPE prediction engine.
 */
function calculateAge(
    dateOfBirth?: string | null,
): number | null {
    if (!dateOfBirth) {
        return null;
    }

    const birth =
        new Date(
            `${dateOfBirth}T00:00:00`,
        );

    if (
        Number.isNaN(
            birth.getTime(),
        )
    ) {
        return null;
    }

    const today =
        new Date();

    let age =
        today.getFullYear()
        -
        birth.getFullYear();

    const monthDifference =
        today.getMonth()
        -
        birth.getMonth();

    if (
        monthDifference < 0
        ||
        (
            monthDifference === 0
            &&
            today.getDate()
            <
            birth.getDate()
        )
    ) {
        age -= 1;
    }

    return age;
}


/**
 * Derive the presentation state used for the latest stored
 * LTFU assessment.
 *
 * The stored prediction threshold is always respected.
 * MEDISCOPE does not invent additional arbitrary risk
 * categories on this page.
 */
function predictionState(
    prediction:
        ClinicianPatientIntelligence[
        'latest_prediction'
        ],
): string {
    if (!prediction) {
        return 'NO_STORED_ASSESSMENT';
    }

    const logisticAbove =
        prediction.logistic_probability
        >=
        prediction.threshold_used;

    const xgboostAbove =
        prediction.xgboost_probability
        >=
        prediction.threshold_used;

    if (
        logisticAbove
        &&
        xgboostAbove
    ) {
        return 'BOTH_ABOVE_THRESHOLD';
    }

    if (
        logisticAbove
        !== xgboostAbove
    ) {
        return 'MODEL_DISAGREEMENT';
    }

    return 'BOTH_BELOW_THRESHOLD';
}


function predictionStateLabel(
    state: string,
): string {
    switch (state) {
        case 'BOTH_ABOVE_THRESHOLD':
            return 'Both models above threshold';

        case 'MODEL_DISAGREEMENT':
            return 'Models disagree';

        case 'BOTH_BELOW_THRESHOLD':
            return 'Both models below threshold';

        case 'NO_STORED_ASSESSMENT':
            return 'No stored assessment';

        default:
            return humaniseValue(
                state,
            );
    }
}


// =====================================================
// MODEL PROBABILITY PANEL
// =====================================================

function ModelProbability(
    {
        label,
        probability,
        classification,
        threshold,
        model,
    }: {
        label: string;

        probability: number;

        classification: string;

        threshold: number;

        model:
        | 'logistic'
        | 'xgboost';
    },
) {
    const percentage =
        Math.max(
            0,
            Math.min(
                100,
                probability
                * 100,
            ),
        );

    const thresholdPercentage =
        Math.max(
            0,
            Math.min(
                100,
                threshold
                * 100,
            ),
        );

    return (
        <article className="patient-model-card">
            <div className="patient-model-heading">
                <div>
                    <span>
                        {label}
                    </span>

                    <strong>
                        {
                            formatProbability(
                                probability,
                            )
                        }
                    </strong>
                </div>

                <span
                    className="patient-model-classification"
                    data-model={
                        model
                    }
                >
                    {
                        humaniseValue(
                            classification,
                        )
                    }
                </span>
            </div>

            <div className="patient-model-track">
                <i
                    className={
                        model
                    }
                    style={{
                        width:
                            `${percentage}%`,
                    }}
                />

                <b
                    style={{
                        left:
                            `${thresholdPercentage}%`,
                    }}
                    title={
                        `Stored threshold: ${Math.round(
                            threshold
                            * 100,
                        )}%`
                    }
                />
            </div>

            <div className="patient-model-scale">
                <span>
                    0%
                </span>

                <span>
                    Threshold{' '}
                    {
                        Math.round(
                            threshold
                            * 100,
                        )
                    }%
                </span>

                <span>
                    100%
                </span>
            </div>
        </article>
    );
}


// =====================================================
// CLINICAL VALUE
// =====================================================

function ClinicalValue(
    {
        label,
        value,
        note,
    }: {
        label: string;

        value: string;

        note?: string;
    },
) {
    return (
        <div className="patient-clinical-value">
            <span>
                {label}
            </span>

            <strong>
                {value}
            </strong>

            {
                note && (
                    <small>
                        {note}
                    </small>
                )
            }
        </div>
    );
}


// =====================================================
// CLINICAL HISTORY ITEM
// =====================================================

function ClinicalHistoryEntry(
    {
        record,
        index,
    }: {
        record: ClinicalRecord;

        index: number;
    },
) {
    return (
        <article className="clinical-history-entry">
            <div className="clinical-history-marker">
                <span />

                {
                    index > 0 && (
                        <i />
                    )
                }
            </div>

            <div className="clinical-history-card">
                <header>
                    <div>
                        <span className="eyebrow">
                            Clinical record
                        </span>

                        <strong>
                            {
                                formatDate(
                                    record
                                        .last_clinic_visit_date
                                    ??
                                    record.created_at
                                    ??
                                    null,
                                )
                            }
                        </strong>
                    </div>

                    <small>
                        {
                            record.created_at
                                ? formatDateTime(
                                    record.created_at,
                                )
                                : ''
                        }
                    </small>
                </header>

                <div className="clinical-history-grid">
                    <ClinicalValue
                        label="Regimen"
                        value={
                            record.last_regimen
                            || 'Not recorded'
                        }
                    />

                    <ClinicalValue
                        label="Viral load"
                        value={
                            record.current_viral_load
                                !== null
                                &&
                                record.current_viral_load
                                !== undefined
                                ? `${formatNumber(
                                    record.current_viral_load,
                                )} copies/mL`
                                : 'Not recorded'
                        }
                    />

                    <ClinicalValue
                        label="ARV refill"
                        value={
                            record.days_of_arv_refill
                                !== null
                                &&
                                record.days_of_arv_refill
                                !== undefined
                                ? `${record.days_of_arv_refill} days`
                                : 'Not recorded'
                        }
                    />

                    <ClinicalValue
                        label="Pregnancy status"
                        value={
                            record.pregnancy_status
                            || 'Not recorded'
                        }
                    />
                </div>

                {
                    record.notes && (
                        <p className="clinical-history-note">
                            {record.notes}
                        </p>
                    )
                }
            </div>
        </article>
    );
}


// =====================================================
// PREDICTION HISTORY CHART
// =====================================================

function PredictionHistoryChart(
    {
        predictions,
    }: {
        predictions:
        ClinicianPatientIntelligence[
        'prediction_history'
        ];
    },
) {
    const ordered =
        useMemo(
            () =>
                [...predictions]
                    .sort(
                        (
                            first,
                            second,
                        ) =>
                            new Date(
                                first.generated_at,
                            ).getTime()
                            -
                            new Date(
                                second.generated_at,
                            ).getTime(),
                    )
                    .slice(
                        -8,
                    ),
            [
                predictions,
            ],
        );


    if (
        ordered.length === 0
    ) {
        return (
            <div className="patient-intelligence-empty">
                <TrendingUp size={22} />

                <strong>
                    No prediction history
                </strong>

                <span>
                    Stored prediction history will appear here
                    after assessments have been generated.
                </span>
            </div>
        );
    }


    return (
        <div className="patient-risk-history">
            <div className="patient-risk-history-legend">
                <span>
                    <i className="logistic" />

                    Logistic Regression
                </span>

                <span>
                    <i className="xgboost" />

                    XGBoost
                </span>
            </div>


            <div className="patient-risk-history-chart">
                {
                    ordered.map(
                        (
                            prediction,
                        ) => (
                            <div
                                className="patient-risk-history-column"
                                key={
                                    prediction.id
                                }
                            >
                                <div className="patient-risk-history-bars">
                                    <i
                                        className="logistic"
                                        title={
                                            `Logistic Regression ${formatProbability(
                                                prediction
                                                    .logistic_probability,
                                            )}`
                                        }
                                        style={{
                                            height:
                                                `${Math.max(
                                                    4,
                                                    prediction
                                                        .logistic_probability
                                                    * 100,
                                                )}%`,
                                        }}
                                    />

                                    <i
                                        className="xgboost"
                                        title={
                                            `XGBoost ${formatProbability(
                                                prediction
                                                    .xgboost_probability,
                                            )}`
                                        }
                                        style={{
                                            height:
                                                `${Math.max(
                                                    4,
                                                    prediction
                                                        .xgboost_probability
                                                    * 100,
                                                )}%`,
                                        }}
                                    />
                                </div>

                                <strong>
                                    {
                                        new Date(
                                            prediction
                                                .generated_at,
                                        )
                                            .toLocaleDateString(
                                                [],
                                                {
                                                    month:
                                                        'short',

                                                    day:
                                                        'numeric',
                                                },
                                            )
                                    }
                                </strong>

                                <span>
                                    {
                                        humaniseValue(
                                            prediction
                                                .agreement_status,
                                        )
                                    }
                                </span>
                            </div>
                        ),
                    )
                }
            </div>
        </div>
    );
}


// =====================================================
// PAGE
// =====================================================

export default function PatientIntelligencePage() {
    const navigate =
        useNavigate();

    const {
        patientId,
    } =
        useParams<{
            patientId: string;
        }>();


    // ===================================================
    // STATE
    // ===================================================

    const [
        intelligence,
        setIntelligence,
    ] =
        useState<
            ClinicianPatientIntelligence | null
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

    const [
        error,
        setError,
    ] =
        useState(
            '',
        );


    // ===================================================
    // LOAD PATIENT INTELLIGENCE
    //
    // IMPORTANT:
    // This endpoint reads stored analytical evidence only.
    // Opening this page must never generate a prediction.
    // ===================================================

    useEffect(
        () => {
            let active =
                true;

            async function load() {
                if (!patientId) {
                    setError(
                        'A patient identifier was not provided.',
                    );

                    setLoading(
                        false,
                    );

                    return;
                }

                setLoading(
                    true,
                );

                setError(
                    '',
                );

                try {
                    const response =
                        await api.clinicianPatientIntelligence(
                            patientId,
                        );

                    if (!active) {
                        return;
                    }

                    setIntelligence(
                        response,
                    );
                } catch (
                errorValue
                ) {
                    if (!active) {
                        return;
                    }

                    setError(
                        errorValue instanceof Error
                            ? errorValue.message
                            : 'Unable to load patient intelligence.',
                    );
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
            patientId,
        ],
    );


    // ===================================================
    // LOADING
    // ===================================================

    if (loading) {
        return (
            <>
                <PageHeader
                    eyebrow="Patient intelligence"
                    title="Preparing clinical intelligence…"
                    description="Loading patient demographics, clinical history and stored LTFU assessments."
                />

                <div className="patient-intelligence-loading">
                    <BrainCircuit size={27} />

                    <strong>
                        Loading patient intelligence
                    </strong>

                    <span>
                        Retrieving longitudinal clinical and
                        stored prediction information…
                    </span>
                </div>
            </>
        );
    }


    // ===================================================
    // ERROR / ACCESS FAILURE
    // ===================================================

    if (
        error
        ||
        !intelligence
    ) {
        return (
            <>
                <PageHeader
                    eyebrow="Patient intelligence"
                    title="Unable to open patient"
                    description="Only patients actively assigned to your clinician account may be viewed here."
                />

                <div className="form-error">
                    {
                        error
                        || 'Patient intelligence is unavailable.'
                    }
                </div>

                <button
                    type="button"
                    className="button secondary"
                    onClick={
                        () =>
                            navigate(
                                '/app/patients',
                            )
                    }
                >
                    <ArrowLeft size={16} />

                    Back to assigned patients
                </button>
            </>
        );
    }


    // ===================================================
    // RESPONSE DESTRUCTURING
    // ===================================================

    const {
        patient,

        latest_clinical_record:
        latestRecord,

        clinical_history:
        clinicalHistory,

        latest_prediction:
        latestPrediction,

        prediction_history:
        predictionHistory,

        missing_features:
        missingFeatures,
    } =
        intelligence;


    const age =
        calculateAge(
            patient.date_of_birth,
        );


    const state =
        predictionState(
            latestPrediction,
        );


    const predictionComplete =
        missingFeatures.length === 0;


    // ===================================================
    // RENDER
    // ===================================================

    return (
        <>
            {/* =================================================
                PATIENT WORKSPACE NAVIGATION

                Patient Detail:
                    operational record, full clinical review,
                    deliberate generation of a fresh prediction.

                Patient Intelligence:
                    stored predictions, longitudinal analytics,
                    agreement/disagreement, data quality and
                    reproducibility.

                This separation prevents analytical page views
                from silently generating prediction records.
                ================================================= */}

            <div className="patient-intelligence-navigation">
                <button
                    type="button"
                    className="patient-intelligence-back"
                    onClick={
                        () =>
                            navigate(
                                `/app/patients/${patientId}`,
                            )
                    }
                >
                    <ArrowLeft size={16} />

                    Patient record
                </button>

                <button
                    type="button"
                    className="text-button"
                    onClick={
                        () =>
                            navigate(
                                '/app/patients',
                            )
                    }
                >
                    All assigned patients
                </button>
            </div>


            {/* =================================================
                PATIENT HERO
                ================================================= */}

            <section className="patient-intelligence-hero">
                <div className="patient-intelligence-avatar">
                    <UserRound size={28} />
                </div>

                <div className="patient-intelligence-identity">
                    <span className="eyebrow">
                        Longitudinal clinical intelligence
                    </span>

                    <div className="patient-intelligence-title-row">
                        <h1>
                            {
                                patient.first_name
                            }{' '}
                            {
                                patient.last_name
                            }
                        </h1>

                        <span
                            className="patient-status-chip"
                            data-status={
                                patient.status
                            }
                        >
                            {
                                humaniseValue(
                                    patient.status,
                                )
                            }
                        </span>
                    </div>

                    <strong>
                        {
                            patient
                                .synthetic_patient_number
                        }
                    </strong>

                    <div className="patient-intelligence-meta">
                        <span>
                            <UserRound size={14} />

                            {
                                patient.sex
                            }

                            {
                                age !== null
                                    ? ` · ${age} years`
                                    : ''
                            }
                        </span>

                        <span>
                            <MapPin size={14} />

                            {
                                patient.state
                            }

                            {' · '}

                            {
                                patient.lga
                            }
                        </span>

                        <span>
                            <ShieldCheck size={14} />

                            Synthetic patient
                        </span>
                    </div>

                    <div className="patient-intelligence-hero-actions">
                        <button
                            type="button"
                            className="text-button"
                            onClick={
                                () =>
                                    navigate(
                                        `/app/patients/${patientId}`,
                                    )
                            }
                        >
                            <FileText size={14} />

                            Open clinical record
                        </button>
                    </div>
                </div>
            </section>


            {/* =================================================
                CLINICAL SNAPSHOT
                ================================================= */}

            <section className="patient-snapshot-grid">

                {/* -------------------------------------------
                    LAST CLINIC VISIT
                    ------------------------------------------- */}

                <div className="patient-snapshot-card">
                    <div className="patient-snapshot-icon">
                        <CalendarDays size={19} />
                    </div>

                    <span>
                        Last clinic visit
                    </span>

                    <strong>
                        {
                            formatDate(
                                latestRecord
                                    ?.last_clinic_visit_date,
                            )
                        }
                    </strong>

                    <small>
                        Most recent stored record
                    </small>
                </div>


                {/* -------------------------------------------
                    VIRAL LOAD
                    ------------------------------------------- */}

                <div className="patient-snapshot-card">
                    <div className="patient-snapshot-icon viral">
                        <Activity size={19} />
                    </div>

                    <span>
                        Viral load
                    </span>

                    <strong>
                        {
                            latestRecord
                                ?.current_viral_load
                                !== null
                                &&
                                latestRecord
                                    ?.current_viral_load
                                !== undefined
                                ? formatNumber(
                                    latestRecord
                                        .current_viral_load,
                                )
                                : '—'
                        }
                    </strong>

                    <small>
                        copies/mL
                    </small>
                </div>


                {/* -------------------------------------------
                    ARV REFILL
                    ------------------------------------------- */}

                <div className="patient-snapshot-card">
                    <div className="patient-snapshot-icon refill">
                        <Pill size={19} />
                    </div>

                    <span>
                        ARV refill
                    </span>

                    <strong>
                        {
                            latestRecord
                                ?.days_of_arv_refill
                                !== null
                                &&
                                latestRecord
                                    ?.days_of_arv_refill
                                !== undefined
                                ? `${latestRecord.days_of_arv_refill} days`
                                : '—'
                        }
                    </strong>

                    <small>
                        Latest recorded duration
                    </small>
                </div>


                {/* -------------------------------------------
                    REGIMEN
                    ------------------------------------------- */}

                <div className="patient-snapshot-card">
                    <div className="patient-snapshot-icon regimen">
                        <Stethoscope size={19} />
                    </div>

                    <span>
                        Latest regimen
                    </span>

                    <strong>
                        {
                            latestRecord
                                ?.last_regimen
                            || 'Not recorded'
                        }
                    </strong>

                    <small>
                        Current stored clinical record
                    </small>
                </div>
            </section>


            {/* =================================================
                PATIENT + CLINICAL INFORMATION
                ================================================= */}

            <section className="patient-intelligence-main-grid">

                {/* -------------------------------------------
                    DEMOGRAPHICS
                    ------------------------------------------- */}

                <article className="panel patient-detail-panel">
                    <div className="patient-panel-heading">
                        <div>
                            <span className="eyebrow">
                                Patient profile
                            </span>

                            <h2>
                                Personal information
                            </h2>
                        </div>

                        <UserRound size={20} />
                    </div>

                    <div className="patient-detail-grid">
                        <ClinicalValue
                            label="Patient number"
                            value={
                                patient
                                    .synthetic_patient_number
                            }
                        />

                        <ClinicalValue
                            label="Full name"
                            value={
                                `${patient.first_name} ${patient.last_name}`
                            }
                        />

                        <ClinicalValue
                            label="Date of birth"
                            value={
                                formatDate(
                                    patient
                                        .date_of_birth,
                                )
                            }
                            note={
                                age !== null
                                    ? `${age} years`
                                    : undefined
                            }
                        />

                        <ClinicalValue
                            label="Sex"
                            value={
                                patient.sex
                            }
                        />

                        <ClinicalValue
                            label="State"
                            value={
                                patient.state
                            }
                        />

                        <ClinicalValue
                            label="LGA"
                            value={
                                patient.lga
                            }
                        />
                    </div>
                </article>


                {/* -------------------------------------------
                    LATEST CLINICAL RECORD
                    ------------------------------------------- */}

                <article className="panel patient-detail-panel">
                    <div className="patient-panel-heading">
                        <div>
                            <span className="eyebrow">
                                Current state
                            </span>

                            <h2>
                                Latest clinical record
                            </h2>
                        </div>

                        <HeartPulse size={20} />
                    </div>

                    {
                        latestRecord
                            ? (
                                <div className="patient-detail-grid">
                                    <ClinicalValue
                                        label="ART start date"
                                        value={
                                            formatDate(
                                                latestRecord
                                                    .art_start_date,
                                            )
                                        }
                                    />

                                    <ClinicalValue
                                        label="Age at ART initiation"
                                        value={
                                            latestRecord
                                                .age_at_art_initiation
                                                !== null
                                                &&
                                                latestRecord
                                                    .age_at_art_initiation
                                                !== undefined
                                                ? `${latestRecord.age_at_art_initiation}`
                                                : 'Not recorded'
                                        }
                                    />

                                    <ClinicalValue
                                        label="Regimen"
                                        value={
                                            latestRecord
                                                .last_regimen
                                            || 'Not recorded'
                                        }
                                    />

                                    <ClinicalValue
                                        label="ARV refill"
                                        value={
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
                                    />

                                    <ClinicalValue
                                        label="Current viral load"
                                        value={
                                            latestRecord
                                                .current_viral_load
                                                !== null
                                                &&
                                                latestRecord
                                                    .current_viral_load
                                                !== undefined
                                                ? `${formatNumber(
                                                    latestRecord.current_viral_load,
                                                )} copies/mL`
                                                : 'Not recorded'
                                        }
                                    />

                                    <ClinicalValue
                                        label="Pregnancy status"
                                        value={
                                            latestRecord
                                                .pregnancy_status
                                            || 'Not recorded'
                                        }
                                    />

                                    <ClinicalValue
                                        label="Last clinic visit"
                                        value={
                                            formatDate(
                                                latestRecord
                                                    .last_clinic_visit_date,
                                            )
                                        }
                                    />
                                </div>
                            )
                            : (
                                <div className="patient-intelligence-empty">
                                    <FileText size={22} />

                                    <strong>
                                        No clinical record
                                    </strong>

                                    <span>
                                        No stored clinical information is
                                        currently available for this patient.
                                    </span>
                                </div>
                            )
                    }
                </article>
            </section>


            {/* =================================================
                LTFU INTELLIGENCE
                ================================================= */}

            <section className="panel patient-ltfu-panel">
                <div className="patient-ltfu-heading">
                    <div>
                        <span className="eyebrow">
                            Machine-learning decision support
                        </span>

                        <h2>
                            LTFU risk intelligence
                        </h2>

                        <p>
                            Stored Logistic Regression and XGBoost
                            outputs remain separate so agreement,
                            disagreement and historical changes remain
                            visible to the reviewing clinician. No model
                            is executed simply by opening this page.
                        </p>
                    </div>

                    <BrainCircuit size={25} />
                </div>


                {
                    latestPrediction
                        ? (
                            <>
                                {/* ---------------------------------------
                                    OVERALL STORED ASSESSMENT STATE
                                    --------------------------------------- */}

                                <div
                                    className="patient-risk-hero"
                                    data-state={
                                        state
                                    }
                                >
                                    <div className="patient-risk-hero-icon">
                                        {
                                            state
                                                === 'MODEL_DISAGREEMENT'
                                                ? (
                                                    <AlertTriangle size={24} />
                                                )
                                                : (
                                                    <CheckCircle2 size={24} />
                                                )
                                        }
                                    </div>

                                    <div>
                                        <span>
                                            Latest stored assessment
                                        </span>

                                        <strong>
                                            {
                                                predictionStateLabel(
                                                    state,
                                                )
                                            }
                                        </strong>

                                        <small>
                                            Generated{' '}
                                            {
                                                formatDateTime(
                                                    latestPrediction
                                                        .generated_at,
                                                )
                                            }
                                        </small>
                                    </div>

                                    <div className="patient-risk-review-state">
                                        <span>
                                            Clinical review
                                        </span>

                                        <strong>
                                            {
                                                humaniseValue(
                                                    latestPrediction
                                                        .clinical_review_status,
                                                )
                                            }
                                        </strong>
                                    </div>
                                </div>


                                {/* ---------------------------------------
                                    TWO-MODEL COMPARISON
                                    --------------------------------------- */}

                                <div className="patient-model-grid">
                                    <ModelProbability
                                        label="Logistic Regression"
                                        probability={
                                            latestPrediction
                                                .logistic_probability
                                        }
                                        classification={
                                            latestPrediction
                                                .logistic_classification
                                        }
                                        threshold={
                                            latestPrediction
                                                .threshold_used
                                        }
                                        model="logistic"
                                    />

                                    <ModelProbability
                                        label="XGBoost"
                                        probability={
                                            latestPrediction
                                                .xgboost_probability
                                        }
                                        classification={
                                            latestPrediction
                                                .xgboost_classification
                                        }
                                        threshold={
                                            latestPrediction
                                                .threshold_used
                                        }
                                        model="xgboost"
                                    />
                                </div>


                                {/* ---------------------------------------
                                    PREDICTION METADATA
                                    --------------------------------------- */}

                                <div className="prediction-metadata-grid">
                                    <div>
                                        <span>
                                            Model agreement
                                        </span>

                                        <strong>
                                            {
                                                humaniseValue(
                                                    latestPrediction
                                                        .agreement_status,
                                                )
                                            }
                                        </strong>
                                    </div>

                                    <div>
                                        <span>
                                            Stored threshold
                                        </span>

                                        <strong>
                                            {
                                                formatProbability(
                                                    latestPrediction
                                                        .threshold_used,
                                                )
                                            }
                                        </strong>
                                    </div>

                                    <div>
                                        <span>
                                            Feature schema
                                        </span>

                                        <strong>
                                            {
                                                latestPrediction
                                                    .input_schema_version
                                            }
                                        </strong>
                                    </div>

                                    <div>
                                        <span>
                                            Input completeness
                                        </span>

                                        <strong>
                                            {
                                                predictionComplete
                                                    ? 'Complete'
                                                    : `${missingFeatures.length} missing`
                                            }
                                        </strong>
                                    </div>
                                </div>
                            </>
                        )
                        : (
                            <div className="patient-intelligence-empty large">
                                <BrainCircuit size={27} />

                                <strong>
                                    No stored LTFU assessment
                                </strong>

                                <span>
                                    This patient does not yet have a stored
                                    two-model assessment. Return to the patient
                                    record if a new clinical prediction is
                                    appropriate. Viewing intelligence never
                                    generates a prediction automatically.
                                </span>

                                <button
                                    type="button"
                                    className="button secondary"
                                    onClick={
                                        () =>
                                            navigate(
                                                `/app/patients/${patientId}`,
                                            )
                                    }
                                >
                                    <BrainCircuit size={17} />

                                    Open patient record to assess
                                </button>
                            </div>
                        )
                }


                {/* -------------------------------------------
                    CLINICAL DISCLAIMER
                    ------------------------------------------- */}

                <div className="patient-prediction-disclaimer">
                    <ShieldCheck size={17} />

                    <span>
                        Model probabilities are decision-support
                        outputs, not diagnoses or guarantees of
                        future behaviour. Clinical judgement and
                        contextual review remain essential.
                    </span>
                </div>


                {/* -------------------------------------------
                    NEXT CLINICAL ACTION
                    ------------------------------------------- */}

                <div className="patient-intelligence-next-action">
                    <span>
                        Need to review the source clinical
                        information or generate a new assessment?
                    </span>

                    <button
                        type="button"
                        className="button secondary"
                        onClick={
                            () =>
                                navigate(
                                    `/app/patients/${patientId}`,
                                )
                        }
                    >
                        <Stethoscope size={16} />

                        Open patient record
                    </button>
                </div>
            </section>


            {/* =================================================
                PREDICTION HISTORY + DATA QUALITY
                ================================================= */}

            <section className="patient-intelligence-main-grid">

                {/* -------------------------------------------
                    PREDICTION HISTORY
                    ------------------------------------------- */}

                <article className="panel patient-detail-panel">
                    <div className="patient-panel-heading">
                        <div>
                            <span className="eyebrow">
                                Longitudinal analytics
                            </span>

                            <h2>
                                Prediction history
                            </h2>
                        </div>

                        <TrendingUp size={20} />
                    </div>

                    <PredictionHistoryChart
                        predictions={
                            predictionHistory
                        }
                    />
                </article>


                {/* -------------------------------------------
                    DATA QUALITY
                    ------------------------------------------- */}

                <article className="panel patient-detail-panel">
                    <div className="patient-panel-heading">
                        <div>
                            <span className="eyebrow">
                                Analytical assurance
                            </span>

                            <h2>
                                Data quality
                            </h2>
                        </div>

                        <Database size={20} />
                    </div>

                    {
                        latestPrediction
                            ? (
                                <>
                                    <div
                                        className={
                                            missingFeatures.length
                                                === 0
                                                ? 'patient-data-quality good'
                                                : 'patient-data-quality warning'
                                        }
                                    >
                                        {
                                            missingFeatures.length
                                                === 0
                                                ? (
                                                    <CheckCircle2 size={21} />
                                                )
                                                : (
                                                    <AlertTriangle size={21} />
                                                )
                                        }

                                        <div>
                                            <strong>
                                                {
                                                    missingFeatures.length
                                                        === 0
                                                        ? 'Complete stored input snapshot'
                                                        : `${missingFeatures.length} missing input${missingFeatures.length
                                                            === 1
                                                            ? ''
                                                            : 's'
                                                        } detected`
                                                }
                                            </strong>

                                            <span>
                                                {
                                                    missingFeatures.length
                                                        === 0
                                                        ? 'No null or blank values were detected in the latest stored prediction snapshot.'
                                                        : 'Missing information should be considered when interpreting the stored model output.'
                                                }
                                            </span>
                                        </div>
                                    </div>


                                    {
                                        missingFeatures.length > 0 && (
                                            <div className="patient-missing-feature-grid">
                                                {
                                                    missingFeatures.map(
                                                        (
                                                            feature,
                                                        ) => (
                                                            <span
                                                                key={
                                                                    feature
                                                                }
                                                            >
                                                                {
                                                                    humaniseValue(
                                                                        feature,
                                                                    )
                                                                }
                                                            </span>
                                                        ),
                                                    )
                                                }
                                            </div>
                                        )
                                    }
                                </>
                            )
                            : (
                                <div className="patient-intelligence-empty">
                                    <Database size={22} />

                                    <strong>
                                        No prediction snapshot
                                    </strong>

                                    <span>
                                        Input-quality information becomes
                                        available after a prediction is stored.
                                    </span>
                                </div>
                            )
                    }
                </article>
            </section>


            {/* =================================================
                REPRODUCIBILITY SNAPSHOT
                ================================================= */}

            {
                latestPrediction && (
                    <section className="panel patient-input-snapshot-panel">
                        <div className="patient-panel-heading">
                            <div>
                                <span className="eyebrow">
                                    Reproducibility
                                </span>

                                <h2>
                                    Stored model-input snapshot
                                </h2>

                                <p>
                                    The values below are the model inputs
                                    preserved with this prediction for
                                    traceability and reproducibility.
                                </p>
                            </div>

                            <Database size={20} />
                        </div>


                        <div className="patient-input-snapshot-grid">
                            {
                                Object.entries(
                                    latestPrediction
                                        .input_snapshot,
                                ).map(
                                    (
                                        [
                                            key,
                                            value,
                                        ],
                                    ) => {
                                        const missing =
                                            value === null
                                            ||
                                            value === '';

                                        return (
                                            <div
                                                key={
                                                    key
                                                }
                                                className={
                                                    missing
                                                        ? 'missing'
                                                        : ''
                                                }
                                            >
                                                <span>
                                                    {
                                                        humaniseValue(
                                                            key,
                                                        )
                                                    }
                                                </span>

                                                <strong>
                                                    {
                                                        missing
                                                            ? 'Missing'
                                                            : typeof value
                                                                === 'object'
                                                                ? JSON.stringify(
                                                                    value,
                                                                )
                                                                : String(
                                                                    value,
                                                                )
                                                    }
                                                </strong>
                                            </div>
                                        );
                                    },
                                )
                            }
                        </div>
                    </section>
                )
            }


            {/* =================================================
                CLINICAL HISTORY
                ================================================= */}

            <section className="panel patient-clinical-history-panel">
                <div className="patient-panel-heading">
                    <div>
                        <span className="eyebrow">
                            Longitudinal care
                        </span>

                        <h2>
                            Clinical record history
                        </h2>

                        <p>
                            {
                                clinicalHistory.length
                            } stored clinical record{
                                clinicalHistory.length === 1
                                    ? ''
                                    : 's'
                            } for this synthetic patient.
                        </p>
                    </div>

                    <Clock3 size={20} />
                </div>


                {
                    clinicalHistory.length
                        === 0
                        ? (
                            <div className="patient-intelligence-empty">
                                <FileText size={22} />

                                <strong>
                                    No clinical history
                                </strong>

                                <span>
                                    Historical clinical records have not
                                    yet been stored for this patient.
                                </span>
                            </div>
                        )
                        : (
                            <div className="clinical-history-timeline">
                                {
                                    clinicalHistory.map(
                                        (
                                            record,
                                            index,
                                        ) => (
                                            <ClinicalHistoryEntry
                                                key={
                                                    record.id
                                                }
                                                record={
                                                    record
                                                }
                                                index={
                                                    index
                                                }
                                            />
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
