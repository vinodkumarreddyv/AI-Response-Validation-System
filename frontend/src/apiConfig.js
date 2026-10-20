// API Configuration for local development and cloud production deployment
const RAW_URL = import.meta.env.VITE_API_URL || "";
export const API_BASE = RAW_URL.replace(/\/+$/, "");

export const API_ENDPOINTS = {
  EVALUATION_SUBMIT: `${API_BASE}/api/evaluation/submit`,
  EVALUATION_UPLOAD: `${API_BASE}/api/evaluation/upload-reference`,
  DASHBOARD: `${API_BASE}/api/dashboard`,
  REPORT: `${API_BASE}/api/report`,
  AUTH_GOOGLE: `${API_BASE}/api/auth/google`,
  AUTH_EMAIL_OTP: `${API_BASE}/api/auth/email/send-otp`,
  AUTH_EMAIL_VERIFY: `${API_BASE}/api/auth/email/verify`,
  AUTH_PHONE_OTP: `${API_BASE}/api/auth/phone/send-otp`,
  AUTH_PHONE_VERIFY: `${API_BASE}/api/auth/phone/verify`,
  AUTH_DUAL_OTP: `${API_BASE}/api/auth/dual/send-otp`,
  AUTH_DUAL_VERIFY: `${API_BASE}/api/auth/dual/verify`,
  AUTH_GUEST: `${API_BASE}/api/auth/guest`,
  AUTH_ME: `${API_BASE}/api/auth/me`,
  AUTH_CREDITS_USE: `${API_BASE}/api/auth/credits/use`,
  AUTH_CREDITS_REFILL: `${API_BASE}/api/auth/credits/refill`,
};

export default API_ENDPOINTS;
