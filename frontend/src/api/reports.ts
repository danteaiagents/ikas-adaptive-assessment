import apiClient from './client';
import { TestResult } from '../types';

export const getProgress = async () => {
  return new Promise((resolve) => setTimeout(() => resolve([
    { date: '2026-07-01', score: 65 },
    { date: '2026-07-05', score: 72 },
    { date: '2026-07-10', score: 78 },
    { date: '2026-07-15', score: 85 },
    { date: '2026-07-22', score: 89 },
  ]), 500));
};
