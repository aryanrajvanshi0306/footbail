import React, { useEffect, useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { Users, MapPin, Tv, ArrowRight, Activity } from 'lucide-react';
import { api, getUser, logout } from '../../lib/api';

export default function AdminDashboard() {
  const me = getUser();
  const nav = useNavigate();
  const [stats, setStats] = useState({});
  useEffect(() => { api.get('/admin/stats').then((r) => setStats(r.data)); }, []);

  return (
    <div className="min-h-screen bg-bg" data-testid="admin-dashboard">
      <header className="border-b border-line">
        <div className="max-w-6xl mx-auto px-6 py-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 bg-accent-green text-black font-bold flex items-center justify-center font-display text-2xl leading-none">f</div>
            <div>
              <div className="font-display text-2xl tracking-wider">FOOTBAIL · CONTROL ROOM</div>
              <div className="font-mono text-[10px] text-ink-muted uppercase tracking-widest">{me?.name} · ADMIN</div>
            </div>
          </div>
          <div className="flex gap-2">
            <Link to="/home" data-testid="admin-to-app" className="border border-line px-3 h-9 inline-flex items-center font-mono uppercase text-xs tracking-widest hover:border-accent-green">App View</Link>
            <button onClick={logout} className="border border-line px-3 h-9 font-mono uppercase text-xs tracking-widest hover:border-accent-green">Logout</button>
          </div>
        </div>
      </header>

      <main className="max-w-6xl mx-auto px-6 py-6">
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3" data-testid="admin-stat-grid">
          {[
            ['Players', stats.players ?? '—'],
            ['Coaches', stats.coaches ?? '—'],
            ['Referees', stats.referees ?? '—'],
            ['Turf Owners', stats.turf_owners ?? '—'],
            ['Turfs', stats.turfs ?? '—'],
            ['Matches', stats.matches_total ?? '—'],
            ['Live Now', stats.matches_live ?? 0, '#FF3B30'],
            ['Posts', stats.posts ?? '—'],
          ].map(([l, v, color]) => (
            <div key={l} className="bg-bg-card border border-line p-4">
              <div className="font-mono text-[10px] uppercase tracking-widest text-ink-muted">{l}</div>
              <div className="font-display text-4xl mt-1" style={{ color: color || '#fff' }}>{v}</div>
            </div>
          ))}
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-3 mt-6" data-testid="admin-action-cards">
          <ActionCard
            testid="action-users" to="/admin/users"
            title="USERS" subtitle="Create Turf Owners & Referees · View all"
            icon={Users}
          />
          <ActionCard
            testid="action-turfs" to="/admin/turfs"
            title="TURFS" subtitle="Add new turfs to the network"
            icon={MapPin}
          />
          <ActionCard
            testid="action-control" to="/admin/match-control"
            title="MATCH CONTROL" subtitle="Schedule match → camera goes live"
            icon={Tv} highlight
          />
        </div>

        <div className="mt-6">
          <div className="font-mono text-[10px] uppercase tracking-widest text-ink-muted">SYSTEM</div>
          <div className="bg-bg-card border border-line p-4 flex items-center gap-3 mt-2">
            <Activity className="w-5 h-5 text-status-success" />
            <div className="flex-1">
              <div className="font-mono text-sm">All systems operational · Camera grid ONLINE · AI offside service READY</div>
              <div className="font-mono text-[10px] text-ink-muted uppercase tracking-widest">ap-south-1 · 2026.05</div>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}

function ActionCard({ to, title, subtitle, icon: Icon, highlight, testid }) {
  return (
    <Link
      data-testid={testid}
      to={to}
      className={`block p-5 border ${highlight ? 'border-accent-green bg-accent-green text-black/10 hover:bg-accent-green text-black/20' : 'border-line bg-bg-card hover:border-accent-green'} transition-colors`}
    >
      <Icon className="w-7 h-7 mb-3 text-accent-green" />
      <div className="font-display text-2xl tracking-wider">{title}</div>
      <div className="text-xs text-ink-muted mt-1">{subtitle}</div>
      <div className="flex justify-end mt-3"><ArrowRight className="w-4 h-4" /></div>
    </Link>
  );
}
