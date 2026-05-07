import { useEffect, useMemo, useState } from "react";
import { motion } from "framer-motion";
import { useNavigate } from "react-router-dom";
import PreMatchBriefDrawer from "../../components/matchday/PreMatchBriefDrawer";
import QRTicketModal from "../../components/matchday/QRTicketModal";

type MatchSummary = {
  id: string; home_team: string; away_team: string;
  scheduled_at: string; scheduled_at_ist: string;
  status: "scheduled" | "live" | "complete" | "cancelled" | string;
  format: string; skill_bracket: string;
  score: { home: number; away: number };
  spots_remaining?: number;
};

type Tab = "Upcoming" | "Live" | "Completed" | "Last Minute";

export default function PlayerMatches(): JSX.Element {
  const nav = useNavigate();
  const [matches, setMatches] = useState<MatchSummary[]>([]);
  const [lastMin, setLastMin] = useState<MatchSummary[]>([]);
  const [tab, setTab] = useState<Tab>("Upcoming");
  const [selectedDay, setSelectedDay] = useState<number>(0);
  const [briefMatchId, setBriefMatchId] = useState<string | null>(null);
  const [ticketMatchId, setTicketMatchId] = useState<string | null>(null);

  useEffect(() => {
    fetch("/v2/matches/", { headers: hdr() }).then((r) => r.json()).then(setMatches);
    fetch("/v2/matches/last-minute", { headers: hdr() }).then((r) => r.json()).then(setLastMin);
  }, []);

  const filtered = useMemo(() => {
    if (tab === "Upcoming") return matches.filter((m) => m.status === "scheduled");
    if (tab === "Live") return matches.filter((m) => m.status === "live");
    if (tab === "Completed") return matches.filter((m) => m.status === "complete");
    return lastMin;
  }, [tab, matches, lastMin]);

  return (
    <div className="min-h-screen bg-bg pb-24" data-testid="player-matches-page">
      {/* CALENDAR STRIP */}
      <div className="sticky top-0 z-30 bg-bg/95 backdrop-blur border-b border-line">
        <div className="max-w-2xl mx-auto px-4 py-3 flex gap-2 overflow-x-auto" data-testid="calendar-strip">
          {Array.from({ length: 14 }).map((_, i) => {
            const d = new Date(); d.setDate(d.getDate() + i);
            const hasBooking = matches.some((m) => sameDay(new Date(m.scheduled_at), d));
            const isSel = i === selectedDay;
            return (
              <button
                key={i}
                data-testid={`calendar-day-${i}`}
                onClick={() => setSelectedDay(i)}
                className={`relative flex-shrink-0 w-10 h-12 flex flex-col items-center justify-center rounded-full ${isSel ? "bg-accent-green text-black" : "text-ink-muted"}`}
              >
                <span className={`font-mono text-[10px] uppercase ${i === 0 ? "font-bold" : ""}`}>{d.toLocaleDateString("en-IN", { weekday: "short" })[0]}</span>
                <span className={`font-display text-base ${i === 0 ? "font-bold" : ""}`}>{d.getDate()}</span>
                {hasBooking && !isSel && <span className="absolute bottom-0.5 w-1 h-1 bg-accent-green rounded-full" />}
                {isSel && <motion.div layoutId="cal-sel" className="absolute inset-0 rounded-full" />}
              </button>
            );
          })}
        </div>
      </div>

      {/* TABS */}
      <div className="max-w-2xl mx-auto px-4 mt-3 flex gap-2 overflow-x-auto" data-testid="match-tabs">
        {(["Upcoming", "Live", "Completed", "Last Minute"] as Tab[]).map((t) => {
          const live = t === "Live" && matches.some((m) => m.status === "live");
          const lm = t === "Last Minute" && lastMin.length > 0;
          return (
            <button
              key={t}
              data-testid={`tab-${t.toLowerCase().replace(/\s+/g, "-")}`}
              onClick={() => setTab(t)}
              className={`relative px-3 h-9 rounded-full font-mono text-[10px] uppercase tracking-widest whitespace-nowrap ${tab === t ? "bg-accent-green text-black font-bold" : "border border-line text-ink-muted"}`}
            >
              {t === "Live" && live ? <span className="inline-block w-1.5 h-1.5 bg-accent-green rounded-full mr-1.5 animate-pulse" /> : null}
              {t === "Last Minute" ? "⚡ Last Minute" : t}
              {lm && <span className="absolute -top-1 -right-1 w-2 h-2 bg-accent-amber rounded-full" />}
            </button>
          );
        })}
      </div>

      {/* MATCH LIST */}
      <div className="max-w-2xl mx-auto px-4 mt-4 space-y-3">
        {filtered.length === 0 && <div className="text-center py-12 text-ink-muted font-mono text-[10px] uppercase tracking-widest">No matches.</div>}
        {filtered.map((m) => (
          <MatchCard key={m.id} m={m} onBrief={() => setBriefMatchId(m.id)} onTicket={() => setTicketMatchId(m.id)} onOpen={() => nav(`/matches/${m.id}`)} />
        ))}
      </div>

      {/* PRE-MATCH BRIEF DRAWER */}
      {briefMatchId && (
        <PreMatchBriefDrawer matchId={briefMatchId} onClose={() => setBriefMatchId(null)} />
      )}

      {/* QR TICKET */}
      {ticketMatchId && (
        <QRTicketModal matchId={ticketMatchId} onClose={() => setTicketMatchId(null)} />
      )}
    </div>
  );
}

