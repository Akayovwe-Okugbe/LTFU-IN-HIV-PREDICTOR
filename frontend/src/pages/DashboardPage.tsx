import {
  Activity,
  AlertTriangle,
  ArrowRight,
  BarChart3,
  BrainCircuit,
  CheckCircle2,
  CircleGauge,
  CircleUserRound,
  Clock3,
  Database,
  HeartPulse,
  LockKeyhole,
  MessageSquare,
  ShieldCheck,
  Stethoscope,
  UserCheck,
  UserCog,
  Users,
  ScrollText,
  TrendingUp,
} from 'lucide-react';

import {
  useEffect,
  useMemo,
  useState,
} from 'react';

import {
  useNavigate,
} from 'react-router-dom';

import {
  PageHeader,
  StatCard,
} from '../components/UI';

import {
  useAuth,
} from '../context/AuthContext';

import {
  api,
} from '../lib/api';

import type {
  ClinicianDashboardResponse,
  ClinicianPredictionTrendPoint,
  ClinicianPriorityPatient,
  HealthRecordChangeRequest,
  MessageItem,
  Patient,
  UserProfile,
} from '../lib/types';


// =====================================================
// DATE FORMATTING
// =====================================================

function formatShortDate(
  value: string,
): string {
  return new Date(
    value,
  ).toLocaleDateString(
    [],
    {
      day: 'numeric',
      month: 'short',
    },
  );
}


// =====================================================
// ACCOUNT STATUS FORMATTING
// =====================================================

