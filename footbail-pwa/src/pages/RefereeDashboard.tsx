import { Loader2, Shield, CheckCircle, Clock, XCircle } from "lucide-react";
import { useDashboard } from "../hooks/useDashboard";
import { useAuthStore } from "../stores/authStore";
import StatCard from "../components/StatCard";

interface VARIncident {
  match: string; type: string; minute: number;
  confidence_pct: number; status: "Pending" | "Reviewed" | "Dismissed";
}
interface RefData {
  stats: { val: string; label: string; delta?: string }[];
  incidents: VARIncident[];
  ai_status: string;
}

const StatusBadge = ({ status }: { status: VARIncident["status"] }) => {
  const cfg = {
    Reviewed:  { color: "text-[#00ff88] bg-[#00ff88]/10 border-[#00ff88]/30", icon: CheckCircle },
    Pending:   { color: "text-[#f59e0b] bg-[#f59e0b]/10 border-[#f59e0b]/30", icon: Clock },
    Dismissed: { color: "text-[#6b7280] bg-[#6b7280]/10 border-[#6b7280]/30", icon: XCircle },
  }[status];
  const Icon = cfg.icon;
  return (
    <span className={`flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-semibold border ${cfg.color}`}>
      <Icon size={11} /> {status}
    </span>
  );
};

export default function RefereeDashboard() {
  const { user } = useAuthStore();
  const { data, isLoading } = useDashboard();
  const dash = data as RefData | undefined;

  if (isLoading) return (
    <div className="flex items-center justify-center h-64">
      <Loader2 size={32} className="text-[#00ff88] animate-spin" />
    </div>
  );

  return (
    <div className="p-6 max-w-6xl mx-auto animate-fade-in">
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-white">
          VAR Panel, <span className="text-[#00ff88]">{user?.name?.split(" ")[0]}</span> 🟨
        </h1>
        <p className="text-sm text-[#6b7280] mt-0.5">Real-time AI-assisted officiating</p>
      </div>

      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
        {dash?.stats.map((s) => <StatCard key={s.label} {...s} />)}
      </div>

      {/* AI Engine Status */}
      <div className="card mb-6 border-[#3b82f6]/20 bg-[#3b82f6]/5">
        <div className="flex items-center gap-2 mb-1">
          <Shield size={16} className="text-[#3b82f6]" />
          <span className="text-xs font-semibold text-[#3b82f6] uppercase tracking-wider">AI Engine Status</span>
        </div>
        <p className="text-sm text-[#d1d5db]">{dash?.ai_status}</p>
      </div>

      {/* VAR Incidents */}
      <div className="card">
        <h2 className="text-sm font-semibold text-[#6b7280] uppercase tracking-wider mb-4">VAR Incidents</h2>
        <div className="space-y-3">
          {dash?.incidents.map((inc, i) => (
            <div key={i} className="p-4 bg-[#13131a] rounded-xl border border-[#2a2a3d]
                                    hover:border-[#3b82f6]/40 transition-all">
              <div className="flex flex-wrap items-start justify-between gap-2">
                <div>
                  <p className="text-white font-medium text-sm">{inc.match}</p>
                  <div className="flex items-center gap-2 mt-1 flex-wrap">
                    <span className="text-xs px-2 py-0.5 bg-[#2a2a3d] text-[#9ca3af] rounded font-mono">
                      {inc.type}
                    </span>
                    <span className="text-xs text-[#6b7280]">{inc.minute}'</span>
                    <span className="text-xs text-[#f59e0b] font-semibold">
                      {inc.confidence_pct}% confidence
                    </span>
                  </div>
                </div>
                <StatusBadge status={inc.status} />
              </div>
              {inc.status === "Pending" && (
                <div className="flex gap-2 mt-3">
                  <button className="btn-primary text-xs px-3 py-1.5">Review Clip</button>
                  <button className="btn-secondary text-xs px-3 py-1.5">Dismiss</button>
                </div>
              )}
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
