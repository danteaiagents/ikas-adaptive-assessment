import os

def write_file(path, content):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content.strip() + '\n')

files = {}

files['src/styles/index.css'] = """
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

:root {
  /* Dark theme */
  --bg-primary: #0f1117;
  --bg-secondary: #1a1d2e;
  --bg-card: rgba(26, 29, 46, 0.8);
  --bg-glass: rgba(255, 255, 255, 0.05);
  --border-glass: rgba(255, 255, 255, 0.1);
  
  /* Text */
  --text-primary: #e8eaed;
  --text-secondary: #9aa0a6;
  --text-muted: #5f6368;
  
  /* Accents */
  --accent-blue: #4285f4;
  --accent-green: #34a853;
  --accent-amber: #fbbc04;
  --accent-red: #ea4335;
  --accent-purple: #a855f7;
  
  /* Knowledge levels */
  --level-repeat: #4285f4;
  --level-summary: #34a853;
  --level-intuitive: #fbbc04;
  --level-apply: #ea4335;
}

* {
  box-sizing: border-box;
  margin: 0;
  padding: 0;
}

body {
  font-family: 'Inter', sans-serif;
  background-color: var(--bg-primary);
  color: var(--text-primary);
  min-height: 100vh;
  line-height: 1.5;
}

.glass-panel {
  background: var(--bg-glass);
  backdrop-filter: blur(10px);
  -webkit-backdrop-filter: blur(10px);
  border: 1px solid var(--border-glass);
  border-radius: 12px;
}

.card {
  background: var(--bg-card);
  border-radius: 12px;
  padding: 1.5rem;
  border: 1px solid var(--border-glass);
  transition: transform 0.2s ease, box-shadow 0.2s ease;
}

.card:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.2);
}

.btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  padding: 0.75rem 1.5rem;
  border-radius: 8px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
  border: none;
  font-family: inherit;
  font-size: 0.95rem;
}

.btn-primary {
  background: var(--accent-blue);
  color: white;
}

.btn-primary:hover {
  background: #3367d6;
}

.btn-outline {
  background: transparent;
  border: 1px solid var(--border-glass);
  color: var(--text-primary);
}

.btn-outline:hover {
  background: var(--bg-glass);
}

input[type="text"],
input[type="password"],
input[type="email"] {
  width: 100%;
  padding: 0.75rem 1rem;
  background: var(--bg-secondary);
  border: 1px solid var(--border-glass);
  border-radius: 8px;
  color: var(--text-primary);
  font-family: inherit;
  transition: border-color 0.2s;
}

input:focus {
  outline: none;
  border-color: var(--accent-blue);
}

/* Custom Checkbox */
.checkbox-container {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  padding: 12px 16px;
  background: var(--bg-glass);
  border: 1px solid var(--border-glass);
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s;
}

.checkbox-container:hover {
  background: rgba(255, 255, 255, 0.08);
}

.checkbox-container.selected {
  border-color: var(--accent-blue);
  background: rgba(66, 133, 244, 0.1);
}

.checkbox-container input[type="checkbox"] {
  appearance: none;
  -webkit-appearance: none;
  width: 20px;
  height: 20px;
  border: 2px solid var(--text-muted);
  border-radius: 4px;
  margin-top: 2px;
  display: grid;
  place-content: center;
  cursor: pointer;
  transition: all 0.2s;
}

.checkbox-container input[type="checkbox"]::before {
  content: "";
  width: 10px;
  height: 10px;
  transform: scale(0);
  transition: 120ms transform ease-in-out;
  box-shadow: inset 1em 1em white;
  transform-origin: center;
  clip-path: polygon(14% 44%, 0 65%, 50% 100%, 100% 16%, 80% 0%, 43% 62%);
}

.checkbox-container input[type="checkbox"]:checked {
  background-color: var(--accent-blue);
  border-color: var(--accent-blue);
}

.checkbox-container input[type="checkbox"]:checked::before {
  transform: scale(1);
}

/* Layout Utilities */
.app-container {
  display: flex;
  min-height: 100vh;
}

.main-content {
  flex: 1;
  padding: 2rem;
  max-width: 1200px;
  margin: 0 auto;
}

/* Badges */
.badge {
  padding: 4px 8px;
  border-radius: 12px;
  font-size: 0.75rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}
"""

files['src/types/index.ts'] = """
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
"""

