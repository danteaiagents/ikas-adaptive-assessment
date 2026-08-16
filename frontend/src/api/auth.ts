import apiClient from './client';
import { AuthResponse } from '../types';

interface BackendAuthResponse {
  success: boolean;
  data: {
    access_token: string;
    user_id: string;
  };
}

export const login = async (email: string, password: string): Promise<AuthResponse> => {
  const response = await apiClient.post<BackendAuthResponse>('/login', {
    email,
    password,
  });

  const { access_token, user_id } = response.data.data;

  return {
    accessToken: access_token,
    user: {
      id: user_id,
      email,
      name: email.split('@')[0],
      role: 'student',
    },
  };
};

export const register = async (email: string, password: string, name: string): Promise<AuthResponse> => {
  const response = await apiClient.post<BackendAuthResponse>('/register', {
    email,
    password,
    username: name,
  });

  const { access_token, user_id } = response.data.data;

  return {
    accessToken: access_token,
    user: {
      id: user_id,
      email,
      name,
      role: 'student',
    },
  };
};

export const logout = async (): Promise<void> => {
  try {
    await apiClient.post('/logout');
  } catch {
    // Ignore logout errors to ensure clean client teardown
  }
};

