import { Loader2, Brain, Calendar, TrendingUp, TrendingDown, Minus } from "lucide-react";
import { useDashboard } from "../hooks/useDashboard";
import { useAuthStore } from "../stores/authStore";
import StatCard from "../components/StatCard";

interface PlayerRow {
  name: string; pos: string; rating: number;
  form: "↑" | "→" | "↓"; goals: number; fatigue_pct: number;
}
interface CoachData {
  stats: { val: string; label: string; delta?: string }[];
  squad: PlayerRow[];
  next_session: { title: string; date: string; time: string; venue: string };
  ai_suggestion: string;
}

const FormIcon = ({ form }: { form: string }) =>
  form === "↑" ? <TrendingUp size={14} className="text-[#00ff88]" />
  : form === "↓" ? <TrendingDown size={14} className="text-[#ef4444]" />
  : <Minus size={14} className="text-[#f59e0b]" />;

export default function CoachDashboard() {
  const { user } = useAuthStore();
  const { data, isLoading } = useDashboard();
  const dash = data as CoachData | undefined;

  if (isLoading) return (
    <div className="flex items-center justify-center h-64">
      <Loader2 size={32} className="text-[#00ff88] animate-spin" />
    </div>
  );

  return (
    <div className="p-6 max-w-7xl mx-auto animate-fade-in">
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-white">
          Coach Dashboard, <span className="text-[#00ff88]">{user?.name?.split(" ")[0]}</span> 📋
        </h1>
        <p className="text-sm text-[#6b7280] mt-0.5">Squad overview · Season 2025–26</p>
      </div>

      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
        {dash?.stats.map((s) => <StatCard key={s.label} {...s} />)}
      </div>

      <div className="grid lg:grid-cols-3 gap-6">
        {/* Squad Table */}
        <div className="lg:col-span-2 card">
          <h2 className="text-sm font-semibold text-[#6b7280] uppercase tracking-wider mb-4">Squad Performance</h2>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-[#2a2a3d] text-[#6b7280] text-left">
                  <th className="pb-2 font-medium">Player</th>
                  <th className="pb-2 font-medium">Pos</th>
                  <th className="pb-2 font-medium">Rating</th>
                  <th className="pb-2 font-medium">Form</th>
                  <th className="pb-2 font-medium">Goals</th>
                  <th className="pb-2 font-medium">Fatigue</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[#2a2a3d]">
                {dash?.squad.map((p) => (
                  <tr key={p.name} className="hover:bg-[#2a2a3d]/30 transition-colors">
                    <td className="py-3 font-medium text-white">{p.name}</td>
                    <td className="py-3">
                      <span className="px-2 py-0.5 rounded text-xs bg-[#2a2a3d] text-[#9ca3af] font-mono">{p.pos}</span>
                    </td>
                    <td className="py-3 text-[#00ff88] font-bold">{p.rating.toFixed(1)}</td>
                    <td className="py-3"><FormIcon form={p.form} /></td>
                    <td className="py-3 text-white">{p.goals}</td>
                    <td className="py-3 w-24">
                      <div className="flex items-center gap-2">
                        <div className="flex-1 h-1.5 bg-[#2a2a3d] rounded-full overflow-hidden">
                          <div
                            className="h-full rounded-full transition-all"
                            style={{
                              width: `${p.fatigue_pct}%`,
                              background: p.fatigue_pct > 80 ? "#ef4444" : p.fatigue_pct > 60 ? "#f59e0b" : "#00ff88",
                            }}
                          />
                        </div>
                        <span className="text-xs text-[#6b7280] w-8">{p.fatigue_pct}%</span>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        {/* Sidebar */}
        <div className="space-y-4">
          {/* AI Suggestion */}
          <div className="card border-[#00ff88]/20 bg-[#00ff88]/5">
            <div className="flex items-center gap-2 mb-2">
              <Brain size={16} className="text-[#00ff88]" />
              <span className="text-xs font-semibold text-[#00ff88] uppercase tracking-wider">AI Suggestion</span>
            </div>
            <p className="text-sm text-[#d1d5db] leading-relaxed">{dash?.ai_suggestion}</p>
          </div>

          {/* Next Session */}
          {dash?.next_session && (
            <div className="card">
              <div className="flex items-center gap-2 mb-3">
                <Calendar size={16} className="text-[#f59e0b]" />
                <span className="text-xs font-semibold text-[#f59e0b] uppercase tracking-wider">Next Session</span>
              </div>
              <p className="text-white font-bold">{dash.next_session.title}</p>
              <p className="text-sm text-[#9ca3af] mt-1">{dash.next_session.date} · {dash.next_session.time}</p>
              <p className="text-xs text-[#6b7280] mt-1">{dash.next_session.venue}</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
