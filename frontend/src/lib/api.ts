import type {
  AdministrationMetadata,
  AdminPatientSummary,
  AuditLogItem,
  AuditLogListResponse,
  AuditLogMetadata,
  ClinicianAssignment,
  ClinicalRecord,
  HealthRecordChangeRequest,
  MessageItem,
  MessageRecipient,
  Patient,
  PredictionResponse,
  SentMessageItem,
  TokenPairResponse,
  TotpConfirmResponse,
  TotpSetupResponse,
  UserProfile,
} from './types';


// =====================================================
// API CONFIGURATION
// =====================================================

const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL
  ??
  'http://127.0.0.1:8000/api/v1';


// =====================================================
// CUSTOM API ERROR
// =====================================================

export class ApiError extends Error {
  status: number;

  constructor(
    message: string,
    status: number,
  ) {
    super(
      message,
    );

    this.name =
      'ApiError';

    this.status =
      status;
  }
}


// =====================================================
// ACCESS TOKEN
// =====================================================

function storedAccessToken():
  string | null {
  return sessionStorage.getItem(
    'mediscope_access_token',
  );
}


// =====================================================
// SHARED REQUEST HELPER
// =====================================================

async function request<T>(
  path: string,
  init: RequestInit = {},
): Promise<T> {
  const token =
    storedAccessToken();

  const headers =
    new Headers(
      init.headers,
    );

  headers.set(
    'Accept',
    'application/json',
  );

  if (init.body) {
    headers.set(
      'Content-Type',
      'application/json',
    );
  }

  if (token) {
    headers.set(
      'Authorization',
      `Bearer ${token}`,
    );
  }

  const response =
    await fetch(
      `${API_BASE_URL}${path}`,
      {
        ...init,
        headers,
      },
    );

  if (!response.ok) {
    let message =
      `Request failed with status ${response.status}.`;

    try {
      const body =
        await response.json();

      message =
        body.detail
        ??
        body.message
        ??
        message;
    } catch {
      // The backend returned a non-JSON error.
    }

    throw new ApiError(
      message,
      response.status,
    );
  }

  if (
    response.status
    === 204
  ) {
    return undefined as T;
  }

  return (response.json() as Promise<T>);
}


// =====================================================
// API CLIENT
// =====================================================

