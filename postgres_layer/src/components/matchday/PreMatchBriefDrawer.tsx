import { useEffect, useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { AreaChart, Area, ResponsiveContainer, XAxis, YAxis } from "recharts";

type Brief = {
  match_id: string;
  team_form: { home: { results: string[]; avg_scored: number; avg_conceded: number };
               away: { results: string[]; avg_scored: number; avg_conceded: number } };
  head_to_head: { wins_home: number; draws: number; wins_away: number };
  win_probability: { home_pct: number; draw_pct: number; away_pct: number };
  player_form_timelines: { rating: number; goals: number; assists: number; match_date: string }[];
  key_matchups: { label: string; ours: string; theirs: string; edge: string }[];
  tactical_role_card: { position: string; instruction: string; targets: string[]; watch_out: string };
};

interface Props { matchId: string; onClose: () => void; }

export default function PreMatchBriefDrawer({ matchId, onClose }: Props): JSX.Element {
  const [data, setData] = useState<Brief | null>(null);

  useEffect(() => {
    fetch(`/v2/matches/${matchId}/pre-match-brief`, { headers: { Authorization: `Bearer ${localStorage.getItem("fb_token") ?? ""}` } })
      .then((r) => r.json()).then((d: Brief) => setData(d));
  }, [matchId]);

  return (
    <AnimatePresence>
      <motion.div
        className="fixed inset-0 z-50 bg-black/70 flex items-end justify-center"
        initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}
        onClick={onClose}
        data-testid="prematch-overlay"
      >
        <motion.div
          drag="y" dragConstraints={{ top: 0, bottom: 200 }} dragElastic={0.2}
          onDragEnd={(_e, info) => { if (info.offset.y > 120) onClose(); }}
          className="w-full max-w-2xl bg-bg-card border-t border-line rounded-t-2xl"
          style={{ height: "75vh" }}
          initial={{ y: "100%" }} animate={{ y: 0 }} exit={{ y: "100%" }}
          transition={{ type: "spring", damping: 28, stiffness: 280 }}
          onClick={(e) => e.stopPropagation()}
          data-testid="prematch-drawer"
        >
          <div className="w-12 h-1 rounded-full bg-line mx-auto mt-2" />
          <div className="p-4 overflow-y-auto h-full pb-12">
            <div className="font-mono text-[10px] uppercase tracking-widest text-accent-purple">⚡ PRE-MATCH BRIEF</div>
            <div className="font-display text-xl font-bold tracking-tight mt-1">YOUR INTEL PACK</div>

            {!data ? (
              <div className="text-center py-12 text-ink-muted">Loading…</div>
            ) : (
              <div className="space-y-4 mt-4">
                {/* WIN PROBABILITY */}
                <div className="bg-bg-elevated border border-line p-4" data-testid="win-prob">
                  <div className="font-mono text-[10px] uppercase tracking-widest text-ink-muted">WIN PROBABILITY</div>
                  <div className="grid grid-cols-2 gap-3 mt-2">
                    <div className="text-center">
                      <div style={{ fontFamily: "JetBrains Mono", fontWeight: 700, fontSize: 24, color: "var(--city-accent)" }}>{data.win_probability.home_pct}%</div>
                      <div className="font-mono text-[9px] uppercase text-ink-muted">HOME</div>
                    </div>
                    <div className="text-center">
                      <div style={{ fontFamily: "JetBrains Mono", fontWeight: 700, fontSize: 24, color: "#38BDF8" }}>{data.win_probability.away_pct}%</div>
                      <div className="font-mono text-[9px] uppercase text-ink-muted">AWAY</div>
                    </div>
                  </div>
                  <div className="font-mono text-[9px] uppercase text-ink-muted mt-2">Calculated from last 5 matches</div>
                </div>

                {/* TEAM FORM */}
                <div className="grid grid-cols-2 gap-2">
                  {(["home", "away"] as const).map((side) => (
                    <div key={side} className="bg-bg-elevated border border-line p-3">
                      <div className="font-mono text-[10px] uppercase text-ink-muted">{side.toUpperCase()} FORM</div>
                      <div className="flex gap-1 mt-2">
                        {data.team_form[side].results.map((r, i) => (
                          <div key={i} className="w-6 h-6 flex items-center justify-center font-mono font-bold text-[10px]"
                               style={{ background: r === "W" ? "#00E676" : r === "D" ? "#FFB830" : "#FF4D4D", color: "#0A0F1E" }}>
                            {r}
                          </div>
                        ))}
                      </div>
                    </div>
                  ))}
                </div>

                {/* H2H */}
                {data.head_to_head && (
                  <div className="grid grid-cols-3 bg-bg-elevated border border-line p-3 text-center">
                    {[["W", data.head_to_head.wins_home, "#00E676"], ["D", data.head_to_head.draws, "#FFB830"], ["L", data.head_to_head.wins_away, "#FF4D4D"]].map(([l, v, c]) => (
                      <div key={l as string}>
                        <div className="font-display text-2xl font-bold" style={{ color: c as string }}>{v as number}</div>
                        <div className="font-mono text-[9px] uppercase text-ink-muted">{l as string}</div>
                      </div>
                    ))}
                  </div>
                )}

                {/* PLAYER FORM */}
                {data.player_form_timelines?.length > 0 && (
                  <div className="bg-bg-elevated border border-line p-3" style={{ height: 140 }}>
                    <div className="font-mono text-[10px] uppercase text-ink-muted mb-1">YOUR LAST 5</div>
                    <ResponsiveContainer>
                      <AreaChart data={data.player_form_timelines}>
                        <XAxis dataKey="match_date" hide /><YAxis domain={[40, 100]} hide />
                        <Area dataKey="rating" stroke="var(--city-accent)" fill="var(--city-accent)" fillOpacity={0.4} />
                      </AreaChart>
                    </ResponsiveContainer>
                  </div>
                )}

                {/* TACTICAL ROLE CARD */}
                {data.tactical_role_card && (
                  <div className="bg-accent-purple/10 border border-accent-purple/40 p-3" data-testid="role-card">
                    <div className="font-mono text-[10px] uppercase tracking-widest text-accent-purple">⚡ {data.tactical_role_card.position}</div>
                    <div className="text-sm mt-1">{data.tactical_role_card.instruction}</div>
                    <div className="flex gap-2 mt-2 flex-wrap">
                      {(data.tactical_role_card.targets || []).map((t, i) => (
                        <span key={i} className="px-2 py-1 rounded-full text-[10px] font-mono" style={{ background: "var(--city-accent)", color: "#0A0F1E" }}>{t}</span>
                      ))}
                    </div>
                  </div>
                )}

                {/* SHARE */}
                <button
                  data-testid="share-prediction-btn"
                  onClick={() => window.open(`https://wa.me/?text=${encodeURIComponent(`My pre-match brief says ${data.win_probability.home_pct}% chance to win.`)}`, "_blank")}
                  className="w-full h-12 bg-accent-green text-black font-mono uppercase tracking-widest text-xs font-bold rounded-md"
                >
                  Share to WhatsApp
                </button>
              </div>
            )}
          </div>
        </motion.div>
      </motion.div>
    </AnimatePresence>
  );
}
