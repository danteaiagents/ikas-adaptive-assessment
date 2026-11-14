import React, { useEffect, useState } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import {
  Radar, RadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis,
  ResponsiveContainer,
} from 'recharts';
import { ArrowLeft, BookOpen, ExternalLink, Video, Clock, Target } from 'lucide-react';
import { SessionReport, KnowledgeLevel, ReportRecommendation } from '../types';
import { getSessionReport } from '../api/reports';

const LEVELS: KnowledgeLevel[] = ['Repeat', 'Summary', 'Intuitive', 'Apply'];

const LEVEL_COLORS: Record<KnowledgeLevel, string> = {
  Repeat:    'var(--accent-blue,   #3b82f6)',
  Summary:   'var(--accent-purple, #8b5cf6)',
  Intuitive: 'var(--accent-amber,  #f59e0b)',
  Apply:     'var(--accent-green,  #10b981)',
};

/** Returns a background colour based on 0-1 accuracy */
function heatColour(accuracy: number): string {
  if (accuracy >= 0.8) return 'rgba(16,185,129,0.35)';
  if (accuracy >= 0.6) return 'rgba(16,185,129,0.18)';
  if (accuracy >= 0.4) return 'rgba(245,158,11,0.25)';
  if (accuracy >= 0.2) return 'rgba(239,68,68,0.22)';
  return 'rgba(239,68,68,0.10)';
}

/**
 * Strips the concept-id prefix and level suffix from masteryGrid keys like
 * "c-ai-llm-001/Repeat" → "c-ai-llm-001/Repeat" is mapped to a display name
 * using the concept_mastery data from the session report.
 */
function buildHeatmapFromReport(report: SessionReport) {
  return Object.entries(report.concept_mastery).map(([id, data]) => ({ id, ...data }));
}

