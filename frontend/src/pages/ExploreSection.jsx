import React, { useEffect, useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import { ChevronLeft } from 'lucide-react';
import { api } from '../lib/api';
import FIFACard from '../components/FIFACard';
import { fmtINR } from '../lib/constants';

export default function ExploreSection() {
  const { section } = useParams();
  const [data, setData] = useState([]);

  useEffect(() => { api.get(`/explore/${section}`).then((r) => setData(r.data)).catch(() => setData([])); }, [section]);

  return (
    <div className="px-4 pt-4 pb-24" data-testid={`explore-section-${section}`}>
      <Link to="/explore" className="font-mono text-[10px] uppercase tracking-widest text-ink-muted hover:text-white flex items-center gap-1" data-testid="back-to-explore">
        <ChevronLeft className="w-3 h-3" /> Back to Explore
      </Link>
      <div className="font-display text-3xl mt-2 mb-4">{section.toUpperCase()}</div>

      {section === 'leaderboard' && (
        <div className="space-y-2" data-testid="leaderboard-list">
          {data.map((u, i) => (
            <div key={u.id} className="flex items-center gap-3 bg-bg-card border border-line p-3">
              <div className="w-10 font-display text-3xl text-accent-amber">#{i + 1}</div>
              <div className="flex-1">
                <div className="font-bold">{u.name}</div>
                <div className="font-mono text-[10px] text-ink-muted uppercase tracking-widest">{u.position} · {u.card_tier}</div>
              </div>
              <div className="font-mono font-bold text-2xl">{u.overall}</div>
            </div>
          ))}
        </div>
      )}

      {section === 'coach' && (
        <div className="space-y-3" data-testid="coaches-list">
          {data.map((c) => (
            <div key={c.id} className="bg-bg-card border border-line p-4">
              <div className="flex items-center gap-3">
                <div className="w-12 h-12 rounded-full bg-accent-green text-black font-bold flex items-center justify-center font-display text-xl">{c.name[0]}</div>
                <div className="flex-1">
                  <div className="font-bold">{c.name}</div>
                  <div className="font-mono text-[10px] text-ink-muted uppercase tracking-widest">★ {c.rating} · {c.sessions} sessions</div>
                </div>
                <div className="text-right">
                  <div className="font-mono font-bold">{fmtINR(c.price_per_hour)}</div>
                  <div className="font-mono text-[10px] text-ink-muted uppercase">per hour</div>
                </div>
              </div>
              <div className="text-xs text-ink-muted mt-2">{c.bio}</div>
            </div>
          ))}
        </div>
      )}

      {section === 'teams' && (
        <div className="grid grid-cols-2 gap-3">
          {data.map((t) => (
            <div key={t.id} className="bg-bg-card border border-line p-4">
              <div className="w-10 h-10" style={{ background: t.logo_color }} />
              <div className="font-display text-xl mt-2">{t.name.toUpperCase()}</div>
              <div className="font-mono text-[10px] uppercase tracking-widest text-ink-muted mt-1">{t.city} · {t.members} members</div>
              <div className="font-mono text-xs mt-2">🏆 {t.trophies}</div>
            </div>
          ))}
        </div>
      )}

      {section === 'partners' && (
        <div className="space-y-2">
          {data.map((p) => (
            <div key={p.id} className="bg-bg-card border border-line p-4 flex items-center justify-between">
              <div>
                <div className="font-bold">{p.name}</div>
                <div className="font-mono text-[10px] text-ink-muted uppercase">{p.category}</div>
              </div>
              <div className="bg-accent-amber text-black font-bold px-3 py-1 font-mono text-xs uppercase tracking-widest">{p.discount}</div>
            </div>
          ))}
        </div>
      )}

      {section === 'drills' && (
        <div className="space-y-2">
          {data.map((d) => (
            <div key={d.id} className="bg-bg-card border border-line p-4">
              <div className="font-display text-xl">{d.title.toUpperCase()}</div>
              <div className="flex gap-2 mt-2 font-mono text-[10px] uppercase">
                <span className="border border-line px-2 py-0.5">{d.duration}</span>
                <span className="border border-accent-green text-accent-green px-2 py-0.5">{d.difficulty}</span>
                <span className="border border-line px-2 py-0.5">{d.focus}</span>
              </div>
            </div>
          ))}
        </div>
      )}

      {section === 'events' && (
        <div className="space-y-2">
          {data.map((e) => (
            <div key={e.id} className="bg-bg-card border border-line p-4">
              <div className="font-display text-xl">{e.title.toUpperCase()}</div>
              <div className="font-mono text-[10px] uppercase tracking-widest text-ink-muted mt-1">{e.date} · {e.city}</div>
              <div className="font-mono text-accent-amber mt-2">{e.prize}</div>
            </div>
          ))}
        </div>
      )}

      {section === 'turfs' && (
        <div className="space-y-2">
          {data.map((t) => (
            <div key={t.id} className="bg-bg-card border border-line overflow-hidden">
              <div className="h-32 bg-cover bg-center" style={{ backgroundImage: `url(${t.image})` }} />
              <div className="p-4">
                <div className="font-display text-xl">{t.name.toUpperCase()}</div>
                <div className="font-mono text-[10px] text-ink-muted uppercase tracking-widest">{t.city} · {t.address}</div>
                <div className="flex justify-between items-center mt-2">
                  <span className="font-mono text-xs">★ {t.rating}</span>
                  <span className="font-mono font-bold">{fmtINR(t.price_per_slot)}</span>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {section === 'trophies' && (
        <div className="grid grid-cols-2 gap-3">
          {data.map((t) => (
            <div key={t.id} className={`p-4 border ${t.unlocked ? 'border-accent-amber bg-bg-card' : 'border-line opacity-50'}`}>
              <div className="font-display text-xl">{t.name.toUpperCase()}</div>
              <div className="font-mono text-[10px] uppercase mt-1" style={{ color: t.rarity === 'Legendary' ? '#FFD700' : t.rarity === 'Epic' ? '#FF3B30' : '#A1A1A1' }}>{t.rarity}</div>
              <div className="font-mono text-xs mt-1">{t.unlocked ? '✓ Unlocked' : 'Locked'}</div>
            </div>
          ))}
        </div>
      )}

      {section === 'tournaments' && (
        <div className="space-y-2">
          {data.map((t) => (
            <div key={t.id} className="bg-bg-card border border-line p-4">
              <div className="font-display text-xl">{t.name.toUpperCase()}</div>
              <div className="font-mono text-[10px] uppercase mt-1 text-accent-amber">{t.status}</div>
              <div className="font-mono text-xs mt-1">{t.teams} teams · Matchday {t.matchday}</div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
