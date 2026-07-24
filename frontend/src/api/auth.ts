import apiClient from './client';
import { AuthResponse } from '../types';

export const login = async (email: string, password: string): Promise<AuthResponse> => {
  return new Promise((resolve) => setTimeout(() => resolve({
    accessToken: 'mock-token',
    user: { id: 'u1', email, name: 'Test User', role: 'student' }
  }), 1000));
};

export const register = async (email: string, password: string, name: string): Promise<AuthResponse> => {
  return new Promise((resolve) => setTimeout(() => resolve({
    accessToken: 'mock-token',
    user: { id: 'u2', email, name, role: 'student' }
  }), 1000));
};

export const logout = async (): Promise<void> => {
  return new Promise((resolve) => setTimeout(resolve, 500));
};
