import React from 'react';
import { X, CheckCircle, AlertTriangle, AlertCircle, Info } from 'lucide-react';
import { useToastStore, Toast as ToastItem, ToastType } from '../store/toastStore';

const TOAST_STYLES: Record<ToastType, { border: string; icon: React.ReactNode; accent: string }> = {
  error: {
    border: 'var(--accent-red, #ef4444)',
    accent: 'var(--accent-red, #ef4444)',
    icon: <AlertCircle size={18} />,
  },
  warning: {
    border: 'var(--accent-amber, #f59e0b)',
    accent: 'var(--accent-amber, #f59e0b)',
    icon: <AlertTriangle size={18} />,
  },
  success: {
    border: 'var(--accent-green, #10b981)',
    accent: 'var(--accent-green, #10b981)',
    icon: <CheckCircle size={18} />,
  },
  info: {
    border: 'var(--accent-blue, #3b82f6)',
    accent: 'var(--accent-blue, #3b82f6)',
    icon: <Info size={18} />,
  },
};

const ToastCard: React.FC<{ toast: ToastItem }> = ({ toast }) => {
  const removeToast = useToastStore((s) => s.removeToast);
  const style = TOAST_STYLES[toast.type];

  return (
    <div
      onClick={() => removeToast(toast.id)}
      style={{
        display: 'flex',
        alignItems: 'flex-start',
        gap: '0.75rem',
        padding: '0.875rem 1rem',
        borderRadius: '10px',
        background: 'var(--bg-secondary, rgba(26,29,46,0.95))',
        backdropFilter: 'blur(12px)',
        border: `1px solid ${style.border}`,
        boxShadow: '0 8px 24px rgba(0,0,0,0.4)',
        cursor: 'pointer',
        maxWidth: '360px',
        minWidth: '260px',
        animation: 'toastSlideIn 0.25s ease',
      }}
      title="Click to dismiss"
    >
      <span style={{ color: style.accent, flexShrink: 0, marginTop: '1px' }}>{style.icon}</span>
      <span
        style={{
          flex: 1,
          fontSize: '0.875rem',
          color: 'var(--text-primary, #e2e8f0)',
          lineHeight: 1.45,
          wordBreak: 'break-word',
        }}
      >
        {toast.message}
      </span>
      <button
        onClick={(e) => { e.stopPropagation(); removeToast(toast.id); }}
        style={{
          background: 'none',
          border: 'none',
          color: 'var(--text-muted, #6b7280)',
          cursor: 'pointer',
          padding: 0,
          flexShrink: 0,
          display: 'flex',
          alignItems: 'center',
        }}
        aria-label="Dismiss"
      >
        <X size={14} />
      </button>
    </div>
  );
};

const Toast: React.FC = () => {
  const toasts = useToastStore((s) => s.toasts);

  if (toasts.length === 0) return null;

  return (
    <>
      <style>{`
        @keyframes toastSlideIn {
          from { opacity: 0; transform: translateX(20px); }
          to   { opacity: 1; transform: translateX(0); }
        }
      `}</style>
      <div
        style={{
          position: 'fixed',
          bottom: '1.5rem',
          right: '1.5rem',
          zIndex: 9999,
          display: 'flex',
          flexDirection: 'column',
          gap: '0.5rem',
          pointerEvents: 'auto',
        }}
        aria-live="polite"
        aria-atomic="false"
      >
        {toasts.map((toast) => (
          <ToastCard key={toast.id} toast={toast} />
        ))}
      </div>
    </>
  );
};

export default Toast;
