import {
    BrainCircuit,
    CheckCircle2,
    Database,
    HeartHandshake,
    History,
    LockKeyhole,
    ShieldCheck,
    Stethoscope,
} from 'lucide-react';

import {
    Link,
} from 'react-router-dom';

import {
    Brand,
} from '../components/Brand';


// =====================================================
// ABOUT PAGE
// =====================================================

/**
 * Public explanation of the MEDISCOPE prototype.
 *
 * The content deliberately distinguishes machine-learning
 * decision support from diagnosis or autonomous care.
 */
export default function AboutPage() {
    return (
        <div className="simple-page">

            {/* =================================================
          NAVIGATION
          ================================================= */}

            <header className="marketing-nav">
                <Brand />

                <Link
                    className="button ghost small"
                    to="/"
                >
                    Back home
                </Link>
            </header>


            <main>

                {/* =================================================
            HERO
            ================================================= */}

                <section className="simple-hero about-hero">
                    <span className="eyebrow">
                        About MEDISCOPE
                    </span>

                    <h1>
                        Clinical intelligence with human judgement
                        at the centre.
                    </h1>

                    <p className="simple-hero-lead">
                        MEDISCOPE is a capstone prototype for secure HIV
                        retention decision support. It combines
                        role-based clinical workflows, auditable records,
                        secure messaging and two-model LTFU risk
                        estimation while explicitly preserving clinician
                        oversight.
                    </p>
                </section>


                {/* =================================================
            PROJECT FOUNDATIONS
            ================================================= */}

                <section className="about-section">
                    <div className="content-grid">
                        <article>
                            <HeartHandshake size={22} />

                            <h3>
                                Purpose
                            </h3>

                            <p>
                                Support earlier identification of synthetic
                                patients who may benefit from
                                retention-focused clinical review and
                                additional continuity-of-care support.
                            </p>
                        </article>

                        <article>
                            <History size={22} />

                            <h3>
                                Governance
                            </h3>

                            <p>
                                Predictions are traceable to deployed model
                                versions, classification thresholds, feature
                                schema information, input snapshots and the
                                requesting account.
                            </p>
                        </article>

                        <article>
                            <ShieldCheck size={22} />

                            <h3>
                                Safety
                            </h3>

                            <p>
                                The prototype uses synthetic patient records,
                                and its prediction outputs are not diagnoses,
                                treatment recommendations or autonomous
                                discharge decisions.
                            </p>
                        </article>
                    </div>
                </section>


                {/* =================================================
            WHY RETENTION SUPPORT
            ================================================= */}

                <section className="about-section about-section-soft">
                    <div className="about-split">
                        <div>
                            <span className="eyebrow">
                                The problem space
                            </span>

                            <h2 className="section-heading-dark">
                                Supporting continuity before disengagement
                                becomes loss to follow-up.
                            </h2>

                            <p className="section-paragraph-dark">
                                Retention in HIV treatment programmes
                                depends on continued engagement with care.
                                MEDISCOPE explores whether routinely
                                available clinical and treatment features
                                can be used to surface patterns associated
                                with LTFU risk early enough to support
                                human review.
                            </p>

                            <p className="section-paragraph-dark">
                                The platform therefore focuses on
                                prioritisation rather than automation:
                                prediction is one signal within a broader
                                clinical workflow.
                            </p>
                        </div>

                        <div className="about-principles">
                            <article>
                                <CheckCircle2 size={19} />

                                <div>
                                    <strong>
                                        Earlier visibility
                                    </strong>

                                    <span>
                                        Highlight records that may warrant
                                        closer retention-focused review.
                                    </span>
                                </div>
                            </article>

                            <article>
                                <CheckCircle2 size={19} />

                                <div>
                                    <strong>
                                        Explainable workflow
                                    </strong>

                                    <span>
                                        Preserve probabilities, thresholds,
                                        model identity and input context.
                                    </span>
                                </div>
                            </article>

                            <article>
                                <CheckCircle2 size={19} />

                                <div>
                                    <strong>
                                        Human authority
                                    </strong>

                                    <span>
                                        Keep clinical interpretation and action
                                        with qualified users.
                                    </span>
                                </div>
                            </article>
                        </div>
                    </div>
                </section>


                {/* =================================================
            PLATFORM ARCHITECTURE
            ================================================= */}

                <section className="about-section">
                    <div className="marketing-section-heading">
                        <span className="eyebrow">
                            Platform architecture
                        </span>

                        <h2 className="section-heading-light">
                            A full-stack prototype rather than a standalone
                            prediction model.
                        </h2>

                        <p className="section-paragraph-light">
                            MEDISCOPE connects machine learning with the
                            security, workflow and governance components
                            required to demonstrate how predictive
                            analytics could sit inside a wider clinical
                            application.
                        </p>
                    </div>

                    <div className="about-architecture-grid">
                        <article>
                            <Database size={21} />

                            <h3>
                                Structured records
                            </h3>

                            <p>
                                Synthetic patient and clinical information
                                is managed through a PostgreSQL-backed API
                                with controlled workflow access.
                            </p>
                        </article>

                        <article>
                            <BrainCircuit size={21} />

                            <h3>
                                ML inference
                            </h3>

                            <p>
                                Logistic Regression and XGBoost pipelines
                                independently generate LTFU probability
                                estimates from an aligned deployed feature
                                schema.
                            </p>
                        </article>

                        <article>
                            <Stethoscope size={21} />

                            <h3>
                                Clinical workflow
                            </h3>

                            <p>
                                Clinicians interact with assigned patients,
                                clinical records, change requests and
                                prediction history through role-aware
                                application routes.
                            </p>
                        </article>

                        <article>
                            <LockKeyhole size={21} />

                            <h3>
                                Security layer
                            </h3>

                            <p>
                                JWT authentication, refresh-token rotation,
                                email verification, MFA and RBAC protect
                                account and clinical operations.
                            </p>
                        </article>
                    </div>
                </section>


                {/* =================================================
            MODEL DESIGN
            ================================================= */}

                <section className="about-section about-model-section">
                    <div>
                        <span className="eyebrow">
                            Two-model decision support
                        </span>

                        <h2 className="section-heading-light">
                            Agreement is useful.
                            Disagreement is information too.
                        </h2>

                        <p className="section-paragraph-light">
                            MEDISCOPE does not hide the individual model
                            outputs behind a single unexplained score.
                            Logistic Regression and XGBoost each produce
                            their own positive-class probability and
                            classification.
                        </p>

                        <p className="section-paragraph-light">
                            When the models agree, clinicians can see the
                            shared classification. When they disagree,
                            MEDISCOPE explicitly surfaces that difference
                            and encourages review of the wider patient
                            context.
                        </p>
                    </div>

                    <div className="about-model-card">
                        <BrainCircuit size={28} />

                        <span>
                            Prediction record
                        </span>

                        <strong>
                            Model probability
                        </strong>

                        <strong>
                            Classification threshold
                        </strong>

                        <strong>
                            Model version
                        </strong>

                        <strong>
                            Input snapshot
                        </strong>

                        <strong>
                            Agreement status
                        </strong>

                        <strong>
                            Clinical disclaimer
                        </strong>
                    </div>
                </section>


                {/* =================================================
            RESPONSIBLE USE
            ================================================= */}

                <section className="about-section responsible-use">
                    <div className="marketing-section-heading">
                        <span className="eyebrow">
                            Responsible use
                        </span>

                        <h2 className="section-heading-light">
                            MEDISCOPE is intentionally limited.
                        </h2>
                    </div>

                    <div className="responsible-use-grid">
                        <article>
                            <ShieldCheck size={21} />

                            <h3>
                                Synthetic data only
                            </h3>

                            <p>
                                Patient records shown in the prototype are
                                synthetic and exist solely for demonstration,
                                development and testing.
                            </p>
                        </article>

                        <article>
                            <Stethoscope size={21} />

                            <h3>
                                Not a diagnosis
                            </h3>

                            <p>
                                An LTFU risk estimate does not diagnose a
                                patient, determine prognosis or replace
                                professional clinical assessment.
                            </p>
                        </article>

                        <article>
                            <HeartHandshake size={21} />

                            <h3>
                                No autonomous action
                            </h3>

                            <p>
                                Predictions should not independently trigger
                                treatment, discharge or patient-management
                                decisions.
                            </p>
                        </article>
                    </div>
                </section>


                {/* =================================================
            CTA
            ================================================= */}

                <section className="simple-page-cta">
                    <div>
                        <span className="eyebrow">
                            Explore MEDISCOPE
                        </span>

                        <h2>
                            See how the prototype brings security,
                            workflow and machine learning together.
                        </h2>
                    </div>

                    <Link
                        className="button primary"
                        to="/login"
                    >
                        Enter secure workspace
                    </Link>
                </section>
            </main>

            {/* =================================================
                FOOTER
                ================================================= */}

            <footer className="marketing-footer">
                <Brand />

                <p>
                    MEDISCOPE is a synthetic healthcare
                    decision-support prototype. It does not provide
                    medical diagnosis or autonomous clinical
                    decisions.
                </p>

                <nav>
                    <Link to="/">
                        Home
                    </Link>

                    <Link to="/contact">
                        Contact
                    </Link>

                    <Link to="/login">
                        Sign in
                    </Link>
                </nav>
            </footer>
        </div>
    );
}
