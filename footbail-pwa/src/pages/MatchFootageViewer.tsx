import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { useParams, useNavigate } from "react-router-dom";
import { Loader2, MessageSquare, Plus, AlertCircle } from "lucide-react";
import HLSPlayer from "../components/HLSPlayer";
import { footageApi, api } from "../api/client";

interface Annotation {
  id: string;
  timestamp_sec: number;
  comment: string | null;
  created_at: string;
}

interface VideoOut {
  id: string; status: string; title: string | null;
  processed_hls_url: string | null; ai_analysis: Record<string, unknown> | null;
  duration_sec: number | null;
}

export default function MatchFootageViewer() {
  const { videoId } = useParams<{ videoId: string }>();
  const navigate = useNavigate();
  const [newComment, setNewComment] = useState("");
  const [addingAt, setAddingAt] = useState<number | null>(null);

  const { data: video, isLoading: vidLoading } = useQuery<VideoOut>({
    queryKey: ["video", videoId],
    queryFn: () => api.get(`/footage/${videoId}`),
    enabled: !!videoId,
    refetchInterval: (d) =>
      d.state.data?.status === "processing" ? 5000 : false,
  });

  const { data: streamData } = useQuery<{ hls_url: string }>({
    queryKey: ["video-stream", videoId],
    queryFn: () => footageApi.stream(videoId!),
    enabled: !!videoId && video?.status === "ready",
  });

  const { data: annotations = [], refetch: refetchAnnotations } = useQuery<Annotation[]>({
    queryKey: ["annotations", videoId],
    queryFn: () => api.get(`/footage/${videoId}/annotations`),
    enabled: !!videoId,
  });

  const addAnnotation = async () => {
    if (!newComment.trim() || addingAt === null) return;
    await api.post(`/footage/${videoId}/annotate`, {
      video_id: videoId,
      timestamp_sec: addingAt,
      comment: newComment,
    });
    setNewComment("");
    setAddingAt(null);
    refetchAnnotations();
  };

  if (!videoId) return <div className="p-6 text-[#ef4444]">No video ID</div>;
  if (vidLoading) return (
    <div className="flex items-center justify-center h-64">
      <Loader2 size={32} className="text-[#00ff88] animate-spin" />
    </div>
  );

  return (
    <div className="p-6 max-w-6xl mx-auto animate-fade-in">
      <button onClick={() => navigate(-1)}
        className="text-[#00ff88] text-sm mb-4 hover:underline">← Back</button>

      <h1 className="text-xl font-bold text-white mb-4">
        {video?.title ?? "Match Footage"}
      </h1>

      <div className="grid lg:grid-cols-3 gap-6">
        {/* Player */}
        <div className="lg:col-span-2 space-y-4">
          {video?.status === "ready" && streamData?.hls_url ? (
            <HLSPlayer src={streamData.hls_url} className="w-full" />
          ) : video?.status === "processing" ? (
            <div className="aspect-video bg-[#13131a] rounded-xl border border-[#2a2a3d]
                            flex flex-col items-center justify-center gap-3">
              <Loader2 size={36} className="text-[#00ff88] animate-spin" />
              <p className="text-[#9ca3af] text-sm">AI is processing your footage…</p>
              <div className="flex items-center gap-2 text-xs text-[#6b7280]">
                <span className="w-2 h-2 rounded-full bg-[#00ff88] animate-pulse" />
                YOLOv10 + ByteTrack running
              </div>
            </div>
          ) : video?.status === "error" ? (
            <div className="aspect-video bg-[#13131a] rounded-xl border border-[#ef4444]/30
                            flex flex-col items-center justify-center gap-3">
              <AlertCircle size={36} className="text-[#ef4444]" />
              <p className="text-[#9ca3af] text-sm">Processing failed. Please re-upload.</p>
            </div>
          ) : (
            <div className="aspect-video bg-[#13131a] rounded-xl border border-[#2a2a3d]
                            flex items-center justify-center">
              <p className="text-[#6b7280]">Uploading…</p>
            </div>
          )}

          {/* AI Analysis */}
          {video?.ai_analysis && (
            <div className="card border-[#00ff88]/20 bg-[#00ff88]/5">
              <p className="text-xs font-semibold text-[#00ff88] uppercase tracking-wider mb-2">
                🤖 AI Analysis
              </p>
              <div className="grid grid-cols-3 gap-3 text-center">
                {[
                  { label: "Events", val: video.ai_analysis.events_detected as number ?? 0 },
                  { label: "Model", val: "YOLOv10" },
                  { label: "Latency", val: `${video.ai_analysis.inference_ms ?? 0}ms` },
                ].map((item) => (
                  <div key={item.label} className="bg-[#13131a] rounded-lg p-3">
                    <p className="text-lg font-bold text-[#00ff88]">{item.val}</p>
                    <p className="text-xs text-[#6b7280]">{item.label}</p>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* Annotations sidebar */}
        <div className="space-y-4">
          <div className="card">
            <div className="flex items-center gap-2 mb-3">
              <MessageSquare size={16} className="text-[#00ff88]" />
              <h2 className="text-sm font-semibold text-white">Annotations</h2>
            </div>

            {/* Add annotation */}
            <div className="mb-4 space-y-2">
              <input
                type="number"
                placeholder="Timestamp (seconds)"
                value={addingAt ?? ""}
                onChange={(e) => setAddingAt(Number(e.target.value))}
                className="w-full bg-[#0a0a0f] border border-[#2a2a3d] rounded-lg px-3 py-2
                           text-white text-sm focus:outline-none focus:border-[#00ff88]"
              />
              <textarea
                placeholder="Add a coaching note…"
                value={newComment}
                onChange={(e) => setNewComment(e.target.value)}
                rows={2}
                className="w-full bg-[#0a0a0f] border border-[#2a2a3d] rounded-lg px-3 py-2
                           text-white text-sm focus:outline-none focus:border-[#00ff88] resize-none"
              />
              <button onClick={addAnnotation}
                disabled={!newComment.trim() || addingAt === null}
                className="btn-primary w-full text-sm py-2 flex items-center justify-center gap-2">
                <Plus size={14} /> Add Annotation
              </button>
            </div>

            {/* List */}
            <div className="space-y-2 max-h-80 overflow-y-auto">
              {annotations.length === 0 ? (
                <p className="text-xs text-[#6b7280] text-center py-4">No annotations yet</p>
              ) : (
                annotations.map((ann) => (
                  <div key={ann.id} className="p-3 bg-[#13131a] rounded-lg border border-[#2a2a3d]">
                    <div className="flex items-center gap-2 mb-1">
                      <span className="text-xs font-mono text-[#00ff88]">
                        {Math.floor(ann.timestamp_sec / 60)}:{String(ann.timestamp_sec % 60).padStart(2, "0")}
                      </span>
                    </div>
                    <p className="text-xs text-[#d1d5db]">{ann.comment}</p>
                  </div>
                ))
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
