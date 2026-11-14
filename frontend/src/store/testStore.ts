import { create } from 'zustand';
import { Question, TestSession } from '../types';

interface TestState {
  session: TestSession | null;
  currentQuestion: Question | null;
  questionNumber: number;
  questionStartTime: number;
  responses: Record<string, string[]>;
  timeRemaining: number;
  startTest: (session: TestSession, firstQuestion: Question, duration: number) => void;
  setResponse: (questionId: string, optionIds: string[]) => void;
  nextQuestion: (question: Question) => void;
  updateTime: (timeLeft: number) => void;
  endTest: () => void;
}

export const useTestStore = create<TestState>((set) => ({
  session: null,
  currentQuestion: null,
  questionNumber: 1,
  questionStartTime: 0,
  responses: {},
  timeRemaining: 0,
  startTest: (session, firstQuestion, duration) => set({
    session,
    currentQuestion: firstQuestion,
    questionNumber: 1,
    questionStartTime: Date.now(),
    timeRemaining: duration * 60,
    responses: {}
  }),
  setResponse: (questionId, optionIds) => set((state) => ({
    responses: { ...state.responses, [questionId]: optionIds }
  })),
  nextQuestion: (question) => set((state) => ({
    currentQuestion: question,
    questionNumber: state.questionNumber + 1,
    questionStartTime: Date.now(),
  })),
  updateTime: (timeLeft) => set({ timeRemaining: timeLeft }),
  endTest: () => set({ session: null, currentQuestion: null, questionNumber: 1, questionStartTime: 0 })
}));
