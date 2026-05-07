import React, { useEffect, useState } from 'react';
import { useParams, Link, useNavigate } from 'react-router-dom';
import { ChevronLeft, Sparkles, Target, Activity, Zap } from 'lucide-react';
import { api, getUser } from '../lib/api';
import { getCityTheme } from '../lib/cityTheme';

/**
 * Module 03 — Pre-Match Intelligence Pack.
 * Win probability bar · Form timelines · H2H · Key matchup card · AI tactical brief · Personal role card
 */
export default function MatchBrief() {
  const { id } = useParams();
  const nav = useNavigate();
  const me = getUser();
  const [data, setData] = useState(null);

  useEffect(() => { api.get(`/matches/${id}/brief`).then((r) => setData(r.data)); }, [id]);

  if (!data) {
    return (
      <div className="min-h-screen bg-bg flex flex-col items-center justify-center text-ink-muted" data-testid="brief-loading">
        <div className="w-10 h-10 border-2 border-accent-purple border-t-transparent rounded-full animate-spin" />
        <div className="font-mono text-[10px] uppercase tracking-widest mt-4">AI building your brief…</div>
      </div>
    );
  }

  const theme = getCityTheme(me?.city || 'Mumbai');
  const wp = data.win_probability;

  return (
    <div className="min-h-screen bg-bg pb-20" data-testid="match-brief-page">
      <header className="border-b border-line bg-bg/95 backdrop-blur sticky top-0 z-30">
        <div className="max-w-2xl mx-auto px-4 py-3 flex items-center justify-between">
          <button onClick={() => nav(-1)} className="font-mono text-[10px] uppercase tracking-widest text-ink-muted hover:text-ink flex items-center gap-1" data-testid="back-btn">
            <ChevronLeft className="w-3 h-3" /> Back
          </button>
          <div className="font-display text-base tracking-wider font-bold">PRE-MATCH BRIEF</div>
          <div />
        </div>
      </header>

      <main className="max-w-2xl mx-auto px-4 py-4 space-y-4">
        {/* Win probability hero */}
        <div className="bg-bg-card border border-accent-purple/40 p-4 relative overflow-hidden" data-testid="win-prob-block">
          <div className="flex items-center gap-2 mb-3">
            <Sparkles className="w-4 h-4 text-accent-purple" />
            <span className="font-mono text-[10px] uppercase tracking-widest text-accent-purple">AI WIN PROBABILITY</span>
          </div>
          <div className="grid grid-cols-3 mb-2 font-mono text-xs">
            <div className="text-left">
              <div className="font-display text-3xl font-bold text-ink" data-testid="wp-home">{wp.home}%</div>
              <div className="text-[10px] uppercase tracking-widest text-ink-muted">Home</div>
            </div>
            <div className="text-center">
              <div className="font-display text-3xl font-bold text-ink-muted" data-testid="wp-draw">{wp.draw}%</div>
              <div className="text-[10px] uppercase tracking-widest text-ink-muted">Draw</div>
            </div>
            <div className="text-right">
              <div className="font-display text-3xl font-bold text-ink" data-testid="wp-away">{wp.away}%</div>
              <div className="text-[10px] uppercase tracking-widest text-ink-muted">Away</div>
            </div>
          </div>
          <div className="h-2 flex w-full overflow-hidden rounded-full">
            <div className="bg-accent-green" style={{ width: `${wp.home}%` }} />
            <div className="bg-ink-dim" style={{ width: `${wp.draw}%` }} />
            <div className="bg-accent-blue" style={{ width: `${wp.away}%` }} />
          </div>
        </div>

        {/* AI Tactical brief */}
        <div className="bg-bg-card border border-line p-4" data-testid="ai-brief-block">
          <div className="flex items-center gap-2 mb-2">
            <Sparkles className="w-4 h-4 text-accent-purple" />
            <span className="font-mono text-[10px] uppercase tracking-widest text-accent-purple">
              TACTICAL BRIEF · {data.ai_brief_source}
            </span>
          </div>
          <div className="text-sm leading-relaxed whitespace-pre-wrap text-ink">{data.ai_brief}</div>
        </div>

        {/* Form bars */}
        <div className="grid grid-cols-2 gap-3" data-testid="form-block">
          {[data.home_form, data.away_form].map((f, i) => (
            <div key={i} className="bg-bg-card border border-line p-3">
              <div className="font-mono text-[10px] uppercase tracking-widest text-ink-muted">{i === 0 ? 'HOME FORM' : 'AWAY FORM'}</div>
              <div className="font-display text-lg mt-0.5 tracking-wide truncate">{f.team.toUpperCase()}</div>
              <div className="flex gap-1 mt-2">
                {f.form.map((r, j) => (
                  <div
                    key={j}
                    data-testid={`form-${i}-${j}`}
                    className="flex-1 h-7 flex items-center justify-center font-mono font-bold text-xs"
                    style={{
                      background: r === 'W' ? '#00E676' : r === 'D' ? '#FFB830' : '#FF4D4D',
                      color: r === 'D' ? '#0A0F1E' : '#0A0F1E',
                    }}
                  >{r}</div>
                ))}
              </div>
              <div className="font-mono text-[10px] uppercase tracking-widest text-ink-muted mt-2">
                {f.wins}W · {f.draws}D · {f.losses}L
              </div>
            </div>
          ))}
        </div>

        {/* Key matchup */}
        <div className="bg-bg-card border-l-2 p-4" style={{ borderLeftColor: theme.accent }} data-testid="matchup-block">
          <div className="flex items-center gap-2">
            <Target className="w-4 h-4" style={{ color: theme.accent }} />
            <span className="font-mono text-[10px] uppercase tracking-widest" style={{ color: theme.accent }}>KEY MATCHUP</span>
          </div>
          <div className="font-display text-2xl mt-1 font-bold">{data.key_matchup.label.toUpperCase()}</div>
          <div className="grid grid-cols-[1fr_auto_1fr] items-center gap-3 mt-3 text-sm">
            <div className="text-right">
              <div className="font-mono text-[10px] uppercase tracking-widest text-ink-muted">OURS</div>
              <div className="font-bold">{data.key_matchup.ours}</div>
            </div>
            <div className="font-mono text-xs text-ink-dim">VS</div>
            <div className="text-left">
              <div className="font-mono text-[10px] uppercase tracking-widest text-ink-muted">THEIRS</div>
              <div className="font-bold">{data.key_matchup.theirs}</div>
            </div>
          </div>
          <div className="bg-bg-elevated border border-line p-2 mt-3">
            <div className="font-mono text-[10px] uppercase tracking-widest text-ink-muted">EDGE</div>
            <div className="text-sm">{data.key_matchup.edge}</div>
          </div>
        </div>

        {/* Personal role card */}
        <div className="bg-bg-card border border-accent-amber/40 p-4" data-testid="role-card-block">
          <div className="flex items-center gap-2">
            <Zap className="w-4 h-4 text-accent-amber" />
            <span className="font-mono text-[10px] uppercase tracking-widest text-accent-amber">YOUR ROLE · {data.role_card.position}</span>
          </div>
          <div className="text-sm mt-2 text-ink">{data.role_card.instruction}</div>
          <div className="mt-3">
            <div className="font-mono text-[10px] uppercase tracking-widest text-ink-muted">TARGETS</div>
            <ul className="mt-1 space-y-1">
              {data.role_card.targets.map((t, i) => (
                <li key={i} className="font-mono text-xs flex items-start gap-2">
                  <span className="text-accent-green">▸</span> {t}
                </li>
              ))}
            </ul>
          </div>
          <div className="mt-3 bg-accent-red/10 border border-accent-red/30 p-2">
            <div className="font-mono text-[10px] uppercase tracking-widest text-accent-red">⚠ WATCH OUT</div>
            <div className="text-xs mt-0.5">{data.role_card.watch_out}</div>
          </div>
        </div>

        {/* H2H */}
        <div data-testid="h2h-block">
          <div className="font-mono text-[10px] uppercase tracking-widest text-ink-muted mb-2">HEAD TO HEAD · LAST 3</div>
          <div className="space-y-1">
            {data.h2h.map((h, i) => (
              <div key={i} className="bg-bg-card border border-line px-3 py-2 flex items-center gap-3 font-mono text-xs">
                <span className="text-ink-muted">{h.date}</span>
                <span className="flex-1">{h.home_team}</span>
                <span className="font-bold text-base text-ink">{h.home_score}–{h.away_score}</span>
                <span className="flex-1 text-right">{h.away_team}</span>
                <span className="text-[10px] uppercase tracking-widest" style={{ color: h.winner === 'Draw' ? '#FFB830' : '#00E676' }}>
                  {h.winner === 'Draw' ? 'D' : 'W'}
                </span>
              </div>
            ))}
          </div>
        </div>
      </main>
    </div>
  );
}
