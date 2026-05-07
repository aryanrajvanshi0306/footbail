import { useEffect, useRef, useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import FIFACard from "../player/FIFACard";

type SlideType = "intro" | "goal" | "save" | "turning_point" | "error" | "motm";

interface Moment {
  slide_index: number; type: SlideType | string; minute: number | null;
  player_id: string | null; player_name: string | null; player_avatar_url: string | null;
  caption: string; thumbnail_url: string | null; is_clutch: boolean; emoji: string;
}

interface Story {
  match_title: string; result: string;
  moments: Moment[];
  motm: { name: string; position: string; rating: number; tier: string; attributes: any } | null;
  share_text: string; share_url: string;
}

interface Props { matchId: string; }

export default function MatchStoryPlayer({ matchId }: Props): JSX.Element {
  const [story, setStory] = useState<Story | null>(null);
  const [idx, setIdx] = useState<number>(0);
  const [paused, setPaused] = useState<boolean>(false);
  const timerRef = useRef<number | null>(null);

  useEffect(() => {
    fetch(`/v2/matches/${matchId}/story`, { headers: { Authorization: `Bearer ${localStorage.getItem("fb_token") ?? ""}` } })
      .then((r) => r.json()).then(setStory);
  }, [matchId]);

  useEffect(() => {
    if (!story || paused) return;
    timerRef.current = window.setTimeout(() => {
      setIdx((i) => Math.min(story.moments.length, i + 1));
    }, 3000);
    return () => { if (timerRef.current) window.clearTimeout(timerRef.current); };
  }, [idx, paused, story]);

  if (!story) return <div className="min-h-screen bg-black flex items-center justify-center text-ink-muted">Loading…</div>;

  const slides: Array<{ kind: SlideType; data?: Moment }> = [
    { kind: "intro" },
    ...story.moments.map((m) => ({ kind: m.type as SlideType, data: m })),
    ...(story.motm ? [{ kind: "motm" as SlideType }] : []),
  ];
  const total = slides.length;
  const cur = slides[Math.min(idx, total - 1)];

  const tap = (side: "left" | "right"): void => {
    if (side === "left") setIdx((i) => Math.max(0, i - 1));
    else setIdx((i) => Math.min(total - 1, i + 1));
  };

  return (
    <div className="fixed inset-0 z-50 bg-black flex items-center justify-center" data-testid="match-story-player">
      {/* Progress bars */}
      <div className="absolute top-2 left-2 right-2 flex gap-1 z-20">
        {slides.map((_s, i) => (
          <div key={i} className="flex-1 h-0.5 bg-white/30 overflow-hidden">
            <div className="h-full bg-white transition-all" style={{ width: i < idx ? "100%" : i === idx ? (paused ? "0%" : "100%") : "0%", transitionDuration: paused ? "0ms" : "3000ms" }} />
          </div>
        ))}
      </div>

      {/* Tap zones */}
      <button className="absolute left-0 top-0 bottom-0 w-1/3 z-10" onClick={() => tap("left")} aria-label="Previous" />
      <button className="absolute right-0 top-0 bottom-0 w-1/3 z-10" onClick={() => tap("right")} aria-label="Next" />
      <button className="absolute left-1/3 right-1/3 top-0 bottom-0 z-10" onPointerDown={() => setPaused(true)} onPointerUp={() => setPaused(false)} aria-label="Pause" />

      {/* Slide content */}
      <AnimatePresence mode="wait">
        <motion.div
          key={idx}
          initial={{ scale: cur.data?.is_clutch ? 0.9 : 1, opacity: 0 }}
          animate={{ scale: 1, opacity: 1 }}
          exit={{ opacity: 0 }}
          transition={{ duration: 0.3 }}
          className={`relative w-full h-full max-w-md mx-auto flex flex-col items-center justify-center p-6 text-white ${cur.data?.is_clutch ? "ring-[1.5px] ring-accent-gold" : ""}`}
        >
          {cur.data?.is_clutch && (
            <span className="absolute top-8 left-4 px-2 py-1 bg-accent-gold text-black font-mono text-[10px] uppercase tracking-widest rounded-full">🔥 CLUTCH</span>
          )}

          {cur.kind === "intro" && (
            <div className="text-center pitch-bg w-full h-full flex flex-col items-center justify-center">
              <div className="font-display tracking-tight" style={{ fontSize: 72, fontWeight: 800 }}>{story.result}</div>
              <div className="font-mono uppercase mt-2 text-accent-amber tracking-[0.4em]">FULL TIME</div>
              <div className="mt-4 font-display text-2xl">{story.match_title.toUpperCase()}</div>
            </div>
          )}

          {cur.kind === "goal" && (
            <>
              <Avatar src={cur.data?.player_avatar_url} name={cur.data?.player_name} />
              <div className="font-display mt-6" style={{ fontSize: 48, color: "#00E676", fontWeight: 800 }}>GOAL!</div>
              <Caption>{cur.data?.caption}</Caption>
              <Minute m={cur.data?.minute ?? 0} />
            </>
          )}

          {cur.kind === "save" && (
            <>
              <Avatar src={cur.data?.player_avatar_url} name={cur.data?.player_name} />
              <div className="font-display mt-6" style={{ fontSize: 36, color: "#38BDF8", fontWeight: 800 }}>🧤 WORLD CLASS SAVE</div>
              <Caption>{cur.data?.caption}</Caption>
              <Minute m={cur.data?.minute ?? 0} />
            </>
          )}

          {cur.kind === "turning_point" && (
            <>
              <div className="w-full max-w-sm h-3 bg-bg-elevated overflow-hidden">
                <div style={{ width: "70%", background: "var(--city-accent)" }} className="h-full transition-all duration-700" />
              </div>
              <div className="font-display mt-6" style={{ fontSize: 36, color: "var(--city-accent)" }}>⚡ TURNING POINT</div>
              <Caption>{cur.data?.caption}</Caption>
            </>
          )}

          {cur.kind === "error" && (
            <div className="absolute inset-0 flex flex-col items-center justify-center" style={{ background: "#2D0000" }}>
              <Avatar src={cur.data?.player_avatar_url} name={cur.data?.player_name} />
              <div className="font-display mt-6" style={{ fontSize: 36, color: "#FF4D4D", fontWeight: 800 }}>❌ COSTLY MISTAKE</div>
              <Caption>{cur.data?.caption}</Caption>
              <Minute m={cur.data?.minute ?? 0} />
            </div>
          )}

          {cur.kind === "motm" && story.motm && (
            <div className="text-center">
              <Confetti />
              <FIFACard player={{
                overall: story.motm.attributes?.overall ?? 80,
                position: story.motm.position, name: story.motm.name,
                attributes: story.motm.attributes ?? { pac: 80, sho: 80, pas: 80, dri: 80, def: 60, phy: 75 },
                tier: story.motm.tier, city: "Mumbai",
              }} size="md" />
              <div className="font-display mt-4" style={{ fontSize: 28, color: "#F59E0B", fontWeight: 800 }}>MAN OF THE MATCH</div>
            </div>
          )}
        </motion.div>
      </AnimatePresence>

      {/* Share */}
      <button
        data-testid="share-story-btn"
        onClick={() => window.open(`https://wa.me/?text=${encodeURIComponent(story.share_text)}`, "_blank")}
        className="fixed bottom-6 left-1/2 -translate-x-1/2 z-30 px-6 h-11 rounded-full bg-accent-green text-black font-mono text-xs uppercase tracking-widest font-bold"
      >
        Share Story
      </button>
    </div>
  );
}

function Avatar({ src, name }: { src: string | null | undefined; name: string | null | undefined }): JSX.Element {
  return (
    <div className="w-24 h-24 rounded-full bg-bg-card border-2 border-white/20 overflow-hidden flex items-center justify-center font-display text-4xl">
      {src ? <img src={src} alt="" className="w-full h-full object-cover" /> : (name?.[0] ?? "?")}
    </div>
  );
}
function Caption({ children }: { children: any }): JSX.Element { return <div className="text-center text-base mt-3 px-6">{children}</div>; }
function Minute({ m }: { m: number }): JSX.Element {
  return <div className="mt-3 px-3 py-1 bg-white/10 rounded-full font-mono text-xs">{m}'</div>;
}
function Confetti(): JSX.Element {
  return (
    <div className="absolute inset-0 pointer-events-none overflow-hidden">
      {Array.from({ length: 20 }).map((_, i) => (
        <div key={i}
          className="absolute w-1.5 h-1.5"
          style={{
            top: `${Math.random() * 60}%`, left: `${Math.random() * 100}%`,
            background: "var(--city-accent)",
            transform: `rotate(${Math.random() * 360}deg)`,
            animation: `slide-up ${0.6 + Math.random()}s ease-out`,
          }} />
      ))}
    </div>
  );
}
