import React, { useEffect, useState } from 'react';
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
} from 'recharts';
import { TrendingUp, Award, BarChart2, Clock } from 'lucide-react';
import { getProgress } from '../api/reports';
import { getTopics } from '../api/topics';
import { ProgressData, ProgressSession, Topic } from '../types';

const PRESET_LABELS: Record<string, string> = {
  quick: 'Quick (10q)',
  standard: 'Standard (25q)',
  comprehensive: 'Comprehensive (50q)',
};

function formatDate(isoString: string): string {
  return new Date(isoString).toLocaleDateString(undefined, {
    month: 'short', day: 'numeric', year: 'numeric',
  });
}

function formatDuration(minutes: number): string {
  return minutes >= 60 ? `${Math.floor(minutes / 60)}h ${minutes % 60}m` : `${minutes}m`;
}

const StatCard: React.FC<{ label: string; value: string | number; icon: React.ReactNode; accent: string }> = ({
  label, value, icon, accent,
}) => (
  <div style={{ display: 'flex', alignItems: 'center', gap: '1rem', padding: '1.25rem', background: 'var(--bg-secondary)', borderRadius: '12px', border: '1px solid var(--border-glass)' }}>
    <div style={{
      width: '48px', height: '48px', borderRadius: '12px',
      background: `${accent}22`, border: `1px solid ${accent}44`,
      display: 'flex', alignItems: 'center', justifyContent: 'center',
      color: accent, flexShrink: 0,
    }}>
      {icon}
    </div>
    <div>
      <div style={{ fontSize: '1.75rem', fontWeight: 700, color: 'var(--text-primary)', lineHeight: 1 }}>
        {value}
      </div>
      <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)', marginTop: '0.25rem' }}>
        {label}
      </div>
    </div>
  </div>
);

