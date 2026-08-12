import {
  Activity,
  ArrowRight,
  BrainCircuit,
  CheckCircle2,
  ClipboardCheck,
  HeartHandshake,
  History,
  LockKeyhole,
  MessageSquare,
  ShieldCheck,
  Sparkles,
  Stethoscope,
  UsersRound,
} from 'lucide-react';

import {
  Link,
} from 'react-router-dom';

import {
  Brand,
} from '../components/Brand';


// =====================================================
// LANDING PAGE
// =====================================================

/**
 * Public MEDISCOPE landing page.
 *
 * The page introduces the prototype without exposing
 * authenticated clinical functionality.
 *
 * It communicates:
 * - the retention-support problem;
 * - MEDISCOPE's decision-support purpose;
 * - two-model LTFU prediction;
 * - clinician oversight;
 * - security and auditability;
 * - synthetic-data constraints.
 */
export default function LandingPage() {
  return (
    <div className="marketing-page">

      {/* =================================================
          NAVIGATION
          ================================================= */}

      <header className="marketing-nav">
        <Brand />

        <nav>
          <Link to="/about">
            About
          </Link>

          <Link to="/contact">
            Contact
          </Link>

          <Link
            className="button ghost small"
            to="/login"
          >
            Sign in
          </Link>

          <Link
            className="button primary small"
            to="/register"
          >
            Create account
          </Link>
        </nav>
      </header>


      <main>

        {/* =================================================
            HERO
            ================================================= */}

        <section className="hero">
          <div className="hero-copy">
            <span className="pill">
              <Sparkles size={15} />

              Responsible AI for retention support
            </span>

            <h1>
              See risk earlier.
              <br />

              <em>
                Keep care connected.
              </em>
            </h1>

            <p>
              MEDISCOPE combines secure clinical workflows
              with two-model machine-learning decision
              support to help clinicians identify synthetic
              patients who may benefit from additional
              retention-focused review.
            </p>

            <div className="hero-actions">
              <Link
                className="button primary"
                to="/login"
              >
                Enter secure workspace

                <ArrowRight size={18} />
              </Link>

              <Link
                className="button ghost"
                to="/about"
              >
                Explore the platform
              </Link>
            </div>

            <div className="trust-row">
              <span>
                <ShieldCheck />
                Role-based access
              </span>

              <span>
                <LockKeyhole />
                MFA protected
              </span>

              <span>
                <CheckCircle2 />
                Auditable predictions
              </span>
            </div>
          </div>


          {/* -----------------------------------------------
              HERO VISUAL
              ----------------------------------------------- */}

          <div className="hero-visual">
            <div className="halo halo-one" />
            <div className="halo halo-two" />

            <div className="glass-panel prediction-demo">
              <div className="demo-top">
                <span className="status-chip">
                  LTFU risk intelligence
                </span>

                <BrainCircuit />
              </div>

              <div className="risk-ring">
                <div>
                  <strong>
                    82%
                  </strong>

                  <span>
                    Estimated LTFU Risk
                  </span>
                </div>
              </div>

              <div className="model-bars">
                <div>
                  <span>
                    Logistic Regression
                  </span>

                  <b>
                    84%
                  </b>

                  <i
                    style={{
                      width: '84%',
                    }}
                  />
                </div>

                <div>
                  <span>
                    XGBoost
                  </span>

                  <b>
                    80%
                  </b>

                  <i
                    style={{
                      width: '80%',
                    }}
                  />
                </div>
              </div>

              <div className="demo-note">
                Two independent models produced similar
                risk estimates for this example patient.
                Decision support only · clinician review required
              </div>
            </div>

            <div className="floating-card card-a">
              <span>
                Retention signal
              </span>

              <strong>
                2 models agree
              </strong>
            </div>

            <div className="floating-card card-b">
              <span>
                Audit trail
              </span>

              <strong>
                Fully traceable
              </strong>
            </div>
          </div>
        </section>


        {/* =================================================
            TRUST STRIP
            ================================================= */}

        <section className="feature-strip">
          <div>
            <strong>
              Secure by design
            </strong>

            <span>
              JWT · MFA · RBAC
            </span>
          </div>

          <div>
            <strong>
              Clinically traceable
            </strong>

            <span>
              History · Versions · Snapshots
            </span>
          </div>

          <div>
            <strong>
              Model-aware
            </strong>

            <span>
              Logistic Regression · XGBoost
            </span>
          </div>

          <div>
            <strong>
              Synthetic prototype
            </strong>

            <span>
              No real patient data
            </span>
          </div>
        </section>


        {/* =================================================
            PRODUCT INTRODUCTION
            ================================================= */}

        <section className="marketing-section">
          <div className="marketing-section-heading">
            <span className="eyebrow">
              Built around continuity of care
            </span>

            <h2 className="section-heading-light">
              Clinical decision support that fits into a
              broader care workflow.
            </h2>

            <p className="section-paragraph-light">
              MEDISCOPE is more than a prediction screen.
              It brings together secure access, synthetic
              patient records, clinician assignment,
              messaging, change-request review and
              auditable risk estimation in one prototype.
            </p>
          </div>

          <div className="marketing-card-grid">
            <article className="marketing-feature-card">
              <div className="marketing-feature-icon">
                <Stethoscope size={22} />
              </div>

              <h3>
                Clinician workspace
              </h3>

              <p>
                Review assigned synthetic patients, maintain
                clinical records and request LTFU risk
                predictions without leaving the clinical
                workflow.
              </p>
            </article>

            <article className="marketing-feature-card">
              <div className="marketing-feature-icon">
                <BrainCircuit size={22} />
              </div>

              <h3>
                Two-model intelligence
              </h3>

              <p>
                Logistic Regression and XGBoost provide
                parallel probability estimates so model
                agreement and disagreement remain visible
                to the clinician.
              </p>
            </article>

            <article className="marketing-feature-card">
              <div className="marketing-feature-icon">
                <History size={22} />
              </div>

              <h3>
                Traceable predictions
              </h3>

              <p>
                Each prediction retains model references,
                thresholds, feature schema information and
                an input snapshot for later review.
              </p>
            </article>
          </div>
        </section>


        {/* =================================================
            HOW MEDISCOPE WORKS
            ================================================= */}

        <section className="marketing-section marketing-section-soft">
          <div className="marketing-section-heading">
            <span className="eyebrow">
              From record to review
            </span>

            <h2 className="section-heading-dark">
              A human remains in the decision loop.
            </h2>

            <p className="section-paragraph-dark">
              MEDISCOPE is designed to surface information,
              not replace clinical judgement. Risk outputs
              are intended to support review and
              prioritisation rather than create autonomous
              treatment or discharge decisions.
            </p>

          </div>

          <div className="workflow-grid">
            <article>
              <span className="workflow-number">
                01
              </span>

              <Activity size={20} />

              <h3>
                Review the record
              </h3>

              <p>
                Current demographic, treatment and clinical
                information is assembled from the linked
                synthetic patient profile.
              </p>
            </article>

            <article>
              <span className="workflow-number">
                02
              </span>

              <BrainCircuit size={20} />

              <h3>
                Estimate LTFU risk
              </h3>

              <p>
                The deployed Logistic Regression and
                XGBoost pipelines independently estimate
                the probability of loss to follow-up.
              </p>
            </article>

            <article>
              <span className="workflow-number">
                03
              </span>

              <ClipboardCheck size={20} />

              <h3>
                Compare model outputs
              </h3>

              <p>
                Agreement, disagreement, threshold and
                probability information are presented
                clearly rather than hidden behind a single
                label.
              </p>
            </article>

            <article>
              <span className="workflow-number">
                04
              </span>

              <HeartHandshake size={20} />

              <h3>
                Apply human judgement
              </h3>

              <p>
                The clinician reviews the prediction in
                context and decides whether additional
                retention support is appropriate.
              </p>
            </article>
          </div>
        </section>


        {/* =================================================
            ROLE-AWARE PLATFORM
            ================================================= */}

        <section className="marketing-section">
          <div className="marketing-split">
            <div>
              <span className="eyebrow">
                Role-aware by design
              </span>

              <h2 className="section-heading-light">
                Different users see only what they need.
              </h2>

              <p>
                MEDISCOPE separates patient-facing,
                clinician and administrative workflows.
                Frontend navigation reflects each role,
                while backend role-based access control
                remains the authoritative security layer.
              </p>

              <Link
                className="text-link"
                to="/about"
              >
                Learn more about MEDISCOPE

                <ArrowRight size={15} />
              </Link>
            </div>

            <div className="role-preview-grid">
              <article>
                <UsersRound size={20} />

                <div>
                  <strong>
                    Standard user
                  </strong>

                  <span>
                    Health profile · messages · change requests · security
                  </span>
                </div>
              </article>

              <article>
                <Stethoscope size={20} />

                <div>
                  <strong>
                    Clinician
                  </strong>

                  <span>
                    Assigned patients · records · predictions · review workflows
                  </span>
                </div>
              </article>

              <article>
                <ShieldCheck size={20} />

                <div>
                  <strong>
                    Administrator
                  </strong>

                  <span>
                    User management · roles · linking · patient assignment
                  </span>
                </div>
              </article>
            </div>
          </div>
        </section>


        {/* =================================================
            SAFETY & SECURITY
            ================================================= */}

        <section className="marketing-section safety-section">
          <div className="marketing-section-heading">
            <span className="eyebrow">
              Responsible prototype
            </span>

            <h2 className="section-heading-light">
              Security and governance are part of the
              architecture—not an afterthought.
            </h2>
          </div>

          <div className="safety-grid">
            <article>
              <LockKeyhole size={21} />

              <h3>
                Strong authentication
              </h3>

              <p>
                Email verification, password security,
                rotating refresh sessions and
                authenticator-based MFA protect access to
                the application.
              </p>
            </article>

            <article>
              <ShieldCheck size={21} />

              <h3>
                Controlled access
              </h3>

              <p>
                Role-aware permissions limit administrative,
                clinical and user-facing operations to
                authorised account types.
              </p>
            </article>

            <article>
              <History size={21} />

              <h3>
                Auditability
              </h3>

              <p>
                Important account, patient, assignment,
                messaging and prediction actions can be
                recorded for later inspection.
              </p>
            </article>

            <article>
              <MessageSquare size={21} />

              <h3>
                Permitted communication
              </h3>

              <p>
                Messaging follows role-aware recipient
                rules rather than allowing unrestricted
                communication across the platform.
              </p>
            </article>
          </div>
        </section>


        {/* =================================================
            FINAL CTA
            ================================================= */}

        <section className="marketing-cta">
          <div>
            <span className="eyebrow">
              MEDISCOPE
            </span>

            <h2 className="section-heading-dark">
              Secure intelligence.
              Human decisions.
              Better continuity.
            </h2>

            <p>
              Explore a working prototype that brings
              machine-learning decision support into a
              secure, role-aware healthcare workflow.
            </p>
          </div>

          <div className="marketing-cta-actions">
            <Link
              className="button primary"
              to="/login"
            >
              Sign in

              <ArrowRight size={17} />
            </Link>

            <Link
              className="button ghost"
              to="/about"
            >
              About the project
            </Link>
          </div>
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
          <Link to="/about">
            About
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
