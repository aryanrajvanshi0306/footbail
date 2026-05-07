import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Trophy, Users, ChevronRight, Star, Calendar, ArrowRight, BookOpen, MessageSquare } from 'lucide-react';
import { api, getUser } from '../lib/api';

/**
 * Coach onboarding landing — distinct from /home (which is player-centric).
 * Reached automatically after coach signs up or logs in.
 * Surfaces:
 *  - Coach intro hero
 *  - Coach quick-actions (Sessions, Drills, Players, Messages)
 *  - Hint to fill marketplace profile (rate, languages, certifications)
 */
export default function CoachLanding() {
  const nav = useNavigate();
  const me = getUser();
  const [stats, setStats] = useState({ sessions: 0, players: 0, rating: 0 });

  useEffect(() => {
    if (!me) { nav('/login'); return; }
    if (me.role !== 'coach') { nav('/home'); return; }
    api.get('/auth/me').then((r) => {
      setStats({
        sessions: r.data.sessions ?? 0,
        players: r.data.players_coached ?? 0,
        rating: r.data.rating ?? 4.8,
      });
    }).catch(() => {});
  }, []);

  if (!me || me.role !== 'coach') return null;

  return (
    <div className="px-4 pt-4 pb-24" data-testid="coach-landing">
      {/* Hero */}
      <div className="relative overflow-hidden bg-bg-card border border-line p-6 city-shine">
        <div className="grain absolute inset-0" />
        <div className="relative">
          <div className="font-mono text-[10px] uppercase tracking-widest text-accent-blue">Coach Console</div>
          <div className="font-display text-3xl mt-1">Welcome, {me.name?.split(' ')[0]?.toUpperCase()}</div>
          <div className="text-sm text-ink-muted mt-1">Your AI-assisted coaching workspace.</div>

          <div className="flex gap-2 mt-4 text-[10px] font-mono uppercase tracking-widest">
            <Pill icon={Calendar} v={stats.sessions} l="Sessions" testid="coach-sessions" />
            <Pill icon={Users} v={stats.players} l="Players" testid="coach-players" />
            <Pill icon={Star} v={stats.rating} l="Rating" testid="coach-rating" />
          </div>
        </div>
      </div>

      {/* Action grid */}
      <div className="mt-5 grid grid-cols-2 gap-3" data-testid="coach-actions">
        <Action title="My Sessions"  blurb="Schedule + manage 1:1s"   icon={Calendar} accent="#38BDF8" testid="coach-action-sessions" onClick={() => nav('/explore/coach')} />
        <Action title="Drill Library" blurb="50+ AI-curated drills"   icon={BookOpen} accent="#A78BFA" testid="coach-action-drills"   onClick={() => nav('/explore/drills')} />
        <Action title="Players"       blurb="Browse FIFA card squad" icon={Users}   accent="#00E676"  testid="coach-action-players"  onClick={() => nav('/explore/leaderboard')} />
        <Action title="Messages"      blurb="Player chats + notes"   icon={MessageSquare} accent="#FFB830" testid="coach-action-messages" onClick={() => nav('/feed')} />
      </div>

      {/* Marketplace hint */}
      <div className="mt-5 bg-bg-card border border-accent-blue/40 p-4 city-pattern" data-testid="coach-marketplace-hint">
        <div className="flex items-start gap-3">
          <Trophy className="w-5 h-5 text-accent-amber shrink-0 mt-0.5"/>
          <div className="flex-1">
            <div className="font-display text-lg">Boost your visibility</div>
            <div className="text-sm text-ink-muted mt-0.5">
              Coaches with a complete profile (rate, certs, languages) get <b className="text-accent-green">3.4x</b> more
              session requests. Polish yours before the weekend rush.
            </div>
            <button
              data-testid="coach-complete-profile-btn"
              onClick={() => nav('/profile')}
              className="mt-3 inline-flex items-center gap-1.5 text-xs font-mono uppercase tracking-widest text-accent-blue hover:gap-2.5 transition-all"
            >
              Complete profile <ArrowRight className="w-3.5 h-3.5"/>
            </button>
          </div>
        </div>
      </div>

      {/* CTA: try player view */}
      <button
        data-testid="coach-back-to-player-btn"
        onClick={() => nav('/home')}
        className="mt-5 w-full text-xs font-mono uppercase tracking-widest text-ink-muted hover:text-accent-green border border-line py-3"
      >
        ← Switch to Player View
      </button>
    </div>
  );
}

function Pill({ icon: Icon, v, l, testid }) {
  return (
    <div data-testid={testid} className="flex-1 bg-black/40 border border-line px-3 py-2 flex items-center gap-2">
      <Icon className="w-3.5 h-3.5 text-accent-blue" />
      <div>
        <div className="text-[9px] text-ink-muted">{l}</div>
        <div className="font-mono font-bold text-sm">{v}</div>
      </div>
    </div>
  );
}

function Action({ title, blurb, icon: Icon, accent, onClick, testid }) {
  return (
    <button
      data-testid={testid}
      onClick={onClick}
      className="text-left bg-bg-card border border-line p-4 hover:border-[var(--ac)] transition-colors group"
      style={{ '--ac': accent }}
    >
      <Icon className="w-6 h-6" style={{ color: accent }} />
      <div className="font-display text-base mt-2">{title}</div>
      <div className="text-xs text-ink-muted mt-0.5 line-clamp-2">{blurb}</div>
      <div className="mt-2 text-[10px] font-mono uppercase tracking-widest opacity-0 group-hover:opacity-100 transition-opacity flex items-center gap-1" style={{ color: accent }}>
        Open <ChevronRight className="w-3 h-3"/>
      </div>
    </button>
  );
}