const ProgressPage: React.FC = () => {
  const [topics, setTopics]   = useState<Topic[]>([]);
  const [topicId, setTopicId] = useState<string>('');
  const [data, setData]       = useState<ProgressData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError]     = useState<string | null>(null);

  // Load topic list once on mount
  useEffect(() => {
    getTopics('s-ai').then((t) => {
      setTopics(t);
      if (t.length > 0) setTopicId(t[0].id);
    });
  }, []);

  // Reload progress whenever selected topic changes
  useEffect(() => {
    if (!topicId) return;
    setLoading(true);
    setData(null);
    setError(null);
    getProgress(topicId)
      .then(setData)
      .catch((err) => {
        setError(err?.response?.data?.error || 'Failed to load progress.');
      })
      .finally(() => setLoading(false));
  }, [topicId]);

  // Chart data: convert theta to 0-100 score for display
  const chartData = (data?.history ?? []).map((s) => ({
    date: formatDate(s.date),
    score: s.score,
  }));

  const summary = data?.summary;

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '2rem' }}>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '1rem' }}>
        <h1 style={{ fontSize: '2rem', fontWeight: 700 }}>Learning Progress</h1>
        {topics.length > 1 && (
          <select
            value={topicId}
            onChange={(e) => setTopicId(e.target.value)}
            style={{
              background: 'var(--bg-secondary)',
              border: '1px solid var(--border-glass)',
              borderRadius: '8px',
              padding: '0.5rem 1rem',
              color: 'var(--text-primary)',
              fontSize: '0.9rem',
              cursor: 'pointer',
            }}
          >
            {topics.map(t => (
              <option key={t.id} value={t.id}>{t.name}</option>
            ))}
          </select>
        )}
      </div>

      {/* Stats cards */}
      {summary && (
        <div style={{ display: 'flex', gap: '1.25rem', flexWrap: 'wrap' }}>
          <StatCard
            label="Sessions Taken"
            value={summary.total_sessions}
            icon={<BarChart2 size={22} />}
            accent="var(--accent-blue, #3b82f6)"
          />
          <StatCard
            label="Average Score"
            value={`${summary.avg_score}%`}
            icon={<TrendingUp size={22} />}
            accent="var(--accent-purple, #8b5cf6)"
          />
          <StatCard
            label="Best Score"
            value={`${summary.best_score}%`}
            icon={<Award size={22} />}
            accent="var(--accent-green, #10b981)"
          />
        </div>
      )}

      {/* Score trend chart */}
      <div className="card" style={{ height: '360px' }}>
        <h3 style={{ fontSize: '1.1rem', marginBottom: '1rem', color: 'var(--text-secondary)' }}>
          Score Trend — LLMs &amp; Prompting
        </h3>
        {loading ? (
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '80%', color: 'var(--text-muted)' }}>
            Loading…
          </div>
        ) : error ? (
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '80%', color: 'var(--accent-red, #ef4444)', fontSize: '0.9rem' }}>
            {error}
          </div>
        ) : chartData.length === 0 ? (
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '80%', color: 'var(--text-muted)', fontSize: '0.9rem' }}>
            No sessions completed yet. Take a test to see your progress here.
          </div>
        ) : (
          <ResponsiveContainer width="100%" height="90%">
            <LineChart data={chartData} margin={{ top: 5, right: 30, left: 20, bottom: 5 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="var(--border-glass)" />
              <XAxis dataKey="date" tick={{ fill: 'var(--text-secondary)', fontSize: 12 }} stroke="var(--border-glass)" />
              <YAxis domain={[0, 100]} tick={{ fill: 'var(--text-secondary)' }} stroke="var(--border-glass)" />
              <Tooltip
                contentStyle={{ backgroundColor: 'var(--bg-secondary)', border: '1px solid var(--border-glass)', borderRadius: '8px' }}
                formatter={(v: number) => [`${v}%`, 'Score']}
              />
              <Line
                type="monotone" dataKey="score"
                stroke="var(--accent-blue)" strokeWidth={3}
                dot={{ fill: 'var(--bg-primary)', stroke: 'var(--accent-blue)', strokeWidth: 2, r: 4 }}
                activeDot={{ r: 6 }}
              />
            </LineChart>
          </ResponsiveContainer>
        )}
      </div>

      {/* Session history table */}
      {!loading && !error && data && data.history.length > 0 && (
        <div className="card">
          <h3 style={{ fontSize: '1.1rem', marginBottom: '1.25rem', color: 'var(--text-secondary)' }}>
            Session History
          </h3>
          <div style={{ overflowX: 'auto' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.875rem' }}>
              <thead>
                <tr style={{ borderBottom: '1px solid var(--border-glass)' }}>
                  {['Date', 'Preset', 'Questions', 'Score', 'Time Limit'].map((h) => (
                    <th key={h} style={{ textAlign: 'left', padding: '0.5rem 0.75rem', color: 'var(--text-muted)', fontWeight: 500 }}>
                      {h}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {[...data.history].reverse().map((s: ProgressSession) => (
                  <tr key={s.session_id} style={{ borderBottom: '1px solid var(--border-glass)' }}>
                    <td style={{ padding: '0.75rem', color: 'var(--text-secondary)' }}>
                      {formatDate(s.date)}
                    </td>
                    <td style={{ padding: '0.75rem', color: 'var(--text-primary)' }}>
                      {PRESET_LABELS[s.preset] ?? s.preset}
                    </td>
                    <td style={{ padding: '0.75rem', color: 'var(--text-secondary)' }}>
                      {s.correct_count}/{s.total_questions}
                    </td>
                    <td style={{ padding: '0.75rem' }}>
                      <span
                        style={{
                          fontWeight: 700,
                          color: s.score >= 70
                            ? 'var(--accent-green, #10b981)'
                            : s.score >= 50
                              ? 'var(--accent-amber, #f59e0b)'
                              : 'var(--accent-red, #ef4444)',
                        }}
                      >
                        {s.score}%
                      </span>
                    </td>
                    <td style={{ padding: '0.75rem', color: 'var(--text-muted)', display: 'flex', alignItems: 'center', gap: '0.3rem' }}>
                      <Clock size={13} />
                      {formatDuration(s.time_limit_minutes)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
};

export default ProgressPage;
