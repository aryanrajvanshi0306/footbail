import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Plus, Calendar, MapPin } from 'lucide-react';
import { api } from '../lib/api';

export default function Matches() {
  const nav = useNavigate();
  const [tab, setTab] = useState('scheduled');
  const [matches, setMatches] = useState([]);

  useEffect(() => { api.get('/matches').then((r) => setMatches(r.data)); }, []);

  const filtered = matches.filter((m) => tab === 'scheduled' ? m.status !== 'complete' : m.status === 'complete');

  return (
    <div className="px-4 pt-4 pb-24" data-testid="matches-page">
      <div className="flex items-center justify-between mb-4">
        <div>
          <div className="font-mono text-[10px] uppercase tracking-widest text-ink-muted">Matchday Engine</div>
          <div className="font-display text-3xl">MATCHES</div>
        </div>
        <button
          data-testid="create-match-btn"
          onClick={() => nav('/matches/create')}
          className="flex items-center gap-1 bg-accent-green text-black font-bold px-3 h-10 font-mono text-xs uppercase tracking-widest hover:bg-[#00C853]"
        >
          <Plus className="w-4 h-4" /> Create
        </button>
      </div>

      <div className="flex border border-line mb-4" data-testid="match-tabs">
        <button data-testid="tab-scheduled" onClick={() => setTab('scheduled')} className={`flex-1 h-10 font-mono uppercase text-xs tracking-widest ${tab === 'scheduled' ? 'bg-accent-green text-black font-bold' : 'text-ink-muted'}`}>Scheduled</button>
        <button data-testid="tab-past" onClick={() => setTab('past')} className={`flex-1 h-10 font-mono uppercase text-xs tracking-widest ${tab === 'past' ? 'bg-accent-green text-black font-bold' : 'text-ink-muted'}`}>Past</button>
      </div>

      {filtered.length === 0 && (
        <div className="text-center text-ink-muted py-12 border border-dashed border-line">
          No {tab} matches. Hit Create to schedule one.
        </div>
      )}

      <div className="space-y-3">
        {filtered.map((m) => (
          <button
            key={m.id}
            data-testid={`match-${m.id}`}
            onClick={() => nav(`/matches/${m.id}`)}
            className="w-full text-left bg-bg-card border border-line p-4 hover:border-accent-green"
          >
            <div className="flex items-center justify-between mb-2">
              <span className={`font-mono text-[10px] uppercase tracking-widest px-2 py-0.5 ${m.status === 'live' ? 'bg-accent-red text-black font-bold animate-pulse-red' : m.status === 'complete' ? 'bg-bg-elevated text-ink-muted' : 'bg-accent-amber text-black font-bold'}`}>
                {m.status}
              </span>
              <span className="font-mono text-xs text-ink-muted">{m.format}</span>
            </div>
            <div className="grid grid-cols-3 items-center">
              <div className="text-right">
                <div className="font-display text-xl">{m.home_team.toUpperCase()}</div>
              </div>
              <div className="text-center">
                {m.status === 'complete' ? (
                  <div className="font-mono font-bold text-2xl">{m.score?.home} <span className="text-ink-muted">:</span> {m.score?.away}</div>
                ) : (
                  <div className="font-mono text-xs text-accent-amber">VS</div>
                )}
              </div>
              <div className="text-left">
                <div className="font-display text-xl">{m.away_team.toUpperCase()}</div>
              </div>
            </div>
            <div className="flex items-center gap-3 mt-3 font-mono text-[10px] uppercase tracking-widest text-ink-muted">
              <span className="flex items-center gap-1"><Calendar className="w-3 h-3" /> {new Date(m.scheduled_at).toLocaleString('en-IN', { dateStyle: 'medium', timeStyle: 'short' })}</span>
              <span className="flex items-center gap-1"><MapPin className="w-3 h-3" /> {m.turf_name}</span>
            </div>
          </button>
        ))}
      </div>
    </div>
  );
}
