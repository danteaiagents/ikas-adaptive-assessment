import apiClient from './client';
import { Topic } from '../types';

interface BackendTopic {
  id: string;
  name: string;
  description: string | null;
  subject_id: string;
  subject_name: string;
  concept_count: number;
  question_count: number;
}

function mapTopic(t: BackendTopic): Topic {
  return {
    id: t.id,
    name: t.name,
    description: t.description ?? undefined,
    subjectId: t.subject_id,
    subjectName: t.subject_name,
    conceptCount: t.concept_count,
    questionCount: t.question_count,
  };
}

export const getTopics = async (subjectId?: string): Promise<Topic[]> => {
  const params = subjectId ? { subject_id: subjectId } : {};
  const { data: resp } = await apiClient.get<{ success: boolean; data: BackendTopic[] }>(
    '/topics',
    { params }
  );
  // Only return topics that have questions loaded
  return resp.data.filter(t => t.question_count > 0).map(mapTopic);
};
