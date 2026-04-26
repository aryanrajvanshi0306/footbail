import { Loader2 } from "lucide-react";
import { useDashboard } from "../hooks/useDashboard";
import { useAuthStore } from "../stores/authStore";
import StatCard from "../components/StatCard";

interface DashboardData {
  stats: { val: string; label: string; delta?: string; color?: string }[];
  recent_matches: {
    date: string; opponent: string; result: string; score: string;
    rating: number; goals: number; assists: number;
  }[];
  ai_insight: string;
  heatmap_data: number[];
  sparkline: number[];
}

export default function PlayerDashboard() {
  const { user } = useAuthStore();
  const { data, isLoading, isError } = useDashboard();
  const dash = data as DashboardData | undefined;

  if (isLoading) return (
    <div className="flex items-center justify-center h-64">
      <Loader2 size={32} className="text-[#00ff88] animate-spin" />
    </div>
  );

  if (isError) return (
    <div className="flex items-center justify-center h-64 text-[#ef4444]">
      Failed to load dashboard
    </div>
  );

  const sparkMax = Math.max(...(dash?.sparkline ?? [1]));
  const heatCols = 10;
  const heatRows = 8;

  return (
    <div className="p-6 max-w-7xl mx-auto animate-fade-in">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-white">
            Welcome back, <span className="text-[#00ff88]">{user?.name?.split(" ")[0]}</span> ⚽
          </h1>
          <p className="text-sm text-[#6b7280] mt-0.5">Season 2025–26 · Mumbai Division A</p>
        </div>
        <span className="hidden sm:block text-xs bg-[#00ff88]/10 text-[#00ff88] border border-[#00ff88]/20
                         px-3 py-1.5 rounded-full font-semibold uppercase tracking-wide">
          {user?.role}
        </span>
      </div>

      {/* Stat cards */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
        {dash?.stats.map((s) => (
          <StatCard key={s.label} {...s} />
        ))}
      </div>

      {/* AI Insight */}
      <div className="card mb-6 border-[#00ff88]/20 bg-[#00ff88]/5">
        <div className="flex items-start gap-3">
          <span className="text-2xl flex-shrink-0">🤖</span>
          <div>
            <p className="text-xs text-[#00ff88] font-semibold uppercase tracking-wider mb-1">
              AI Performance Insight
            </p>
            <p className="text-sm text-[#d1d5db] leading-relaxed">{dash?.ai_insight}</p>
          </div>
        </div>
      </div>

      <div className="grid lg:grid-cols-2 gap-6">
        {/* Recent Matches */}
        <div className="card">
          <h2 className="text-sm font-semibold text-[#6b7280] uppercase tracking-wider mb-4">
            Recent Matches
          </h2>
          <div className="space-y-3">
            {dash?.recent_matches.map((m, i) => (
              <div key={i} className="flex items-center justify-between py-2
                                      border-b border-[#2a2a3d] last:border-0">
                <div className="flex items-center gap-3">
                  <span className={`w-7 h-7 rounded-full flex items-center justify-center text-xs
                                   font-bold flex-shrink-0
                    ${m.result === "W" ? "bg-[#00ff88]/20 text-[#00ff88]"
                    : m.result === "L" ? "bg-[#ef4444]/20 text-[#ef4444]"
                    : "bg-[#f59e0b]/20 text-[#f59e0b]"}`}>
                    {m.result}
                  </span>
                  <div>
                    <p className="text-sm text-white font-medium">vs {m.opponent}</p>
                    <p className="text-xs text-[#6b7280]">{m.date} · {m.score}</p>
                  </div>
                </div>
                <div className="text-right">
                  <p className="text-sm font-bold text-[#00ff88]">{m.rating.toFixed(1)}</p>
                  <p className="text-xs text-[#6b7280]">{m.goals}G {m.assists}A</p>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Heatmap + Sparkline */}
        <div className="space-y-4">
          {/* Rating Sparkline */}
          <div className="card">
            <h2 className="text-sm font-semibold text-[#6b7280] uppercase tracking-wider mb-3">
              Rating Trend
            </h2>
            <div className="flex items-end gap-1 h-16">
              {dash?.sparkline.map((v, i) => (
                <div
                  key={i}
                  className="flex-1 rounded-sm bg-[#00ff88] transition-all"
                  style={{ height: `${(v / sparkMax) * 100}%`, opacity: 0.4 + (v / sparkMax) * 0.6 }}
                />
              ))}
            </div>
            <div className="flex justify-between text-xs text-[#6b7280] mt-1">
              <span>12 matches ago</span>
              <span className="text-[#00ff88] font-semibold">Now</span>
            </div>
          </div>

          {/* Pitch Heatmap */}
          <div className="card">
            <h2 className="text-sm font-semibold text-[#6b7280] uppercase tracking-wider mb-3">
              Pitch Heatmap
            </h2>
            <div
              className="w-full rounded-lg overflow-hidden border border-[#2a2a3d]"
              style={{ aspectRatio: "10/8" }}
            >
              <div
                className="w-full h-full grid"
                style={{ gridTemplateColumns: `repeat(${heatCols}, 1fr)` }}
              >
                {(dash?.heatmap_data ?? []).slice(0, heatCols * heatRows).map((v, i) => (
                  <div
                    key={i}
                    className="heatmap-cell"
                    style={{
                      background: `rgba(0, 255, 136, ${Math.min(v, 1) * 0.85})`,
                    }}
                  />
                ))}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