export const api = {

  // ===================================================
  // AUTHENTICATION
  // ===================================================

  login: (
    email: string,
    password: string,
  ) =>
    request<
      Record<
        string,
        unknown
      >
    >(
      '/auth/login',
      {
        method: 'POST',

        body:
          JSON.stringify({
            email,
            password,
          }),
      },
    ),


  completeMfa: (
    mfaChallengeToken: string,
    code: string,
  ) =>
    request<TokenPairResponse>(
      '/auth/mfa/totp/login',
      {
        method: 'POST',

        body:
          JSON.stringify({
            mfa_challenge_token:
              mfaChallengeToken,

            code,
          }),
      },
    ),


  // ---------------------------------------------------
  // Mandatory clinician/admin MFA enrolment
  // ---------------------------------------------------

  beginRequiredMfaSetup: (
    mfaSetupToken: string,
  ) =>
    request<TotpSetupResponse>(
      '/auth/mfa/totp/setup/login',
      {
        method: 'POST',

        body:
          JSON.stringify({
            mfa_setup_token:
              mfaSetupToken,
          }),
      },
    ),


  confirmRequiredMfaSetup: (
    mfaSetupToken: string,
    code: string,
  ) =>
    request<
      TokenPairResponse & {
        message: string;
        recovery_codes: string[];
      }
    >(
      '/auth/mfa/totp/confirm/login',
      {
        method: 'POST',

        body:
          JSON.stringify({
            mfa_setup_token:
              mfaSetupToken,

            code,
          }),
      },
    ),


  // ---------------------------------------------------
  // Registration / verification
  // ---------------------------------------------------

  register: (
    payload:
      Record<
        string,
        unknown
      >,
  ) =>
    request<{
      message: string;
    }>(
      '/auth/register',
      {
        method: 'POST',

        body:
          JSON.stringify(
            payload,
          ),
      },
    ),


  verifyEmail: (
    email: string,
    otp: string,
  ) =>
    request<{
      message: string;
    }>(
      '/auth/email/verify',
      {
        method: 'POST',

        body:
          JSON.stringify({
            email,
            otp,
          }),
      },
    ),


  resendVerification: (
    email: string,
  ) =>
    request<{
      message: string;
    }>(
      '/auth/email/resend',
      {
        method: 'POST',

        body:
          JSON.stringify({
            email,
          }),
      },
    ),


  // ---------------------------------------------------
  // Password recovery
  // ---------------------------------------------------

  forgotPassword: (
    email: string,
  ) =>
    request<{
      message: string;
    }>(
      '/auth/password/forgot',
      {
        method: 'POST',

        body:
          JSON.stringify({
            email,
          }),
      },
    ),


  resetPassword: (
    token: string,
    newPassword: string,
  ) =>
    request<{
      message: string;
    }>(
      '/auth/password/reset',
      {
        method: 'POST',

        body:
          JSON.stringify({
            token,

            new_password:
              newPassword,
          }),
      },
    ),


  // ===================================================
  // CURRENT USER PROFILE
  // ===================================================

  currentUser: () =>
    request<UserProfile>(
      '/users/me',
    ),


  updateCurrentUser: (
    payload:
      Partial<
        Pick<
          UserProfile,
          | 'first_name'
          | 'last_name'
          | 'phone'
          | 'gender'
          | 'date_of_birth'
        >
      >,
  ) =>
    request<UserProfile>(
      '/users/me',
      {
        method: 'PATCH',

        body:
          JSON.stringify(
            payload,
          ),
      },
    ),


  linkedPatient: () =>
    request<
      Patient | null
    >(
      '/users/me/patient',
    ),


  // ===================================================
  // CHANGE REQUESTS
  // ===================================================

  myChangeRequests: () =>
    request<
      HealthRecordChangeRequest[]
    >(
      '/change-requests/mine',
    ),


  submitChangeRequest: (
    payload: {
      field_name: string;

      proposed_value: string;

      reason?: string;
    },
  ) =>
    request<
      HealthRecordChangeRequest
    >(
      '/change-requests',
      {
        method: 'POST',

        body:
          JSON.stringify(
            payload,
          ),
      },
    ),


  pendingChangeRequests: () =>
    request<
      HealthRecordChangeRequest[]
    >(
      '/change-requests/pending',
    ),


  // ===================================================
  // NORMAL AUTHENTICATED MFA SETTINGS
  // ===================================================

  beginTotpSetup: () =>
    request<TotpSetupResponse>(
      '/auth/mfa/totp/setup',
      {
        method: 'POST',
      },
    ),


  confirmTotpSetup: (
    code: string,
  ) =>
    request<TotpConfirmResponse>(
      '/auth/mfa/totp/confirm',
      {
        method: 'POST',

        body:
          JSON.stringify({
            code,
          }),
      },
    ),


  disableTotp: (
    password: string,
    code: string,
  ) =>
    request<{
      message: string;
    }>(
      '/auth/mfa/totp/disable',
      {
        method: 'POST',

        body:
          JSON.stringify({
            password,
            code,
          }),
      },
    ),


  // ===================================================
  // CLINICAL
  // ===================================================

  assignedPatients: () =>
    request<Patient[]>(
      '/clinical/patients',
    ),


  clinicalRecords: (
    patientId: string,
  ) =>
    request<
      ClinicalRecord[]
    >(
      `/clinical/patients/${patientId}/records`,
    ),


  // ===================================================
  // ADMINISTRATION
  // ===================================================

  adminMetadata: () =>
    request<AdministrationMetadata>(
      '/admin/metadata',
    ),

  adminUsers: () =>
    request<UserProfile[]>(
      '/admin/users',
    ),


  // ===================================================
  // PREDICTIONS
  // ===================================================

  predictionModels: () =>
    request<unknown[]>(
      '/predictions/models',
    ),


  predictPatient: (
    patientId: string,
  ) =>
    request<PredictionResponse>(
      `/predictions/patients/${patientId}`,
      {
        method: 'POST',
      },
    ),


  predictionHistory: (
    patientId: string,
  ) =>
    request<unknown[]>(
      `/predictions/patients/${patientId}/history`,
    ),


  manualPrediction: (
    payload:
      Record<
        string,
        unknown
      >,
  ) =>
    request<PredictionResponse>(
      '/predictions/manual',
      {
        method: 'POST',

        body:
          JSON.stringify(
            payload,
          ),
      },
    ),


  // ===================================================
  // MESSAGING
  // ===================================================

  inbox: () =>
    request<MessageItem[]>(
      '/messages/inbox',
    ),


  sentMessages: () =>
    request<
      SentMessageItem[]
    >(
      '/messages/sent',
    ),


  messageRecipients: () =>
    request<
      MessageRecipient[]
    >(
      '/messages/recipients',
    ),


  sendMessage: (
    payload: {
      recipient_ids: string[];

      subject: string;

      body: string;
    },
  ) =>
    request<unknown>(
      '/messages',
      {
        method: 'POST',

        body:
          JSON.stringify(
            payload,
          ),
      },
    ),


  markMessageRead: (
    messageId: string,
  ) =>
    request<void>(
      `/messages/${messageId}/read`,
      {
        method: 'POST',
      },
    ),


  deleteInboxMessage: (
    messageId: string,
  ) =>
    request<void>(
      `/messages/${messageId}`,
      {
        method: 'DELETE',
      },
    ),


  // =====================================================
  // ADMINISTRATION — USERS
  // =====================================================

  adminUser: (
    userId: string,
  ) =>
    request<UserProfile>(
      `/admin/users/${userId}`,
    ),


  adminCreateUser: (
    payload: {
      email: string;
      password: string;
      first_name: string;
      last_name: string;
      date_of_birth?: string | null;
      phone?: string | null;
      gender?: string | null;
      role: string;
    },
  ) =>
    request<UserProfile>(
      '/admin/users',
      {
        method: 'POST',

        body: JSON.stringify(
          payload,
        ),
      },
    ),


  adminUpdateUser: (
    userId: string,
    payload: Partial<{
      first_name: string;
      last_name: string;
      phone: string | null;
      gender: string | null;
      date_of_birth: string | null;
    }>,
  ) =>
    request<UserProfile>(
      `/admin/users/${userId}`,
      {
        method: 'PATCH',

        body: JSON.stringify(
          payload,
        ),
      },
    ),


  adminChangeUserRole: (
    userId: string,
    role: string,
  ) =>
    request<UserProfile>(
      `/admin/users/${userId}/role`,
      {
        method: 'PATCH',

        body: JSON.stringify({
          role,
        }),
      },
    ),


  adminChangeUserStatus: (
    userId: string,
    accountStatus: string,
  ) =>
    request<UserProfile>(
      `/admin/users/${userId}/status`,
      {
        method: 'PATCH',

        body: JSON.stringify({
          account_status:
            accountStatus,
        }),
      },
    ),


  adminDeleteUser: (
    userId: string,
  ) =>
    request<void>(
      `/admin/users/${userId}`,
      {
        method: 'DELETE',
      },
    ),


  // =====================================================
  // ADMINISTRATION — PATIENTS & ASSIGNMENTS
  // =====================================================

  adminPatients: () =>
    request<AdminPatientSummary[]>(
      '/admin/patients',
    ),


  adminAssignments: (
    options?: {
      clinicianUserId?: string;
      patientId?: string;
      activeOnly?: boolean;
    },
  ) => {
    const params =
      new URLSearchParams();

    if (
      options?.clinicianUserId
    ) {
      params.set(
        'clinician_user_id',
        options.clinicianUserId,
      );
    }

    if (
      options?.patientId
    ) {
      params.set(
        'patient_id',
        options.patientId,
      );
    }

    if (
      options?.activeOnly
      !== undefined
    ) {
      params.set(
        'active_only',
        String(
          options.activeOnly,
        ),
      );
    }

    const query =
      params.toString();

    return request<
      ClinicianAssignment[]
    >(
      `/admin/assignments${query
        ? `?${query}`
        : ''
      }`,
    );
  },


  adminAssignClinician: (
    clinicianUserId: string,
    patientId: string,
  ) =>
    request<ClinicianAssignment>(
      '/admin/assignments',
      {
        method: 'POST',

        body: JSON.stringify({
          clinician_user_id:
            clinicianUserId,

          patient_id:
            patientId,
        }),
      },
    ),


  adminEndAssignment: (
    assignmentId: string,
  ) =>
    request<ClinicianAssignment>(
      `/admin/assignments/${assignmentId}`,
      {
        method: 'DELETE',
      },
    ),


  adminLinkUserToPatient: (
    patientId: string,
    userId: string,
  ) =>
    request<{
      message: string;
    }>(
      `/admin/patients/${patientId}/link-user`,
      {
        method: 'PATCH',

        body: JSON.stringify({
          user_id:
            userId,
        }),
      },
    ),


  adminUnlinkUserFromPatient: (
    patientId: string,
  ) =>
    request<{
      message: string;
    }>(
      `/admin/patients/${patientId}/link-user`,
      {
        method: 'DELETE',
      },
    ),


  // ===================================================
  // ADMINISTRATOR AUDIT LOGS
  // ===================================================

  auditLogs: (
    options?: {
      search?: string;

      action?: string;

      outcome?: string;

      resourceType?: string;

      actorUserId?: string;

      dateFrom?: string;

      dateTo?: string;

      limit?: number;

      offset?: number;
    },
  ) => {
    const params =
      new URLSearchParams();

    if (
      options?.search
    ) {
      params.set(
        'search',
        options.search,
      );
    }

    if (
      options?.action
    ) {
      params.set(
        'action',
        options.action,
      );
    }

    if (
      options?.outcome
    ) {
      params.set(
        'outcome',
        options.outcome,
      );
    }

    if (
      options?.resourceType
    ) {
      params.set(
        'resource_type',
        options.resourceType,
      );
    }

    if (
      options?.actorUserId
    ) {
      params.set(
        'actor_user_id',
        options.actorUserId,
      );
    }

    if (
      options?.dateFrom
    ) {
      params.set(
        'date_from',
        options.dateFrom,
      );
    }

    if (
      options?.dateTo
    ) {
      params.set(
        'date_to',
        options.dateTo,
      );
    }

    params.set(
      'limit',
      String(
        options?.limit
        ?? 50,
      ),
    );

    params.set(
      'offset',
      String(
        options?.offset
        ?? 0,
      ),
    );

    return request<
      AuditLogListResponse
    >(
      `/admin/audit-logs?${params.toString()}`,
    );
  },


  auditLog: (
    auditLogId: string,
  ) =>
    request<AuditLogItem>(
      `/admin/audit-logs/${auditLogId}`,
    ),


  auditLogMetadata: () =>
    request<AuditLogMetadata>(
      '/admin/audit-logs/metadata',
    ),
};



