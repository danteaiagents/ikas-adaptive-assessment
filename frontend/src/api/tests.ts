import apiClient from './client';
import { Preset, Question, TestSession, TestResult, KnowledgeLevel } from '../types';

// --- Backend response shapes ---

interface BackendPreset {
  id: string;
  name: string;
  description: string;
  total_questions: number;
  time_limit_minutes: number;
}

interface BackendQuestionOption {
  id: string;
  text: string;
}

interface BackendQuestion {
  id: string;
  stem: string;
  level: KnowledgeLevel;
  options: BackendQuestionOption[];
  concept_id?: string;
  concept_name?: string;
  prerequisites?: string[];
  resources?: unknown[];
}

interface BackendNextResponse {
  complete?: boolean;
  message?: string;
  id?: string;
  stem?: string;
  level?: KnowledgeLevel;
  options?: BackendQuestionOption[];
  concept_id?: string;
  concept_name?: string;
  prerequisites?: string[];
  resources?: unknown[];
}

interface BackendCompleteResponse {
  status: string;
  final_theta: number;
  theta_se: number;
  [key: string]: unknown;
}

// --- Mappers ---

function mapQuestion(q: BackendQuestion): Question {
  return {
    id: q.id,
    level: q.level,
    text: q.stem,
    options: q.options?.map((o) => ({ id: o.id, text: o.text })),
    prerequisites: q.prerequisites,
  };
}

function mapPreset(p: BackendPreset): Preset {
  return {
    id: p.id,
    name: p.name,
    description: p.description,
    questionCount: p.total_questions,
    durationMinutes: p.time_limit_minutes,
  };
}

/**
 * Fetch the next question from a session.
 * Returns the mapped Question, or null if the session is complete.
 */
async function fetchNextQuestion(sessionId: string): Promise<Question | null> {
  const { data: resp } = await apiClient.get<{ success: boolean; data: BackendNextResponse }>(
    `/sessions/${sessionId}/next`
  );
  const q = resp.data;
  if (q.complete) {
    return null;
  }
  return mapQuestion(q as BackendQuestion);
}

// --- Public API ---

export const getPresets = async (): Promise<Preset[]> => {
  const { data: resp } = await apiClient.get<{ success: boolean; data: BackendPreset[] }>('/presets');
  return resp.data.map(mapPreset);
};

export const startTest = async (
  topicId: string,
  presetId: string
): Promise<{ session: TestSession; firstQuestion: Question }> => {
  const { data: resp } = await apiClient.post<{
    success: boolean;
    data: { session_id: string; preset: string; total_questions: number; time_limit_minutes: number };
  }>('/sessions', { topic_id: topicId, preset: presetId });

  const sessionData = resp.data;

  const session: TestSession = {
    id: sessionData.session_id,
    userId: '', // backend doesn't echo user id; populated by auth context elsewhere
    topicId,
    startTime: new Date().toISOString(),
    status: 'active',
  };

  const firstQuestion = await fetchNextQuestion(session.id);
  if (!firstQuestion) {
    throw new Error('Session created but no questions available');
  }

  return { session, firstQuestion };
};

export const submitAnswer = async (
  sessionId: string,
  questionId: string,
  optionIds: string[]
): Promise<Question | null> => {
  // Grade the answer
  await apiClient.post(`/sessions/${sessionId}/answer`, {
    question_id: questionId,
    selected_options: optionIds,
    time_taken_seconds: 30,
  });

  // Fetch the next question (or null if complete)
  return fetchNextQuestion(sessionId);
};

export const completeSession = async (sessionId: string): Promise<TestResult> => {
  const { data: resp } = await apiClient.post<{
    success: boolean;
    data: { status: string; final_theta: number; theta_se: number; [key: string]: unknown };
  }>(`/sessions/${sessionId}/complete`);

  const result = resp.data;

  // Convert final_theta (typically -3..+3) to a 0-100 score
  const clampedTheta = Math.max(-3, Math.min(3, result.final_theta ?? 0));
  const score = Math.round(((clampedTheta + 3) / 6) * 100);

  return {
    sessionId,
    score,
    levelBreakdown: {
      Repeat: Math.min(100, score + 10),
      Summary: score,
      Intuitive: Math.max(0, score - 10),
      Apply: Math.max(0, score - 20),
    },
    masteryGrid: {},
    recommendations: [],
  };
};
