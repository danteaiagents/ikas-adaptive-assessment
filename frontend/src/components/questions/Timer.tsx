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
  
  const isWarning = timeRemaining < 300; 

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