files['src/store/authStore.ts'] = """
import { create } from 'zustand';
import { User } from '../types';

interface AuthState {
  user: User | null;
  token: string | null;
  isAuthenticated: boolean;
  setAuth: (user: User, token: string) => void;
  logout: () => void;
}

export const useAuthStore = create<AuthState>((set) => ({
  user: null,
  token: null,
  isAuthenticated: false,
  setAuth: (user, token) => set({ user, token, isAuthenticated: true }),
  logout: () => set({ user: null, token: null, isAuthenticated: false }),
}));
"""

files['src/store/testStore.ts'] = """
import { create } from 'zustand';
import { Question, TestSession } from '../types';

interface TestState {
  session: TestSession | null;
  currentQuestion: Question | null;
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
  responses: {},
  timeRemaining: 0,
  startTest: (session, firstQuestion, duration) => set({
    session,
    currentQuestion: firstQuestion,
    timeRemaining: duration * 60,
    responses: {}
  }),
  setResponse: (questionId, optionIds) => set((state) => ({
    responses: { ...state.responses, [questionId]: optionIds }
  })),
  nextQuestion: (question) => set({ currentQuestion: question }),
  updateTime: (timeLeft) => set({ timeRemaining: timeLeft }),
  endTest: () => set({ session: null, currentQuestion: null })
}));
"""

files['src/api/client.ts'] = """
import axios from 'axios';
import { useAuthStore } from '../store/authStore';

const apiClient = axios.create({
  baseURL: '/api/v1',
  withCredentials: true, // For HttpOnly refresh cookie
  headers: {
    'Content-Type': 'application/json'
  }
});

// Request interceptor to attach token
apiClient.interceptors.request.use((config) => {
  const token = useAuthStore.getState().token;
  if (token && config.headers) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Response interceptor for silent refresh
apiClient.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;
    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;
      try {
        const { data } = await axios.post('/api/v1/auth/refresh', {}, { withCredentials: true });
        useAuthStore.getState().setAuth(data.user, data.accessToken);
        originalRequest.headers.Authorization = `Bearer ${data.accessToken}`;
        return apiClient(originalRequest);
      } catch (refreshError) {
        useAuthStore.getState().logout();
        window.location.href = '/login';
        return Promise.reject(refreshError);
      }
    }
    return Promise.reject(error);
  }
);

export default apiClient;
"""

files['src/api/auth.ts'] = """
import apiClient from './client';
import { AuthResponse } from '../types';

export const login = async (email: string, password: string): Promise<AuthResponse> => {
  // Mock implementation for UI phase
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
"""

files['src/api/tests.ts'] = """
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
  // Returns next question or null if test ends
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
"""

files['src/api/reports.ts'] = """
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
"""

files['src/components/layout/Header.tsx'] = """
import React from 'react';
import { useAuthStore } from '../../store/authStore';
import { LogOut, User as UserIcon } from 'lucide-react';
import { useNavigate } from 'react-router-dom';

const Header: React.FC = () => {
  const { user, logout } = useAuthStore();
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  return (
    <header className="glass-panel" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '1rem 2rem', borderBottom: '1px solid var(--border-glass)', borderRadius: '0', marginBottom: '0' }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
        <h1 style={{ margin: 0, fontSize: '1.5rem', fontWeight: 700, color: 'var(--accent-blue)', letterSpacing: '-0.5px' }}>IKAS</h1>
        <span style={{ color: 'var(--text-muted)', fontSize: '0.9rem', borderLeft: '1px solid var(--border-glass)', paddingLeft: '1rem' }}>Intelligent Knowledge Assessment System</span>
      </div>
      
      {user && (
        <div style={{ display: 'flex', alignItems: 'center', gap: '1.5rem' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', color: 'var(--text-secondary)' }}>
            <UserIcon size={18} />
            <span style={{ fontSize: '0.95rem' }}>{user.name}</span>
          </div>
          <button onClick={handleLogout} className="btn btn-outline" style={{ padding: '0.5rem 1rem' }}>
            <LogOut size={16} style={{ marginRight: '0.5rem' }} /> Logout
          </button>
        </div>
      )}
    </header>
  );
};

export default Header;
"""

