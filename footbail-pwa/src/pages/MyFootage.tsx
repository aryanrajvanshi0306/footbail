import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { Film, Plus, Clock, CheckCircle, Loader2, AlertCircle } from "lucide-react";
import { useMyVideos } from "../hooks/useDashboard";
import VideoUpload from "../components/VideoUpload";

const StatusBadge = ({ status }: { status: string }) => {
  const cfg = {
    ready:      { icon: CheckCircle, color: "text-[#00ff88]", label: "Ready" },
    processing: { icon: Loader2,     color: "text-[#f59e0b]", label: "Processing" },
    uploading:  { icon: Clock,       color: "text-[#3b82f6]", label: "Uploading" },
    error:      { icon: AlertCircle, color: "text-[#ef4444]", label: "Error" },
  }[status] ?? { icon: Clock, color: "text-[#6b7280]", label: status };
  const Icon = cfg.icon;
  return (
    <span className={`flex items-center gap-1 text-xs font-semibold ${cfg.color}`}>
      <Icon size={12} className={status === "processing" ? "animate-spin" : ""} />
      {cfg.label}
    </span>
  );
};

export default function MyFootage() {
  const [showUpload, setShowUpload] = useState(false);
  const { data: videos = [], refetch } = useMyVideos();
  const navigate = useNavigate();

  return (
    <div className="p-6 max-w-6xl mx-auto animate-fade-in">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-white">My Footage 🎬</h1>
          <p className="text-sm text-[#6b7280] mt-0.5">{videos.length} video{videos.length !== 1 ? "s" : ""}</p>
        </div>
        <button onClick={() => setShowUpload(!showUpload)}
          className="btn-primary flex items-center gap-2 text-sm px-4 py-2">
          <Plus size={16} /> Upload
        </button>
      </div>

      {showUpload && (
        <div className="mb-6 animate-slide-up">
          <VideoUpload
            onComplete={() => { setShowUpload(false); refetch(); }}
          />
        </div>
      )}

      {videos.length === 0 && !showUpload ? (
        <div className="flex flex-col items-center justify-center py-20 text-center">
          <Film size={48} className="text-[#4b5563] mb-4" />
          <p className="text-white font-semibold text-lg mb-1">No footage yet</p>
          <p className="text-sm text-[#6b7280] mb-4">Upload your first match clip to get started</p>
          <button onClick={() => setShowUpload(true)} className="btn-primary px-5 py-2 text-sm">
            Upload Footage
          </button>
        </div>
      ) : (
        <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-4">
          {videos.map((v) => (
            <div
              key={v.id}
              onClick={() => v.status === "ready" && navigate(`/footage/${v.id}`)}
              className={`card group transition-all duration-200
                ${v.status === "ready"
                  ? "cursor-pointer hover:border-[#00ff88]/40 hover:bg-[#1a1a26]/80"
                  : "opacity-80"}`}
            >
              {/* Thumbnail */}
              <div className="aspect-video bg-[#0a0a0f] rounded-lg mb-3 overflow-hidden
                              flex items-center justify-center border border-[#2a2a3d]">
                {v.thumbnail_url ? (
                  <img src={v.thumbnail_url} alt="" className="w-full h-full object-cover" />
                ) : (
                  <Film size={28} className="text-[#4b5563]" />
                )}
              </div>

              <div className="flex items-start justify-between gap-2">
                <div className="min-w-0">
                  <p className="text-sm font-semibold text-white truncate">
                    {v.title ?? "Untitled clip"}
                  </p>
                  <p className="text-xs text-[#6b7280] mt-0.5">
                    {new Date(v.created_at).toLocaleDateString("en-IN")}
                    {v.duration_sec ? ` · ${Math.floor(v.duration_sec / 60)}m` : ""}
                  </p>
                </div>
                <StatusBadge status={v.status} />
              </div>

              {v.ai_analysis && (
                <p className="text-xs text-[#00ff88] mt-2">
                  🤖 {(v.ai_analysis.events_detected as number | undefined) ?? 0} events detected
                </p>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