const ResultsPage: React.FC = () => {
  const location = useLocation();
  const navigate  = useNavigate();
  const result    = location.state?.result;

  const [report, setReport]     = useState<SessionReport | null>(null);
  const [loading, setLoading]   = useState(false);
  const [reportError, setReportError] = useState(false);

  useEffect(() => {
    if (!result?.sessionId) return;
    setLoading(true);
    getSessionReport(result.sessionId)
      .then(setReport)
      .catch(() => setReportError(true))
      .finally(() => setLoading(false));
  }, [result?.sessionId]);

  if (!result) return <div style={{ padding: '2rem' }}>No results found.</div>;

  // ── Radar data from levelBreakdown ────────────────────────────────────
  const radarData = LEVELS.map((level) => ({
    level,
    score: result.levelBreakdown[level] ?? 0,
    fullMark: 100,
  }));

  // ── Concept×level heatmap — always from the session report ────────────
  const concepts = report ? buildHeatmapFromReport(report) : [];
  const recommendations: ReportRecommendation[] = report?.recommendations ?? [];

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '2rem' }}>
      {/* Header */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
        <button
          className="btn btn-outline"
          onClick={() => navigate('/dashboard')}
          style={{ padding: '0.5rem', borderRadius: '50%' }}
        >
          <ArrowLeft size={20} />
        </button>
        <h1 style={{ fontSize: '2rem', fontWeight: 700 }}>Assessment Results</h1>
      </div>

      {/* Top row: score card + radar */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 2fr', gap: '2rem' }}>
        <div
          className="card"
          style={{
            display: 'flex', flexDirection: 'column', alignItems: 'center',
            justifyContent: 'center', padding: '3rem 2rem',
            background: 'linear-gradient(135deg, rgba(52,168,83,0.1), rgba(26,29,46,0.8))',
            border: '1px solid rgba(52,168,83,0.3)',
          }}
        >
          <div style={{ fontSize: '1rem', color: 'var(--text-secondary)', textTransform: 'uppercase', letterSpacing: '1px', marginBottom: '1rem' }}>
            Overall Score
          </div>
          <div style={{ fontSize: '5rem', fontWeight: 800, color: 'var(--accent-green)', lineHeight: 1 }}>
            {report?.score ?? result.score}%
          </div>
          {report && (
            <div style={{ marginTop: '1.5rem', display: 'flex', flexDirection: 'column', gap: '0.5rem', alignItems: 'center', width: '100%' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', fontSize: '0.85rem', color: 'var(--text-secondary)' }}>
                <Target size={14} />
                {report.correct_count}/{report.total_questions} correct
              </div>
              {report.time_stats.avg_time_seconds > 0 && (
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', fontSize: '0.85rem', color: 'var(--text-secondary)' }}>
                  <Clock size={14} />
                  Avg {Math.round(report.time_stats.avg_time_seconds)}s per question
                </div>
              )}
              {/* Score breakdown */}
              <div style={{
                marginTop: '0.75rem', padding: '0.75rem 1rem', borderRadius: '8px',
                background: 'rgba(255,255,255,0.04)', border: '1px solid var(--border-glass)',
                width: '100%', display: 'flex', flexDirection: 'column', gap: '0.4rem',
              }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.78rem' }}>
                  <span style={{ color: 'var(--text-muted)' }}>Accuracy</span>
                  <span style={{ color: 'var(--text-primary)', fontWeight: 600 }}>
                    {(report as any).raw_score ?? Math.round((report.correct_count / report.total_questions) * 100)}%
                  </span>
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.78rem' }}>
                  <span style={{ color: 'var(--text-muted)' }}>Ability (IRT θ)</span>
                  <span style={{ color: 'var(--text-primary)', fontWeight: 600 }}>
                    {(report as any).theta_score ?? Math.round(((report.theta + 3) / 6) * 100)}%
                  </span>
                </div>
                <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)', marginTop: '0.2rem', lineHeight: 1.4, borderTop: '1px solid var(--border-glass)', paddingTop: '0.4rem' }}>
                  Score = 60% accuracy + 40% difficulty-weighted ability
                </div>
              </div>
            </div>
          )}
        </div>

        <div className="card" style={{ height: '350px' }}>
          <h3 style={{ fontSize: '1.1rem', marginBottom: '1rem', color: 'var(--text-secondary)' }}>
            Cognitive Level Analysis
          </h3>
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

      {/* Concept × Level Heatmap */}
      <div className="card">
        <h3 style={{ fontSize: '1.1rem', marginBottom: '1.5rem', color: 'var(--text-secondary)' }}>
          Concept Mastery Breakdown
        </h3>

        {loading && (
          <div style={{ padding: '2rem', textAlign: 'center', color: 'var(--text-muted)' }}>
            Loading concept breakdown…
          </div>
        )}

        {!loading && reportError && (
          <div style={{ padding: '1.5rem', textAlign: 'center', color: 'var(--text-muted)', fontSize: '0.9rem' }}>
            Could not load detailed concept breakdown. Please check your connection.
          </div>
        )}

        {!loading && !reportError && concepts.length === 0 && (
          <div style={{ padding: '1.5rem', textAlign: 'center', color: 'var(--text-muted)', fontSize: '0.9rem' }}>
            No concept data available for this session.
          </div>
        )}

        {!loading && concepts.length > 0 && (
          <div style={{ overflowX: 'auto' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.875rem' }}>
              <thead>
                <tr>
                  <th style={{
                    textAlign: 'left', padding: '0.6rem 0.75rem',
                    color: 'var(--text-muted)', fontWeight: 500,
                    borderBottom: '1px solid var(--border-glass)',
                  }}>
                    Concept
                  </th>
                  {LEVELS.map((lvl) => (
                    <th
                      key={lvl}
                      style={{
                        padding: '0.6rem 0.75rem', color: LEVEL_COLORS[lvl],
                        fontWeight: 600, textAlign: 'center', whiteSpace: 'nowrap',
                        borderBottom: '1px solid var(--border-glass)',
                      }}
                    >
                      {lvl}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {concepts.map((concept) => (
                  <tr key={concept.id} style={{ borderBottom: '1px solid var(--border-glass)' }}>
                    {/* Human-readable name — always from Neo4j concept.name */}
                    <td style={{
                      padding: '0.7rem 0.75rem',
                      color: 'var(--text-primary)',
                      fontWeight: 500,
                    }}>
                      {concept.name}
                    </td>
                    {LEVELS.map((lvl) => {
                      const cell = concept.levels[lvl];
                      if (!cell) {
                        return (
                          <td key={lvl} style={{
                            padding: '0.7rem 0.75rem', textAlign: 'center',
                            color: 'var(--text-muted)', fontSize: '0.8rem',
                          }}>
                            —
                          </td>
                        );
                      }
                      const pct = Math.round(cell.accuracy * 100);
                      return (
                        <td
                          key={lvl}
                          style={{
                            padding: '0.7rem 0.75rem', textAlign: 'center',
                            background: heatColour(cell.accuracy),
                            borderRadius: '4px',
                          }}
                          title={`${concept.name} · ${lvl}: ${cell.correct} of ${cell.total} correct`}
                        >
                          <span style={{ fontWeight: 600, color: 'var(--text-primary)' }}>
                            {pct}%
                          </span>
                          <span style={{
                            fontSize: '0.7rem', color: 'var(--text-muted)',
                            marginLeft: '0.3rem',
                          }}>
                            ({cell.correct}/{cell.total})
                          </span>
                        </td>
                      );
                    })}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Recommendations */}
      <div className="card">
        <h3 style={{ fontSize: '1.1rem', marginBottom: '1rem', color: 'var(--text-secondary)' }}>
          Recommended Resources
        </h3>

        {loading && (
          <p style={{ fontSize: '0.9rem', color: 'var(--text-muted)' }}>Loading recommendations…</p>
        )}

        {!loading && recommendations.length === 0 && (
          <p style={{ fontSize: '0.9rem', color: 'var(--text-muted)' }}>
            Great performance! No specific resources needed right now.
          </p>
        )}

        {!loading && recommendations.length > 0 && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
            {recommendations.map((rec) => (
              <a
                key={rec.id}
                href={rec.url || '#'}
                target={rec.url ? '_blank' : undefined}
                rel="noreferrer"
                style={{
                  display: 'flex', alignItems: 'flex-start', gap: '1rem',
                  padding: '1rem', background: 'var(--bg-glass)', borderRadius: '8px',
                  textDecoration: 'none', border: '1px solid var(--border-glass)',
                  transition: 'background 0.2s',
                }}
              >
                <div style={{ color: rec.type === 'video' ? 'var(--accent-red, #ef4444)' : 'var(--accent-blue)' }}>
                  {rec.type === 'video' ? <Video size={24} /> : <BookOpen size={24} />}
                </div>
                <div style={{ flex: 1 }}>
                  <div style={{
                    fontWeight: 500, color: 'var(--text-primary)', marginBottom: '0.25rem',
                    display: 'flex', alignItems: 'center', justifyContent: 'space-between',
                  }}>
                    {rec.title}
                    {rec.url && <ExternalLink size={14} color="var(--text-muted)" />}
                  </div>
                  <div style={{ fontSize: '0.75rem', display: 'flex', gap: '0.75rem', flexWrap: 'wrap' }}>
                    <span style={{ color: 'var(--accent-amber)', fontWeight: 600, textTransform: 'uppercase' }}>
                      Target: {rec.target_level}
                    </span>
                    {rec.concept_name && (
                      <span style={{ color: 'var(--text-muted)' }}>
                        Concept: {rec.concept_name}
                      </span>
                    )}
                  </div>
                </div>
              </a>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

export default ResultsPage;