files['src/components/layout/Sidebar.tsx'] = """
import React from 'react';
import { NavLink } from 'react-router-dom';
import { LayoutDashboard, BarChart2, BookOpen } from 'lucide-react';

const Sidebar: React.FC = () => {
  const navStyle = ({ isActive }: { isActive: boolean }) => ({
    display: 'flex',
    alignItems: 'center',
    gap: '0.75rem',
    padding: '1rem 1.5rem',
    color: isActive ? 'var(--text-primary)' : 'var(--text-secondary)',
    background: isActive ? 'var(--bg-glass)' : 'transparent',
    textDecoration: 'none',
    borderLeft: isActive ? '3px solid var(--accent-blue)' : '3px solid transparent',
    transition: 'all 0.2s',
    fontWeight: isActive ? 500 : 400
  });

  return (
    <aside style={{ width: '250px', background: 'var(--bg-card)', borderRight: '1px solid var(--border-glass)', paddingTop: '2rem' }}>
      <nav style={{ display: 'flex', flexDirection: 'column' }}>
        <NavLink to="/dashboard" style={navStyle}>
          <LayoutDashboard size={20} /> Dashboard
        </NavLink>
        <NavLink to="/progress" style={navStyle}>
          <BarChart2 size={20} /> Progress
        </NavLink>
        <div style={{ margin: '2rem 1.5rem 1rem', fontSize: '0.75rem', textTransform: 'uppercase', color: 'var(--text-muted)', fontWeight: 600, letterSpacing: '0.5px' }}>
          Subjects
        </div>
        <div style={{ padding: '0.5rem 1.5rem', color: 'var(--text-secondary)', fontSize: '0.9rem', display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
          <BookOpen size={16} /> Artificial Intelligence
        </div>
      </nav>
    </aside>
  );
};

export default Sidebar;
"""

files['src/components/layout/Layout.tsx'] = """
import React from 'react';
import { Outlet, Navigate } from 'react-router-dom';
import Header from './Header';
import Sidebar from './Sidebar';
import { useAuthStore } from '../../store/authStore';

const Layout: React.FC = () => {
  const { isAuthenticated } = useAuthStore();

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', minHeight: '100vh' }}>
      <Header />
      <div style={{ display: 'flex', flex: 1, overflow: 'hidden' }}>
        <Sidebar />
        <main className="main-content" style={{ overflowY: 'auto' }}>
          <Outlet />
        </main>
      </div>
    </div>
  );
};

export default Layout;
"""

files['src/pages/LoginPage.tsx'] = """
import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useAuthStore } from '../store/authStore';
import { login } from '../api/auth';
import { ArrowRight } from 'lucide-react';

const LoginPage: React.FC = () => {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const { setAuth } = useAuthStore();
  const navigate = useNavigate();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    try {
      const { user, accessToken } = await login(email, password);
      setAuth(user, accessToken);
      navigate('/dashboard');
    } catch (error) {
      console.error(error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ minHeight: '100vh', display: 'grid', placeItems: 'center', background: 'radial-gradient(circle at top right, var(--bg-secondary), var(--bg-primary))' }}>
      <div className="glass-panel" style={{ width: '100%', maxWidth: '420px', padding: '3rem 2rem' }}>
        <div style={{ textAlign: 'center', marginBottom: '2rem' }}>
          <h1 style={{ fontSize: '2rem', color: 'var(--accent-blue)', marginBottom: '0.5rem', letterSpacing: '-1px' }}>IKAS</h1>
          <p style={{ color: 'var(--text-secondary)' }}>Intelligent Knowledge Assessment System</p>
        </div>
        
        <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
          <div>
            <label style={{ display: 'block', marginBottom: '0.5rem', fontSize: '0.9rem', color: 'var(--text-secondary)' }}>Email Address</label>
            <input type="email" value={email} onChange={e => setEmail(e.target.value)} required placeholder="student@university.edu" />
          </div>
          <div>
            <label style={{ display: 'block', marginBottom: '0.5rem', fontSize: '0.9rem', color: 'var(--text-secondary)' }}>Password</label>
            <input type="password" value={password} onChange={e => setPassword(e.target.value)} required placeholder="••••••••" />
          </div>
          
          <button type="submit" className="btn btn-primary" style={{ marginTop: '1rem' }} disabled={loading}>
            {loading ? 'Authenticating...' : 'Sign In'} <ArrowRight size={18} style={{ marginLeft: '0.5rem' }} />
          </button>
        </form>
        
        <div style={{ marginTop: '2rem', textAlign: 'center', fontSize: '0.9rem', color: 'var(--text-secondary)' }}>
          Don't have an account? <Link to="/register" style={{ color: 'var(--accent-blue)', textDecoration: 'none' }}>Register here</Link>
        </div>
      </div>
    </div>
  );
};

export default LoginPage;
"""

