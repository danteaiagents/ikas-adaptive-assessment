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

export interface Topic {
  id: string;
  name: string;
  description?: string;
  subjectId?: string;
  subjectName?: string;
  conceptCount: number;
  questionCount: number;
}

export interface QuestionOption {
  id: string;
  text: string;
}

export interface Prerequisite {
  id: string;
  stem: string;          // the actual prerequisite question text
  concept_id: string;
  concept_name: string;  // concept it belongs to (for grouping)
  level: KnowledgeLevel;
}

export interface Question {
  id: string;
  level: KnowledgeLevel;
  text: string;
  options?: QuestionOption[];
  prerequisites?: Prerequisite[];
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

// ── Sprint 1: Report & Progress types ─────────────────────────────────────────

export interface ConceptLevelStats {
  total: number;
  correct: number;
  accuracy: number;
}

export interface ConceptMastery {
  name: string;
  levels: Partial<Record<KnowledgeLevel, ConceptLevelStats>>;
}

export interface ReportRecommendation {
  id: string;
  title: string;
  url: string;
  type: 'video' | 'article' | 'documentation' | 'exercise';
  target_level: KnowledgeLevel;
  concept_id: string;
  concept_name: string;
}

export interface TimeStats {
  avg_time_seconds: number;
  total_time_seconds: number;
  slowest_level: KnowledgeLevel | null;
}

export interface SessionReport {
  session_id: string;
  total_questions: number;
  correct_count: number;
  score: number;        // blended: 60% raw + 40% IRT
  raw_score: number;    // pure accuracy %
  theta_score: number;  // IRT theta normalised 0-100
  theta: number;
  theta_se: number;
  level_breakdown: Partial<Record<KnowledgeLevel, { total: number; correct: number; accuracy: number }>>;
  concept_mastery: Record<string, ConceptMastery>;
  time_stats: TimeStats;
  recommendations: ReportRecommendation[];
}

export interface ProgressSession {
  session_id: string;
  date: string;
  preset: string;
  total_questions: number;
  correct_count: number;
  score: number;        // blended
  raw_score?: number;   // pure accuracy %
  theta: number;
  time_limit_minutes: number;
}

export interface ProgressSummary {
  total_sessions: number;
  avg_score: number;
  best_score: number;
  latest_theta: number | null;
}

export interface ProgressData {
  user_id: string;
  topic_id: string;
  history: ProgressSession[];
  summary: ProgressSummary;
}

