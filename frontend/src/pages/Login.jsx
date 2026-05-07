import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { toast } from 'sonner';
import { Mail, Smartphone, Loader2 } from 'lucide-react';
import { api, saveAuth } from '../lib/api';

const TABS = [
  { id: 'email', label: 'Email', icon: Mail, testid: 'tab-email' },
  { id: 'otp',   label: 'Phone OTP', icon: Smartphone, testid: 'tab-otp' },
];

export default function Login() {
  const nav = useNavigate();
  const [tab, setTab] = useState('email');

  // Email state
  const [email, setEmail] = useState('arjun@demo.in');
  const [password, setPassword] = useState('demo123');

  // OTP state
  const [phone, setPhone] = useState('');
  const [otp, setOtp] = useState('');
  const [otpSent, setOtpSent] = useState(false);
  const [otpHint, setOtpHint] = useState('');

  const [loading, setLoading] = useState(false);

  const submitEmail = async (e) => {
    e.preventDefault();
    setLoading(true);
    try {
      const r = await api.post('/auth/login', { email, password });
      saveAuth(r.data.access_token, r.data.user);
      toast.success(`Welcome back, ${r.data.user.name}`);
      nav(r.data.user.role === 'admin' ? '/admin'
          : r.data.user.role === 'coach' ? '/coach/onboard'
          : '/home');
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Login failed');
    } finally {
      setLoading(false);
    }
  };

  const sendOtp = async (e) => {
    e?.preventDefault();
    setLoading(true);
    try {
      const r = await api.post('/auth/otp/send', { phone });
      setOtpSent(true);
      setOtpHint(r.data?.dev_otp || '');
      toast.success(r.data?.message || 'OTP sent');
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Failed to send OTP');
    } finally {
      setLoading(false);
    }
  };

  const verifyOtp = async (e) => {
    e.preventDefault();
    setLoading(true);
    try {
      const r = await api.post('/auth/otp/verify', { phone, otp, role: 'player', city: 'Mumbai' });
      saveAuth(r.data.access_token, r.data.user);
      toast.success(`Welcome ${r.data.user.name}`);
      nav('/home');
    } catch (err) {
      toast.error(err.response?.data?.detail || 'OTP verification failed');
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

        <div className="grid grid-cols-2 gap-1 mb-4 bg-black/40 p-1 rounded-lg" data-testid="auth-tabs">
          {TABS.map(({ id, label, icon: Icon, testid }) => (
            <button
              key={id}
              data-testid={testid}
              onClick={() => { setTab(id); setOtpSent(false); setOtp(''); }}
              className={`px-3 py-2 text-xs font-mono uppercase tracking-widest rounded transition-all flex items-center justify-center gap-1.5 ${
                tab === id ? 'bg-accent-green text-black font-bold' : 'text-ink-muted hover:text-white'
              }`}
            >
              <Icon className="w-3.5 h-3.5" /> {label}
            </button>
          ))}
        </div>

        {tab === 'email' && (
          <form onSubmit={submitEmail} className="space-y-3" data-testid="login-form">
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
        )}

        {tab === 'otp' && (
          <div className="space-y-3" data-testid="otp-form">
            <div>
              <label className="font-mono text-[10px] uppercase tracking-widest text-ink-muted">Mobile Number</label>
              <input
                data-testid="otp-phone-input"
                type="tel"
                value={phone}
                onChange={(e) => setPhone(e.target.value)}
                placeholder="9876543210"
                disabled={otpSent}
                className="w-full mt-1 bg-black/60 border border-line h-12 px-4 text-white focus:border-accent-green outline-none disabled:opacity-60"
                required
              />
            </div>

            {!otpSent && (
              <button
                data-testid="otp-send-btn"
                disabled={loading || phone.replace(/\D/g, '').length < 10}
                onClick={sendOtp}
                className="w-full bg-accent-green text-black h-12 font-display text-xl tracking-widest uppercase hover:bg-[#00C853] disabled:opacity-50 transition-colors font-bold flex items-center justify-center gap-2"
              >
                {loading ? <Loader2 className="w-5 h-5 animate-spin" /> : null}
                {loading ? 'Sending…' : 'Send OTP'}
              </button>
            )}

            {otpSent && (
              <form onSubmit={verifyOtp} className="space-y-3">
                <div>
                  <label className="font-mono text-[10px] uppercase tracking-widest text-ink-muted">6-digit OTP</label>
                  <input
                    data-testid="otp-code-input"
                    type="text"
                    inputMode="numeric"
                    pattern="[0-9]{6}"
                    maxLength={6}
                    value={otp}
                    onChange={(e) => setOtp(e.target.value.replace(/\D/g, ''))}
                    placeholder="••••••"
                    className="w-full mt-1 bg-black/60 border border-line h-12 px-4 text-white text-center font-mono text-xl tracking-[0.5em] focus:border-accent-green outline-none"
                    required
                    autoFocus
                  />
                  {otpHint && (
                    <div data-testid="otp-dev-hint" className="text-[10px] font-mono text-accent-amber mt-1">
                      DEV mode — use OTP: <b className="text-accent-green">{otpHint}</b>
                    </div>
                  )}
                </div>
                <button
                  data-testid="otp-verify-btn"
                  disabled={loading || otp.length !== 6}
                  className="w-full bg-accent-green text-black h-12 font-display text-xl tracking-widest uppercase hover:bg-[#00C853] disabled:opacity-50 transition-colors font-bold"
                >
                  {loading ? 'Verifying…' : 'Verify & Enter'}
                </button>
                <button
                  type="button"
                  data-testid="otp-resend-btn"
                  onClick={() => { setOtpSent(false); setOtp(''); }}
                  className="w-full text-xs font-mono uppercase tracking-widest text-ink-muted hover:text-accent-green"
                >
                  ← Change number
                </button>
              </form>
            )}
          </div>
        )}

        {tab === 'email' && (
          <div className="mt-6 grid grid-cols-3 gap-2">
            <button data-testid="quick-player-btn" onClick={() => quick('arjun@demo.in', 'demo123')} className="border border-line p-2 text-xs font-mono uppercase hover:border-accent-green hover:text-accent-green transition-colors rounded-lg">Player</button>
            <button data-testid="quick-coach-btn" onClick={() => quick('ravi@coach.in', 'demo123')} className="border border-line p-2 text-xs font-mono uppercase hover:border-accent-blue hover:text-accent-blue transition-colors rounded-lg">Coach</button>
            <button data-testid="quick-admin-btn" onClick={() => quick('admin@footbail.in', 'admin123')} className="border border-line p-2 text-xs font-mono uppercase hover:border-accent-amber hover:text-accent-amber transition-colors rounded-lg">Admin</button>
          </div>
        )}

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
