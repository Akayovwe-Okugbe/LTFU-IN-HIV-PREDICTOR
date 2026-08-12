// =====================================================
// MEDISCOPE FRONTEND TYPES
// =====================================================

export type Role =
  | 'ADMINISTRATOR'
  | 'CLINICIAN'
  | 'USER';


// =====================================================
// USER / ACCOUNT
// =====================================================

export interface UserProfile {
  id: string;

  email: string;

  first_name: string;
  last_name: string;

  phone?: string | null;

  gender?:
  | 'Male'
  | 'Female'
  | string
  | null;

  date_of_birth?: string | null;

  role: Role;

  account_status: string;

  mfa_enabled: boolean;

  email_verified_at?: string | null;

  last_login_at?: string | null;

  created_at?: string;
  updated_at?: string;
}


// =====================================================
// PATIENT
// =====================================================

export interface Patient {
  id: string;

  linked_user_id?: string | null;

  synthetic_patient_number: string;

  first_name: string;
  last_name: string;

  date_of_birth?: string | null;

  sex: string;

  state: string;

  lga: string;

  status: string;

  is_synthetic: boolean;

  created_at?: string;
  updated_at?: string;
}


// =====================================================
// CLINICAL RECORD
// =====================================================

export interface ClinicalRecord {
  id: string;

  patient_id: string;

  art_start_date?: string | null;

  age_at_art_initiation?: number | null;

  last_regimen?: string | null;

  days_of_arv_refill?: number | null;

  current_viral_load?: number | null;

  pregnancy_status?: string | null;

  last_clinic_visit_date?: string | null;

  notes?: string | null;

  created_at?: string;
  updated_at?: string;
}


// =====================================================
// HEALTH-RECORD CHANGE REQUEST
// =====================================================

export interface HealthRecordChangeRequest {
  id: string;

  patient_id: string;

  requested_by: string;

  field_name: string;

  previous_value?: string | null;

  proposed_value: string;

  reason?: string | null;

  status: string;

  reviewed_by?: string | null;

  reviewed_at?: string | null;

  review_comment?: string | null;

  created_at: string;

  updated_at: string;
}


// =====================================================
// MESSAGE TYPES
// =====================================================

export interface MessageItem {
  message_id: string;

  sender_id?: string | null;

  sender_name?: string | null;

  subject: string;

  body: string;

  message_type?: string;

  created_at: string;

  read_at?: string | null;
}


export interface SentMessageItem {
  id: string;

  recipient_ids: string[];

  subject: string;

  body: string;

  message_type: string;

  created_at: string;
}


export interface MessageRecipient {
  id: string;

  email: string;

  first_name: string;

  last_name: string;

  role: Role;
}


// =====================================================
// PREDICTION TYPES
// =====================================================

export interface PredictionModelResult {
  model_name: string;

  model_version: string;

  probability: number;

  classification: string;

  threshold: number;
}


export interface PredictionResponse {
  prediction_id: string;

  patient_id?: string | null;

  generated_at: string;

  logistic_regression:
  PredictionModelResult;

  xgboost:
  PredictionModelResult;

  agreement_status:
  | 'AGREE'
  | 'DISAGREE';

  overall_summary: string;

  explanation_notes: string[];

  clinical_disclaimer: string;

  input_schema_version: string;
}


// =====================================================
// MFA TYPES
// =====================================================

export interface TotpSetupResponse {
  provisioning_uri: string;

  manual_secret: string;

  message: string;
}


export interface TotpConfirmResponse {
  message: string;

  recovery_codes: string[];
}


// =====================================================
// AUTHENTICATION TOKEN RESPONSE
// =====================================================

export interface TokenPairResponse {
  access_token: string;

  refresh_token: string;

  token_type: string;
}


// =====================================================
// ADMINISTRATION
// =====================================================

export type AdministrationMetadata = {
  roles: Role[];

  account_statuses: string[];
};


export type AdminPatientSummary = {
  id: string;

  synthetic_patient_number: string;

  first_name?: string | null;

  last_name?: string | null;

  sex?: string | null;

  state?: string | null;

  lga?: string | null;

  status?: string | null;

  linked_user_id?: string | null;

  is_synthetic: boolean;
};


export type ClinicianAssignment = {
  id: string;

  clinician_user_id: string;

  patient_id: string;

  assigned_by: string;

  assigned_at: string;

  ended_at?: string | null;

  is_active: boolean;
};


// =====================================================
// AUDIT LOGS
// =====================================================

export type AuditLogItem = {
  id: string;

  actor_user_id?: string | null;

  actor_name?: string | null;

  actor_email?: string | null;

  action: string;

  outcome: string;

  resource_type?: string | null;

  resource_id?: string | null;

  ip_address?: string | null;

  user_agent?: string | null;

  details?: Record<
    string,
    unknown
  > | null;

  created_at: string;
};


export type AuditLogListResponse = {
  items: AuditLogItem[];

  total: number;

  limit: number;

  offset: number;
};


export type AuditLogMetadata = {
  actions: string[];

  outcomes: string[];

  resource_types: string[];
};
