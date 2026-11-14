import axios from 'axios';
import { useAuthStore } from '../store/authStore';
import { useToastStore } from '../store/toastStore';

const apiClient = axios.create({
  baseURL: '/api/v1',
  withCredentials: true,
  headers: {
    'Content-Type': 'application/json'
  }
});

apiClient.interceptors.request.use((config) => {
  const token = useAuthStore.getState().token;
  if (token && config.headers) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

apiClient.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;

    // ── 401 token refresh ────────────────────────────────────────────────
    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;
      try {
        const { data } = await axios.post('/api/v1/auth/refresh', {}, { withCredentials: true });
        useAuthStore.getState().setAuth(data.user, data.accessToken);
        originalRequest.headers.Authorization = `Bearer ${data.accessToken}`;
        return apiClient(originalRequest);
      } catch (refreshError) {
        useAuthStore.getState().logout();
        window.location.href = '/login';
        return Promise.reject(refreshError);
      }
    }

    // ── Toast on 4xx / 5xx (except silent 401 handled above) ────────────
    if (error.response) {
      const status: number = error.response.status;
      const serverMessage: string =
        error.response.data?.error ||
        error.response.data?.message ||
        error.message ||
        'An unexpected error occurred.';

      if (status >= 500) {
        useToastStore.getState().addToast(`Server error (${status}): ${serverMessage}`, 'error');
      } else if (status >= 400 && status !== 401) {
        useToastStore.getState().addToast(serverMessage, 'warning');
      }
    } else if (error.request) {
      // Network error — no response received
      useToastStore.getState().addToast('Network error: unable to reach the server.', 'error');
    }

    return Promise.reject(error);
  }
);

export default apiClient;

