import type { ClinicalRecord, MessageItem, Patient, PredictionResponse, UserProfile } from './types';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? 'http://127.0.0.1:8000/api/v1';

export class ApiError extends Error {
  status: number;
  constructor(message: string, status: number) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
  }
}

function storedAccessToken(): string | null {
  return sessionStorage.getItem('mediscope_access_token');
}

async function request<T>(path: string, init: RequestInit = {}): Promise<T> {
  const token = storedAccessToken();
  const headers = new Headers(init.headers);
  headers.set('Accept', 'application/json');
  if (init.body) headers.set('Content-Type', 'application/json');
  if (token) headers.set('Authorization', `Bearer ${token}`);

  const response = await fetch(`${API_BASE_URL}${path}`, { ...init, headers });
  if (!response.ok) {
    let message = `Request failed with status ${response.status}.`;
    try {
      const body = await response.json();
      message = body.detail ?? body.message ?? message;
    } catch { /* Response was not JSON. */ }
    throw new ApiError(message, response.status);
  }
  if (response.status === 204) return undefined as T;
  return response.json() as Promise<T>;
}

export const api = {
  login: (email: string, password: string) =>
    request<Record<string, unknown>>('/auth/login', {
      method: 'POST',
      body: JSON.stringify({ email, password }),
    }),

  completeMfa: (mfa_challenge_token: string, code: string) =>
    request<{ access_token: string; refresh_token: string; token_type: string }>('/auth/mfa/totp/login', {
      method: 'POST',
      body: JSON.stringify({ mfa_challenge_token, code }),
    }),

  register: (payload: Record<string, unknown>) =>
    request<{ message: string }>('/auth/register', { method: 'POST', body: JSON.stringify(payload) }),

  verifyEmail: (email: string, otp: string) =>
    request<{ message: string }>('/auth/email/verify', { method: 'POST', body: JSON.stringify({ email, otp }) }),

  forgotPassword: (email: string) =>
    request<{ message: string }>('/auth/password/forgot', { method: 'POST', body: JSON.stringify({ email }) }),

  currentUser: () => request<UserProfile>('/users/me'),
  assignedPatients: () => request<Patient[]>('/clinical/patients'),
  adminUsers: () => request<UserProfile[]>('/admin/users'),
  predictionModels: () => request<unknown[]>('/predictions/models'),
  predictPatient: (patientId: string) => request<PredictionResponse>(`/predictions/patients/${patientId}`, { method: 'POST' }),
  predictionHistory: (patientId: string) => request<unknown[]>(`/predictions/patients/${patientId}/history`),
  manualPrediction: (payload: Record<string, unknown>) => request<PredictionResponse>('/predictions/manual', { method: 'POST', body: JSON.stringify(payload) }),
  clinicalRecords: (patientId: string) => request<ClinicalRecord[]>(`/clinical/patients/${patientId}/records`),
  inbox: () => request<MessageItem[]>('/messages/inbox'),
  pendingChangeRequests: () => request<unknown[]>('/change-requests/pending'),
};
