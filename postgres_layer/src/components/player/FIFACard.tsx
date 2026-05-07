import { useRef, useState, type CSSProperties } from "react";
import html2canvas from "html2canvas";
import { motion } from "framer-motion";

export type FIFACardData = {
  overall: number;
  position: string;
  name: string;
  attributes: { pac: number; sho: number; pas: number; dri: number; def: number; phy: number };
  tier: "bronze" | "silver" | "gold" | "toty" | string;
  city: string;
  oyp_label?: string;
  avatar_url?: string | null;
  club_badge_url?: string | null;
};

type Size = "sm" | "md" | "lg";

const SIZES: Record<Size, { w: number; h: number; ovr: number; pos: number; name: number; pad: number; avatar: number }> = {
  sm: { w: 100, h: 140, ovr: 22, pos: 9, name: 11, pad: 8, avatar: 36 },
  md: { w: 160, h: 220, ovr: 36, pos: 11, name: 14, pad: 10, avatar: 50 },
  lg: { w: 240, h: 330, ovr: 56, pos: 14, name: 20, pad: 14, avatar: 72 },
};

const TIER_GRADIENTS: Record<string, string> = {
  bronze: "linear-gradient(135deg,#7A4423 0%,#C68A60 45%,#5C3017 100%)",
  silver: "linear-gradient(135deg,#7A7E85 0%,#D9DEE6 45%,#5B5F66 100%)",
  gold:   "linear-gradient(135deg,#9C6B00 0%,#FFD56B 45%,#7A5300 100%)",
  toty:   "linear-gradient(135deg,#001433 0%,#00E5FF 45%,#02173E 100%)",
};

interface Props {
  player: FIFACardData;
  size?: Size;
  showShareButton?: boolean;
  publicCvUrl?: string;
}

