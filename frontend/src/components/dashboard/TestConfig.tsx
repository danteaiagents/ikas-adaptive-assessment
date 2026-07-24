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
