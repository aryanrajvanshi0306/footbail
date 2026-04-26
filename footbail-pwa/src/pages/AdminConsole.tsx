import { useState } from "react";
import { Loader2, RefreshCw, Users, ShieldCheck, Server, Activity } from "lucide-react";
import { useAdminMetrics, useAdminUsers } from "../hooks/useDashboard";
import StatCard from "../components/StatCard";

interface ServiceHealth { name: string; status: string; color: string }
interface AdminData {
  stats: { val: string; label: string; delta?: string }[];
  recent_users: { id: string; name: string; role: string; phone?: string; email?: string }[];
  aws_health: ServiceHealth[];
  security_log: string[];
}

const TABS = ["Overview", "Users", "Infrastructure", "Security"] as const;
type Tab = typeof TABS[number];

export default function AdminConsole() {
  const [tab, setTab] = useState<Tab>("Overview");
  const { data, isLoading, refetch } = useAdminMetrics();
  const { data: users } = useAdminUsers();
  const dash = data as AdminData | undefined;

  if (isLoading) return (
    <div className="flex items-center justify-center h-64">
      <Loader2 size={32} className="text-[#00ff88] animate-spin" />
    </div>
  );

  return (
    <div className="p-6 max-w-7xl mx-auto animate-fade-in">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-white">Admin Console 🛡️</h1>
          <p className="text-sm text-[#6b7280] mt-0.5">footbAIl platform management</p>
        </div>
        <button onClick={() => refetch()}
          className="flex items-center gap-2 btn-secondary text-sm px-3 py-2">
          <RefreshCw size={14} /> Refresh
        </button>
      </div>

      {/* Tabs */}
      <div className="flex gap-1 mb-6 bg-[#13131a] border border-[#2a2a3d] rounded-xl p-1">
        {TABS.map((t) => (
          <button
            key={t}
            onClick={() => setTab(t)}
            className={`flex-1 py-2 px-4 rounded-lg text-sm font-medium transition-all
              ${tab === t ? "bg-[#00ff88] text-black" : "text-[#6b7280] hover:text-white"}`}
          >
            {t}
          </button>
        ))}
      </div>

      {/* Overview */}
      {tab === "Overview" && (
        <div className="space-y-6 animate-fade-in">
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
            {dash?.stats.map((s) => <StatCard key={s.label} {...s} />)}
          </div>

          <div className="grid lg:grid-cols-2 gap-6">
            <div className="card">
              <div className="flex items-center gap-2 mb-4">
                <Users size={16} className="text-[#00ff88]" />
                <h2 className="text-sm font-semibold text-[#6b7280] uppercase tracking-wider">Recent Users</h2>
              </div>
              <div className="space-y-2">
                {(dash?.recent_users ?? []).slice(0, 5).map((u) => (
                  <div key={u.id} className="flex items-center justify-between py-2 border-b border-[#2a2a3d] last:border-0">
                    <div>
                      <p className="text-sm text-white font-medium">{u.name}</p>
                      <p className="text-xs text-[#6b7280]">{u.phone ?? u.email ?? "—"}</p>
                    </div>
                    <span className={`text-xs px-2 py-0.5 rounded-full font-semibold capitalize
                      ${{ player:"bg-[#3b82f6]/20 text-[#3b82f6]",
                          coach:"bg-[#f59e0b]/20 text-[#f59e0b]",
                          referee:"bg-purple-500/20 text-purple-400",
                          admin:"bg-[#ef4444]/20 text-[#ef4444]" }[u.role] ?? ""}`}>
                      {u.role}
                    </span>
                  </div>
                ))}
              </div>
            </div>

            <div className="card">
              <div className="flex items-center gap-2 mb-4">
                <Activity size={16} className="text-[#00ff88]" />
                <h2 className="text-sm font-semibold text-[#6b7280] uppercase tracking-wider">Security Log</h2>
              </div>
              <div className="space-y-2">
                {(dash?.security_log ?? []).map((log, i) => (
                  <div key={i} className="flex items-center gap-3 py-2 text-sm border-b border-[#2a2a3d] last:border-0">
                    <span className="w-2 h-2 rounded-full bg-[#00ff88] flex-shrink-0" />
                    <span className="text-[#9ca3af]">{log}</span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Users */}
      {tab === "Users" && (
        <div className="card animate-fade-in">
          <h2 className="text-sm font-semibold text-[#6b7280] uppercase tracking-wider mb-4">All Users</h2>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-[#2a2a3d] text-[#6b7280] text-left">
                  <th className="pb-2 font-medium">Name</th>
                  <th className="pb-2 font-medium">Contact</th>
                  <th className="pb-2 font-medium">Role</th>
                  <th className="pb-2 font-medium">Verified</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[#2a2a3d]">
                {(users ?? []).map((u) => (
                  <tr key={u.id} className="hover:bg-[#2a2a3d]/30">
                    <td className="py-3 text-white font-medium">{u.name}</td>
                    <td className="py-3 text-[#9ca3af]">{u.phone ?? u.email ?? "—"}</td>
                    <td className="py-3 capitalize text-[#9ca3af]">{u.role}</td>
                    <td className="py-3">
                      {u.is_verified
                        ? <span className="text-[#00ff88] text-xs">✓ Yes</span>
                        : <span className="text-[#6b7280] text-xs">No</span>}
                    </td>
                  </tr>
                ))}
                {(!users || users.length === 0) && (
                  <tr><td colSpan={4} className="py-6 text-center text-[#6b7280]">No users yet</td></tr>
                )}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Infrastructure */}
      {tab === "Infrastructure" && (
        <div className="card animate-fade-in">
          <div className="flex items-center gap-2 mb-4">
            <Server size={16} className="text-[#00ff88]" />
            <h2 className="text-sm font-semibold text-[#6b7280] uppercase tracking-wider">Service Health</h2>
          </div>
          <div className="grid sm:grid-cols-2 gap-3">
            {(dash?.aws_health ?? []).map((svc) => (
              <div key={svc.name} className="flex items-center justify-between p-4
                                              bg-[#13131a] rounded-xl border border-[#2a2a3d]">
                <div className="flex items-center gap-3">
                  <span className="w-2.5 h-2.5 rounded-full bg-[#00ff88]" />
                  <span className="text-sm text-white">{svc.name}</span>
                </div>
                <span className="text-xs text-[#00ff88] font-semibold">{svc.status}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Security */}
      {tab === "Security" && (
        <div className="card animate-fade-in">
          <div className="flex items-center gap-2 mb-4">
            <ShieldCheck size={16} className="text-[#00ff88]" />
            <h2 className="text-sm font-semibold text-[#6b7280] uppercase tracking-wider">Security Events</h2>
          </div>
          <div className="space-y-2">
            {(dash?.security_log ?? []).map((log, i) => (
              <div key={i} className="flex items-center gap-3 p-3 bg-[#13131a] rounded-xl
                                      border border-[#2a2a3d] text-sm text-[#9ca3af]">
                <span className="w-2 h-2 rounded-full bg-[#00ff88] flex-shrink-0" />
                {log}
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
