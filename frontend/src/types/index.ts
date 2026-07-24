export type KnowledgeLevel = 'Repeat' | 'Summary' | 'Intuitive' | 'Apply';

export interface User {
  id: string;
  email: string;
  name: string;
  role: 'student' | 'instructor' | 'author';
}

export interface AuthResponse {
  accessToken: string;
  user: User;
}

export interface QuestionOption {
  id: string;
  text: string;
}

export interface Question {
  id: string;
  level: KnowledgeLevel;
  text: string;
  options?: QuestionOption[];
  prerequisites?: string[];
}

export interface Preset {
  id: string;
  name: string;
  description: string;
  questionCount: number;
  durationMinutes: number;
}

export interface TestSession {
  id: string;
  userId: string;
  topicId: string;
  startTime: string;
  status: 'active' | 'completed';
}

export interface TestResult {
  sessionId: string;
  score: number;
  levelBreakdown: Record<KnowledgeLevel, number>;
  masteryGrid: Record<string, number>;
  recommendations: ResourceRecommendation[];
}

export interface ResourceRecommendation {
  id: string;
  title: string;
  url: string;
  level: KnowledgeLevel;
  type: 'video' | 'article' | 'documentation' | 'exercise';
}
