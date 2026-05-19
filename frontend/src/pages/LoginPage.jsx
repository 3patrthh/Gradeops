import React, { useState } from 'react';
import { login } from '../services/authService';

function LoginPage({ onLogin }) {
  const [role, setRole] = useState('instructor');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);

  const handleLogin = async () => {
    if (!email || !password) return;
    setLoading(true);

    try {
      await login({ email, password, role });
      onLogin(role);
    } catch (error) {
      console.warn('FastAPI auth not available; using prototype login.', error);
      onLogin(role);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="login-wrap">
      <div className="login-card fade-up">
        <div className="login-logo">Grade<span>Ops</span></div>
        <div className="login-subtitle">AI-Powered Exam Grading Pipeline</div>

        <div style={{ fontSize: 12, color: 'var(--muted)', marginBottom: 12, fontFamily: 'var(--ff-mono)', textTransform: 'uppercase', letterSpacing: .6 }}>Sign in as</div>
        <div className="role-tabs">
          <button className={`role-tab ${role === 'instructor' ? 'active' : ''}`} onClick={() => setRole('instructor')}>
            🎓 Instructor
          </button>
          <button className={`role-tab ${role === 'ta' ? 'active' : ''}`} onClick={() => setRole('ta')}>
            📋 Teaching Assistant
          </button>
        </div>

        <div className="form-group">
          <div className="form-label">Email</div>
          <input type="email" placeholder={role === 'instructor' ? 'prof@university.edu' : 'ta@university.edu'}
            value={email} onChange={e => setEmail(e.target.value)}
            onKeyDown={e => e.key === 'Enter' && handleLogin()}
          />
        </div>
        <div className="form-group">
          <div className="form-label">Password</div>
          <input type="password" placeholder="••••••••" value={password}
            onChange={e => setPassword(e.target.value)}
            onKeyDown={e => e.key === 'Enter' && handleLogin()}
          />
        </div>

        <button className="btn-primary" onClick={handleLogin} disabled={loading}>
          {loading ? 'Signing in…' : 'Sign In →'}
        </button>

        <div className="demo-hint">
          <strong style={{ color: 'var(--gold)' }}>Demo</strong> — use any email + password.<br/>
          Select role above to switch between Instructor and TA views.
        </div>
      </div>
    </div>
  );
}

// ─── OVERVIEW TAB ─────────────────────────────────────────────────────────

export default LoginPage;
