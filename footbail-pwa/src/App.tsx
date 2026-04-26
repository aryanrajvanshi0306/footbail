import { Navigate, Route, Routes } from "react-router-dom";
import { useAuthStore } from "./stores/authStore";
import Layout from "./components/Layout";
import RoleGuard from "./components/RoleGuard";

// Pages
import Login              from "./pages/Login";
import Dashboard          from "./pages/Dashboard";
import PlayerDashboard    from "./pages/PlayerDashboard";
import CoachDashboard     from "./pages/CoachDashboard";
import RefereeDashboard   from "./pages/RefereeDashboard";
import AdminConsole       from "./pages/AdminConsole";
import MatchFinder        from "./pages/MatchFinder";
import MatchFootageViewer from "./pages/MatchFootageViewer";
import MyFootage          from "./pages/MyFootage";
import CoachConnect       from "./pages/CoachConnect";
import SmartTurfMap       from "./pages/SmartTurfMap";
import DigitalCV          from "./pages/DigitalCV";
import NotFound           from "./pages/NotFound";

function RequireAuth({ children }: { children: React.ReactNode }) {
  const { isAuthenticated } = useAuthStore();
  if (!isAuthenticated) return <Navigate to="/login" replace />;
  return <Layout>{children}</Layout>;
}

export default function App() {
  return (
    <Routes>
      {/* Public */}
      <Route path="/login" element={<Login />} />

      {/* Protected — all roles */}
      <Route path="/dashboard" element={<RequireAuth><Dashboard /></RequireAuth>} />
      <Route path="/matches"   element={<RequireAuth><MatchFinder /></RequireAuth>} />
      <Route path="/coaches"   element={<RequireAuth><CoachConnect /></RequireAuth>} />
      <Route path="/turfs"     element={<RequireAuth><SmartTurfMap /></RequireAuth>} />
      <Route path="/cv"        element={<RequireAuth><DigitalCV /></RequireAuth>} />
      <Route path="/cv/:playerId" element={<RequireAuth><DigitalCV /></RequireAuth>} />

      {/* Player + Admin */}
      <Route path="/footage"   element={
        <RequireAuth>
          <RoleGuard allowed={["player", "admin"]}>
            <MyFootage />
          </RoleGuard>
        </RequireAuth>
      } />
      <Route path="/footage/:videoId" element={<RequireAuth><MatchFootageViewer /></RequireAuth>} />
      <Route path="/upload" element={
        <RequireAuth>
          <RoleGuard allowed={["player", "admin"]}>
            <MyFootage />
          </RoleGuard>
        </RequireAuth>
      } />

      {/* Coach-specific */}
      <Route path="/squad" element={
        <RequireAuth>
          <RoleGuard allowed={["coach", "admin"]}>
            <CoachDashboard />
          </RoleGuard>
        </RequireAuth>
      } />

      {/* Referee */}
      <Route path="/var" element={
        <RequireAuth>
          <RoleGuard allowed={["referee", "admin"]}>
            <RefereeDashboard />
          </RoleGuard>
        </RequireAuth>
      } />

      {/* Admin */}
      <Route path="/admin/users"     element={<RequireAuth><RoleGuard allowed={["admin"]}><AdminConsole /></RoleGuard></RequireAuth>} />
      <Route path="/admin/turfs"     element={<RequireAuth><RoleGuard allowed={["admin"]}><AdminConsole /></RoleGuard></RequireAuth>} />
      <Route path="/admin/analytics" element={<RequireAuth><RoleGuard allowed={["admin"]}><AdminConsole /></RoleGuard></RequireAuth>} />

      {/* Default */}
      <Route path="/" element={<Navigate to="/dashboard" replace />} />
      <Route path="*" element={<NotFound />} />
    </Routes>
  );
}
