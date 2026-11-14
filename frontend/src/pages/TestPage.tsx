import React, { useState } from 'react';
import { useTestStore } from '../store/testStore';
import MCQRenderer from '../components/questions/MCQRenderer';
import Timer from '../components/questions/Timer';
import { submitAnswer, completeSession } from '../api/tests';
import { useNavigate } from 'react-router-dom';
import { ChevronRight, ShieldAlert, BookMarked, Lightbulb } from 'lucide-react';
import { Prerequisite } from '../types';

const TestPage: React.FC = () => {
  const { session, currentQuestion, questionNumber, responses, setResponse } = useTestStore();
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();

  if (!session || !currentQuestion) {
    return <div style={{ padding: '2rem' }}>No active test session. <a href="/dashboard">Return to Dashboard</a></div>;
  }

  const selectedOptions = responses[currentQuestion.id] || [];

  const handleNext = async () => {
    setLoading(true);
    try {
      const timeTaken = Math.round((Date.now() - useTestStore.getState().questionStartTime) / 1000);
      const nextQ = await submitAnswer(session.id, currentQuestion.id, selectedOptions, timeTaken);
      if (nextQ) {
        useTestStore.getState().nextQuestion(nextQ);
      } else {
        const result = await completeSession(session.id);
        useTestStore.getState().endTest();
        navigate('/results', { state: { result } });
      }
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const getLevelColor = (level: string) => {
    switch (level) {
      case 'Repeat':    return 'var(--level-repeat)';
      case 'Summary':   return 'var(--level-summary)';
      case 'Intuitive': return 'var(--level-intuitive)';
      case 'Apply':     return 'var(--level-apply)';
      default:          return 'var(--text-secondary)';
    }
  };

  const totalQuestions = (session as any).questionCount as number | undefined;
  const isRepeatLevel = currentQuestion.level === 'Repeat';

  // Deduplicate prerequisites by question ID (in case of duplicate edges in graph)
  const prereqs: Prerequisite[] = currentQuestion.prerequisites
    ? Array.from(new Map(currentQuestion.prerequisites.map(p => [p.id, p])).values())
    : [];

  // Group prerequisite questions by concept for cleaner display
  const prereqByConcept: Map<string, { concept_name: string; items: Prerequisite[] }> = new Map();
  for (const p of prereqs) {
    const key = p.concept_id || p.concept_name;
    if (!prereqByConcept.has(key)) {
      prereqByConcept.set(key, { concept_name: p.concept_name, items: [] });
    }
    prereqByConcept.get(key)!.items.push(p);
  }

  return (
    <div style={{ display: 'flex', gap: '2rem', height: 'calc(100vh - 100px)' }}>
      {/* Left: Question */}
      <div style={{ flex: '7', display: 'flex', flexDirection: 'column' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '2rem' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
            <div style={{
              background: `color-mix(in srgb, ${getLevelColor(currentQuestion.level)} 15%, transparent)`,
              color: getLevelColor(currentQuestion.level),
              border: `1px solid color-mix(in srgb, ${getLevelColor(currentQuestion.level)} 30%, transparent)`,
            }} className="badge">
              Level: {currentQuestion.level}
            </div>
            <span style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>
              Question {questionNumber}{totalQuestions ? ` of ${totalQuestions}` : ''}
            </span>
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
              {loading ? 'Processing...' : 'Submit & Continue'}
              <ChevronRight size={18} style={{ marginLeft: '0.5rem' }} />
            </button>
          </div>
        </div>
      </div>

      {/* Right: Sidebar panels */}
      <div style={{ flex: '3', display: 'flex', flexDirection: 'column', gap: '1.5rem', overflowY: 'auto' }}>

        {/* Prerequisite Knowledge Panel */}
        <div className="glass-panel" style={{ padding: '1.5rem' }}>
          <h3 style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', marginBottom: '1rem', textTransform: 'uppercase', letterSpacing: '0.5px', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <BookMarked size={14} /> Prerequisite Knowledge
          </h3>

          {isRepeatLevel ? (
            /* Repeat = foundational — no prerequisites, explain why */
            <div style={{ fontSize: '0.82rem', color: 'var(--text-muted)', lineHeight: 1.6,
              padding: '0.75rem', background: 'rgba(66,133,244,0.06)',
              border: '1px solid rgba(66,133,244,0.2)', borderRadius: '8px' }}>
              <strong style={{ color: 'var(--accent-blue)', display: 'block', marginBottom: '0.3rem' }}>
                Foundation-level question
              </strong>
              This is a <em>Repeat</em> question — it tests core definitions that are the building blocks for all higher levels.
              No prior knowledge within this topic is required.
            </div>
          ) : prereqs.length === 0 ? (
            <p style={{ fontSize: '0.82rem', color: 'var(--text-muted)', fontStyle: 'italic' }}>
              No specific prerequisites identified for this question.
            </p>
          ) : (
            /* Show prerequisite questions grouped by concept */
            <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
              {Array.from(prereqByConcept.values()).map(({ concept_name, items }) => (
                <div key={concept_name}>
                  {/* Concept group header */}
                  <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)', textTransform: 'uppercase',
                    letterSpacing: '0.4px', marginBottom: '0.4rem', paddingLeft: '0.25rem' }}>
                    {concept_name}
                  </div>
                  <ul style={{ listStyle: 'none', display: 'flex', flexDirection: 'column', gap: '0.4rem' }}>
                    {items.map((prereq) => (
                      <li key={prereq.id} style={{
                        fontSize: '0.82rem', padding: '0.55rem 0.75rem',
                        background: 'var(--bg-secondary)', borderRadius: '6px',
                        border: '1px solid var(--border-glass)',
                        display: 'flex', flexDirection: 'column', gap: '0.35rem',
                      }}>
                        {/* Specific question stem — the actual prerequisite knowledge */}
                        <span style={{ color: 'var(--text-primary)', lineHeight: 1.4 }}>
                          <Lightbulb size={11} style={{ color: 'var(--accent-yellow)', marginRight: '0.3rem', verticalAlign: 'middle' }} />
                          {prereq.stem}
                        </span>
                        <span style={{
                          fontSize: '0.68rem', color: 'var(--text-muted)',
                          background: 'var(--bg-glass)', padding: '0.1rem 0.45rem',
                          borderRadius: '8px', width: 'fit-content',
                        }}>
                          {prereq.level} level
                        </span>
                      </li>
                    ))}
                  </ul>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Adaptive Engine Panel */}
        <div className="glass-panel" style={{ padding: '1.5rem', flex: 1 }}>
          <h3 style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', marginBottom: '1rem', textTransform: 'uppercase', letterSpacing: '0.5px' }}>
            Adaptive Engine
          </h3>
          <p style={{ fontSize: '0.85rem', color: 'var(--text-muted)', lineHeight: 1.6 }}>
            IKAS selects questions using Bayesian Knowledge Tracing and Item Response Theory.
            Your answer here will update the mastery estimate for this concept at the{' '}
            <strong style={{ color: getLevelColor(currentQuestion.level) }}>{currentQuestion.level}</strong> level.
          </p>
        </div>
      </div>
    </div>
  );
};

export default TestPage;
