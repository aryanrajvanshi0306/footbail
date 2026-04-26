/**
 * HLSPlayer — wraps HLS.js for cross-browser adaptive bitrate playback.
 * Falls back to native <video> on Safari (which has built-in HLS support).
 */
import { useEffect, useRef, useState } from "react";
import Hls from "hls.js";
import { Loader2, AlertTriangle } from "lucide-react";

interface Props {
  src: string;
  poster?: string;
  autoPlay?: boolean;
  className?: string;
}

export default function HLSPlayer({ src, poster, autoPlay = false, className = "" }: Props) {
  const videoRef = useRef<HTMLVideoElement>(null);
  const hlsRef = useRef<Hls | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const video = videoRef.current;
    if (!video) return;

    setLoading(true);
    setError(null);

    // Safari natively supports HLS
    if (!Hls.isSupported()) {
      if (video.canPlayType("application/vnd.apple.mpegurl")) {
        video.src = src;
        video.addEventListener("loadedmetadata", () => setLoading(false));
      } else {
        setError("HLS playback not supported in this browser.");
        setLoading(false);
      }
      return;
    }

    // Destroy previous instance
    hlsRef.current?.destroy();

    const hls = new Hls({
      enableWorker: true,
      lowLatencyMode: false,
      backBufferLength: 90,
    });
    hlsRef.current = hls;

    hls.attachMedia(video);
    hls.on(Hls.Events.MEDIA_ATTACHED, () => {
      hls.loadSource(src);
    });
    hls.on(Hls.Events.MANIFEST_PARSED, () => {
      setLoading(false);
      if (autoPlay) video.play().catch(() => undefined);
    });
    hls.on(Hls.Events.ERROR, (_ev, data) => {
      if (data.fatal) {
        setError(`HLS error: ${data.details}`);
        setLoading(false);
      }
    });

    return () => {
      hls.destroy();
      hlsRef.current = null;
    };
  }, [src, autoPlay]);

  return (
    <div className={`relative bg-black rounded-xl overflow-hidden ${className}`}>
      <video
        ref={videoRef}
        poster={poster}
        controls
        playsInline
        className="w-full h-full object-contain"
        style={{ aspectRatio: "16/9" }}
      />
      {loading && (
        <div className="absolute inset-0 flex items-center justify-center bg-black/60">
          <Loader2 size={36} className="text-[#00ff88] animate-spin" />
        </div>
      )}
      {error && (
        <div className="absolute inset-0 flex flex-col items-center justify-center bg-black/80 gap-3">
          <AlertTriangle size={36} className="text-[#ef4444]" />
          <p className="text-sm text-[#9ca3af] text-center px-6">{error}</p>
        </div>
      )}
    </div>
  );
}
