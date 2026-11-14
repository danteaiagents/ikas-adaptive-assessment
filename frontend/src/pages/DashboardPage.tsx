import React, { useEffect, useState } from 'react';
import { useAuthStore } from '../store/authStore';
import { getTopics } from '../api/topics';
import { getPresets, startTest } from '../api/tests';
import { Topic, Preset } from '../types';
import { useNavigate } from 'react-router-dom';
import { useTestStore } from '../store/testStore';
import { BookOpen, Clock, ListChecks, Play, ChevronRight, CheckSquare, Square, Info } from 'lucide-react';

const DashboardPage: React.FC = () => {
  const { user } = useAuthStore();
  const navigate = useNavigate();
  const { startTest: setStoreStart } = useTestStore();

  const [topics, setTopics]               = useState<Topic[]>([]);
  const [presets, setPresets]             = useState<Preset[]>([]);
  const [selectedTopicIds, setSelectedTopicIds] = useState<Set<string>>(new Set());
  const [selectedPreset, setSelectedPreset]     = useState<Preset | null>(null);
  const [loading, setLoading]             = useState(false);
  const [topicsLoading, setTopicsLoading] = useState(true);

  useEffect(() => {
    Promise.all([getTopics('s-ai'), getPresets()]).then(([t, p]) => {
      setTopics(t);
      setPresets(p);
      // Pre-select first topic and standard preset
      if (t.length > 0) setSelectedTopicIds(new Set([t[0].id]));
      const standard = p.find(pr => pr.id === 'standard') ?? p[0];
      if (standard) setSelectedPreset(standard);
    }).finally(() => setTopicsLoading(false));
  }, []);

  const toggleTopic = (id: string) => {
    setSelectedTopicIds(prev => {
      const next = new Set(prev);
      if (next.has(id)) {
        // Don't allow deselecting the last topic
        if (next.size === 1) return prev;
        next.delete(id);
      } else {
        next.add(id);
      }
      return next;
    });
  };

  const isMultiTopic = selectedTopicIds.size > 1;

  // For now: always run on the first selected topic (multi-topic engine is a backlog item)
  const primaryTopicId = topics.find(t => selectedTopicIds.has(t.id))?.id ?? '';

  const handleStart = async () => {
    if (!primaryTopicId || !selectedPreset) return;
    setLoading(true);
    try {
      const { session, firstQuestion } = await startTest(primaryTopicId, selectedPreset.id);
      setStoreStart(session, firstQuestion, selectedPreset.durationMinutes);
      navigate('/test');
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const selectedNames = topics
    .filter(t => selectedTopicIds.has(t.id))
    .map(t => t.name)
    .join(', ');

  const canStart = selectedTopicIds.size > 0 && !!selectedPreset && !loading;

  return (
    <div>
      {/* Header */}
      <div style={{ marginBottom: '2rem' }}>
        <h1 style={{ fontSize: '2rem', marginBottom: '0.5rem', fontWeight: 700 }}>
          Welcome back, {user?.name.split(' ')[0]}
        </h1>
        <p style={{ color: 'var(--text-secondary)' }}>
          Select one or more topics and an assessment type to begin your adaptive evaluation.
        </p>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 380px', gap: '2rem', alignItems: 'start' }}>

        {/* Left: Topic Selection (multi-select checkboxes) */}
        <div>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '1rem' }}>
            <h2 style={{ fontSize: '1.1rem', fontWeight: 600, color: 'var(--text-secondary)', textTransform: 'uppercase', letterSpacing: '0.5px', margin: 0 }}>
              Choose Topics
            </h2>
            <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
              {selectedTopicIds.size} selected
            </span>
          </div>

          {topicsLoading ? (
            <div style={{ color: 'var(--text-muted)', padding: '2rem', textAlign: 'center' }}>Loading topics…</div>
          ) : (
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: '1rem' }}>
              {topics.map(topic => {
                const isSelected = selectedTopicIds.has(topic.id);
                return (
                  <div
                    key={topic.id}
                    className="card"
                    onClick={() => toggleTopic(topic.id)}
                    style={{
                      cursor: 'pointer',
                      border: isSelected
                        ? '1px solid var(--accent-blue)'
                        : '1px solid var(--border-glass)',
                      background: isSelected
                        ? 'linear-gradient(135deg, rgba(66,133,244,0.12), rgba(26,29,46,0.8))'
                        : undefined,
                      transition: 'all 0.2s ease',
                      userSelect: 'none',
                    }}
                  >
                    <div style={{ display: 'flex', alignItems: 'flex-start', gap: '0.75rem' }}>
                      {/* Checkbox icon */}
                      <div style={{ flexShrink: 0, marginTop: '1px', color: isSelected ? 'var(--accent-blue)' : 'var(--text-muted)' }}>
                        {isSelected
                          ? <CheckSquare size={18} />
                          : <Square size={18} />
                        }
                      </div>
                      <div style={{ flex: 1, minWidth: 0 }}>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.35rem' }}>
                          <BookOpen size={15} style={{ color: 'var(--accent-blue)', flexShrink: 0 }} />
                          <h3 style={{ fontSize: '0.95rem', fontWeight: 600, margin: 0, lineHeight: 1.3 }}>
                            {topic.name}
                          </h3>
                        </div>
                        {topic.description && (
                          <p style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', marginBottom: '0.6rem', lineHeight: 1.5, margin: '0 0 0.5rem 0' }}>
                            {topic.description}
                          </p>
                        )}
                        <div style={{ display: 'flex', gap: '1rem', fontSize: '0.78rem', color: 'var(--text-muted)', marginTop: '0.5rem' }}>
                          <span>{topic.conceptCount} concepts</span>
                          <span>{topic.questionCount} questions</span>
                        </div>
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          )}

          {/* Multi-topic notice */}
          {isMultiTopic && (
            <div style={{
              marginTop: '1rem',
              padding: '0.75rem 1rem',
              background: 'rgba(251, 188, 4, 0.08)',
              border: '1px solid rgba(251, 188, 4, 0.3)',
              borderRadius: '8px',
              display: 'flex',
              alignItems: 'flex-start',
              gap: '0.6rem',
              fontSize: '0.82rem',
              color: 'var(--text-secondary)',
            }}>
              <Info size={15} style={{ color: 'var(--accent-yellow)', flexShrink: 0, marginTop: '1px' }} />
              <span>
                <strong style={{ color: 'var(--text-primary)' }}>Multi-topic mode coming soon.</strong>
                {' '}This test will run on <strong style={{ color: 'var(--accent-blue)' }}>{topics.find(t => t.id === primaryTopicId)?.name}</strong> (first selected).
                Cross-topic adaptive scoring with combined benchmarks is planned.
              </span>
            </div>
          )}
        </div>

        {/* Right: Assessment Config */}
        <div style={{ position: 'sticky', top: '2rem' }}>
          <h2 style={{ fontSize: '1.1rem', fontWeight: 600, marginBottom: '1rem', color: 'var(--text-secondary)', textTransform: 'uppercase', letterSpacing: '0.5px' }}>
            Assessment Type
          </h2>
          <div className="glass-panel" style={{ padding: '1.5rem', display: 'flex', flexDirection: 'column', gap: '1rem' }}>
            {presets.map(preset => {
              const isSelected = selectedPreset?.id === preset.id;
              return (
                <div
                  key={preset.id}
                  onClick={() => setSelectedPreset(preset)}
                  style={{
                    padding: '1rem',
                    borderRadius: '8px',
                    cursor: 'pointer',
                    border: isSelected ? '1px solid var(--accent-blue)' : '1px solid var(--border-glass)',
                    background: isSelected ? 'rgba(66,133,244,0.08)' : 'var(--bg-secondary)',
                    transition: 'all 0.15s ease',
                  }}
                >
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.4rem' }}>
                    <span style={{ fontWeight: 600, fontSize: '0.95rem', color: isSelected ? 'var(--accent-blue)' : 'var(--text-primary)' }}>
                      {preset.name}
                    </span>
                    {isSelected && <ChevronRight size={16} style={{ color: 'var(--accent-blue)' }} />}
                  </div>
                  <p style={{ fontSize: '0.82rem', color: 'var(--text-secondary)', marginBottom: '0.6rem' }}>
                    {preset.description}
                  </p>
                  <div style={{ display: 'flex', gap: '1rem', fontSize: '0.8rem', color: 'var(--text-muted)' }}>
                    <span style={{ display: 'flex', alignItems: 'center', gap: '0.25rem' }}>
                      <ListChecks size={13} /> {preset.questionCount} Qs
                    </span>
                    <span style={{ display: 'flex', alignItems: 'center', gap: '0.25rem' }}>
                      <Clock size={13} /> {preset.durationMinutes} min
                    </span>
                  </div>
                </div>
              );
            })}

            <div style={{ borderTop: '1px solid var(--border-glass)', paddingTop: '1rem', marginTop: '0.5rem' }}>
              <p style={{ fontSize: '0.82rem', color: 'var(--text-muted)', marginBottom: '0.75rem', lineHeight: 1.6 }}>
                {selectedTopicIds.size > 0 ? (
                  <>
                    <span style={{ color: 'var(--text-secondary)' }}>Topics: </span>
                    <strong style={{ color: 'var(--text-primary)' }}>{selectedNames}</strong>
                    <br />
                    <span style={{ color: 'var(--text-secondary)' }}>Preset: </span>
                    <strong style={{ color: 'var(--text-primary)' }}>{selectedPreset?.name ?? '—'}</strong>
                  </>
                ) : (
                  <span>Select at least one topic to continue.</span>
                )}
              </p>
              <button
                className="btn btn-primary"
                style={{ width: '100%', justifyContent: 'center', opacity: canStart ? 1 : 0.5 }}
                onClick={handleStart}
                disabled={!canStart}
              >
                <Play size={16} style={{ marginRight: '0.5rem' }} />
                {loading ? 'Starting…' : 'Begin Assessment'}
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default DashboardPage;