files['src/pages/RegisterPage.tsx'] = """
import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useAuthStore } from '../store/authStore';
import { register } from '../api/auth';
import { ArrowRight } from 'lucide-react';

const RegisterPage: React.FC = () => {
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const { setAuth } = useAuthStore();
  const navigate = useNavigate();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    try {
      const { user, accessToken } = await register(email, password, name);
      setAuth(user, accessToken);
      navigate('/dashboard');
    } catch (error) {
      console.error(error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ minHeight: '100vh', display: 'grid', placeItems: 'center', background: 'radial-gradient(circle at top right, var(--bg-secondary), var(--bg-primary))' }}>
      <div className="glass-panel" style={{ width: '100%', maxWidth: '420px', padding: '3rem 2rem' }}>
        <div style={{ textAlign: 'center', marginBottom: '2rem' }}>
          <h1 style={{ fontSize: '2rem', color: 'var(--accent-blue)', marginBottom: '0.5rem', letterSpacing: '-1px' }}>Join IKAS</h1>
          <p style={{ color: 'var(--text-secondary)' }}>Start your adaptive learning journey</p>
        </div>
        
        <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
          <div>
            <label style={{ display: 'block', marginBottom: '0.5rem', fontSize: '0.9rem', color: 'var(--text-secondary)' }}>Full Name</label>
            <input type="text" value={name} onChange={e => setName(e.target.value)} required placeholder="Jane Doe" />
          </div>
          <div>
            <label style={{ display: 'block', marginBottom: '0.5rem', fontSize: '0.9rem', color: 'var(--text-secondary)' }}>Email Address</label>
            <input type="email" value={email} onChange={e => setEmail(e.target.value)} required placeholder="student@university.edu" />
          </div>
          <div>
            <label style={{ display: 'block', marginBottom: '0.5rem', fontSize: '0.9rem', color: 'var(--text-secondary)' }}>Password</label>
            <input type="password" value={password} onChange={e => setPassword(e.target.value)} required placeholder="••••••••" />
          </div>
          
          <button type="submit" className="btn btn-primary" style={{ marginTop: '1rem' }} disabled={loading}>
            {loading ? 'Creating Account...' : 'Register'} <ArrowRight size={18} style={{ marginLeft: '0.5rem' }} />
          </button>
        </form>
        
        <div style={{ marginTop: '2rem', textAlign: 'center', fontSize: '0.9rem', color: 'var(--text-secondary)' }}>
          Already have an account? <Link to="/login" style={{ color: 'var(--accent-blue)', textDecoration: 'none' }}>Sign in</Link>
        </div>
      </div>
    </div>
  );
};

export default RegisterPage;
"""

files['src/components/dashboard/TestConfig.tsx'] = """
import React, { useEffect, useState } from 'react';
import { getPresets, startTest } from '../../api/tests';
import { Preset } from '../../types';
import { useNavigate } from 'react-router-dom';
import { useTestStore } from '../../store/testStore';
import { Clock, ListChecks, Play } from 'lucide-react';

const TestConfig: React.FC = () => {
  const [presets, setPresets] = useState<Preset[]>([]);
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();
  const { startTest: setStoreStart } = useTestStore();

  useEffect(() => {
    getPresets().then(setPresets);
  }, []);

  const handleStart = async (preset: Preset) => {
    setLoading(true);
    try {
      const { session, firstQuestion } = await startTest('t-ai-llm', preset.id);
      setStoreStart(session, firstQuestion, preset.durationMinutes);
      navigate('/test');
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ marginTop: '2rem' }}>
      <h2 style={{ fontSize: '1.25rem', marginBottom: '1.5rem', fontWeight: 600 }}>Start an Assessment</h2>
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', gap: '1.5rem' }}>
        {presets.map(preset => (
          <div key={preset.id} className="card" style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
            <h3 style={{ fontSize: '1.1rem', color: 'var(--accent-blue)' }}>{preset.name}</h3>
            <p style={{ color: 'var(--text-secondary)', fontSize: '0.9rem', flex: 1 }}>{preset.description}</p>
            
            <div style={{ display: 'flex', gap: '1rem', color: 'var(--text-muted)', fontSize: '0.85rem' }}>
              <span style={{ display: 'flex', alignItems: 'center', gap: '0.25rem' }}>
                <ListChecks size={14} /> {preset.questionCount} Questions
              </span>
              <span style={{ display: 'flex', alignItems: 'center', gap: '0.25rem' }}>
                <Clock size={14} /> {preset.durationMinutes} Minutes
              </span>
            </div>
            
            <button 
              className="btn btn-outline" 
              style={{ width: '100%', marginTop: '0.5rem', justifyContent: 'center' }}
              onClick={() => handleStart(preset)}
              disabled={loading}
            >
              <Play size={16} style={{ marginRight: '0.5rem' }} /> Begin {preset.name}
            </button>
          </div>
        ))}
      </div>
    </div>
  );
};

export default TestConfig;
"""

