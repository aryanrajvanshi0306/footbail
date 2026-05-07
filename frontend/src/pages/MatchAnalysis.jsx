import React, { useEffect, useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import { ChevronLeft, Trophy, TrendingUp, Activity, Sparkles } from 'lucide-react';
import { api, getUser } from '../lib/api';
import { EVENT_META } from '../lib/constants';
import ShareHighlight from '../components/ShareHighlight';

export default function MatchAnalysis() {
  const { id } = useParams();
  const [data, setData] = useState(null);
  const me = getUser();
  useEffect(() => { api.get(`/matches/${id}/analysis`).then((r) => setData(r.data)); }, [id]);
  if (!data) return <div className="p-8 text-ink-muted bg-bg min-h-screen">Loading…</div>;

  const { match, events, stats, summary, summary_source, motm, heatmap_points } = data;

  return (
    <div className="min-h-screen bg-bg pb-20" data-testid="analysis-page">
      <header className="border-b border-line">
        <div className="max-w-3xl mx-auto px-4 py-3 flex items-center justify-between">
          <Link to="/home" data-testid="back-home" className="font-mono text-[10px] uppercase tracking-widest text-ink-muted hover:text-white flex items-center gap-1"><ChevronLeft className="w-3 h-3" /> Home</Link>
          <div className="font-display text-xl tracking-wider">PERFORMANCE</div>
          <div />
        </div>
      </header>

      <main className="max-w-3xl mx-auto px-4 py-4 space-y-4">
        {/* Final score */}
        <div className="bg-bg-card border border-line p-4">
          <div className="grid grid-cols-3 items-center">
            <div className="text-right font-display text-2xl">{match.home_team.toUpperCase()}</div>
            <div className="text-center font-mono font-bold text-4xl text-accent-amber">
              {match.score?.home || 0} : {match.score?.away || 0}
            </div>
            <div className="text-left font-display text-2xl">{match.away_team.toUpperCase()}</div>
          </div>
          <div className="text-center font-mono text-[10px] uppercase tracking-widest text-ink-muted mt-2">
            FT · {match.turf_name}
          </div>
        </div>

        {/* AI Summary */}
        <div className="bg-bg-card border border-accent-purple/60 p-4 relative overflow-hidden" data-testid="ai-summary">
          <div className="flex items-center gap-2 mb-2">
            <Sparkles className="w-4 h-4 text-accent-purple" />
            <span className="font-mono text-[10px] uppercase tracking-widest text-accent-purple">
              AI MATCH ANALYSIS {summary_source ? `· ${summary_source}` : ''}
            </span>
          </div>
          <div className="text-sm leading-relaxed whitespace-pre-wrap">{summary}</div>
        </div>

        {/* Share Highlight Reel — viral loop */}
        <div className="bg-bg-card border border-line p-4" data-testid="share-block">
          <ShareHighlight match={match} motm={motm} userCity={me?.city || 'Mumbai'} goalCount={match.score?.home || 0} />
        </div>

        {/* MOTM */}
        <div className="bg-bg-card border border-line p-4 flex items-center gap-4" data-testid="motm">
          <div className="w-16 h-16 bg-gradient-to-br from-yellow-600 to-amber-900 flex items-center justify-center">
            <Trophy className="w-8 h-8 text-yellow-200" />
          </div>
          <div className="flex-1">
            <div className="font-mono text-[10px] uppercase tracking-widest text-accent-amber">MAN OF THE MATCH</div>
            <div className="font-display text-2xl">{motm.name.toUpperCase()}</div>
            <div className="font-mono text-xs text-ink-muted">{motm.position} · {motm.goals}G · {motm.assists}A</div>
          </div>
          <div className="font-mono font-bold text-3xl text-accent-amber">{motm.rating}</div>
        </div>

        {/* Stats */}
        <div className="space-y-2 font-mono text-sm" data-testid="match-stats">
          <div className="font-mono text-[10px] uppercase tracking-widest text-ink-muted">MATCH STATS</div>
          {[
            ['Possession', stats.possession.home + '%', stats.possession.away + '%'],
            ['Shots', stats.shots.home, stats.shots.away],
            ['Shots on Target', stats.shots_on_target.home, stats.shots_on_target.away],
            ['Passes', stats.passes.home, stats.passes.away],
            ['Pass Accuracy', stats.pass_accuracy.home + '%', stats.pass_accuracy.away + '%'],
            ['Fouls', stats.fouls.home, stats.fouls.away],
            ['Offsides', stats.offsides.home, stats.offsides.away],
            ['Corners', stats.corners.home, stats.corners.away],
          ].map(([label, h, a]) => {
            const total = (typeof h === 'number' ? h : parseFloat(h)) + (typeof a === 'number' ? a : parseFloat(a)) || 1;
            const hp = ((typeof h === 'number' ? h : parseFloat(h)) / total) * 100;
            return (
              <div key={label} className="bg-bg-card border border-line p-3">
                <div className="text-center font-mono text-[10px] uppercase tracking-widest text-ink-muted">{label}</div>
                <div className="grid grid-cols-3 items-center gap-2 mt-1">
                  <div className="text-right font-bold">{h}</div>
                  <div className="h-1.5 bg-line relative flex">
                    <div className="bg-accent-green text-black" style={{ width: `${hp}%` }} />
                    <div className="bg-brand-secondary" style={{ width: `${100 - hp}%` }} />
                  </div>
                  <div className="font-bold">{a}</div>
                </div>
              </div>
            );
          })}
        </div>

        {/* Heatmap */}
        <div data-testid="heatmap-block">
          <div className="font-mono text-[10px] uppercase tracking-widest text-ink-muted mb-2">PLAYER HEATMAP · {motm.name.toUpperCase()}</div>
          <div className="relative aspect-video pitch-bg border border-line overflow-hidden">
            <svg className="absolute inset-0 w-full h-full opacity-30" viewBox="0 0 100 60" preserveAspectRatio="none">
              <rect x="2" y="2" width="96" height="56" fill="none" stroke="white" strokeWidth="0.3" />
              <line x1="50" y1="2" x2="50" y2="58" stroke="white" strokeWidth="0.3" />
              <circle cx="50" cy="30" r="6" fill="none" stroke="white" strokeWidth="0.3" />
            </svg>
            {heatmap_points.map((p, i) => (
              <div key={i} className="absolute w-16 h-16 -translate-x-1/2 -translate-y-1/2 rounded-full" style={{
                left: `${p.x}%`, top: `${p.y}%`,
                background: 'radial-gradient(circle, rgba(255,59,48,0.6) 0%, transparent 70%)',
              }} />
            ))}
          </div>
        </div>

        {/* Event timeline */}
        <div data-testid="analysis-events">
          <div className="font-mono text-[10px] uppercase tracking-widest text-ink-muted mb-2">EVENT TIMELINE</div>
          <div className="space-y-1">
            {events.map((e) => {
              const m = EVENT_META[e.type] || { label: e.type, color: '#A1A1A1', icon: '•' };
              return (
                <div key={e.id} className="bg-bg-card border border-line px-3 py-2 flex items-center gap-3">
                  <div className="w-7 h-7 flex items-center justify-center font-mono font-bold text-sm" style={{ background: m.color, color: '#000' }}>{m.icon}</div>
                  <div className="flex-1 min-w-0">
                    <div className="font-mono text-xs uppercase tracking-widest">{m.label}</div>
                    <div className="text-xs text-ink-muted truncate">{e.notes}</div>
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
