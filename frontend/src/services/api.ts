import axios from 'axios';

export const AUTH_TOKEN_STORAGE_KEY = 'auth_token';
export const AUTH_SESSION_EXPIRED_EVENT = 'aicrm:auth-session-expired';

const api = axios.create({
  baseURL: process.env.REACT_APP_API_URL || '/api',
  headers: {
    'Content-Type': 'application/json',
  },
});

const isAuthenticationAttempt = (url?: string) => {
  const value = String(url || '');
  return (
    value.includes('/auth/login') ||
    value.includes('/auth/register') ||
    value.includes('/auth/verify-email') ||
    value.includes('/auth/resend-verification')
  );
};

export const shouldExpireSession = (
  status?: number,
  url?: string,
  token?: string | null,
) => status === 401 && Boolean(token) && !isAuthenticationAttempt(url);

api.interceptors.request.use((config) => {
  const token = localStorage.getItem(AUTH_TOKEN_STORAGE_KEY);
  if (token) {
    config.headers.Authorization = 'Bearer ' + token;
  }
  return config;
});

api.interceptors.response.use(
  (response) => response,
  (error) => {
    const token = localStorage.getItem(AUTH_TOKEN_STORAGE_KEY);
    if (
      shouldExpireSession(
        error.response?.status,
        error.config?.url,
        token,
      )
    ) {
      localStorage.removeItem(AUTH_TOKEN_STORAGE_KEY);
      window.dispatchEvent(new CustomEvent(AUTH_SESSION_EXPIRED_EVENT));
    }
    return Promise.reject(error);
  },
);

export default api;
