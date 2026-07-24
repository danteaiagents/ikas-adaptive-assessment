import React from 'react';
import { NavLink } from 'react-router-dom';
import { LayoutDashboard, BarChart2, BookOpen } from 'lucide-react';

const Sidebar: React.FC = () => {
  const navStyle = ({ isActive }: { isActive: boolean }) => ({
    display: 'flex',
    alignItems: 'center',
    gap: '0.75rem',
    padding: '1rem 1.5rem',
    color: isActive ? 'var(--text-primary)' : 'var(--text-secondary)',
    background: isActive ? 'var(--bg-glass)' : 'transparent',
    textDecoration: 'none',
    borderLeft: isActive ? '3px solid var(--accent-blue)' : '3px solid transparent',
    transition: 'all 0.2s',
    fontWeight: isActive ? 500 : 400
  });

  return (
    <aside style={{ width: '250px', background: 'var(--bg-card)', borderRight: '1px solid var(--border-glass)', paddingTop: '2rem' }}>
      <nav style={{ display: 'flex', flexDirection: 'column' }}>
        <NavLink to="/dashboard" style={navStyle}>
          <LayoutDashboard size={20} /> Dashboard
        </NavLink>
        <NavLink to="/progress" style={navStyle}>
          <BarChart2 size={20} /> Progress
        </NavLink>
        <div style={{ margin: '2rem 1.5rem 1rem', fontSize: '0.75rem', textTransform: 'uppercase', color: 'var(--text-muted)', fontWeight: 600, letterSpacing: '0.5px' }}>
          Subjects
        </div>
        <div style={{ padding: '0.5rem 1.5rem', color: 'var(--text-secondary)', fontSize: '0.9rem', display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
          <BookOpen size={16} /> Artificial Intelligence
        </div>
      </nav>
    </aside>
  );
};

export default Sidebar;
