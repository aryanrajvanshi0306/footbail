import { useAuthStore } from "../stores/authStore";
import PlayerDashboard from "./PlayerDashboard";
import CoachDashboard from "./CoachDashboard";
import RefereeDashboard from "./RefereeDashboard";
import AdminConsole from "./AdminConsole";

export default function Dashboard() {
  const { user } = useAuthStore();
  switch (user?.role) {
    case "coach":   return <CoachDashboard />;
    case "referee": return <RefereeDashboard />;
    case "admin":   return <AdminConsole />;
    default:        return <PlayerDashboard />;
  }
}
