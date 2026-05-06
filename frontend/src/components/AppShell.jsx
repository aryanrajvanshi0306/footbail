import React from 'react';
import { Outlet, NavLink, useNavigate } from 'react-router-dom';
import { Home, Calendar, Rss, Compass, User } from 'lucide-react';
import { getUser, logout } from '../lib/api';

const NAV = [
  { to: '/home', label: 'Home', icon: Home, testid: 'nav-home' },
  { to: '/matches', label: 'Matches', icon: Calendar, testid: 'nav-matches' },
  { to: '/feed', label: 'Feed', icon: Rss, testid: 'nav-feed' },
  { to: '/explore', label: 'Explore', icon: Compass, testid: 'nav-explore' },
  { to: '/profile', label: 'Profile', icon: User, testid: 'nav-profile' },
];

export default function AppShell() {
  const user = getUser();
  const nav = useNavigate();
  return (
    <div className="min-h-screen bg-bg pb-20">
      {/* Top bar */}
      <header className="sticky top-0 z-40 bg-bg/95 backdrop-blur border-b border-line" data-testid="app-topbar">
        <div className="max-w-2xl mx-auto px-4 py-3 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 bg-brand-primary flex items-center justify-center font-display text-xl leading-none tracking-tighter">f</div>
            <div>
              <div className="font-display text-xl leading-none tracking-wider">FOOTBAIL</div>
              <div className="text-[10px] text-ink-muted font-mono uppercase tracking-widest">{user?.role}</div>
            </div>
          </div>
          <div className="flex items-center gap-3">
            {user?.role === 'admin' && (
              <button
                data-testid="go-admin-btn"
                onClick={() => nav('/admin')}
                className="text-xs font-mono uppercase text-brand-accent border border-brand-accent px-2 py-1 hover:bg-brand-accent hover:text-black"
              >
                Admin
              </button>
            )}
            <button
              data-testid="logout-btn"
              onClick={logout}
              className="text-xs font-mono uppercase text-ink-muted hover:text-brand-primary"
            >
              Logout
            </button>
          </div>
        </div>
      </header>

      <main className="max-w-2xl mx-auto" data-testid="app-main">
        <Outlet />
      </main>

      {/* Bottom Nav */}
      <nav className="fixed bottom-0 left-0 right-0 bg-bg-elevated border-t border-line z-40" data-testid="bottom-nav">
        <div className="max-w-2xl mx-auto grid grid-cols-5">
          {NAV.map(({ to, label, icon: Icon, testid }) => (
            <NavLink
              key={to}
              to={to}
              data-testid={testid}
              className={({ isActive }) =>
                `flex flex-col items-center justify-center gap-0.5 py-3 transition-colors ${
                  isActive ? 'text-brand-primary' : 'text-ink-muted hover:text-white'
                }`
              }
            >
              {({ isActive }) => (
                <>
                  <Icon className="w-5 h-5" strokeWidth={isActive ? 2.5 : 1.8} />
                  <span className="text-[10px] font-mono uppercase tracking-wider">{label}</span>
                </>
              )}
            </NavLink>
          ))}
        </div>
      </nav>
    </div>
  );
}
