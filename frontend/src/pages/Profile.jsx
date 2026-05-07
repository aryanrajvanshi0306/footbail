import React, { useEffect, useState } from 'react';
import { api, getUser } from '../lib/api';
import FIFACard from '../components/FIFACard';

export default function Profile() {
  const [me, setMe] = useState(getUser());
  useEffect(() => { api.get('/auth/me').then((r) => setMe(r.data)).catch(() => {}); }, []);
  if (!me) return null;

  return (
    <div className="px-4 pt-4 pb-24" data-testid="profile-page">
      <div>
        <div className="font-mono text-[10px] uppercase tracking-widest text-ink-muted">Your Identity</div>
        <div className="font-display text-3xl">PROFILE</div>
      </div>

      {me.role === 'player' ? (
        <div className="mt-4 flex flex-col items-center" data-testid="player-profile">
          <FIFACard
            overall={me.overall || 74}
            position={me.position || 'CM'}
            name={me.name?.split(' ')[0]}
            attributes={me.attributes}
            tier={me.card_tier || 'silver'}
            size="lg"
          />
          <div className="font-display text-3xl mt-3">{me.name?.toUpperCase()}</div>
          <div className="font-mono text-xs uppercase tracking-widest text-accent-amber">{me.position} · {me.city}</div>

          <div className="w-full mt-6">
            <div className="font-mono text-[10px] uppercase tracking-widest text-ink-muted mb-2">XP Progress</div>
            <div className="bg-bg-card border border-line p-3">
              <div className="flex justify-between font-mono text-xs">
                <span>{me.xp || 0}</span>
                <span>{me.xp_to_next || 1000}</span>
              </div>
              <div className="h-2 bg-line mt-1 relative">
                <div className="absolute left-0 top-0 bottom-0 bg-brand-accent" style={{ width: `${Math.min(100, ((me.xp || 0) / (me.xp_to_next || 1000)) * 100)}%` }} />
              </div>
              <div className="text-xs text-ink-muted mt-1">{me.card_tier} → next tier</div>
            </div>
          </div>

          <div className="w-full mt-4 grid grid-cols-2 gap-2">
            <Stat l="Matches" v={me.stats?.matches ?? 0} />
            <Stat l="Goals" v={me.stats?.goals ?? 0} />
            <Stat l="Assists" v={me.stats?.assists ?? 0} />
            <Stat l="Streak 🔥" v={me.stats?.streak ?? 0} />
            <Stat l="Consistency" v={`${me.consistency ?? 0}%`} />
            <Stat l="Card Tier" v={(me.card_tier || 'bronze').toUpperCase()} />
          </div>

          <div className="w-full mt-4 bg-bg-card border border-line p-3">
            <div className="font-mono text-[10px] uppercase tracking-widest text-ink-muted">Form (last 10)</div>
            <div className="flex items-end gap-1 mt-2 h-20">
              {[6, 7, 5, 8, 7, 8, 9, 7, 8, 9].map((v, i) => (
                <div key={i} className="flex-1 bg-accent-green text-black" style={{ height: `${v * 10}%` }} />
              ))}
            </div>
          </div>
        </div>
      ) : (
        <div className="mt-4 bg-bg-card border border-line p-6 text-center" data-testid="non-player-profile">
          <div className="w-20 h-20 rounded-full bg-accent-green text-black font-bold flex items-center justify-center font-display text-4xl mx-auto">
            {me.name?.[0]}
          </div>
          <div className="font-display text-3xl mt-3">{me.name?.toUpperCase()}</div>
          <div className="font-mono text-xs uppercase tracking-widest text-accent-amber">{me.role} · {me.email}</div>
          {me.role === 'coach' && (
            <div className="mt-4 grid grid-cols-2 gap-2 text-left">
              <Stat l="Sessions" v={me.sessions ?? 0} />
              <Stat l="Rating" v={`★ ${me.rating ?? '—'}`} />
            </div>
          )}
        </div>
      )}
    </div>
  );
}

const Stat = ({ l, v }) => (
  <div className="bg-bg-card border border-line p-3">
    <div className="font-mono text-[10px] uppercase tracking-widest text-ink-muted">{l}</div>
    <div className="font-mono font-bold text-xl mt-0.5">{v}</div>
  </div>
);