export default function FIFACard({ player, size = "md", showShareButton = false, publicCvUrl }: Props): JSX.Element {
  const dims = SIZES[size];
  const ref = useRef<HTMLDivElement | null>(null);
  const [busy, setBusy] = useState<boolean>(false);
  const isHolo = player.tier === "gold" || player.tier === "toty";

  const positionAttrs = positionSpecific(player.position, player.attributes);

  const cardStyle: CSSProperties = {
    width: dims.w,
    height: dims.h,
    background: TIER_GRADIENTS[player.tier] ?? TIER_GRADIENTS.bronze,
    color: "#1A1100",
    padding: dims.pad,
    position: "relative",
    overflow: "hidden",
    borderRadius: 12,
  };

  const share = async (): Promise<void> => {
    if (!ref.current) return;
    setBusy(true);
    try {
      const canvas = await html2canvas(ref.current, { backgroundColor: null, scale: 2, useCORS: true, logging: false });
      const blob = await new Promise<Blob | null>((res) => canvas.toBlob((b) => res(b), "image/png", 0.95));
      if (!blob) return;
      const file = new File([blob], "footbail-card.png", { type: "image/png" });
      if (navigator.canShare && navigator.canShare({ files: [file] })) {
        await navigator.share({ title: `${player.name} · footbAIl`, files: [file] });
      } else {
        const a = document.createElement("a");
        a.href = URL.createObjectURL(blob);
        a.download = "footbail-card.png";
        a.click();
      }
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="relative inline-block" data-testid="fifa-card-wrap">
      <motion.div
        ref={ref}
        style={cardStyle}
        initial={{ scale: 0.96, opacity: 0 }}
        animate={{ scale: 1, opacity: 1 }}
        transition={{ duration: 0.3, ease: "easeOut" }}
        data-testid="fifa-card"
      >
        {/* City pattern at 8% opacity */}
        <div className="absolute inset-0 pointer-events-none" style={{ backgroundImage: "var(--city-pattern)", backgroundSize: 120, opacity: 0.08, mixBlendMode: "screen" }} />
        {/* Holographic shimmer for gold/toty only */}
        {isHolo && (
          <div className="absolute inset-0 pointer-events-none" style={{
            background: "linear-gradient(110deg, transparent 30%, rgba(255,255,255,0.45) 50%, transparent 70%)",
            backgroundSize: "200% 100%", animation: "city-shine 6s linear infinite", mixBlendMode: "screen",
          }} />
        )}
        {/* City accent radial glow at bottom */}
        <div className="absolute -bottom-10 left-1/2 -translate-x-1/2 pointer-events-none" style={{
          width: 120, height: 120,
          background: "radial-gradient(circle, var(--city-accent) 0%, transparent 70%)",
          opacity: 0.6,
        }} />

        {/* TOP: OVR + position + tier label */}
        <div className="relative z-10 flex justify-between items-start">
          <div>
            <div style={{ fontFamily: "JetBrains Mono", fontWeight: 800, fontSize: dims.ovr, lineHeight: 1 }}>{player.overall}</div>
            <div style={{ fontFamily: "JetBrains Mono", fontWeight: 700, fontSize: dims.pos, letterSpacing: 1.5, opacity: 0.85 }}>
              {player.position}
            </div>
          </div>
          <div style={{ fontSize: dims.pos, letterSpacing: 1.5, opacity: 0.7, textTransform: "uppercase" }}>
            {player.tier}
          </div>
        </div>

        {/* CENTER: avatar + OYP label */}
        <div className="relative z-10 flex flex-col items-center mt-1">
          <div className="rounded-full bg-black/25 flex items-center justify-center" style={{ width: dims.avatar, height: dims.avatar }}>
            {player.avatar_url
              ? <img src={player.avatar_url} alt="" className="w-full h-full rounded-full object-cover" />
              : <span style={{ fontFamily: "DM Sans", fontWeight: 700, fontSize: dims.avatar * 0.5 }}>{player.name?.[0]?.toUpperCase()}</span>}
          </div>
          {player.oyp_label && (
            <div style={{ color: "var(--city-accent)", fontFamily: "JetBrains Mono", fontSize: dims.pos - 1, marginTop: 4, letterSpacing: 1.5, textTransform: "uppercase" }}>
              {player.oyp_label}
            </div>
          )}
        </div>

        {/* NAME */}
        <div className="relative z-10 text-center mt-1" style={{ fontFamily: "DM Sans", fontWeight: 700, fontSize: dims.name, letterSpacing: 1, textTransform: "uppercase" }}>
          {player.name}
        </div>

        {/* POSITION-SPECIFIC ATTRS */}
        <div className="relative z-10 grid grid-cols-2 gap-x-2 gap-y-0.5 mt-1" style={{ fontFamily: "JetBrains Mono", fontWeight: 600, fontSize: dims.pos }}>
          {positionAttrs.map(([k, v]) => (
            <div key={k}><b style={{ fontSize: dims.pos + 2 }}>{v}</b> {k}</div>
          ))}
        </div>

        {/* Watermark + QR for share variant only */}
        {showShareButton && publicCvUrl && (
          <div className="absolute bottom-1 right-1 text-[7px] font-mono opacity-70">footbAIl.in</div>
        )}
      </motion.div>

      {showShareButton && (
        <button
          data-testid="share-card-btn"
          onClick={share}
          disabled={busy}
          className="absolute -bottom-2 left-1/2 -translate-x-1/2 px-3 h-7 rounded-full bg-accent-green text-black font-bold text-[10px] uppercase tracking-widest hover:opacity-90 disabled:opacity-50"
        >
          {busy ? "…" : "Share"}
        </button>
      )}
    </div>
  );
}

function positionSpecific(pos: string, a: FIFACardData["attributes"]): [string, number][] {
  if (pos === "GK") return [["DIV", a.def], ["REF", a.phy], ["HAN", a.dri]];
  if (["CB", "LB", "RB"].includes(pos)) return [["DEF", a.def], ["PHY", a.phy], ["PAS", a.pas]];
  if (["CM", "CDM", "CAM"].includes(pos)) return [["PAS", a.pas], ["DRI", a.dri], ["PHY", a.phy]];
  if (["LW", "RW"].includes(pos)) return [["PAC", a.pac], ["DRI", a.dri], ["SHO", a.sho]];
  if (["ST", "CF"].includes(pos)) return [["PAC", a.pac], ["SHO", a.sho], ["DRI", a.dri]];
  return [["PAC", a.pac], ["SHO", a.sho], ["PAS", a.pas]];
}