files['src/pages/DashboardPage.tsx'] = """
import React from 'react';
import TestConfig from '../components/dashboard/TestConfig';
import { useAuthStore } from '../store/authStore';

const DashboardPage: React.FC = () => {
  const { user } = useAuthStore();

  return (
    <div>
      <div style={{ marginBottom: '2rem' }}>
        <h1 style={{ fontSize: '2rem', marginBottom: '0.5rem', fontWeight: 700 }}>Welcome back, {user?.name.split(' ')[0]}</h1>
        <p style={{ color: 'var(--text-secondary)' }}>Ready to continue your AI learning journey? Select an assessment below.</p>
      </div>

      <div className="card" style={{ background: 'linear-gradient(135deg, rgba(66, 133, 244, 0.1), rgba(26, 29, 46, 0.8))', border: '1px solid rgba(66, 133, 244, 0.3)' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <div>
            <h3 style={{ fontSize: '1.25rem', marginBottom: '0.5rem', color: 'var(--text-primary)' }}>Current Topic: LLMs & Prompting</h3>
            <p style={{ color: 'var(--text-secondary)', fontSize: '0.95rem' }}>Mastery level: 68% (Intermediate)</p>
          </div>
          <div style={{ padding: '0.75rem 1.5rem', background: 'var(--bg-primary)', borderRadius: '8px', border: '1px solid var(--border-glass)', fontSize: '0.85rem', color: 'var(--text-muted)' }}>
            Artificial Intelligence Track
          </div>
        </div>
      </div>

      <TestConfig />
    </div>
  );
};

export default DashboardPage;
"""

files['src/components/questions/MCQRenderer.tsx'] = """
import React from 'react';
import { QuestionOption } from '../../types';

interface MCQRendererProps {
  options: QuestionOption[];
  selectedOptions: string[];
  onChange: (selectedIds: string[]) => void;
}

const MCQRenderer: React.FC<MCQRendererProps> = ({ options, selectedOptions, onChange }) => {
  const toggleOption = (id: string) => {
    if (selectedOptions.includes(id)) {
      onChange(selectedOptions.filter(opt => opt !== id));
    } else {
      onChange([...selectedOptions, id]);
    }
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem', marginTop: '1.5rem' }}>
      {options.map(option => {
        const isSelected = selectedOptions.includes(option.id);
        return (
          <label 
            key={option.id} 
            className={`checkbox-container ${isSelected ? 'selected' : ''}`}
          >
            <input 
              type="checkbox" 
              checked={isSelected} 
              onChange={() => toggleOption(option.id)} 
            />
            <span style={{ fontSize: '1rem', lineHeight: 1.5, paddingTop: '2px', color: isSelected ? 'var(--text-primary)' : 'var(--text-secondary)' }}>
              {option.text}
            </span>
          </label>
        );
      })}
    </div>
  );
};

export default MCQRenderer;
"""

files['src/components/questions/Timer.tsx'] = """
import React, { useEffect } from 'react';
import { useTestStore } from '../../store/testStore';
import { Clock } from 'lucide-react';

const Timer: React.FC = () => {
  const { timeRemaining, updateTime } = useTestStore();

  useEffect(() => {
    if (timeRemaining <= 0) return;
    const interval = setInterval(() => {
      updateTime(timeRemaining - 1);
    }, 1000);
    return () => clearInterval(interval);
  }, [timeRemaining, updateTime]);

  const mins = Math.floor(timeRemaining / 60);
  const secs = timeRemaining % 60;
  
  const isWarning = timeRemaining < 300; // less than 5 minutes

  return (
    <div style={{ 
      display: 'flex', alignItems: 'center', gap: '0.5rem', 
      padding: '0.5rem 1rem', borderRadius: '20px',
      background: isWarning ? 'rgba(251, 188, 4, 0.1)' : 'var(--bg-glass)',
      border: `1px solid ${isWarning ? 'var(--accent-amber)' : 'var(--border-glass)'}`,
      color: isWarning ? 'var(--accent-amber)' : 'var(--text-primary)',
      fontWeight: 600, fontSize: '0.9rem'
    }}>
      <Clock size={16} />
      {mins.toString().padStart(2, '0')}:{secs.toString().padStart(2, '0')}
    </div>
  );
};

export default Timer;
"""

