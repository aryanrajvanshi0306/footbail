import React, { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { Calendar, MapPin, Tv, BarChart3 } from 'lucide-react';
import { api, getUser } from '../lib/api';
import { EVENT_META } from '../lib/constants';

export default function MatchDetail() {
  const { id } = useParams();
  const nav = useNavigate();
  const me = getUser();
  const [match, setMatch] = useState(null);
  const [tab, setTab] = useState('facts');

  useEffect(() => { api.get(`/matches/${id}`).then((r) => setMatch(r.data)); }, [id]);

  if (!match) return <div className="p-8 text-ink-muted">Loading…</div>;

  return (
    <div className="px-4 pt-4 pb-24" data-testid="match-detail-page">
      <div className="bg-bg-card border border-line p-4">
        <span className={`font-mono text-[10px] uppercase tracking-widest px-2 py-0.5 ${match.status === 'live' ? 'bg-brand-primary text-white animate-pulse-red' : match.status === 'complete' ? 'bg-bg-elevated text-ink-muted' : 'bg-brand-accent text-black'}`}>
          {match.status}
        </span>
        <div className="grid grid-cols-3 items-center mt-3">
          <div className="text-right font-display text-2xl">{match.home_team.toUpperCase()}</div>
          <div className="text-center">
            {match.status === 'complete' || match.status === 'live' ? (
              <div className="font-mono text-3xl font-bold">{match.score?.home} : {match.score?.away}</div>
            ) : (
              <div className="font-mono text-brand-accent">VS</div>
            )}
          </div>
          <div className="text-left font-display text-2xl">{match.away_team.toUpperCase()}</div>
        </div>
        <div className="flex flex-wrap gap-3 mt-3 font-mono text-[10px] uppercase tracking-widest text-ink-muted">
          <span className="flex items-center gap-1"><Calendar className="w-3 h-3" /> {new Date(match.scheduled_at).toLocaleString('en-IN')}</span>
          <span className="flex items-center gap-1"><MapPin className="w-3 h-3" /> {match.turf_name}</span>
        </div>
        <div className="flex gap-2 mt-3">
          {match.status === 'live' && (
            <button data-testid="watch-broadcast-btn" onClick={() => nav(`/broadcast/${id}`)} className="flex-1 bg-brand-primary text-white h-10 font-mono uppercase text-xs tracking-widest flex items-center justify-center gap-1 hover:bg-[#D63026]">
              <Tv className="w-3.5 h-3.5" /> Watch Live
            </button>
          )}
          {match.status === 'complete' && (
            <button data-testid="view-analysis-btn" onClick={() => nav(`/match/${id}/analysis`)} className="flex-1 bg-brand-accent text-black h-10 font-mono uppercase text-xs tracking-widest flex items-center justify-center gap-1">
              <BarChart3 className="w-3.5 h-3.5" /> View Analysis
            </button>
          )}
          {(me?.role === 'admin' || me?.role === 'referee') && match.status === 'scheduled' && (
            <button data-testid="goto-var-btn" onClick={() => nav(`/admin/var/${id}`)} className="flex-1 border border-brand-primary text-brand-primary h-10 font-mono uppercase text-xs tracking-widest hover:bg-brand-primary hover:text-white">
              Open VAR Room
            </button>
          )}
        </div>
      </div>

      {/* Tabs */}
      <div className="grid grid-cols-4 border-b border-line mt-4" data-testid="match-tabs">
        {['facts', 'lineup', 'stats', 'h2h'].map((t) => (
          <button
            key={t}
            data-testid={`md-tab-${t}`}
            onClick={() => setTab(t)}
            className={`h-10 font-mono uppercase text-xs tracking-widest ${tab === t ? 'border-b-2 border-brand-primary text-white' : 'text-ink-muted'}`}
          >
            {t}
          </button>
        ))}
      </div>

      {tab === 'facts' && (
        <div className="mt-4 space-y-2" data-testid="tab-facts-content">
          <div className="font-mono text-[10px] uppercase tracking-widest text-ink-muted">EVENT TIMELINE</div>
          {(!match.events || match.events.length === 0) && <div className="text-ink-muted text-sm py-4">No events yet.</div>}
          {match.events?.map((e) => {
            const m = EVENT_META[e.type] || { label: e.type, color: '#fff', icon: '•' };
            return (
              <div key={e.id} className="bg-bg-card border border-line px-3 py-2 flex items-center gap-3" data-testid={`event-${e.id}`}>
                <div className="w-8 h-8 flex items-center justify-center font-mono font-bold" style={{ background: m.color, color: '#000' }}>{m.icon}</div>
                <div className="flex-1">
                  <div className="font-mono text-xs uppercase tracking-widest">{m.label}</div>
                  <div className="text-xs text-ink-muted">{e.notes || `${e.team || ''} ${e.player_name || ''}`}</div>
                </div>
                {e.minute != null && <div className="font-mono text-xs text-brand-accent">{e.minute}'</div>}
              </div>
            );
          })}
        </div>
      )}

      {tab === 'lineup' && (
        <div className="mt-4 grid grid-cols-2 gap-3" data-testid="tab-lineup-content">
          {[match.home_team, match.away_team].map((team) => (
            <div key={team} className="bg-bg-card border border-line p-3">
              <div className="font-display text-xl">{team.toUpperCase()}</div>
              <div className="mt-2 space-y-1 font-mono text-xs">
                {['GK Vikram', 'CB Karan', 'CM Arjun', 'LW Dev', 'ST Rohit'].map((p) => (
                  <div key={p} className="border-b border-line pb-1">{p}</div>
                ))}
              </div>
            </div>
          ))}
        </div>
      )}

      {tab === 'stats' && (
        <div className="mt-4 space-y-2 font-mono text-sm" data-testid="tab-stats-content">
          {[
            ['Possession', '58%', '42%'],
            ['Total Shots', '11', '7'],
            ['On Target', '6', '3'],
            ['Passes', '312', '241'],
            ['Pass %', '84%', '77%'],
            ['Offsides', '2', '1'],
            ['Corners', '5', '3'],
          ].map(([label, h, a]) => (
            <div key={label} className="bg-bg-card border border-line p-3">
              <div className="font-mono text-[10px] uppercase tracking-widest text-ink-muted text-center">{label}</div>
              <div className="grid grid-cols-3 items-center gap-2 mt-1">
                <div className="text-right">{h}</div>
                <div className="h-1.5 bg-line relative">
                  <div className="absolute left-0 top-0 bottom-0 bg-brand-primary" style={{ width: '60%' }} />
                </div>
                <div>{a}</div>
              </div>
            </div>
          ))}
        </div>
      )}

      {tab === 'h2h' && (
        <div className="mt-4 grid grid-cols-2 gap-3" data-testid="tab-h2h-content">
          {[match.home_team, match.away_team].map((team, i) => (
            <div key={team} className="bg-bg-card border border-line p-4 text-center">
              <div className="font-display text-2xl">{team.toUpperCase()}</div>
              <div className="font-mono text-[10px] uppercase tracking-widest text-ink-muted mt-3">Total / Won / Trophies</div>
              <div className="font-mono text-2xl font-bold mt-1">{[24, 18][i]} · {[14, 9][i]} · {[3, 2][i]}</div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
