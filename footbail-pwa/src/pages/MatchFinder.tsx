import { useState } from "react";
import { Loader2, Search, MapPin, Clock, Users, ChevronRight } from "lucide-react";
import { useMatches } from "../hooks/useDashboard";

export default function MatchFinder() {
  const [city, setCity] = useState("");
  const [query, setQuery] = useState("");
  const [page, setPage] = useState(1);
  const { data, isLoading } = useMatches(page, query || undefined);

  const handleSearch = () => { setQuery(city); setPage(1); };

  const statusColor = (s: string) => ({
    scheduled: "bg-[#3b82f6]/20 text-[#3b82f6]",
    live:       "bg-[#ef4444]/20 text-[#ef4444] animate-pulse",
    completed:  "bg-[#6b7280]/20 text-[#6b7280]",
  }[s] ?? "bg-[#2a2a3d] text-[#9ca3af]");

  return (
    <div className="p-6 max-w-5xl mx-auto animate-fade-in">
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-white">Find a Match ⚽</h1>
        <p className="text-sm text-[#6b7280] mt-0.5">Browse upcoming games near you</p>
      </div>

      {/* Search bar */}
      <div className="flex gap-3 mb-6">
        <div className="flex-1 relative">
          <MapPin size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-[#6b7280]" />
          <input
            value={city}
            onChange={(e) => setCity(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && handleSearch()}
            placeholder="Filter by city (e.g. Mumbai)"
            className="w-full bg-[#13131a] border border-[#2a2a3d] rounded-xl pl-9 pr-4 py-3
                       text-white placeholder-[#4b5563] focus:outline-none focus:border-[#00ff88]
                       transition-colors text-sm"
          />
        </div>
        <button onClick={handleSearch} className="btn-primary px-5 flex items-center gap-2">
          <Search size={16} /> Search
        </button>
      </div>

      {isLoading ? (
        <div className="flex justify-center py-16">
          <Loader2 size={32} className="text-[#00ff88] animate-spin" />
        </div>
      ) : (
        <>
          <p className="text-xs text-[#6b7280] mb-4">{data?.total ?? 0} matches found</p>
          <div className="space-y-3">
            {(data?.items ?? []).map((m) => (
              <div key={m.id}
                className="card hover:border-[#00ff88]/30 hover:bg-[#1a1a26]/80
                           transition-all cursor-pointer group">
                <div className="flex items-center justify-between gap-4">
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 mb-2 flex-wrap">
                      <span className={`text-xs px-2 py-0.5 rounded-full font-semibold capitalize ${statusColor(m.status)}`}>
                        {m.status}
                      </span>
                      {m.city && (
                        <span className="flex items-center gap-1 text-xs text-[#6b7280]">
                          <MapPin size={11} /> {m.city}
                        </span>
                      )}
                    </div>
                    <div className="flex items-center gap-3">
                      <span className="text-white font-bold text-lg truncate">{m.home_team}</span>
                      <span className="text-[#6b7280] font-mono text-sm flex-shrink-0">
                        {m.status === "completed"
                          ? `${m.home_score}–${m.away_score}`
                          : "vs"}
                      </span>
                      <span className="text-white font-bold text-lg truncate">{m.away_team}</span>
                    </div>
                    <div className="flex items-center gap-1 mt-2 text-xs text-[#6b7280]">
                      <Clock size={11} />
                      {new Date(m.scheduled_at).toLocaleString("en-IN", {
                        dateStyle: "medium", timeStyle: "short"
                      })}
                    </div>
                  </div>
                  <ChevronRight size={18} className="text-[#4b5563] group-hover:text-[#00ff88] transition-colors flex-shrink-0" />
                </div>
              </div>
            ))}

            {(data?.items ?? []).length === 0 && (
              <div className="text-center py-16 text-[#6b7280]">
                <p className="text-lg mb-1">No matches found</p>
                <p className="text-sm">Try a different city or check back later</p>
              </div>
            )}
          </div>

          {/* Pagination */}
          {(data?.total ?? 0) > 20 && (
            <div className="flex justify-center gap-2 mt-6">
              <button onClick={() => setPage((p) => Math.max(1, p - 1))}
                disabled={page === 1}
                className="btn-secondary text-sm px-4 py-2 disabled:opacity-40">← Prev</button>
              <span className="flex items-center px-4 text-sm text-[#6b7280]">
                Page {page} of {Math.ceil((data?.total ?? 0) / 20)}
              </span>
              <button onClick={() => setPage((p) => p + 1)}
                disabled={page >= Math.ceil((data?.total ?? 0) / 20)}
                className="btn-secondary text-sm px-4 py-2 disabled:opacity-40">Next →</button>
            </div>
          )}
        </>
      )}
    </div>
  );
}