function accountStatusLabel(
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
// STANDARD USER DASHBOARD
// =====================================================

function UserDashboard() {
  const {
    user,
  } = useAuth();

  const navigate =
    useNavigate();

  const [
    messages,
    setMessages,
  ] =
    useState<MessageItem[]>(
      [],
    );

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
    loading,
    setLoading,
  ] =
    useState(true);


  // ===================================================
  // LOAD USER DASHBOARD DATA
  // ===================================================

  useEffect(
    () => {
      let active =
        true;

      async function loadDashboard() {
        const results =
          await Promise.allSettled([
            api.inbox(),
            api.linkedPatient(),
            api.myChangeRequests(),
          ]);

        if (!active) {
          return;
        }

        const [
          messagesResult,
          patientResult,
          requestsResult,
        ] = results;

        if (
          messagesResult.status
          === 'fulfilled'
        ) {
          setMessages(
            messagesResult.value,
          );
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
          requestsResult.status
          === 'fulfilled'
        ) {
          setRequests(
            requestsResult.value,
          );
        }

        setLoading(
          false,
        );
      }

      void loadDashboard();

      return () => {
        active = false;
      };
    },
    [],
  );


  // ===================================================
  // DASHBOARD METRICS
  // ===================================================

  const unreadCount =
    useMemo(
      () =>
        messages.filter(
          (message) =>
            !message.read_at,
        ).length,
      [
        messages,
      ],
    );


  const pendingRequests =
    useMemo(
      () =>
        requests.filter(
          (request) =>
            request.status
            === 'PENDING',
        ).length,
      [
        requests,
      ],
    );


  const recentMessages =
    messages.slice(
      0,
      4,
    );


  // ===================================================
  // RENDER
  // ===================================================

  return (
    <>
      <PageHeader
        eyebrow="My health"
        title={`Welcome back, ${user?.first_name ?? 'there'}.`}
        description="Your health profile, secure messages and record requests in one clear place."
      />


      {/* =================================================
          PRIMARY USER SUMMARY
          ================================================= */}

      <div className="user-overview-grid">

        {/* -----------------------------------------------
            LINKED HEALTH PROFILE
            ----------------------------------------------- */}

        <button
          type="button"
          className="user-overview-card health"
          onClick={
            () =>
              navigate(
                '/app/profile',
              )
          }
        >
          <div className="user-overview-icon">
            <HeartPulse size={22} />
          </div>

          <div className="user-overview-content">
            <span className="eyebrow">
              Health profile
            </span>

            <strong>
              {
                loading
                  ? 'Loading…'
                  : patient
                    ? 'Profile linked'
                    : 'Not linked'
              }
            </strong>

            <p>
              {
                patient
                  ? (
                    patient
                      .synthetic_patient_number
                  )
                  : (
                    'No synthetic health profile is currently linked.'
                  )
              }
            </p>
          </div>

          <ArrowRight
            className="user-overview-arrow"
            size={18}
          />
        </button>


        {/* -----------------------------------------------
            SECURE MESSAGES
            ----------------------------------------------- */}

        <button
          type="button"
          className="user-overview-card messages"
          onClick={
            () =>
              navigate(
                '/app/messages',
              )
          }
        >
          <div className="user-overview-icon">
            <MessageSquare size={22} />
          </div>

          <div className="user-overview-content">
            <span className="eyebrow">
              Messages
            </span>

            <strong>
              {
                unreadCount === 0
                  ? 'All caught up'
                  : `${unreadCount} unread`
              }
            </strong>

            <p>
              Secure communication with your permitted MEDISCOPE contacts.
            </p>
          </div>

          <ArrowRight
            className="user-overview-arrow"
            size={18}
          />
        </button>


        {/* -----------------------------------------------
            CHANGE REQUESTS
            ----------------------------------------------- */}

        <button
          type="button"
          className="user-overview-card requests"
          onClick={
            () =>
              navigate(
                '/app/profile',
              )
          }
        >
          <div className="user-overview-icon">
            <Clock3 size={22} />
          </div>

          <div className="user-overview-content">
            <span className="eyebrow">
              Record requests
            </span>

            <strong>
              {
                pendingRequests === 0
                  ? 'Nothing pending'
                  : `${pendingRequests} awaiting review`
              }
            </strong>

            <p>
              Track requested changes to your linked health information.
            </p>
          </div>

          <ArrowRight
            className="user-overview-arrow"
            size={18}
          />
        </button>
      </div>


      {/* =================================================
          OPTIONAL USER MFA
          ================================================= */}

      {!user?.mfa_enabled && (
        <section className="user-security-banner">
          <div className="user-security-banner-icon">
            <ShieldCheck size={21} />
          </div>

          <div className="user-security-banner-copy">
            <strong>
              Strengthen your account security
            </strong>

            <span>
              Add an authenticator app as an optional second
              sign-in factor.
            </span>
          </div>

          <button
            type="button"
            className="button secondary"
            onClick={
              () =>
                navigate(
                  '/app/settings',
                )
            }
          >
            Set up MFA
          </button>
        </section>
      )}


      {/* =================================================
          MAIN CONTENT
          ================================================= */}

      <div className="user-dashboard-sections">

        {/* -----------------------------------------------
            RECENT MESSAGES
            ----------------------------------------------- */}

        <section className="panel user-dashboard-panel">
          <header className="user-panel-header">
            <div>
              <span className="eyebrow">
                Communication
              </span>

              <h2>
                Recent messages
              </h2>
            </div>

            <button
              type="button"
              className="text-button"
              onClick={
                () =>
                  navigate(
                    '/app/messages',
                  )
              }
            >
              View all

              <ArrowRight size={15} />
            </button>
          </header>

          {
            recentMessages.length === 0
              ? (
                <div className="dashboard-empty">
                  <div className="dashboard-empty-icon">
                    <MessageSquare size={21} />
                  </div>

                  <strong>
                    No messages yet
                  </strong>

                  <span>
                    New secure messages will appear here.
                  </span>
                </div>
              )
              : (
                <div className="dashboard-message-list">
                  {
                    recentMessages.map(
                      (
                        message,
                      ) => (
                        <button
                          type="button"
                          key={
                            message.message_id
                          }
                          className={
                            message.read_at
                              ? 'dashboard-message'
                              : 'dashboard-message unread'
                          }
                          onClick={
                            () =>
                              navigate(
                                '/app/messages',
                              )
                          }
                        >
                          <span
                            className={
                              message.read_at
                                ? 'dashboard-message-dot read'
                                : 'dashboard-message-dot'
                            }
                          />

                          <div className="dashboard-message-copy">
                            <strong>
                              {
                                message.subject
                              }
                            </strong>

                            <span>
                              {
                                message.sender_name
                                ??
                                'MEDISCOPE'
                              }
                            </span>
                          </div>

                          <time>
                            {
                              formatShortDate(
                                message.created_at,
                              )
                            }
                          </time>
                        </button>
                      ),
                    )
                  }
                </div>
              )
          }
        </section>


        {/* -----------------------------------------------
            LINKED HEALTH RECORD
            ----------------------------------------------- */}

        <section className="panel user-dashboard-panel">
          <header className="user-panel-header">
            <div>
              <span className="eyebrow">
                Health record
              </span>

              <h2>
                Your linked profile
              </h2>
            </div>

            {
              patient && (
                <span className="linked-status">
                  <CheckCircle2 size={14} />
                  Linked
                </span>
              )
            }
          </header>

          {
            patient
              ? (
                <>
                  <div className="health-summary-grid">
                    <div>
                      <span>
                        Patient number
                      </span>

                      <strong>
                        {
                          patient.synthetic_patient_number
                        }
                      </strong>
                    </div>

                    <div>
                      <span>
                        State
                      </span>

                      <strong>
                        {
                          patient.state
                        }
                      </strong>
                    </div>

                    <div>
                      <span>
                        LGA
                      </span>

                      <strong>
                        {
                          patient.lga
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
                  </div>

                  <button
                    type="button"
                    className="button secondary user-profile-button"
                    onClick={
                      () =>
                        navigate(
                          '/app/profile',
                        )
                    }
                  >
                    View health profile

                    <ArrowRight size={16} />
                  </button>
                </>
              )
              : (
                <div className="dashboard-empty">
                  <div className="dashboard-empty-icon">
                    <HeartPulse size={21} />
                  </div>

                  <strong>
                    No linked profile
                  </strong>

                  <span>
                    An administrator can link your account to a
                    synthetic patient record.
                  </span>
                </div>
              )
          }
        </section>
      </div>
    </>
  );
}


// =====================================================
// CLINICIAN DASHBOARD
//
// Clinician functionality remains intentionally separate
// from administration. Clinicians are not administrators
// and do not have access to the same system-level
// metrics or governance capabilities.
// =====================================================

function ClinicianDashboard() {
  const {
    user,
  } = useAuth();

  const navigate =
    useNavigate();

  const [
    dashboard,
    setDashboard,
  ] =
    useState<
      ClinicianDashboardResponse | null
    >(
      null,
    );

  const [
    unreadMessages,
    setUnreadMessages,
  ] =
    useState(0);

  const [
    loading,
    setLoading,
  ] =
    useState(true);

  const [
    error,
    setError,
  ] =
    useState('');


  useEffect(
    () => {
      let active = true;

      async function load() {
        setLoading(
          true,
        );

        try {
          const [
            intelligence,
            inbox,
          ] =
            await Promise.all([
              api.clinicianDashboard(),
              api.inbox(),
            ]);

          if (!active) {
            return;
          }

          setDashboard(
            intelligence,
          );

          setUnreadMessages(
            inbox.filter(
              (
                message,
              ) =>
                !message.read_at,
            ).length,
          );
        } catch (
        errorValue
        ) {
          if (active) {
            setError(
              errorValue instanceof Error
                ? errorValue.message
                : 'Unable to load clinical intelligence.',
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
    [],
  );


  if (loading) {
    return (
      <>
        <PageHeader
          eyebrow="Clinical intelligence"
          title="Preparing your care portfolio…"
          description="Loading stored patient and prediction intelligence."
        />

        <div className="dashboard-empty">
          Loading clinical intelligence…
        </div>
      </>
    );
  }


  if (
    error
    ||
    !dashboard
  ) {
    return (
      <>
        <PageHeader
          eyebrow="Clinical intelligence"
          title="Clinician overview"
          description="Assigned-patient and LTFU decision-support intelligence."
        />

        <div className="form-error">
          {
            error
            || 'Clinical intelligence is unavailable.'
          }
        </div>
      </>
    );
  }


  const {
    summary,
  } =
    dashboard;


  const priorityPatients =
    dashboard.priority_patients.filter(
      (
        patient,
      ) =>
        patient.risk_state
        !== 'BOTH_BELOW_THRESHOLD',
    );


  return (
    <>
      <PageHeader
        eyebrow="Clinical intelligence"
        title={`Welcome back, ${user?.first_name ?? 'Clinician'}.`}
        description="A data-informed view of your assigned care portfolio, stored LTFU assessments and patients requiring review."
      />


      {/* =================================================
          PRIMARY CLINICAL KPIs
          ================================================= */}

      <section className="clinician-kpi-grid">
        <button
          type="button"
          onClick={
            () =>
              navigate(
                '/app/patients',
              )
          }
          className="clinician-kpi-card"
        >
          <Stethoscope size={20} />

          <span>
            Assigned patients
          </span>

          <strong>
            {
              summary
                .assigned_patients
            }
          </strong>

          <small>
            Active care portfolio
          </small>
        </button>


        <div className="clinician-kpi-card risk">
          <CircleGauge size={20} />

          <span>
            Above threshold
          </span>

          <strong>
            {
              summary
                .both_above_threshold
            }
          </strong>

          <small>
            Both models above stored threshold
          </small>
        </div>


        <div className="clinician-kpi-card disagreement">
          <AlertTriangle size={20} />

          <span>
            Model disagreement
          </span>

          <strong>
            {
              summary
                .model_disagreement
            }
          </strong>

          <small>
            Requires closer interpretation
          </small>
        </div>


        <button
          type="button"
          onClick={
            () =>
              navigate(
                '/app/messages',
              )
          }
          className="clinician-kpi-card"
        >
          <MessageSquare size={20} />

          <span>
            Unread messages
          </span>

          <strong>
            {unreadMessages}
          </strong>

          <small>
            Secure clinical communication
          </small>
        </button>
      </section>


      {/* =================================================
          PORTFOLIO INTELLIGENCE BANNER
          ================================================= */}

      <section className="clinician-intelligence-banner">
        <div className="clinician-intelligence-icon">
          <BrainCircuit size={23} />
        </div>

        <div>
          <span className="eyebrow">
            Decision-support coverage
          </span>

          <strong>
            {
              summary
                .prediction_coverage_percentage
            }% of your assigned portfolio has a stored LTFU assessment
          </strong>

          <span>
            {
              summary
                .patients_with_predictions
            } assessed ·{' '}
            {
              summary
                .patients_without_predictions
            } without a stored assessment ·{' '}
            {
              summary
                .pending_prediction_reviews
            } awaiting clinical review
          </span>
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
          Review patients

          <ArrowRight size={16} />
        </button>
      </section>


      {/* =================================================
          ANALYTICAL VISUALS
          ================================================= */}

      <section className="clinician-analytics-grid">

        {/* -----------------------------------------------
            RISK DISTRIBUTION
            ----------------------------------------------- */}

        <article className="panel clinician-analytics-card">
          <div className="clinician-card-heading">
            <div>
              <span className="eyebrow">
                Portfolio distribution
              </span>

              <h2>
                Stored assessment states
              </h2>
            </div>

            <BarChart3 size={20} />
          </div>

          <div className="risk-distribution-bars">
            <RiskDistributionBar
              label="Both models above threshold"
              value={
                summary
                  .both_above_threshold
              }
              total={
                summary
                  .assigned_patients
              }
              state="high"
            />

            <RiskDistributionBar
              label="Model disagreement"
              value={
                summary
                  .model_disagreement
              }
              total={
                summary
                  .assigned_patients
              }
              state="review"
            />

            <RiskDistributionBar
              label="Both below threshold"
              value={
                summary
                  .both_below_threshold
              }
              total={
                summary
                  .assigned_patients
              }
              state="lower"
            />

            <RiskDistributionBar
              label="No stored assessment"
              value={
                summary
                  .patients_without_predictions
              }
              total={
                summary
                  .assigned_patients
              }
              state="missing"
            />
          </div>

          <p className="analytics-footnote">
            Categories are derived from each prediction's stored model threshold; MEDISCOPE does not invent arbitrary probability bands.
          </p>
        </article>


        {/* -----------------------------------------------
            MODEL AGREEMENT / DATA QUALITY
            ----------------------------------------------- */}

        <article className="panel clinician-analytics-card">
          <div className="clinician-card-heading">
            <div>
              <span className="eyebrow">
                Analytical assurance
              </span>

              <h2>
                Model & data quality
              </h2>
            </div>

            <Database size={20} />
          </div>

          <div className="clinical-quality-grid">
            <div>
              <strong>
                {
                  summary
                    .patients_with_predictions
                  - summary
                    .model_disagreement
                }
              </strong>

              <span>
                Latest assessments with model agreement
              </span>
            </div>

            <div>
              <strong>
                {
                  summary
                    .complete_prediction_inputs
                }
              </strong>

              <span>
                Complete stored input snapshots
              </span>
            </div>

            <div>
              <strong>
                {
                  summary
                    .incomplete_prediction_inputs
                }
              </strong>

              <span>
                Assessments containing missing inputs
              </span>
            </div>

            <div>
              <strong>
                {
                  summary
                    .pending_prediction_reviews
                }
              </strong>

              <span>
                Assessments pending clinician review
              </span>
            </div>
          </div>
        </article>
      </section>


      {/* =================================================
          PRIORITY REVIEW QUEUE
          ================================================= */}

      <section className="panel clinician-priority-panel">
        <header className="clinician-panel-header">
          <div>
            <span className="eyebrow">
              Prioritisation
            </span>

            <h2>
              Patient review queue
            </h2>

            <p>
              Patients with both models above threshold, disagreement, or no stored assessment are surfaced first.
            </p>
          </div>

          <button
            type="button"
            className="button secondary small"
            onClick={
              () =>
                navigate(
                  '/app/patients',
                )
            }
          >
            All patients
          </button>
        </header>


        <div className="clinician-priority-table">
          <div className="clinician-priority-row header">
            <span>
              Patient
            </span>

            <span>
              Logistic
            </span>

            <span>
              XGBoost
            </span>

            <span>
              Assessment
            </span>

            <span>
              Data
            </span>

            <span />
          </div>


          {
            priorityPatients.length
              === 0
              ? (
                <div className="dashboard-empty">
                  No patients currently meet the review-queue criteria.
                </div>
              )
              : (
                priorityPatients
                  .slice(
                    0,
                    8,
                  )
                  .map(
                    (
                      patient,
                    ) => (
                      <button
                        type="button"
                        className="clinician-priority-row"
                        key={
                          patient.patient_id
                        }
                        onClick={
                          () =>
                            navigate(
                              `/app/patients/${patient.patient_id}/intelligence`,
                            )
                        }
                      >
                        <div className="priority-patient">
                          <strong>
                            {
                              patient
                                .synthetic_patient_number
                            }
                          </strong>

                          <span>
                            {
                              patient.first_name
                            }{' '}
                            {
                              patient.last_name
                            }
                          </span>
                        </div>

                        <ProbabilityCell
                          value={
                            patient
                              .logistic_probability
                          }
                        />

                        <ProbabilityCell
                          value={
                            patient
                              .xgboost_probability
                          }
                        />

                        <RiskStateBadge
                          state={
                            patient
                              .risk_state
                          }
                        />

                        <span>
                          {
                            patient
                              .missing_feature_count
                              === 0
                              ? 'Complete'
                              : `${patient.missing_feature_count} missing`
                          }
                        </span>

                        <ArrowRight size={15} />
                      </button>
                    ),
                  )
              )
          }
        </div>
      </section>


      {/* =================================================
          TREND + MISSING DATA
          ================================================= */}

      <section className="clinician-analytics-grid">
        <article className="panel clinician-analytics-card">
          <div className="clinician-card-heading">
            <div>
              <span className="eyebrow">
                Longitudinal intelligence
              </span>

              <h2>
                Stored prediction trend
              </h2>
            </div>

            <TrendingUp size={20} />
          </div>

          <ClinicianTrendChart
            data={
              dashboard.trend
            }
          />

          <p className="analytics-footnote">
            Monthly points summarise stored prediction events and do not generate new assessments.
          </p>
        </article>


        <article className="panel clinician-analytics-card">
          <div className="clinician-card-heading">
            <div>
              <span className="eyebrow">
                Data quality
              </span>

              <h2>
                Most frequently missing inputs
              </h2>
            </div>

            <Database size={20} />
          </div>

          {
            dashboard
              .missing_features
              .length
              === 0
              ? (
                <div className="dashboard-empty">
                  No missing inputs were detected in the latest stored prediction snapshots.
                </div>
              )
              : (
                <div className="missing-feature-list">
                  {
                    dashboard
                      .missing_features
                      .map(
                        (
                          item,
                        ) => (
                          <div
                            key={
                              item.feature_name
                            }
                          >
                            <span>
                              {
                                item
                                  .feature_name
                                  .replaceAll(
                                    '_',
                                    ' ',
                                  )
                              }
                            </span>

                            <strong>
                              {
                                item
                                  .missing_count
                              }
                            </strong>
                          </div>
                        ),
                      )
                  }
                </div>
              )
          }
        </article>
      </section>


      <div className="clinical-disclaimer-banner">
        <ShieldCheck size={18} />

        <span>
          MEDISCOPE predictions are decision-support outputs generated from synthetic data. They do not replace clinical judgement, diagnosis or individualised care decisions.
        </span>
      </div>
    </>
  );
}


function ProbabilityCell(
  {
    value,
  }: {
    value?: number | null;
  },
) {
  if (
    value === null
    ||
    value === undefined
  ) {
    return (
      <span className="probability-empty">
        —
      </span>
    );
  }

  return (
    <div className="probability-cell">
      <strong>
        {
          Math.round(
            value
            * 100,
          )
        }%
      </strong>

      <span>
        <i
          style={{
            width:
              `${Math.min(
                100,
                Math.max(
                  0,
                  value
                  * 100,
                ),
              )}%`,
          }}
        />
      </span>
    </div>
  );
}


function RiskStateBadge(
  {
    state,
  }: {
    state:
    ClinicianPriorityPatient[
    'risk_state'
    ];
  },
) {
  const labels: Record<
    ClinicianPriorityPatient[
    'risk_state'
    ],
    string
  > = {
    BOTH_ABOVE_THRESHOLD:
      'Above threshold',

    MODEL_DISAGREEMENT:
      'Models disagree',

    BOTH_BELOW_THRESHOLD:
      'Below threshold',

    NO_STORED_ASSESSMENT:
      'No assessment',
  };

  return (
    <span
      className="clinical-risk-badge"
      data-state={
        state
      }
    >
      {
        labels[
        state
        ]
      }
    </span>
  );
}


function RiskDistributionBar(
  {
    label,
    value,
    total,
    state,
  }: {
    label: string;

    value: number;

    total: number;

    state: string;
  },
) {
  const percentage =
    total > 0
      ? (
        value
        /
        total
      )
      * 100
      : 0;

  return (
    <div className="risk-distribution-row">
      <div>
        <span>
          {label}
        </span>

        <strong>
          {value}
        </strong>
      </div>

      <div className="risk-distribution-track">
        <i
          data-state={
            state
          }
          style={{
            width:
              `${percentage}%`,
          }}
        />
      </div>
    </div>
  );
}

function ClinicianTrendChart(
  {
    data,
  }: {
    data:
    ClinicianPredictionTrendPoint[];
  },
) {
  if (
    data.length === 0
  ) {
    return (
      <div className="dashboard-empty">
        Prediction history will appear here as stored assessments accumulate.
      </div>
    );
  }

  return (
    <div className="clinical-trend-chart">
      {
        data.map(
          (
            point,
          ) => (
            <div
              className="clinical-trend-column"
              key={
                point.period
              }
            >
              <div className="clinical-trend-bars">
                <i
                  className="logistic"
                  style={{
                    height:
                      `${Math.max(
                        4,
                        point.mean_logistic_probability
                        * 100,
                      )}%`,
                  }}
                />

                <i
                  className="xgboost"
                  style={{
                    height:
                      `${Math.max(
                        4,
                        point.mean_xgboost_probability
                        * 100,
                      )}%`,
                  }}
                />
              </div>

              <strong>
                {
                  point.period
                    .slice(
                      5,
                    )
                }
              </strong>

              <span>
                {
                  point.prediction_count
                } predictions
              </span>
            </div>
          ),
        )
      }
    </div>
  );
}


// =====================================================
// ADMINISTRATOR DASHBOARD
// =====================================================

function AdministratorDashboard() {
  const {
    user,
  } = useAuth();

  const navigate =
    useNavigate();

  const [
    users,
    setUsers,
  ] =
    useState<UserProfile[]>(
      [],
    );

  const [
    messages,
    setMessages,
  ] =
    useState<MessageItem[]>(
      [],
    );

  const [
    loading,
    setLoading,
  ] =
    useState(true);


  // ===================================================
  // LOAD ADMINISTRATIVE OVERVIEW
  // ===================================================

  useEffect(
    () => {
      let active =
        true;

      async function loadAdministratorDashboard() {
        const [
          userResult,
          messageResult,
        ] =
          await Promise.allSettled([
            api.adminUsers(),
            api.inbox(),
          ]);

        if (!active) {
          return;
        }

        if (
          userResult.status
          === 'fulfilled'
        ) {
          setUsers(
            userResult.value,
          );
        }

        if (
          messageResult.status
          === 'fulfilled'
        ) {
          setMessages(
            messageResult.value,
          );
        }

        setLoading(
          false,
        );
      }

      void loadAdministratorDashboard();

      return () => {
        active = false;
      };
    },
    [],
  );


  // ===================================================
  // ADMINISTRATIVE METRICS
  // ===================================================

  const administrators =
    users.filter(
      (
        account,
      ) =>
        account.role
        === 'ADMINISTRATOR',
    ).length;

  const clinicians =
    users.filter(
      (
        account,
      ) =>
        account.role
        === 'CLINICIAN',
    ).length;

  const standardUsers =
    users.filter(
      (
        account,
      ) =>
        account.role
        === 'USER',
    ).length;

  const activeAccounts =
    users.filter(
      (
        account,
      ) =>
        account.account_status
        === 'ACTIVE',
    ).length;

  const protectedAccounts =
    users.filter(
      (
        account,
      ) =>
        account.mfa_enabled,
    ).length;

  const unreadMessages =
    messages.filter(
      (
        message,
      ) =>
        !message.read_at,
    ).length;


  // ===================================================
  // ACCOUNT STATUS BREAKDOWN
  // ===================================================

  const statusCounts =
    useMemo(
      () => {
        const result:
          Record<
            string,
            number
          > = {};

        for (
          const account
          of users
        ) {
          result[
            account.account_status
          ] =
            (
              result[
              account.account_status
              ]
              ?? 0
            )
            + 1;
        }

        return result;
      },
      [
        users,
      ],
    );


  // ===================================================
  // CHART HELPERS
  // ===================================================

  const maximumRoleCount =
    Math.max(
      administrators,
      clinicians,
      standardUsers,
      1,
    );

  const maximumStatusCount =
    Math.max(
      ...Object.values(
        statusCounts,
      ),
      1,
    );


  // ===================================================
  // RENDER
  // ===================================================

  return (
    <>
      <PageHeader
        eyebrow="Administration overview"
        title={`Welcome, ${user?.first_name ?? 'Administrator'}.`}
        description="Monitor account governance, workforce composition, access status and administrative operations."
      />


      {/* =================================================
          RESPONSIVE ADMIN KPI CARDS
          ================================================= */}

      <div className="admin-kpi-grid">
        <button
          type="button"
          className="admin-kpi-card"
          onClick={
            () =>
              navigate(
                '/app/administration',
              )
          }
        >
          <div className="admin-kpi-icon all">
            <Users size={21} />
          </div>

          <div>
            <span>
              Total accounts
            </span>

            <strong>
              {
                loading
                  ? '—'
                  : users.length
              }
            </strong>

            <small>
              Entire MEDISCOPE directory
            </small>
          </div>
        </button>


        <button
          type="button"
          className="admin-kpi-card"
          onClick={
            () =>
              navigate(
                '/app/administration?role=CLINICIAN',
              )
          }
        >
          <div className="admin-kpi-icon clinician">
            <Stethoscope size={21} />
          </div>

          <div>
            <span>
              Clinicians
            </span>

            <strong>
              {
                loading
                  ? '—'
                  : clinicians
              }
            </strong>

            <small>
              Clinical workforce
            </small>
          </div>
        </button>


        <button
          type="button"
          className="admin-kpi-card"
          onClick={
            () =>
              navigate(
                '/app/administration?role=USER',
              )
          }
        >
          <div className="admin-kpi-icon users">
            <CircleUserRound size={21} />
          </div>

          <div>
            <span>
              Standard users
            </span>

            <strong>
              {
                loading
                  ? '—'
                  : standardUsers
              }
            </strong>

            <small>
              Patient-facing accounts
            </small>
          </div>
        </button>


        <button
          type="button"
          className="admin-kpi-card"
          onClick={
            () =>
              navigate(
                '/app/administration?role=ADMINISTRATOR',
              )
          }
        >
          <div className="admin-kpi-icon administrator">
            <UserCog size={21} />
          </div>

          <div>
            <span>
              Administrators
            </span>

            <strong>
              {
                loading
                  ? '—'
                  : administrators
              }
            </strong>

            <small>
              Privileged governance accounts
            </small>
          </div>
        </button>
      </div>


      {/* =================================================
          AUDIT & GOVERNANCE ACCESS

          Audit logs are a governance capability rather than
          a numerical KPI, so they are presented separately
          from the administrator metric cards.
          ================================================= */}

      <section className="admin-audit-banner">
        <div className="admin-audit-banner-icon">
          <ScrollText size={22} />
        </div>

        <div className="admin-audit-banner-copy">
          <span className="eyebrow">
            Governance & assurance
          </span>

          <strong>
            Review system activity and audit trails
          </strong>

          <span>
            Inspect administrative actions, security events,
            affected resources and recorded outcomes across
            MEDISCOPE.
          </span>
        </div>

        <button
          type="button"
          className="button secondary"
          onClick={
            () =>
              navigate(
                '/app/audit-logs',
              )
          }
        >
          <ScrollText size={16} />

          View audit logs

          <ArrowRight size={15} />
        </button>
      </section>


      {/* =================================================
          SYSTEM GOVERNANCE STRIP
          ================================================= */}

      <section className="admin-overview-strip">
        <div>
          <UserCheck size={18} />

          <span>
            Active accounts
          </span>

          <strong>
            {activeAccounts}
          </strong>
        </div>

        <div>
          <LockKeyhole size={18} />

          <span>
            MFA-enabled accounts
          </span>

          <strong>
            {protectedAccounts}
          </strong>
        </div>

        <button
          type="button"
          onClick={
            () =>
              navigate(
                '/app/messages',
              )
          }
        >
          <MessageSquare size={18} />

          <span>
            Unread messages
          </span>

          <strong>
            {unreadMessages}
          </strong>
        </button>

        <div>
          <ShieldCheck size={18} />

          <span>
            RBAC policy
          </span>

          <strong>
            Enforced
          </strong>
        </div>
      </section>


      {/* =================================================
          ADMINISTRATOR CHARTS
          ================================================= */}

      <div className="admin-dashboard-grid">

        {/* -----------------------------------------------
            ROLE DISTRIBUTION
            ----------------------------------------------- */}

        <section className="panel admin-chart-panel">
          <header className="admin-chart-heading">
            <div>
              <span className="eyebrow">
                Identity governance
              </span>

              <h2>
                Account distribution
              </h2>
            </div>

            <Users size={19} />
          </header>

          <div className="admin-bar-chart">
            <div className="admin-chart-row">
              <div className="admin-chart-label">
                <span>
                  Clinicians
                </span>

                <strong>
                  {clinicians}
                </strong>
              </div>

              <div className="admin-chart-track">
                <span
                  className="clinician"
                  style={{
                    width:
                      `${(
                        clinicians
                        /
                        maximumRoleCount
                      )
                      * 100
                      }%`,
                  }}
                />
              </div>
            </div>


            <div className="admin-chart-row">
              <div className="admin-chart-label">
                <span>
                  Standard users
                </span>

                <strong>
                  {standardUsers}
                </strong>
              </div>

              <div className="admin-chart-track">
                <span
                  className="user"
                  style={{
                    width:
                      `${(
                        standardUsers
                        /
                        maximumRoleCount
                      )
                      * 100
                      }%`,
                  }}
                />
              </div>
            </div>


            <div className="admin-chart-row">
              <div className="admin-chart-label">
                <span>
                  Administrators
                </span>

                <strong>
                  {administrators}
                </strong>
              </div>

              <div className="admin-chart-track">
                <span
                  className="administrator"
                  style={{
                    width:
                      `${(
                        administrators
                        /
                        maximumRoleCount
                      )
                      * 100
                      }%`,
                  }}
                />
              </div>
            </div>
          </div>

          <button
            type="button"
            className="text-button admin-chart-link"
            onClick={
              () =>
                navigate(
                  '/app/administration',
                )
            }
          >
            Open account directory

            <ArrowRight size={15} />
          </button>
        </section>


        {/* -----------------------------------------------
            ACCOUNT STATUS DISTRIBUTION
            ----------------------------------------------- */}

        <section className="panel admin-chart-panel">
          <header className="admin-chart-heading">
            <div>
              <span className="eyebrow">
                Access state
              </span>

              <h2>
                Account status
              </h2>
            </div>

            <ShieldCheck size={19} />
          </header>

          <div className="admin-bar-chart">
            {
              Object.entries(
                statusCounts,
              ).map(
                (
                  [
                    status,
                    count,
                  ],
                ) => (
                  <div
                    className="admin-chart-row"
                    key={
                      status
                    }
                  >
                    <div className="admin-chart-label">
                      <span>
                        {
                          accountStatusLabel(
                            status,
                          )
                        }
                      </span>

                      <strong>
                        {count}
                      </strong>
                    </div>

                    <div className="admin-chart-track">
                      <span
                        className={
                          status === 'ACTIVE'
                            ? 'active'
                            : 'restricted'
                        }
                        style={{
                          width:
                            `${(
                              count
                              /
                              maximumStatusCount
                            )
                            * 100
                            }%`,
                        }}
                      />
                    </div>
                  </div>
                ),
              )
            }

            {
              Object.keys(
                statusCounts,
              ).length
              === 0 && (
                <div className="dashboard-empty">
                  No account status data available.
                </div>
              )
            }
          </div>
        </section>
      </div>


      {/* =================================================
          SECURITY / QUICK OPERATIONS
          ================================================= */}

      <div className="admin-dashboard-grid admin-dashboard-secondary">

        <section className="panel admin-governance-panel">
          <span className="eyebrow">
            Security posture
          </span>

          <h2>
            Administrative safeguards
          </h2>

          <div className="admin-governance-list">
            <div>
              <CheckCircle2 size={17} />

              <span>
                Role-based access control
              </span>

              <strong>
                Enforced
              </strong>
            </div>

            <div>
              <CheckCircle2 size={17} />

              <span>
                Privileged-role MFA
              </span>

              <strong>
                Required
              </strong>
            </div>

            <div>
              <CheckCircle2 size={17} />

              <span>
                Administrative audit logging
              </span>

              <strong>
                Enabled
              </strong>
            </div>

            <div>
              <CheckCircle2 size={17} />

              <span>
                Soft account deletion
              </span>

              <strong>
                Preserves history
              </strong>
            </div>
          </div>
        </section>


        <section className="panel admin-quick-actions">
          <span className="eyebrow">
            Administration
          </span>

          <h2>
            Quick operations
          </h2>

          <button
            type="button"
            onClick={
              () =>
                navigate(
                  '/app/administration',
                )
            }
          >
            <Users size={18} />

            <div>
              <strong>
                Manage accounts
              </strong>

              <span>
                Users, roles and account status
              </span>
            </div>

            <ArrowRight size={16} />
          </button>

          <button
            type="button"
            onClick={
              () =>
                navigate(
                  '/app/administration?role=CLINICIAN',
                )
            }
          >
            <Stethoscope size={18} />

            <div>
              <strong>
                Manage clinical workforce
              </strong>

              <span>
                Clinicians and patient assignments
              </span>
            </div>

            <ArrowRight size={16} />
          </button>

          <button
            type="button"
            onClick={
              () =>
                navigate(
                  '/app/messages',
                )
            }
          >
            <MessageSquare size={18} />

            <div>
              <strong>
                Secure messages
              </strong>

              <span>
                Administrative communication
              </span>
            </div>

            <ArrowRight size={16} />
          </button>
        </section>
      </div>
    </>
  );
}


// =====================================================
// UNSUPPORTED ROLE
// =====================================================

function UnsupportedRoleDashboard() {
  return (
    <section className="panel unsupported-role-panel">
      <AlertTriangle size={28} />

      <h2>
        Workspace unavailable
      </h2>

      <p>
        Your account does not have a recognised MEDISCOPE
        workspace role. Access has not been granted.
      </p>
    </section>
  );
}


// =====================================================
// EXPLICIT ROLE-AWARE DASHBOARD ROUTER
//
// SECURITY:
// No role is treated as Administrator by default.
// Unknown, missing or future roles fail closed.
// =====================================================

export default function DashboardPage() {
  const {
    user,
  } = useAuth();


  if (!user) {
    return (
      <UnsupportedRoleDashboard />
    );
  }


  if (
    user.role === 'USER'
  ) {
    return (
      <UserDashboard />
    );
  }


  if (
    user.role === 'CLINICIAN'
  ) {
    return (
      <ClinicianDashboard />
    );
  }


  if (
    user.role === 'ADMINISTRATOR'
  ) {
    return (
      <AdministratorDashboard />
    );
  }


  // -------------------------------------------------
  // FAIL CLOSED
  //
  // An unknown role must never inherit administrator
  // functionality merely because it failed previous
  // comparisons.
  // -------------------------------------------------

  return (
    <UnsupportedRoleDashboard />
  );
}
