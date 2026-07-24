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
