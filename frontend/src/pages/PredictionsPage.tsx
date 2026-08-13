import {
    Activity,
    AlertTriangle,
    BrainCircuit,
    CheckCircle2,
    Database,
    FlaskConical,
    ShieldAlert,
    Sparkles,
} from 'lucide-react';

import {
    useEffect,
    useState,
    type FormEvent,
} from 'react';

import {
    PageHeader,
} from '../components/UI';

import {
    api,
} from '../lib/api';

import type {
    PredictionResponse,
} from '../lib/types';


// =====================================================
// MANUAL SYNTHETIC INPUT
// =====================================================

type ManualPredictionForm = {
    date_of_birth: string;

    sex: string;

    state: string;

    lga: string;

    patient_transferred_in: boolean;

    art_start_date: string;

    age_at_art_initiation: number;

    last_regimen: string;

    days_of_arv_refill: number;

    current_viral_load: number;

    pregnancy_status: string;

    last_clinic_visit_date: string;
};


const INITIAL_FORM:
    ManualPredictionForm = {
    date_of_birth:
        '1992-04-17',

    sex:
        'Female',

    state:
        'Abia',

    lga:
        'Umuahia North',

    patient_transferred_in:
        false,

    art_start_date:
        '2023-02-10',

    age_at_art_initiation:
        30,

    last_regimen:
        'TDF+3TC+DTG',

    days_of_arv_refill:
        90,

    current_viral_load:
        420,

    pregnancy_status:
        'NP',

    last_clinic_visit_date:
        '2026-08-01',
};


// =====================================================
// PRESENTATION HELPERS
// =====================================================

function percentage(
    value: number,
): string {
    return `${(
        value
        * 100
    ).toFixed(
        1,
    )}%`;
}


function humanise(
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
                letter,
            ) =>
                letter.toUpperCase(),
        );
}


// =====================================================
// MODEL RESULT CARD
// =====================================================

function ModelResultCard(
    {
        name,
        probability,
        classification,
        threshold,
        variant,
    }: {
        name: string;

        probability: number;

        classification: string;

        threshold: number;

        variant:
        'logistic'
        | 'xgboost';
    },
) {
    const width =
        Math.min(
            100,
            Math.max(
                0,
                probability
                * 100,
            ),
        );

    const thresholdPosition =
        Math.min(
            100,
            Math.max(
                0,
                threshold
                * 100,
            ),
        );

    return (
        <article className="manual-model-result">
            <header>
                <div>
                    <span>
                        {name}
                    </span>

                    <strong>
                        {
                            percentage(
                                probability,
                            )
                        }
                    </strong>
                </div>

                <b
                    data-model={
                        variant
                    }
                >
                    {
                        humanise(
                            classification,
                        )
                    }
                </b>
            </header>

            <div className="manual-model-track">
                <i
                    data-model={
                        variant
                    }
                    style={{
                        width:
                            `${width}%`,
                    }}
                />

                <em
                    style={{
                        left:
                            `${thresholdPosition}%`,
                    }}
                />
            </div>

            <footer>
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
            </footer>
        </article>
    );
}


// =====================================================
// PAGE
// =====================================================

