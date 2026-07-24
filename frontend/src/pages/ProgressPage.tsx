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
