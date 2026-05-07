import React, { useEffect, useState } from 'react';
import { toast } from 'sonner';
import { Megaphone, X, Plus, Clock, MapPin } from 'lucide-react';
import { api, getUser } from '../lib/api';
import { getCityTheme } from '../lib/cityTheme';

/**
 * Module 16 — LFG (Looking For Game) widget.
 * Players broadcast a 30min–3hr availability window. City-scoped.
 */
export default function LFGWidget() {
  const me = getUser();
  const theme = getCityTheme(me?.city || 'Mumbai');
  const [list, setList] = useState([]);
  const [showForm, setShowForm] = useState(false);
  const [form, setForm] = useState({
    format: '5v5',
    skill_bracket: 'intermediate',
    earliest_offset_min: 30,
    duration_hr: 2,
    spots: 1,
    note: '',
  });

  const load = () => api.get(`/lfg?city=${encodeURIComponent(me?.city || 'Mumbai')}`).then((r) => setList(r.data));
  useEffect(() => { load(); }, [me?.city]);

  const submit = async (e) => {
    e.preventDefault();
    const earliest = new Date(Date.now() + form.earliest_offset_min * 60_000);
    const latest = new Date(earliest.getTime() + form.duration_hr * 3600_000);
    try {
      await api.post('/lfg', {
        city: me?.city || 'Mumbai',
        format: form.format,
        skill_bracket: form.skill_bracket,
        earliest: earliest.toISOString(),
        latest: latest.toISOString(),
        spots: form.spots,
        note: form.note,
      });
      toast.success('LFG broadcast — players in your city can see this for the next 3 hours');
      setShowForm(false);
      setForm({ format: '5v5', skill_bracket: 'intermediate', earliest_offset_min: 30, duration_hr: 2, spots: 1, note: '' });
      load();
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Failed');
    }
  };

  const cancel = async (id) => {
    await api.delete(`/lfg/${id}`);
    toast.message('LFG cancelled');
    load();
  };

  const formatTime = (iso) => new Date(iso).toLocaleTimeString('en-IN', { hour: '2-digit', minute: '2-digit', hour12: true });

  return (
    <div className="bg-bg-card border border-line p-4" data-testid="lfg-widget">
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2">
          <Megaphone className="w-4 h-4" style={{ color: theme.accent }} />
          <span className="font-mono text-[10px] uppercase tracking-widest" style={{ color: theme.accent }}>
            LOOKING FOR GAME · {me?.city?.toUpperCase() || 'MUMBAI'}
          </span>
        </div>
        <button
          data-testid="open-lfg-form"
          onClick={() => setShowForm(!showForm)}
          className="flex items-center gap-1 px-2 h-7 font-mono text-[10px] uppercase tracking-widest border border-line hover:border-accent-green hover:text-accent-green"
        >
          <Plus className="w-3 h-3" /> Broadcast
        </button>
      </div>

      {showForm && (
        <form onSubmit={submit} className="bg-bg-elevated border border-line p-3 mb-3 space-y-2" data-testid="lfg-form">
          <div className="grid grid-cols-2 gap-2">
            <select data-testid="lfg-format" value={form.format} onChange={(e) => setForm({ ...form, format: e.target.value })} className="bg-bg border border-line h-9 px-2 text-xs font-mono outline-none focus:border-accent-green">
              <option value="5v5">5v5</option><option value="7v7">7v7</option><option value="11v11">11v11</option>
            </select>
            <select data-testid="lfg-skill" value={form.skill_bracket} onChange={(e) => setForm({ ...form, skill_bracket: e.target.value })} className="bg-bg border border-line h-9 px-2 text-xs font-mono outline-none focus:border-accent-green">
              <option value="casual">Casual</option><option value="intermediate">Intermediate</option><option value="competitive">Competitive</option>
            </select>
          </div>
          <div className="grid grid-cols-3 gap-2">
            <Sel testid="lfg-when" label="Starts" value={form.earliest_offset_min} onChange={(v) => setForm({ ...form, earliest_offset_min: v })} options={[
              [30, 'in 30m'], [60, 'in 1h'], [120, 'in 2h'], [240, 'in 4h'],
            ]} />
            <Sel testid="lfg-dur" label="Window" value={form.duration_hr} onChange={(v) => setForm({ ...form, duration_hr: v })} options={[[1, '1h'], [2, '2h'], [3, '3h']]} />
            <Sel testid="lfg-spots" label="Need" value={form.spots} onChange={(v) => setForm({ ...form, spots: v })} options={[[1, '1 spot'], [2, '2 spots'], [3, '3 spots'], [5, '5 spots']]} />
          </div>
          <input
            data-testid="lfg-note"
            placeholder="Note (turf, vibe…) — optional"
            value={form.note}
            onChange={(e) => setForm({ ...form, note: e.target.value })}
            className="w-full bg-bg border border-line h-9 px-2 text-xs outline-none focus:border-accent-green"
          />
          <button
            type="submit"
            data-testid="lfg-submit"
            className="w-full h-10 font-mono text-xs uppercase tracking-widest font-bold"
            style={{ background: theme.accent, color: '#0A0F1E' }}
          >
            Broadcast to {me?.city || 'Mumbai'}
          </button>
        </form>
      )}

      {list.length === 0 ? (
        <div className="text-center py-6 text-ink-muted font-mono text-[10px] uppercase tracking-widest">
          No active broadcasts in your city. Be first.
        </div>
      ) : (
        <div className="space-y-2" data-testid="lfg-list">
          {list.map((l) => (
            <div key={l.id} className="bg-bg-elevated border border-line p-3 flex items-center gap-3">
              <div className="w-9 h-9 rounded-full bg-bg flex items-center justify-center font-display font-bold text-base" style={{ color: theme.accent }}>
                {l.user_name?.[0]}
              </div>
              <div className="flex-1 min-w-0">
                <div className="font-bold text-sm truncate">{l.user_name}</div>
                <div className="font-mono text-[10px] uppercase tracking-widest text-ink-muted truncate">
                  {l.format} · {l.skill_bracket} · need {l.spots}
                </div>
                <div className="flex items-center gap-2 font-mono text-[10px] uppercase tracking-widest text-ink-muted mt-1">
                  <Clock className="w-3 h-3" /> {formatTime(l.earliest)} – {formatTime(l.latest)}
                  {l.note && <><span>·</span><span className="truncate">{l.note}</span></>}
                </div>
              </div>
              {l.user_id === me?.id ? (
                <button
                  data-testid={`lfg-cancel-${l.id}`}
                  onClick={() => cancel(l.id)}
                  className="text-ink-muted hover:text-accent-red"
                  title="Cancel"
                >
                  <X className="w-4 h-4" />
                </button>
              ) : (
                <button
                  data-testid={`lfg-join-${l.id}`}
                  onClick={() => toast.success(`Pinged ${l.user_name} — they'll DM you in the feed`)}
                  className="px-3 h-8 font-mono text-[10px] uppercase tracking-widest font-bold"
                  style={{ background: theme.accent, color: '#0A0F1E' }}
                >
                  I'm In
                </button>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

function Sel({ label, value, onChange, options, testid }) {
  return (
    <label className="block">
      <span className="font-mono text-[9px] uppercase tracking-widest text-ink-muted">{label}</span>
      <select data-testid={testid} value={value} onChange={(e) => onChange(parseInt(e.target.value))} className="w-full bg-bg border border-line h-9 px-2 text-xs font-mono outline-none focus:border-accent-green mt-0.5">
        {options.map(([v, l]) => <option key={v} value={v}>{l}</option>)}
      </select>
    </label>
  );
}
