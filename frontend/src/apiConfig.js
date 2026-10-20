// API Configuration for local development and cloud production deployment
const RAW_URL = import.meta.env.VITE_API_URL || "";
export const API_BASE = RAW_URL.replace(/\/+$/, "");

export const API_ENDPOINTS = {
  EVALUATION_SUBMIT: `${API_BASE}/api/evaluation/submit`,
  EVALUATION_UPLOAD: `${API_BASE}/api/evaluation/upload-reference`,
  DASHBOARD: `${API_BASE}/api/dashboard`,
  REPORT: `${API_BASE}/api/report`,
};

export default API_ENDPOINTS;
