export type Role = 'ADMINISTRATOR' | 'CLINICIAN' | 'USER';

export interface UserProfile {
  id: string;
  email: string;
  first_name: string;
  last_name: string;
  role: Role;
  account_status: string;
  mfa_enabled?: boolean;
}

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
  updated_at?: string;
}

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
  updated_at?: string;
}

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
  logistic_regression: PredictionModelResult;
  xgboost: PredictionModelResult;
  agreement_status: 'AGREE' | 'DISAGREE';
  overall_summary: string;
  explanation_notes: string[];
  clinical_disclaimer: string;
  input_schema_version: string;
}

export interface MessageItem {
  id: string;
  subject: string;
  body: string;
  message_type?: string;
  sender_id?: string | null;
  created_at: string;
  read_at?: string | null;
}
