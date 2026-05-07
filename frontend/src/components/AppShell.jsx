import React, { useEffect } from 'react';
import { Outlet, NavLink, useNavigate } from 'react-router-dom';
import { Home, Calendar, Rss, Compass, User } from 'lucide-react';
import { getUser, logout } from '../lib/api';
import { applyCityTheme, getCityTheme } from '../lib/cityTheme';

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

  // Apply city theme on mount & whenever user changes
  useEffect(() => { applyCityTheme(user?.city); }, [user?.city]);

  const theme = getCityTheme(user?.city);

  return (
    <div className="min-h-screen bg-bg pb-24 city-pattern" data-testid="app-shell">
      {/* Top bar */}
      <header className="sticky top-0 z-40 bg-bg/90 backdrop-blur-xl border-b border-line" data-testid="app-topbar">
        <div className="max-w-2xl mx-auto px-4 py-3 flex items-center justify-between">
          <div className="flex items-center gap-2.5">
            <div
              className="w-9 h-9 flex items-center justify-center font-display font-bold text-lg leading-none"
              style={{ background: theme.accent, color: '#0A0F1E', borderRadius: 10 }}
            >f</div>
            <div>
              <div className="font-display text-xl leading-none tracking-wide font-bold">footbAIl</div>
              <div className="text-[10px] text-ink-muted font-mono uppercase tracking-widest">
                {user?.role} · <span style={{ color: theme.accent }}>{user?.city || 'Mumbai'}</span>
              </div>
            </div>
          </div>
          <div className="flex items-center gap-2">
            {user?.role === 'admin' && (
              <button
                data-testid="go-admin-btn"
                onClick={() => nav('/admin')}
                className="text-[10px] font-mono uppercase tracking-widest px-2.5 py-1.5 border border-line rounded-lg hover:border-accent-amber hover:text-accent-amber transition-colors"
              >
                Admin
              </button>
            )}
            <button
              data-testid="logout-btn"
              onClick={logout}
              className="text-[10px] font-mono uppercase tracking-widest text-ink-muted px-2.5 py-1.5 hover:text-accent-red transition-colors"
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
      <nav className="fixed bottom-0 left-0 right-0 bg-bg-surface/95 backdrop-blur-xl border-t border-line z-40" data-testid="bottom-nav">
        <div className="max-w-2xl mx-auto grid grid-cols-5">
          {NAV.map(({ to, label, icon: Icon, testid }) => (
            <NavLink
              key={to}
              to={to}
              data-testid={testid}
              className={({ isActive }) =>
                `flex flex-col items-center justify-center gap-1 py-3 transition-colors ${
                  isActive ? 'text-accent-green' : 'text-ink-muted hover:text-ink'
                }`
              }
            >
              {({ isActive }) => (
                <>
                  <Icon className="w-5 h-5" strokeWidth={isActive ? 2.4 : 1.8} />
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
