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
        <div className="card" style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', padding: '3rem 2rem', background: 'linear-gradient(135deg, rgba(52, 168, 83, 0.1), rgba(26, 29, 46, 0.8))', border: '1px solid rgba(52, 168, 83, 0.3)' }}>
          <div style={{ fontSize: '1rem', color: 'var(--text-secondary)', textTransform: 'uppercase', letterSpacing: '1px', marginBottom: '1rem' }}>Overall Score</div>
          <div style={{ fontSize: '5rem', fontWeight: 800, color: 'var(--accent-green)', lineHeight: 1 }}>{result.score}%</div>
          <div style={{ marginTop: '1.5rem', padding: '0.5rem 1rem', background: 'var(--bg-primary)', borderRadius: '20px', fontSize: '0.9rem', color: 'var(--text-primary)', border: '1px solid var(--border-glass)' }}>
            Strong performance at foundational levels
          </div>
        </div>

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
