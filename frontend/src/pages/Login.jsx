import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { toast } from 'sonner';
import { api, saveAuth } from '../lib/api';

export default function Login() {
  const nav = useNavigate();
  const [email, setEmail] = useState('arjun@demo.in');
  const [password, setPassword] = useState('demo123');
  const [loading, setLoading] = useState(false);

  const submit = async (e) => {
    e.preventDefault();
    setLoading(true);
    try {
      const r = await api.post('/auth/login', { email, password });
      saveAuth(r.data.access_token, r.data.user);
      toast.success(`Welcome back, ${r.data.user.name}`);
      nav(r.data.user.role === 'admin' ? '/admin' : '/home');
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Login failed');
    } finally {
      setLoading(false);
    }
  };

  const quick = (e, p) => { setEmail(e); setPassword(p); };

  return (
    <div className="min-h-screen relative flex items-end md:items-center justify-center" data-testid="login-page">
      <div
        className="absolute inset-0 bg-cover bg-center"
        style={{ backgroundImage: "url('https://images.unsplash.com/photo-1706675780107-7c43cc487928?crop=entropy&cs=srgb&fm=jpg&ixid=M3w3NTY2OTF8MHwxfHNlYXJjaHwyfHxmb290YmFsbCUyMHN0YWRpdW0lMjBuaWdodHxlbnwwfHx8fDE3NzgwNzY0MzV8MA&ixlib=rb-4.1.0&q=85')" }}
      />
      <div className="absolute inset-0 bg-gradient-to-t from-black via-black/80 to-black/30" />

      <div className="relative w-full max-w-md p-6 md:p-10 z-10">
        <div className="mb-8 grain relative">
          <div className="font-display text-7xl md:text-8xl leading-none tracking-tight font-bold">
            foot<span className="text-accent-green">bAI</span>l
          </div>
          <div className="font-mono text-xs uppercase tracking-[0.3em] text-accent-amber mt-2">
            India's AI Football OS · 2026
          </div>
        </div>

        <form onSubmit={submit} className="space-y-3" data-testid="login-form">
          <div>
            <label className="font-mono text-[10px] uppercase tracking-widest text-ink-muted">Email</label>
            <input
              data-testid="login-email-input"
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="w-full mt-1 bg-black/60 border border-line h-12 px-4 text-white focus:border-accent-green outline-none"
              required
            />
          </div>
          <div>
            <label className="font-mono text-[10px] uppercase tracking-widest text-ink-muted">Password</label>
            <input
              data-testid="login-password-input"
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="w-full mt-1 bg-black/60 border border-line h-12 px-4 text-white focus:border-accent-green outline-none"
              required
            />
          </div>
          <button
            data-testid="login-submit-btn"
            disabled={loading}
            className="w-full bg-accent-green text-black h-12 font-display text-xl tracking-widest uppercase hover:bg-[#00C853] disabled:opacity-50 transition-colors font-bold shadow-glow-green"
          >
            {loading ? 'Signing In...' : 'Kick Off'}
          </button>
        </form>

        <div className="mt-6 grid grid-cols-3 gap-2">
          <button data-testid="quick-player-btn" onClick={() => quick('arjun@demo.in', 'demo123')} className="border border-line p-2 text-xs font-mono uppercase hover:border-accent-green hover:text-accent-green transition-colors rounded-lg">Player</button>
          <button data-testid="quick-coach-btn" onClick={() => quick('ravi@coach.in', 'demo123')} className="border border-line p-2 text-xs font-mono uppercase hover:border-accent-blue hover:text-accent-blue transition-colors rounded-lg">Coach</button>
          <button data-testid="quick-admin-btn" onClick={() => quick('admin@footbail.in', 'admin123')} className="border border-line p-2 text-xs font-mono uppercase hover:border-accent-amber hover:text-accent-amber transition-colors rounded-lg">Admin</button>
        </div>

        <div className="mt-8 text-center text-sm text-ink-muted">
          New on the pitch?{' '}
          <Link data-testid="goto-register-link" to="/register" className="text-accent-green font-bold uppercase tracking-wider">
            Sign Up →
          </Link>
        </div>
      </div>
    </div>
  );
}