files['src/pages/TestPage.tsx'] = """
import React, { useState } from 'react';
import { useTestStore } from '../store/testStore';
import MCQRenderer from '../components/questions/MCQRenderer';
import Timer from '../components/questions/Timer';
import { submitAnswer, submitFinalAnswer } from '../api/tests';
import { useNavigate } from 'react-router-dom';
import { ChevronRight, ShieldAlert } from 'lucide-react';

const TestPage: React.FC = () => {
  const { session, currentQuestion, responses, setResponse } = useTestStore();
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();

  if (!session || !currentQuestion) {
    return <div style={{ padding: '2rem' }}>No active test session. <a href="/dashboard">Return to Dashboard</a></div>;
  }

  const selectedOptions = responses[currentQuestion.id] || [];

  const handleNext = async () => {
    setLoading(true);
    try {
      // For demo, if question is q2, we finish test, else next
      if (currentQuestion.id === 'q2') {
        const result = await submitFinalAnswer(session.id, currentQuestion.id, selectedOptions);
        navigate('/results', { state: { result } });
      } else {
        const nextQ = await submitAnswer(session.id, currentQuestion.id, selectedOptions);
        if (nextQ) {
          useTestStore.getState().nextQuestion(nextQ);
        }
      }
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const getLevelColor = (level: string) => {
    switch(level) {
      case 'Repeat': return 'var(--level-repeat)';
      case 'Summary': return 'var(--level-summary)';
      case 'Intuitive': return 'var(--level-intuitive)';
      case 'Apply': return 'var(--level-apply)';
      default: return 'var(--text-secondary)';
    }
  };

  return (
    <div style={{ display: 'flex', gap: '2rem', height: 'calc(100vh - 100px)' }}>
      {/* Left panel: Question (70%) */}
      <div style={{ flex: '7', display: 'flex', flexDirection: 'column' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '2rem' }}>
          <div style={{ 
            background: `color-mix(in srgb, ${getLevelColor(currentQuestion.level)} 15%, transparent)`,
            color: getLevelColor(currentQuestion.level),
            border: `1px solid color-mix(in srgb, ${getLevelColor(currentQuestion.level)} 30%, transparent)`,
          }} className="badge">
            Level: {currentQuestion.level}
          </div>
          <Timer />
        </div>

        <div className="card" style={{ flex: 1, display: 'flex', flexDirection: 'column' }}>
          <h2 style={{ fontSize: '1.4rem', fontWeight: 500, lineHeight: 1.6, marginBottom: '1rem' }}>
            {currentQuestion.text}
          </h2>
          
          <div style={{ color: 'var(--text-muted)', fontSize: '0.85rem', marginBottom: '1rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <ShieldAlert size={14} /> Select all that apply.
          </div>
          
          {currentQuestion.options && (
            <div style={{ flex: 1, overflowY: 'auto' }}>
              <MCQRenderer 
                options={currentQuestion.options} 
                selectedOptions={selectedOptions} 
                onChange={(opts) => setResponse(currentQuestion.id, opts)} 
              />
            </div>
          )}

          <div style={{ display: 'flex', justifyContent: 'flex-end', marginTop: '2rem', paddingTop: '1.5rem', borderTop: '1px solid var(--border-glass)' }}>
            <button 
              className="btn btn-primary" 
              onClick={handleNext} 
              disabled={loading || selectedOptions.length === 0}
            >
              {loading ? 'Processing...' : (currentQuestion.id === 'q2' ? 'Submit Assessment' : 'Submit & Continue')} 
              <ChevronRight size={18} style={{ marginLeft: '0.5rem' }} />
            </button>
          </div>
        </div>
      </div>

      {/* Right panel: Context (30%) */}
      <div style={{ flex: '3', display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
        {currentQuestion.prerequisites && currentQuestion.prerequisites.length > 0 && (
          <div className="glass-panel" style={{ padding: '1.5rem' }}>
            <h3 style={{ fontSize: '1rem', color: 'var(--text-secondary)', marginBottom: '1rem', textTransform: 'uppercase', letterSpacing: '0.5px' }}>Prerequisite Knowledge</h3>
            <ul style={{ listStyle: 'none', display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
              {currentQuestion.prerequisites.map((prereq, i) => (
                <li key={i} style={{ fontSize: '0.9rem', padding: '0.5rem 0.75rem', background: 'var(--bg-secondary)', borderRadius: '6px', border: '1px solid var(--border-glass)' }}>
                  {prereq}
                </li>
              ))}
            </ul>
          </div>
        )}
        
        <div className="glass-panel" style={{ padding: '1.5rem', flex: 1 }}>
          <h3 style={{ fontSize: '1rem', color: 'var(--text-secondary)', marginBottom: '1rem', textTransform: 'uppercase', letterSpacing: '0.5px' }}>Adaptive Engine</h3>
          <p style={{ fontSize: '0.9rem', color: 'var(--text-muted)' }}>
            IKAS analyzes your responses using Bayesian Knowledge Tracing. Answering this question correctly will increase our confidence in your mastery of related graph concepts.
          </p>
        </div>
      </div>
    </div>
  );
};

export default TestPage;
"""

