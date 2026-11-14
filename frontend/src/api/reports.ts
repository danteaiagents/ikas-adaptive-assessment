import apiClient from './client';
import { ProgressData, SessionReport } from '../types';

/**
 * Fetch a user's session history and summary for a topic.
 * GET /api/v1/progress?topic_id=<topicId>
 */
export const getProgress = async (topicId: string): Promise<ProgressData> => {
  const { data: resp } = await apiClient.get<{ success: boolean; data: ProgressData }>(
    `/progress?topic_id=${encodeURIComponent(topicId)}`
  );
  return resp.data;
};

/**
 * Fetch the enriched post-session report (concept mastery, recommendations, time stats).
 * GET /api/v1/sessions/<sessionId>/report
 */
export const getSessionReport = async (sessionId: string): Promise<SessionReport> => {
  const { data: resp } = await apiClient.get<{ success: boolean; data: SessionReport }>(
    `/sessions/${sessionId}/report`
  );
  return resp.data;
};