function MatchCard({ m, onBrief, onTicket, onOpen }: { m: MatchSummary; onBrief: () => void; onTicket: () => void; onOpen: () => void }): JSX.Element {
  const isLive = m.status === "live";
  const isLastMin = m.spots_remaining !== undefined && m.spots_remaining > 0;
  return (
    <motion.div
      initial={{ opacity: 0, y: 6 }} animate={{ opacity: 1, y: 0 }}
      className={`relative bg-bg-card border-l-[3px] p-4 rounded-r-md ${isLive ? "border-accent-green animate-[pulse-live_2s_infinite]" : isLastMin ? "border-accent-amber" : ""}`}
      style={{ borderLeftColor: !isLive && !isLastMin ? "var(--city-accent)" : undefined }}
      onClick={onOpen}
      data-testid={`match-card-${m.id}`}
    >
      <div className="flex items-center justify-between mb-2">
        <span className={`font-mono text-[9px] uppercase tracking-widest px-2 py-0.5 rounded-full ${isLive ? "bg-accent-green text-black animate-pulse" : "bg-bg-elevated text-ink-muted"}`}>
          {m.status}
        </span>
        <span className="font-mono text-[10px] uppercase tracking-widest text-ink-muted">{m.format} · {m.skill_bracket}</span>
      </div>
      <div className="grid grid-cols-3 items-center">
        <div className="text-right font-display text-lg font-bold truncate">{m.home_team.toUpperCase()}</div>
        <div className="text-center" style={{ fontFamily: "JetBrains Mono", fontWeight: 700 }}>
          {m.status === "complete" || isLive
            ? <span className="text-accent-amber text-2xl">{m.score.home} : {m.score.away}</span>
            : <span className="text-ink-muted text-xs">VS</span>}
        </div>
        <div className="text-left font-display text-lg font-bold truncate">{m.away_team.toUpperCase()}</div>
      </div>
      <div className="flex items-center gap-3 mt-3 font-mono text-[10px] uppercase tracking-widest text-ink-muted">
        ⏰ {new Date(m.scheduled_at).toLocaleString("en-IN", { hour: "2-digit", minute: "2-digit", hour12: true })}
      </div>
      <div className="flex gap-2 mt-3" onClick={(e) => e.stopPropagation()}>
        {m.status === "scheduled" && (
          <button data-testid={`brief-btn-${m.id}`} onClick={onBrief} className="px-3 h-8 border border-accent-amber text-accent-amber font-mono text-[10px] uppercase tracking-widest rounded-md">📋 Brief Ready</button>
        )}
        <button data-testid={`ticket-btn-${m.id}`} onClick={onTicket} className="px-3 h-8 border border-accent-green text-accent-green font-mono text-[10px] uppercase tracking-widest rounded-md">🎫 Ticket</button>
        {m.status === "complete" && (
          <button data-testid={`story-btn-${m.id}`} onClick={() => (window.location.href = `/matches/${m.id}/story`)} className="px-3 h-8 border border-accent-purple text-accent-purple font-mono text-[10px] uppercase tracking-widest rounded-md">Story 🎬</button>
        )}
        {isLastMin && <div className="ml-auto px-2 h-7 inline-flex items-center text-accent-red font-mono text-[10px] uppercase tracking-widest">🔴 {m.spots_remaining} spots left</div>}
      </div>
    </motion.div>
  );
}

function hdr(): HeadersInit {
  const t = localStorage.getItem("fb_token");
  return t ? { Authorization: `Bearer ${t}` } : {};
}
function sameDay(a: Date, b: Date): boolean {
  return a.getFullYear() === b.getFullYear() && a.getMonth() === b.getMonth() && a.getDate() === b.getDate();
}
