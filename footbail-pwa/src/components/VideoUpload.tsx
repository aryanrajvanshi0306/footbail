/**
 * VideoUpload — drag-and-drop or click-to-select video uploader.
 * Flow: getUploadUrl → PUT to S3 with XHR progress → confirm → Celery processes.
 */
import { useCallback, useRef, useState } from "react";
import { CheckCircle, Film, Upload, X, AlertCircle } from "lucide-react";
import { footageApi, uploadToS3WithProgress } from "../api/client";
import { useQueryClient } from "@tanstack/react-query";

type Phase = "idle" | "uploading" | "processing" | "done" | "error";

interface Props {
  matchId?: string;
  onComplete?: (videoId: string) => void;
}

export default function VideoUpload({ matchId, onComplete }: Props) {
  const [phase, setPhase] = useState<Phase>("idle");
  const [progress, setProgress] = useState(0);
  const [error, setError] = useState<string | null>(null);
  const [videoId, setVideoId] = useState<string | null>(null);
  const [dragOver, setDragOver] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);
  const qc = useQueryClient();

  const reset = () => {
    setPhase("idle");
    setProgress(0);
    setError(null);
    setVideoId(null);
  };

  const handleFile = useCallback(
    async (file: File) => {
      if (!file.type.startsWith("video/")) {
        setError("Please select a video file (MP4, MOV, etc.)");
        setPhase("error");
        return;
      }
      if (file.size > 2 * 1024 * 1024 * 1024) {
        setError("File too large. Maximum size is 2 GB.");
        setPhase("error");
        return;
      }

      setPhase("uploading");
      setProgress(0);
      setError(null);

      try {
        // 1. Get presigned upload URL
        const { upload_url, object_key, video_id } = await footageApi.getUploadUrl(
          file.name,
          file.type,
          matchId,
        );
        setVideoId(video_id);

        // 2. Upload directly to S3/LocalStack via XHR (shows real progress)
        await uploadToS3WithProgress(upload_url, file, (pct) => setProgress(pct));

        // 3. Notify backend → triggers Celery job
        setPhase("processing");
        await footageApi.confirm(video_id, object_key, file.size);

        setPhase("done");
        qc.invalidateQueries({ queryKey: ["my-videos"] });
        onComplete?.(video_id);
      } catch (err) {
        const msg = err instanceof Error ? err.message : "Upload failed";
        setError(msg);
        setPhase("error");
      }
    },
    [matchId, onComplete, qc],
  );

  const onDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setDragOver(false);
    const file = e.dataTransfer.files[0];
    if (file) handleFile(file);
  };

  // ── Render ────────────────────────────────────────────────────────────────

  if (phase === "done") {
    return (
      <div className="card flex flex-col items-center gap-4 py-10 text-center animate-fade-in">
        <CheckCircle size={48} className="text-[#00ff88]" />
        <div>
          <p className="text-lg font-bold text-white">Upload Complete!</p>
          <p className="text-sm text-[#6b7280] mt-1">
            AI analysis is running in the background. Check your footage gallery shortly.
          </p>
        </div>
        <button onClick={reset} className="btn-secondary text-sm px-4 py-2">
          Upload Another
        </button>
      </div>
    );
  }

  if (phase === "error") {
    return (
      <div className="card flex flex-col items-center gap-4 py-10 text-center">
        <AlertCircle size={48} className="text-[#ef4444]" />
        <div>
          <p className="text-lg font-bold text-white">Upload Failed</p>
          <p className="text-sm text-[#6b7280] mt-1">{error}</p>
        </div>
        <button onClick={reset} className="btn-primary text-sm px-4 py-2">Try Again</button>
      </div>
    );
  }

  if (phase === "uploading" || phase === "processing") {
    return (
      <div className="card flex flex-col items-center gap-6 py-10">
        <Film size={40} className="text-[#00ff88] animate-pulse" />
        <div className="w-full max-w-sm">
          <div className="flex justify-between text-sm mb-2">
            <span className="text-[#9ca3af]">
              {phase === "uploading" ? "Uploading…" : "Processing with AI…"}
            </span>
            <span className="text-[#00ff88] font-mono">
              {phase === "uploading" ? `${progress}%` : "⚡"}
            </span>
          </div>
          <div className="h-2 bg-[#2a2a3d] rounded-full overflow-hidden">
            {phase === "uploading" ? (
              <div
                className="h-full bg-[#00ff88] rounded-full transition-all duration-200"
                style={{ width: `${progress}%` }}
              />
            ) : (
              <div className="h-full relative overflow-hidden bg-[#2a2a3d] rounded-full progress-indeterminate" />
            )}
          </div>
          {phase === "processing" && (
            <p className="text-xs text-[#6b7280] mt-2 text-center">
              YOLOv10 + ByteTrack is analysing your footage…
            </p>
          )}
        </div>
      </div>
    );
  }

  // Idle drop zone
  return (
    <div
      onDrop={onDrop}
      onDragOver={(e) => { e.preventDefault(); setDragOver(true); }}
      onDragLeave={() => setDragOver(false)}
      onClick={() => inputRef.current?.click()}
      className={`card flex flex-col items-center gap-4 py-14 cursor-pointer transition-all duration-200
        ${dragOver
          ? "border-[#00ff88] bg-[#00ff88]/5 scale-[1.01]"
          : "border-[#2a2a3d] hover:border-[#00ff88]/40 hover:bg-[#00ff88]/5"
        }`}
    >
      <input
        ref={inputRef}
        type="file"
        accept="video/*"
        className="hidden"
        onChange={(e) => {
          const file = e.target.files?.[0];
          if (file) handleFile(file);
          e.target.value = "";
        }}
      />
      <Upload size={40} className={dragOver ? "text-[#00ff88]" : "text-[#4b5563]"} />
      <div className="text-center">
        <p className="text-white font-semibold">
          {dragOver ? "Drop to upload" : "Drop your match footage here"}
        </p>
        <p className="text-sm text-[#6b7280] mt-1">or click to browse · MP4, MOV up to 2 GB</p>
      </div>
      <button
        className="btn-primary text-sm px-5 py-2"
        onClick={(e) => { e.stopPropagation(); inputRef.current?.click(); }}
      >
        Select File
      </button>
    </div>
  );
}
