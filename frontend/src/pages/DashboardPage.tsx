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
