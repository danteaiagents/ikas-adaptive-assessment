import apiClient from './client';
import { Preset, Question, TestSession, TestResult } from '../types';

export const getPresets = async (): Promise<Preset[]> => {
  return [
    { id: 'p1', name: 'Quick Check', description: 'Fast knowledge pulse check on a single level', questionCount: 10, durationMinutes: 15 },
    { id: 'p2', name: 'Standard Assessment', description: 'Balanced assessment across all 4 levels', questionCount: 25, durationMinutes: 45 },
    { id: 'p3', name: 'Comprehensive Exam', description: 'Deep evaluation with thorough level coverage', questionCount: 50, durationMinutes: 90 },
  ];
};

export const startTest = async (topicId: string, presetId: string): Promise<{ session: TestSession, firstQuestion: Question }> => {
  return new Promise((resolve) => setTimeout(() => resolve({
    session: { id: 's1', userId: 'u1', topicId, startTime: new Date().toISOString(), status: 'active' },
    firstQuestion: {
      id: 'q1',
      level: 'Repeat',
      text: 'Which of the following describes a Large Language Model (LLM)?',
      options: [
        { id: 'o1', text: 'A traditional relational database' },
        { id: 'o2', text: 'A neural network trained on vast amounts of text data to predict the next token' },
        { id: 'o3', text: 'A strictly rule-based expert system' },
        { id: 'o4', text: 'A hardware component for rendering graphics' }
      ]
    }
  }), 1000));
};

export const submitAnswer = async (sessionId: string, questionId: string, optionIds: string[]): Promise<Question | null> => {
  return new Promise((resolve) => setTimeout(() => resolve({
    id: 'q2',
    level: 'Summary',
    text: 'Select the concepts that are inherently linked to Prompt Engineering.',
    options: [
      { id: 'o1', text: 'Few-shot prompting' },
      { id: 'o2', text: 'Garbage Collection' },
      { id: 'o3', text: 'System messages' },
      { id: 'o4', text: 'Context windows' }
    ],
    prerequisites: ['What is an LLM']
  }), 800));
};

export const submitFinalAnswer = async (sessionId: string, questionId: string, optionIds: string[]): Promise<TestResult> => {
  return new Promise((resolve) => setTimeout(() => resolve({
    sessionId,
    score: 85,
    levelBreakdown: {
      Repeat: 95,
      Summary: 85,
      Intuitive: 80,
      Apply: 75
    },
    masteryGrid: {
      'Prompt Engineering': 0.9,
      'Tokenization': 0.8,
      'Context Windows': 0.6
    },
    recommendations: [
      { id: 'r1', title: 'Advanced Context Window Strategies', url: '#', level: 'Intuitive', type: 'article' }
    ]
  }), 1000));
};
