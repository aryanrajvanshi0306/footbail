import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { toast } from 'sonner';
import { api, saveAuth } from '../lib/api';

const POSITIONS = ['GK', 'CB', 'LB', 'RB', 'CM', 'CDM', 'CAM', 'LW', 'RW', 'ST'];
const CITIES = ['Mumbai', 'Delhi', 'Bangalore', 'Hyderabad', 'Chennai', 'Kolkata', 'Pune', 'Ahmedabad'];

export default function Register() {
  const nav = useNavigate();
  const [step, setStep] = useState(1);
  const [role, setRole] = useState('player');
  const [form, setForm] = useState({ email: '', password: '', name: '', phone: '', position: 'CM', city: 'Mumbai' });
  const [loading, setLoading] = useState(false);

  const setF = (k, v) => setForm((s) => ({ ...s, [k]: v }));

  const submit = async () => {
    setLoading(true);
    try {
      const body = { ...form, role };
      const r = await api.post('/auth/register', body);
      saveAuth(r.data.access_token, r.data.user);
      toast.success(`Welcome, ${r.data.user.name}!`);
      nav(r.data.user.role === 'coach' ? '/coach/onboard' : '/home');
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Registration failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-bg flex flex-col" data-testid="register-page">
      <header className="border-b border-line p-4">
        <Link to="/login" className="font-mono text-xs uppercase tracking-widest text-ink-muted hover:text-white" data-testid="back-to-login">← Back</Link>
      </header>

      <main className="flex-1 max-w-md mx-auto w-full p-6">
        <div className="mb-8">
          <div className="font-mono text-xs uppercase tracking-widest text-accent-amber">Step {step} of 3</div>
          <div className="font-display text-4xl mt-1">
            {step === 1 && 'Pick Your Role'}
            {step === 2 && 'Your Details'}
            {step === 3 && 'Lock & Load'}
          </div>
          <div className="text-sm text-ink-muted mt-2 font-mono">
            Onboarding is currently open to <span className="text-white">PLAYERS</span> &amp; <span className="text-white">COACHES</span> only.
          </div>
        </div>

        {step === 1 && (
          <div className="space-y-3" data-testid="role-selector">
            {[
              { v: 'player', t: 'Player', d: 'I play. I track. I climb the leaderboard.' },
              { v: 'coach', t: 'Coach', d: 'I train players, build squads, run sessions.' },
            ].map((r) => (
              <button
                key={r.v}
                data-testid={`role-${r.v}`}
                onClick={() => setRole(r.v)}
                className={`w-full text-left p-5 border-2 transition-colors ${
                  role === r.v ? 'border-accent-green bg-accent-green text-black/10' : 'border-line hover:border-ink-muted'
                }`}
              >
                <div className="font-display text-3xl tracking-wider">{r.t.toUpperCase()}</div>
                <div className="text-sm text-ink-muted mt-1">{r.d}</div>
              </button>
            ))}
            <button data-testid="role-next-btn" onClick={() => setStep(2)} className="w-full mt-6 bg-accent-green text-black font-bold h-12 font-display text-xl tracking-widest uppercase hover:bg-[#00C853]">
              Continue →
            </button>
          </div>
        )}

        {step === 2 && (
          <div className="space-y-3" data-testid="details-step">
            <Field label="Full Name" testid="reg-name">
              <input data-testid="reg-name-input" value={form.name} onChange={(e) => setF('name', e.target.value)} className="w-full bg-bg-card border border-line h-12 px-4 text-white focus:border-accent-green outline-none" />
            </Field>
            <Field label="Email" testid="reg-email">
              <input data-testid="reg-email-input" type="email" value={form.email} onChange={(e) => setF('email', e.target.value)} className="w-full bg-bg-card border border-line h-12 px-4 text-white focus:border-accent-green outline-none" />
            </Field>
            <Field label="Phone (optional)" testid="reg-phone">
              <input data-testid="reg-phone-input" value={form.phone} onChange={(e) => setF('phone', e.target.value)} className="w-full bg-bg-card border border-line h-12 px-4 text-white focus:border-accent-green outline-none" placeholder="+91" />
            </Field>
            <Field label="City" testid="reg-city">
              <select data-testid="reg-city-input" value={form.city} onChange={(e) => setF('city', e.target.value)} className="w-full bg-bg-card border border-line h-12 px-4 text-white focus:border-accent-green outline-none">
                {CITIES.map((c) => <option key={c}>{c}</option>)}
              </select>
            </Field>
            {role === 'player' && (
              <Field label="Position" testid="reg-position">
                <select data-testid="reg-position-input" value={form.position} onChange={(e) => setF('position', e.target.value)} className="w-full bg-bg-card border border-line h-12 px-4 text-white focus:border-accent-green outline-none">
                  {POSITIONS.map((p) => <option key={p}>{p}</option>)}
                </select>
              </Field>
            )}
            <div className="flex gap-2 pt-4">
              <button data-testid="back-btn" onClick={() => setStep(1)} className="flex-1 border border-line h-12 font-mono uppercase tracking-widest hover:border-white">← Back</button>
              <button
                data-testid="next-btn"
                disabled={!form.name || !form.email}
                onClick={() => setStep(3)}
                className="flex-1 bg-accent-green text-black font-bold h-12 font-display text-xl tracking-widest uppercase disabled:opacity-50 hover:bg-[#00C853]"
              >
                Next →
              </button>
            </div>
          </div>
        )}

        {step === 3 && (
          <div className="space-y-3" data-testid="password-step">
            <Field label="Password (min 4 chars)" testid="reg-password">
              <input data-testid="reg-password-input" type="password" value={form.password} onChange={(e) => setF('password', e.target.value)} className="w-full bg-bg-card border border-line h-12 px-4 text-white focus:border-accent-green outline-none" />
            </Field>
            <div className="bg-bg-card border border-line p-4 my-4">
              <div className="font-mono text-[10px] uppercase tracking-widest text-ink-muted">SUMMARY</div>
              <div className="mt-2 space-y-1 font-mono text-sm">
                <div>{form.name} · {role.toUpperCase()}</div>
                <div className="text-ink-muted">{form.email}</div>
                <div className="text-ink-muted">{form.city}{role === 'player' ? ` · ${form.position}` : ''}</div>
              </div>
            </div>
            <div className="flex gap-2">
              <button data-testid="back-btn-2" onClick={() => setStep(2)} className="flex-1 border border-line h-12 font-mono uppercase tracking-widest hover:border-white">← Back</button>
              <button
                data-testid="register-submit-btn"
                disabled={loading || form.password.length < 4}
                onClick={submit}
                className="flex-1 bg-accent-green text-black font-bold h-12 font-display text-xl tracking-widest uppercase disabled:opacity-50 hover:bg-[#00C853]"
              >
                {loading ? 'Signing up...' : 'Sign Up'}
              </button>
            </div>
          </div>
        )}
      </main>
    </div>
  );
}

function Field({ label, children, testid }) {
  return (
    <div data-testid={testid}>
      <label className="font-mono text-[10px] uppercase tracking-widest text-ink-muted">{label}</label>
      <div className="mt-1">{children}</div>
    </div>
  );
}
