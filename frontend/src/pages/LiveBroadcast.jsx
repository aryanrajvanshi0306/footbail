import React, { useEffect, useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import { ChevronLeft, Radio, Tv } from 'lucide-react';
import { api } from '../lib/api';
import { EVENT_META } from '../lib/constants';

export default function LiveBroadcast() {
  const { id } = useParams();
  const [data, setData] = useState(null);

  const load = () => api.get(`/matches/${id}/broadcast`).then((r) => setData(r.data));
  useEffect(() => {
    load();
    const t = setInterval(load, 3000); // poll
    return () => clearInterval(t);
  }, [id]);

  if (!data) return <div className="p-8 text-ink-muted bg-black min-h-screen">Loading broadcast…</div>;
  const { match, events } = data;

  return (
    <div className="min-h-screen bg-black" data-testid="live-broadcast-page">
      <header className="border-b border-line">
        <div className="max-w-6xl mx-auto px-4 py-3 flex items-center justify-between">
          <Link to="/home" data-testid="back-home" className="font-mono text-[10px] uppercase tracking-widest text-ink-muted hover:text-white flex items-center gap-1">
            <ChevronLeft className="w-3 h-3" /> Home
          </Link>
          <div className="flex items-center gap-2 font-mono text-xs uppercase tracking-widest">
            {match.status === 'live' ? (
              <><span className="w-2 h-2 bg-accent-green text-black font-bold rounded-full animate-pulse" /><span className="text-accent-green">LIVE</span></>
            ) : match.status === 'complete' ? (
              <span className="text-ink-muted">FULL TIME</span>
            ) : (
              <span className="text-accent-amber">SCHEDULED</span>
            )}
          </div>
        </div>
      </header>

      <main className="max-w-6xl mx-auto px-4 py-4">
        {/* Score */}
        <div className="bg-bg-card border border-line p-4 mb-4">
          <div className="grid grid-cols-3 items-center">
            <div className="text-right font-display text-3xl">{match.home_team.toUpperCase()}</div>
            <div className="text-center font-mono font-bold text-5xl text-accent-amber" data-testid="bcast-score">
              {match.score?.home || 0} : {match.score?.away || 0}
            </div>
            <div className="text-left font-display text-3xl">{match.away_team.toUpperCase()}</div>
          </div>
          <div className="text-center font-mono text-[10px] uppercase tracking-widest text-ink-muted mt-2">
            {match.turf_name} · {match.format}
          </div>
        </div>

        {/* Video pitch */}
        <div className="relative aspect-video pitch-bg border border-line overflow-hidden mb-4" data-testid="bcast-feed">
          <div className="grain absolute inset-0" />
          <svg className="absolute inset-0 w-full h-full opacity-40" viewBox="0 0 100 60" preserveAspectRatio="none">
            <rect x="2" y="2" width="96" height="56" fill="none" stroke="white" strokeWidth="0.3" />
            <line x1="50" y1="2" x2="50" y2="58" stroke="white" strokeWidth="0.3" />
            <circle cx="50" cy="30" r="6" fill="none" stroke="white" strokeWidth="0.3" />
          </svg>
          {match.status === 'live' && [
            [25, 30, '#FF3B30'], [38, 22, '#FF3B30'], [38, 38, '#FF3B30'], [50, 30, '#FF3B30'],
            [62, 22, '#007AFF'], [62, 38, '#007AFF'], [75, 30, '#007AFF'], [88, 30, '#007AFF'],
          ].map(([x, y, c], i) => (
            <div key={i} className="absolute w-3 h-3 rounded-full animate-pulse" style={{ left: `${x}%`, top: `${y}%`, transform: 'translate(-50%, -50%)', background: c, boxShadow: `0 0 8px ${c}` }} />
          ))}
          {match.status === 'live' && (
            <div className="absolute top-2 left-2 flex items-center gap-2 font-mono text-[10px] uppercase tracking-widest">
              <span className="w-2 h-2 rounded-full bg-accent-green text-black font-bold animate-pulse" />
              <span className="text-accent-green">LIVE</span>
              <span className="text-ink-muted">| TURF CAM 01</span>
            </div>
          )}
          {match.status !== 'live' && (
            <div className="absolute inset-0 bg-black/85 flex items-center justify-center font-display text-3xl text-ink-muted">
              {match.status === 'complete' ? 'BROADCAST ENDED' : 'AWAITING KICKOFF'}
            </div>
          )}

          {/* Lower-third event banner — newest event */}
          {events?.[0] && match.status === 'live' && (
            <div className="absolute bottom-0 left-0 right-0 bg-black/85 border-t-2 px-4 py-2 flex items-center gap-3" style={{ borderColor: EVENT_META[events[0].type]?.color || '#fff' }} data-testid="event-banner">
              <div className="w-8 h-8 flex items-center justify-center font-mono font-bold" style={{ background: EVENT_META[events[0].type]?.color || '#fff', color: '#000' }}>
                {EVENT_META[events[0].type]?.icon || '•'}
              </div>
              <div>
                <div className="font-mono text-xs uppercase tracking-widest text-white">{EVENT_META[events[0].type]?.label || events[0].type}</div>
                <div className="text-xs text-ink-muted">{events[0].notes || `${events[0].team || ''} ${events[0].player_name || ''}`}</div>
              </div>
            </div>
          )}
        </div>

        {/* Events feed */}
        <div data-testid="bcast-events-list">
          <div className="font-mono text-[10px] uppercase tracking-widest text-ink-muted mb-2">LIVE EVENTS</div>
          <div className="space-y-1">
            {events?.length === 0 && <div className="text-ink-muted text-sm py-4">No events yet.</div>}
            {events?.map((e) => {
              const m = EVENT_META[e.type] || { label: e.type, color: '#A1A1A1', icon: '•' };
              return (
                <div key={e.id} className="bg-bg-card border border-line px-3 py-2 flex items-center gap-3">
                  <div className="w-7 h-7 flex items-center justify-center font-mono font-bold text-sm" style={{ background: m.color, color: '#000' }}>{m.icon}</div>
                  <div className="flex-1">
                    <div className="font-mono text-xs uppercase tracking-widest">{m.label} {e.auto_detected && <span className="text-[9px] text-accent-amber ml-1">AI</span>}</div>
                    <div className="text-xs text-ink-muted">{e.notes || `${e.team || ''} ${e.player_name || ''}`}</div>
                  </div>
                  {e.minute != null && <div className="font-mono text-xs text-accent-amber">{e.minute}'</div>}
                </div>
              );
            })}
          </div>
        </div>
      </main>
    </div>
  );
}
