import React, { useEffect, useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { toast } from 'sonner';
import { ChevronLeft, Plus, PlayCircle, Tv } from 'lucide-react';
import { api } from '../../lib/api';

export default function AdminMatchControl() {
  const nav = useNavigate();
  const [matches, setMatches] = useState([]);
  const [turfs, setTurfs] = useState([]);
  const [referees, setReferees] = useState([]);
  const [showForm, setShowForm] = useState(false);
  const [form, setForm] = useState({ home_team: 'FC Powai', away_team: 'Andheri United', turf_id: '', scheduled_at: '', referee_id: '' });

  const load = () => {
    api.get('/matches').then((r) => setMatches(r.data));
    api.get('/turfs').then((r) => setTurfs(r.data));
    api.get('/admin/users?role=referee').then((r) => setReferees(r.data));
  };
  useEffect(() => { load(); }, []);

  const submit = async (e) => {
    e.preventDefault();
    try {
      const r = await api.post('/matches', { ...form, scheduled_at: new Date(form.scheduled_at).toISOString() });
      toast.success('Match scheduled. Open VAR Room → Start Camera.');
      setShowForm(false);
      load();
      nav(`/admin/var/${r.data.id}`);
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Failed');
    }
  };

  const startMatch = async (id) => {
    nav(`/admin/var/${id}`);
  };

  return (
    <div className="min-h-screen bg-bg" data-testid="admin-match-control-page">
      <header className="border-b border-line">
        <div className="max-w-6xl mx-auto px-6 py-4 flex items-center justify-between">
          <Link to="/admin" className="font-mono text-[10px] uppercase tracking-widest text-ink-muted flex items-center gap-1 hover:text-white" data-testid="back-to-admin"><ChevronLeft className="w-3 h-3" /> Control Room</Link>
          <div className="font-display text-2xl tracking-wider">MATCH CONTROL</div>
          <button data-testid="schedule-match-btn" onClick={() => setShowForm(true)} className="bg-accent-green text-black font-bold px-3 h-9 inline-flex items-center gap-1 font-mono uppercase text-xs tracking-widest hover:bg-[#00C853]">
            <Plus className="w-4 h-4" /> Schedule Match
          </button>
        </div>
      </header>

      <main className="max-w-6xl mx-auto px-6 py-6">
        <div className="font-mono text-[10px] uppercase tracking-widest text-ink-muted mb-2">CAMERA-CONTROLLED MATCHES</div>
        <div className="text-sm text-ink-muted mb-4">When you click <span className="text-accent-green font-bold">Open VAR Room</span> on a match, the turf camera goes live. Use <span className="text-accent-amber">Start Match</span> in the VAR room to begin recording.</div>

        <div className="space-y-2" data-testid="matches-list">
          {matches.map((m) => (
            <div key={m.id} className="bg-bg-card border border-line p-4 flex items-center gap-4">
              <div className={`px-2 py-0.5 font-mono text-[10px] uppercase tracking-widest ${m.status === 'live' ? 'bg-accent-red text-black font-bold animate-pulse-red' : m.status === 'complete' ? 'bg-bg-elevated text-ink-muted' : 'bg-accent-amber text-black font-bold'}`}>
                {m.status}
              </div>
              <div className="flex-1">
                <div className="font-display text-lg">{m.home_team.toUpperCase()} vs {m.away_team.toUpperCase()}</div>
                <div className="font-mono text-[10px] uppercase tracking-widest text-ink-muted">{m.turf_name} · {new Date(m.scheduled_at).toLocaleString('en-IN')}</div>
              </div>
              {m.status === 'live' && (
                <button data-testid={`watch-${m.id}`} onClick={() => nav(`/broadcast/${m.id}`)} className="border border-line h-9 px-3 font-mono uppercase text-xs tracking-widest hover:border-accent-amber flex items-center gap-1">
                  <Tv className="w-3.5 h-3.5" /> Watch
                </button>
              )}
              <button data-testid={`open-var-${m.id}`} onClick={() => startMatch(m.id)} className="bg-accent-green text-black font-bold h-9 px-4 font-mono uppercase text-xs tracking-widest hover:bg-[#00C853] flex items-center gap-1 text-white">
                <PlayCircle className="w-3.5 h-3.5" /> {m.status === 'live' ? 'Continue VAR' : 'Open VAR Room'}
              </button>
            </div>
          ))}
        </div>
      </main>

      {showForm && (
        <div className="fixed inset-0 bg-black/80 flex items-center justify-center z-50 p-4" data-testid="schedule-match-modal">
          <form onSubmit={submit} className="bg-bg-card border border-line w-full max-w-md p-6 space-y-3">
            <div className="font-display text-2xl">SCHEDULE MATCH</div>
            <input data-testid="m-home" placeholder="Home Team" required value={form.home_team} onChange={(e) => setForm({...form, home_team: e.target.value})} className="w-full bg-bg border border-line h-12 px-3 outline-none focus:border-accent-green" />
            <input data-testid="m-away" placeholder="Away Team" required value={form.away_team} onChange={(e) => setForm({...form, away_team: e.target.value})} className="w-full bg-bg border border-line h-12 px-3 outline-none focus:border-accent-green" />
            <select data-testid="m-turf" required value={form.turf_id} onChange={(e) => setForm({...form, turf_id: e.target.value})} className="w-full bg-bg border border-line h-12 px-3 outline-none focus:border-accent-green">
              <option value="">— Select Turf —</option>
              {turfs.map((t) => <option key={t.id} value={t.id}>{t.name} · {t.city}</option>)}
            </select>
            <select data-testid="m-ref" value={form.referee_id} onChange={(e) => setForm({...form, referee_id: e.target.value})} className="w-full bg-bg border border-line h-12 px-3 outline-none focus:border-accent-green">
              <option value="">— Referee (optional) —</option>
              {referees.map((r) => <option key={r.id} value={r.id}>{r.name}</option>)}
            </select>
            <input data-testid="m-time" type="datetime-local" required value={form.scheduled_at} onChange={(e) => setForm({...form, scheduled_at: e.target.value})} className="w-full bg-bg border border-line h-12 px-3 outline-none focus:border-accent-green" />
            <div className="flex gap-2 pt-2">
              <button data-testid="m-cancel" type="button" onClick={() => setShowForm(false)} className="flex-1 border border-line h-12 font-mono uppercase tracking-widest hover:border-white">Cancel</button>
              <button data-testid="m-submit" type="submit" className="flex-1 bg-accent-green text-black font-bold h-12 font-display text-xl tracking-widest uppercase hover:bg-[#00C853]">Schedule</button>
            </div>
          </form>
        </div>
      )}
    </div>
  );
}