export default function PredictionsPage() {
    const [
        models,
        setModels,
    ] =
        useState<unknown[]>(
            [],
        );

    const [
        result,
        setResult,
    ] =
        useState<
            PredictionResponse | null
        >(
            null,
        );

    const [
        form,
        setForm,
    ] =
        useState<ManualPredictionForm>(
            INITIAL_FORM,
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


    // ===================================================
    // LOAD DEPLOYED MODEL REGISTRY
    // ===================================================

    useEffect(
        () => {
            api.predictionModels()
                .then(
                    setModels,
                )
                .catch(
                    () => {
                        // Model registry failure should not prevent
                        // the manual synthetic form from rendering.
                    },
                );
        },
        [],
    );


    // ===================================================
    // RUN MANUAL SYNTHETIC PREDICTION
    // ===================================================

    async function submit(
        event: FormEvent,
    ) {
        event.preventDefault();

        setError('');
        setBusy(true);

        try {
            const response =
                await api.manualPrediction(
                    form,
                );

            setResult(
                response,
            );
        } catch (
        errorValue
        ) {
            setError(
                errorValue instanceof Error
                    ? errorValue.message
                    : 'Unable to run the prediction.',
            );
        } finally {
            setBusy(false);
        }
    }


    // ===================================================
    // RENDER
    // ===================================================

    return (
        <>
            <PageHeader
                eyebrow="Machine learning"
                title="LTFU risk workspace"
                description="Explore MEDISCOPE's two-model decision-support workflow using synthetic manual inputs."
            />


            {/* =================================================
          CONTEXT
          ================================================= */}

            <section className="prediction-context-banner">
                <div className="prediction-context-icon">
                    <Sparkles size={20} />
                </div>

                <div>
                    <strong>
                        Manual synthetic assessment
                    </strong>

                    <span>
                        This workspace is intended for controlled
                        exploration. It does not replace review of an
                        assigned patient's stored clinical record.
                    </span>
                </div>

                <span className="prediction-model-count">
                    <Database size={15} />

                    {
                        models.length
                        || 2
                    } model records
                </span>
            </section>


            <div className="prediction-workspace enhanced">

                {/* ===============================================
            MANUAL INPUT
            =============================================== */}

                <form
                    className="panel prediction-input-panel"
                    onSubmit={submit}
                >
                    <div className="panel-heading">
                        <div>
                            <span className="eyebrow">
                                Synthetic feature set
                            </span>

                            <h2>
                                Manual risk check
                            </h2>

                            <p>
                                Enter a complete synthetic scenario before
                                submitting it to Logistic Regression and
                                XGBoost.
                            </p>
                        </div>

                        <BrainCircuit size={22} />
                    </div>


                    {/* ---------------------------------------------
              DEMOGRAPHICS
              --------------------------------------------- */}

                    <fieldset className="prediction-fieldset">
                        <legend>
                            Demographics
                        </legend>

                        <div className="compact-form-grid">
                            <label>
                                Date of birth

                                <input
                                    type="date"
                                    required
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


                            <label>
                                Sex

                                <select
                                    className="auth-select"
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
                                    <option value="Female">
                                        Female
                                    </option>

                                    <option value="Male">
                                        Male
                                    </option>
                                </select>
                            </label>


                            <label>
                                State

                                <input
                                    required
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


                            <label>
                                LGA

                                <input
                                    required
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
                    </fieldset>


                    {/* ---------------------------------------------
              TREATMENT
              --------------------------------------------- */}

                    <fieldset className="prediction-fieldset">
                        <legend>
                            Treatment history
                        </legend>

                        <div className="compact-form-grid">
                            <label>
                                ART start date

                                <input
                                    type="date"
                                    required
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


                            <label>
                                Age at ART initiation

                                <input
                                    type="number"
                                    min={0}
                                    required
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
                                                    Number(
                                                        event.target.value,
                                                    ),
                                            })
                                    }
                                />
                            </label>


                            <label>
                                Last regimen

                                <input
                                    required
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


                            <label>
                                ARV refill days

                                <input
                                    type="number"
                                    min={0}
                                    required
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
                                                    Number(
                                                        event.target.value,
                                                    ),
                                            })
                                    }
                                />
                            </label>
                        </div>
                    </fieldset>


                    {/* ---------------------------------------------
              CURRENT CLINICAL STATE
              --------------------------------------------- */}

                    <fieldset className="prediction-fieldset">
                        <legend>
                            Current clinical state
                        </legend>

                        <div className="compact-form-grid">
                            <label>
                                Viral load

                                <input
                                    type="number"
                                    min={0}
                                    required
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
                                                    Number(
                                                        event.target.value,
                                                    ),
                                            })
                                    }
                                />
                            </label>


                            <label>
                                Pregnancy status

                                <select
                                    className="auth-select"
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
                                    <option value="NP">
                                        Not pregnant
                                    </option>

                                    <option value="P">
                                        Pregnant
                                    </option>

                                    <option value="NA">
                                        Not applicable
                                    </option>
                                </select>
                            </label>


                            <label>
                                Last clinic visit

                                <input
                                    type="date"
                                    required
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


                            <label className="prediction-checkbox-card">
                                <input
                                    type="checkbox"
                                    checked={
                                        form.patient_transferred_in
                                    }
                                    onChange={
                                        (
                                            event,
                                        ) =>
                                            setForm({
                                                ...form,

                                                patient_transferred_in:
                                                    event.target.checked,
                                            })
                                    }
                                />

                                <span>
                                    <strong>
                                        Transferred in
                                    </strong>

                                    <small>
                                        Patient entered programme from another
                                        facility.
                                    </small>
                                </span>
                            </label>
                        </div>
                    </fieldset>


                    {error && (
                        <div className="form-error">
                            {error}
                        </div>
                    )}


                    <button
                        className="button primary wide"
                        disabled={
                            busy
                        }
                    >
                        <BrainCircuit size={18} />

                        {
                            busy
                                ? 'Running both models…'
                                : 'Run Logistic Regression + XGBoost'
                        }
                    </button>
                </form>


                {/* ===============================================
            OUTPUT
            =============================================== */}

                <section className="panel prediction-result-panel">
                    {
                        result
                            ? (
                                <>
                                    <div className="panel-heading">
                                        <div>
                                            <span className="eyebrow">
                                                Two-model output
                                            </span>

                                            <h2>
                                                Prediction result
                                            </h2>
                                        </div>

                                        {
                                            result.agreement_status
                                                === 'AGREE'
                                                ? (
                                                    <CheckCircle2 size={22} />
                                                )
                                                : (
                                                    <AlertTriangle size={22} />
                                                )
                                        }
                                    </div>


                                    <div
                                        className="prediction-agreement-hero"
                                        data-agreement={
                                            result.agreement_status
                                        }
                                    >
                                        <span>
                                            Model relationship
                                        </span>

                                        <strong>
                                            {
                                                result.agreement_status
                                                    === 'AGREE'
                                                    ? 'Models agree'
                                                    : 'Models disagree'
                                            }
                                        </strong>

                                        <small>
                                            {
                                                result.overall_summary
                                            }
                                        </small>
                                    </div>


                                    <div className="manual-model-result-grid">
                                        <ModelResultCard
                                            name="Logistic Regression"
                                            probability={
                                                result
                                                    .logistic_regression
                                                    .probability
                                            }
                                            classification={
                                                result
                                                    .logistic_regression
                                                    .classification
                                            }
                                            threshold={
                                                result
                                                    .logistic_regression
                                                    .threshold
                                            }
                                            variant="logistic"
                                        />

                                        <ModelResultCard
                                            name="XGBoost"
                                            probability={
                                                result
                                                    .xgboost
                                                    .probability
                                            }
                                            classification={
                                                result
                                                    .xgboost
                                                    .classification
                                            }
                                            threshold={
                                                result
                                                    .xgboost
                                                    .threshold
                                            }
                                            variant="xgboost"
                                        />
                                    </div>


                                    <div className="prediction-result-metadata">
                                        <div>
                                            <span>
                                                Prediction ID
                                            </span>

                                            <strong>
                                                {
                                                    result.prediction_id
                                                }
                                            </strong>
                                        </div>

                                        <div>
                                            <span>
                                                Generated
                                            </span>

                                            <strong>
                                                {
                                                    new Date(
                                                        result.generated_at,
                                                    )
                                                        .toLocaleString()
                                                }
                                            </strong>
                                        </div>

                                        <div>
                                            <span>
                                                Feature schema
                                            </span>

                                            <strong>
                                                {
                                                    result
                                                        .input_schema_version
                                                }
                                            </strong>
                                        </div>
                                    </div>


                                    {
                                        result
                                            .explanation_notes
                                            .length > 0 && (
                                            <div className="prediction-explanation">
                                                <span className="eyebrow">
                                                    Interpretation notes
                                                </span>

                                                {
                                                    result
                                                        .explanation_notes
                                                        .map(
                                                            (
                                                                note,
                                                            ) => (
                                                                <div
                                                                    key={
                                                                        note
                                                                    }
                                                                >
                                                                    <Activity size={14} />

                                                                    <span>
                                                                        {note}
                                                                    </span>
                                                                </div>
                                                            ),
                                                        )
                                                }
                                            </div>
                                        )
                                    }


                                    <div className="disclaimer enhanced">
                                        <ShieldAlert size={19} />

                                        <span>
                                            {
                                                result
                                                    .clinical_disclaimer
                                            }
                                        </span>
                                    </div>
                                </>
                            )
                            : (
                                <div className="prediction-empty-state">
                                    <div>
                                        <FlaskConical size={28} />
                                    </div>

                                    <h3>
                                        Awaiting prediction
                                    </h3>

                                    <p>
                                        Submit a synthetic scenario to compare
                                        Logistic Regression and XGBoost outputs.
                                    </p>

                                    <span>
                                        Outputs remain separate so agreement and
                                        disagreement can be inspected rather than
                                        hidden by averaging.
                                    </span>
                                </div>
                            )
                    }
                </section>
            </div>
        </>
    );
}