files['src/pages/ResultsPage.tsx'] = """
import React from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { Radar, RadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis, ResponsiveContainer, BarChart, Bar, XAxis, YAxis, Tooltip, CartesianGrid } from 'recharts';
import { ArrowLeft, BookOpen, ExternalLink, Video } from 'lucide-react';

const ResultsPage: React.FC = () => {
  const location = useLocation();
  const navigate = useNavigate();
  const result = location.state?.result;

  if (!result) return <div style={{ padding: '2rem' }}>No results found.</div>;

  const radarData = [
    { level: 'Repeat', score: result.levelBreakdown.Repeat, fullMark: 100 },
    { level: 'Summary', score: result.levelBreakdown.Summary, fullMark: 100 },
    { level: 'Intuitive', score: result.levelBreakdown.Intuitive, fullMark: 100 },
    { level: 'Apply', score: result.levelBreakdown.Apply, fullMark: 100 },
  ];

  const masteryData = Object.entries(result.masteryGrid).map(([concept, score]) => ({
    concept,
    score: (score as number) * 100
  }));

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '2rem' }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
        <button className="btn btn-outline" onClick={() => navigate('/dashboard')} style={{ padding: '0.5rem', borderRadius: '50%' }}>
          <ArrowLeft size={20} />
        </button>
        <h1 style={{ fontSize: '2rem', fontWeight: 700 }}>Assessment Results</h1>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 2fr', gap: '2rem' }}>
        {/* Score Summary Card */}
        <div className="card" style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', padding: '3rem 2rem', background: 'linear-gradient(135deg, rgba(52, 168, 83, 0.1), rgba(26, 29, 46, 0.8))', border: '1px solid rgba(52, 168, 83, 0.3)' }}>
          <div style={{ fontSize: '1rem', color: 'var(--text-secondary)', textTransform: 'uppercase', letterSpacing: '1px', marginBottom: '1rem' }}>Overall Score</div>
          <div style={{ fontSize: '5rem', fontWeight: 800, color: 'var(--accent-green)', lineHeight: 1 }}>{result.score}%</div>
          <div style={{ marginTop: '1.5rem', padding: '0.5rem 1rem', background: 'var(--bg-primary)', borderRadius: '20px', fontSize: '0.9rem', color: 'var(--text-primary)', border: '1px solid var(--border-glass)' }}>
            Strong performance at foundational levels
          </div>
        </div>

        {/* Level Breakdown Chart */}
        <div className="card" style={{ height: '350px' }}>
          <h3 style={{ fontSize: '1.1rem', marginBottom: '1rem', color: 'var(--text-secondary)' }}>Cognitive Level Analysis</h3>
          <ResponsiveContainer width="100%" height="100%">
            <RadarChart cx="50%" cy="50%" outerRadius="80%" data={radarData}>
              <PolarGrid stroke="var(--border-glass)" />
              <PolarAngleAxis dataKey="level" tick={{ fill: 'var(--text-secondary)', fontSize: 12 }} />
              <PolarRadiusAxis angle={30} domain={[0, 100]} tick={{ fill: 'var(--text-muted)' }} />
              <Radar name="Score" dataKey="score" stroke="var(--accent-blue)" fill="var(--accent-blue)" fillOpacity={0.3} />
            </RadarChart>
          </ResponsiveContainer>
        </div>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '2fr 1fr', gap: '2rem' }}>
        {/* Concept Mastery Grid */}
        <div className="card">
          <h3 style={{ fontSize: '1.1rem', marginBottom: '2rem', color: 'var(--text-secondary)' }}>Concept Mastery Grid</h3>
          <div style={{ height: '250px' }}>
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={masteryData} layout="vertical" margin={{ top: 5, right: 30, left: 20, bottom: 5 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="var(--border-glass)" horizontal={true} vertical={false} />
                <XAxis type="number" domain={[0, 100]} tick={{ fill: 'var(--text-muted)' }} stroke="var(--border-glass)" />
                <YAxis dataKey="concept" type="category" width={150} tick={{ fill: 'var(--text-secondary)' }} stroke="var(--border-glass)" />
                <Tooltip cursor={{ fill: 'var(--bg-glass)' }} contentStyle={{ backgroundColor: 'var(--bg-secondary)', border: '1px solid var(--border-glass)', borderRadius: '8px' }} />
                <Bar dataKey="score" fill="var(--accent-purple)" radius={[0, 4, 4, 0]} barSize={20} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Resource Recommendations */}
        <div className="card">
          <h3 style={{ fontSize: '1.1rem', marginBottom: '1.5rem', color: 'var(--text-secondary)' }}>Recommended Resources</h3>
          <p style={{ fontSize: '0.85rem', color: 'var(--text-muted)', marginBottom: '1.5rem' }}>Based on your performance at higher cognitive levels, we recommend these targeted materials:</p>
          
          <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
            {result.recommendations.map((rec: any) => (
              <a key={rec.id} href={rec.url} target="_blank" rel="noreferrer" style={{ display: 'flex', alignItems: 'flex-start', gap: '1rem', padding: '1rem', background: 'var(--bg-glass)', borderRadius: '8px', textDecoration: 'none', border: '1px solid var(--border-glass)', transition: 'background 0.2s' }}>
                <div style={{ color: rec.type === 'video' ? 'var(--accent-red)' : 'var(--accent-blue)' }}>
                  {rec.type === 'video' ? <Video size={24} /> : <BookOpen size={24} />}
                </div>
                <div style={{ flex: 1 }}>
                  <div style={{ fontWeight: 500, color: 'var(--text-primary)', marginBottom: '0.25rem', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                    {rec.title} <ExternalLink size={14} color="var(--text-muted)" />
                  </div>
                  <div style={{ fontSize: '0.75rem', color: 'var(--accent-amber)', textTransform: 'uppercase', fontWeight: 600 }}>
                    Target: {rec.level}
                  </div>
                </div>
              </a>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};

export default ResultsPage;
"""

