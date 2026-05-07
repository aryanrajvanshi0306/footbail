import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { ChevronLeft, Trophy, Users, TrendingUp, Flame } from 'lucide-react';
import { api, getUser } from '../lib/api';

/**
 * City Derby — Module 11 extension. 8 cities ranked by aggregate XP.
 * Anime-coded accents per city. Player's own city is highlighted with a ring.
 */
export default function CityDerby() {
  const me = getUser();
  const [rows, setRows] = useState([]);
  useEffect(() => { api.get('/explore/derby').then((r) => setRows(r.data)); }, []);

  const top = rows[0];
  const myRow = rows.find((r) => r.city === me?.city);

  return (
    <div className="min-h-screen bg-bg pb-24" data-testid="city-derby-page">
      <header className="border-b border-line">
        <div className="max-w-2xl mx-auto px-4 py-3 flex items-center justify-between">
          <Link to="/explore" data-testid="back-to-explore" className="font-mono text-[10px] uppercase tracking-widest text-ink-muted hover:text-ink flex items-center gap-1">
            <ChevronLeft className="w-3 h-3" /> Explore
          </Link>
          <div className="font-display text-base tracking-wider font-bold">CITY DERBY</div>
          <div />
        </div>
      </header>

      <main className="max-w-2xl mx-auto px-4 py-4 space-y-4">
        {/* Hero — current leader */}
        {top && (
          <div
            className="relative overflow-hidden p-5 border-2 city-shine"
            style={{ borderColor: top.accent, background: `radial-gradient(ellipse at top, ${top.accent}26 0%, #0A0F1E 60%, #050810 100%)` }}
            data-testid="derby-hero"
          >
            <div className="font-mono text-[10px] uppercase tracking-[0.3em] mb-1" style={{ color: top.accent }}>👑 CURRENTLY ON TOP</div>
            <div className="font-display text-5xl font-bold tracking-tight">{top.city.toUpperCase()}</div>
            <div className="font-mono text-xs uppercase tracking-widest mt-1" style={{ color: top.accent }}>{top.subtitle}</div>
            <div className="grid grid-cols-3 gap-3 mt-4">
              <Stat label="PLAYERS" value={top.players} icon={Users} />
              <Stat label="MATCHES" value={top.total_matches} icon={Flame} />
              <Stat label="GOALS" value={top.total_goals} icon={Trophy} />
            </div>
            <div className="mt-3 font-mono text-[10px] uppercase tracking-widest text-ink-muted">
              SCORE <span className="text-ink font-bold">{top.score.toLocaleString('en-IN')}</span>
            </div>
          </div>
        )}

        {/* My city call-out */}
        {myRow && myRow.city !== top?.city && (
          <div
            className="bg-bg-card border-2 p-3 flex items-center gap-3"
            style={{ borderColor: myRow.accent }}
            data-testid="my-city-callout"
          >
            <div className="font-display text-3xl font-bold" style={{ color: myRow.accent }}>#{myRow.rank}</div>
            <div className="flex-1">
              <div className="font-mono text-[10px] uppercase tracking-widest text-ink-muted">YOUR CITY · {myRow.subtitle}</div>
              <div className="font-display text-xl font-bold">{myRow.city.toUpperCase()}</div>
              <div className="font-mono text-[10px] uppercase tracking-widest text-ink-muted">
                {myRow.players} players · {myRow.total_xp.toLocaleString('en-IN')} XP
              </div>
            </div>
            <div className="font-mono text-xs text-ink-muted text-right">
              <div>vs #1</div>
              <div className="font-bold text-accent-amber">−{((top?.score || 0) - myRow.score).toLocaleString('en-IN')}</div>
            </div>
          </div>
        )}

        {/* Full ranking */}
        <div data-testid="derby-ranking">
          <div className="font-mono text-[10px] uppercase tracking-widest text-ink-muted mb-2">FULL TABLE</div>
          <div className="space-y-1.5">
            {rows.map((r) => (
              <div
                key={r.city}
                data-testid={`derby-row-${r.city}`}
                className={`flex items-center gap-3 p-3 border bg-bg-card transition-colors hover:translate-x-0.5 ${
                  r.city === me?.city ? 'border-2' : 'border-line'
                }`}
                style={r.city === me?.city ? { borderColor: r.accent } : {}}
              >
                <div className="w-8 font-display text-2xl font-bold text-right" style={{ color: r.accent }}>
                  {r.rank}
                </div>
                <div className="w-1 h-10" style={{ background: r.accent }} />
                <div className="flex-1 min-w-0">
                  <div className="font-display text-lg font-bold tracking-wide truncate">{r.city.toUpperCase()}</div>
                  <div className="font-mono text-[10px] uppercase tracking-widest text-ink-muted truncate">
                    {r.subtitle} · {r.players} players · avg {r.avg_overall}
                  </div>
                </div>
                <div className="text-right">
                  <div className="font-mono font-bold text-lg" style={{ color: r.accent }}>{r.score.toLocaleString('en-IN')}</div>
                  <div className="font-mono text-[10px] uppercase tracking-widest text-ink-muted">{r.total_xp.toLocaleString('en-IN')} XP</div>
                </div>
              </div>
            ))}
          </div>
        </div>

        <div className="bg-bg-elevated border border-line p-3 text-xs font-mono text-ink-muted leading-relaxed">
          <span className="text-accent-amber">SCORING:</span> total XP + (goals × 100) + (matches × 5) + (avg overall × 100). Resets every season.
        </div>
      </main>
    </div>
  );
}

function Stat({ label, value, icon: Icon }) {
  return (
    <div className="bg-black/30 border border-white/10 p-2">
      <Icon className="w-3.5 h-3.5 text-ink-muted mb-1" />
      <div className="font-display text-xl font-bold">{value}</div>
      <div className="font-mono text-[9px] uppercase tracking-widest text-ink-muted">{label}</div>
    </div>
  );
}
