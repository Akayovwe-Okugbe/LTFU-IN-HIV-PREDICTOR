import {
  Activity,
  AlertTriangle,
  ArrowRight,
  CheckCircle2,
  CircleUserRound,
  Clock3,
  HeartPulse,
  LockKeyhole,
  MessageSquare,
  ShieldCheck,
  Stethoscope,
  UserCheck,
  UserCog,
  Users,
  ScrollText,
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
// from administration. A later UI refinement can expand
// this dashboard without affecting administrator or USER
// workflows.
// =====================================================

function ClinicianDashboard() {
  const {
    user,
  } = useAuth();

  const navigate =
    useNavigate();

  const [
    patientCount,
    setPatientCount,
  ] =
    useState(0);

  const [
    messages,
    setMessages,
  ] =
    useState<MessageItem[]>(
      [],
    );


  useEffect(
    () => {
      let active =
        true;

      async function loadClinicianDashboard() {
        const [
          patientResult,
          messageResult,
        ] =
          await Promise.allSettled([
            api.assignedPatients(),
            api.inbox(),
          ]);

        if (!active) {
          return;
        }

        if (
          patientResult.status
          === 'fulfilled'
        ) {
          setPatientCount(
            patientResult.value.length,
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
      }

      void loadClinicianDashboard();

      return () => {
        active = false;
      };
    },
    [],
  );


  const unreadMessages =
    messages.filter(
      (
        message,
      ) =>
        !message.read_at,
    ).length;


  return (
    <>
      <PageHeader
        eyebrow="Clinical workspace"
        title={`Good to see you, ${user?.first_name ?? ''}.`}
        description="Review your assigned patients, secure communication and clinical workflows."
      />

      <div className="admin-kpi-grid">
        <button
          type="button"
          className="admin-kpi-card"
          onClick={
            () =>
              navigate(
                '/app/patients',
              )
          }
        >
          <div className="admin-kpi-icon clinician">
            <Stethoscope size={21} />
          </div>

          <div>
            <span>
              Assigned patients
            </span>

            <strong>
              {patientCount}
            </strong>

            <small>
              Current clinical workload
            </small>
          </div>
        </button>


        <button
          type="button"
          className="admin-kpi-card"
          onClick={
            () =>
              navigate(
                '/app/messages',
              )
          }
        >
          <div className="admin-kpi-icon all">
            <MessageSquare size={21} />
          </div>

          <div>
            <span>
              Unread messages
            </span>

            <strong>
              {unreadMessages}
            </strong>

            <small>
              Secure communication
            </small>
          </div>
        </button>


        <button
          type="button"
          className="admin-kpi-card"
          onClick={
            () =>
              navigate(
                '/app/predictions',
              )
          }
        >
          <div className="admin-kpi-icon users">
            <Activity size={21} />
          </div>

          <div>
            <span>
              Prediction workflow
            </span>

            <strong>
              Active
            </strong>

            <small>
              Decision-support access
            </small>
          </div>
        </button>


        <button
          type="button"
          className="admin-kpi-card"
          onClick={
            () =>
              navigate(
                '/app/settings',
              )
          }
        >
          <div className="admin-kpi-icon administrator">
            <ShieldCheck size={21} />
          </div>

          <div>
            <span>
              Account security
            </span>

            <strong>
              MFA
            </strong>

            <small>
              Required for clinicians
            </small>
          </div>
        </button>
      </div>
    </>
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
