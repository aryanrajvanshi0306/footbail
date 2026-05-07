import React from 'react';
import { useNavigate } from 'react-router-dom';
import { Users, Handshake, Trophy, Dumbbell, CalendarDays, MapPinned, Award, Crown, Megaphone, Swords } from 'lucide-react';

const ITEMS = [
  { key: 'derby',       label: 'City Derby',  icon: Swords,       color: '#A78BFA' },
  { key: 'leaderboard', label: 'Leaderboard', icon: Crown,        color: '#F59E0B' },
  { key: 'coach',       label: 'Coach',       icon: Megaphone,    color: '#FF4D4D' },
  { key: 'teams',       label: 'Teams',       icon: Users,        color: '#38BDF8' },
  { key: 'partners',    label: 'Partners',    icon: Handshake,    color: '#FFB830' },
  { key: 'drills',      label: 'Drills',      icon: Dumbbell,     color: '#00E676' },
  { key: 'turfs',       label: 'Turfs',       icon: MapPinned,    color: '#94A3B8' },
  { key: 'trophies',    label: 'Trophies',    icon: Trophy,       color: '#FFD700' },
  { key: 'tournaments', label: 'Tournaments', icon: Award,        color: '#FF4D4D' },
];

export default function Explore() {
  const nav = useNavigate();
  return (
    <div className="px-4 pt-4 pb-24" data-testid="explore-page">
      <div>
        <div className="font-mono text-[10px] uppercase tracking-widest text-ink-muted">Discover</div>
        <div className="font-display text-3xl">EXPLORE</div>
      </div>

      <div className="grid grid-cols-3 gap-2 mt-4" data-testid="explore-grid">
        {ITEMS.map(({ key, label, icon: Icon, color }) => (
          <button
            key={key}
            data-testid={`explore-${key}`}
            onClick={() => nav(`/explore/${key}`)}
            className="aspect-square bg-bg-card border border-line flex flex-col items-center justify-center gap-2 hover:border-accent-green group transition-colors p-3"
          >
            <Icon className="w-7 h-7 transition-transform group-hover:scale-110" style={{ color }} />
            <span className="font-display text-base tracking-wider">{label.toUpperCase()}</span>
          </button>
        ))}
      </div>

      <div className="mt-6 bg-bg-card border border-line p-4" data-testid="explore-banner">
        <div className="font-mono text-[10px] uppercase tracking-widest text-accent-amber">FEATURED</div>
        <div className="font-display text-2xl mt-1">MUMBAI MONSOON CUP 2026</div>
        <div className="text-sm text-ink-muted mt-1">8 teams · ₹1,50,000 prize pool · Registrations open till 30 Jun</div>
      </div>
    </div>
  );
}
