import React, { useEffect } from 'react';
import { BrowserRouter, Routes, Route, Navigate, useLocation } from 'react-router-dom';
import { Toaster } from 'sonner';
import { api, getUser } from './lib/api';
import Login from './pages/Login';
import Register from './pages/Register';
import Home from './pages/Home';
import Matches from './pages/Matches';
import CreateMatch from './pages/CreateMatch';
import MatchDetail from './pages/MatchDetail';
import Feed from './pages/Feed';
import Explore from './pages/Explore';
import ExploreSection from './pages/ExploreSection';
import Profile from './pages/Profile';
import AdminDashboard from './pages/admin/Dashboard';
import AdminUsers from './pages/admin/Users';
import AdminTurfs from './pages/admin/Turfs';
import AdminMatchControl from './pages/admin/MatchControl';
import VARRoom from './pages/VARRoom';
import LiveBroadcast from './pages/LiveBroadcast';
import MatchAnalysis from './pages/MatchAnalysis';
import MatchBrief from './pages/MatchBrief';
import CityDerby from './pages/CityDerby';
import AppShell from './components/AppShell';

function Protected({ children, roles }) {
  const u = getUser();
  const loc = useLocation();
  if (!u) return <Navigate to="/login" state={{ from: loc }} replace />;
  if (roles && !roles.includes(u.role)) return <Navigate to="/home" replace />;
  return children;
}

function SeedBoot() {
  useEffect(() => {
    api.post('/admin/seed').catch(() => {}); // idempotent; ignore errors
  }, []);
  return null;
}

export default function App() {
  return (
    <BrowserRouter>
      <SeedBoot />
      <Toaster position="top-center" theme="dark" toastOptions={{ style: { background: '#111', border: '1px solid #262626', color: '#fff', borderRadius: 0 } }} />
      <Routes>
        <Route path="/" element={<Navigate to="/home" replace />} />
        <Route path="/login" element={<Login />} />
        <Route path="/register" element={<Register />} />

        {/* Player / Coach app */}
        <Route element={<Protected><AppShell /></Protected>}>
          <Route path="/home" element={<Home />} />
          <Route path="/matches" element={<Matches />} />
          <Route path="/matches/create" element={<CreateMatch />} />
          <Route path="/matches/:id" element={<MatchDetail />} />
          <Route path="/feed" element={<Feed />} />
          <Route path="/explore" element={<Explore />} />
          <Route path="/explore/derby" element={<CityDerby />} />
          <Route path="/explore/:section" element={<ExploreSection />} />
          <Route path="/profile" element={<Profile />} />
        </Route>

        {/* Broadcast & analysis (public-ish, uses login) */}
        <Route path="/broadcast/:id" element={<Protected><LiveBroadcast /></Protected>} />
        <Route path="/match/:id/analysis" element={<Protected><MatchAnalysis /></Protected>} />
        <Route path="/match/:id/brief" element={<Protected><MatchBrief /></Protected>} />

        {/* Admin */}
        <Route path="/admin" element={<Protected roles={['admin']}><AdminDashboard /></Protected>} />
        <Route path="/admin/users" element={<Protected roles={['admin']}><AdminUsers /></Protected>} />
        <Route path="/admin/turfs" element={<Protected roles={['admin']}><AdminTurfs /></Protected>} />
        <Route path="/admin/match-control" element={<Protected roles={['admin']}><AdminMatchControl /></Protected>} />
        <Route path="/admin/var/:id" element={<Protected roles={['admin', 'referee']}><VARRoom /></Protected>} />

        <Route path="*" element={<Navigate to="/home" replace />} />
      </Routes>
    </BrowserRouter>
  );
}