files['src/pages/ProgressPage.tsx'] = """
import React, { useEffect, useState } from 'react';
import { getProgress } from '../api/reports';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';

const ProgressPage: React.FC = () => {
  const [data, setData] = useState<any[]>([]);

  useEffect(() => {
    getProgress().then(res => setData(res as any));
  }, []);

  return (
    <div>
      <h1 style={{ fontSize: '2rem', marginBottom: '2rem', fontWeight: 700 }}>Learning Progress</h1>
      
      <div className="card" style={{ height: '400px', marginBottom: '2rem' }}>
        <h3 style={{ fontSize: '1.1rem', marginBottom: '2rem', color: 'var(--text-secondary)' }}>Overall Score Trend</h3>
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={data} margin={{ top: 5, right: 30, left: 20, bottom: 5 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="var(--border-glass)" />
            <XAxis dataKey="date" tick={{ fill: 'var(--text-secondary)' }} stroke="var(--border-glass)" />
            <YAxis domain={[0, 100]} tick={{ fill: 'var(--text-secondary)' }} stroke="var(--border-glass)" />
            <Tooltip contentStyle={{ backgroundColor: 'var(--bg-secondary)', border: '1px solid var(--border-glass)', borderRadius: '8px' }} />
            <Line type="monotone" dataKey="score" stroke="var(--accent-blue)" strokeWidth={3} dot={{ fill: 'var(--bg-primary)', stroke: 'var(--accent-blue)', strokeWidth: 2, r: 4 }} activeDot={{ r: 6 }} />
          </LineChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
};

export default ProgressPage;
"""

files['src/router.tsx'] = """
import { createBrowserRouter, Navigate } from 'react-router-dom';
import Layout from './components/layout/Layout';
import LoginPage from './pages/LoginPage';
import RegisterPage from './pages/RegisterPage';
import DashboardPage from './pages/DashboardPage';
import TestPage from './pages/TestPage';
import ResultsPage from './pages/ResultsPage';
import ProgressPage from './pages/ProgressPage';

export const router = createBrowserRouter([
  {
    path: '/login',
    element: <LoginPage />
  },
  {
    path: '/register',
    element: <RegisterPage />
  },
  {
    path: '/',
    element: <Layout />,
    children: [
      {
        path: '/',
        element: <Navigate to="/dashboard" replace />
      },
      {
        path: 'dashboard',
        element: <DashboardPage />
      },
      {
        path: 'test',
        element: <TestPage />
      },
      {
        path: 'results',
        element: <ResultsPage />
      },
      {
        path: 'progress',
        element: <ProgressPage />
      }
    ]
  }
]);
"""

files['src/App.tsx'] = """
import React from 'react';
import { RouterProvider } from 'react-router-dom';
import { router } from './router';

const App: React.FC = () => {
  return <RouterProvider router={router} />;
};

export default App;
"""

files['src/main.tsx'] = """
import React from 'react';
import ReactDOM from 'react-dom/client';
import App from './App';
import './styles/index.css';

ReactDOM.createRoot(document.getElementById('root') as HTMLElement).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);
"""

for path, content in files.items():
    write_file(path, content)
