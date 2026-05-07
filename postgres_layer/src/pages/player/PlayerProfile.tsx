import { useEffect, useMemo, useRef, useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  RadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis, Radar,
  LineChart, Line, BarChart, Bar, ResponsiveContainer, Tooltip, XAxis, YAxis, CartesianGrid,
} from "recharts";
import { useParams } from "react-router-dom";
import html2canvas from "html2canvas";
import FIFACard from "../../components/player/FIFACard";

type StatBlock = { matches: number; goals: number; assists: number; minutes: number; [k: string]: number };
type FormPoint = { match_date: string; rating: number; goals: number; assists: number; match_impact_index: number | null; is_motm: boolean };
type DashboardPayload = {
  profile: { id: string; name: string; city: string; role: string; avatar_url: string | null;
             position: string | null; card_tier: string | null; overall: number | null };
  fifa_card: { overall: number; position: string; tier: string; name: string;
               attributes: { pac: number; sho: number; pas: number; dri: number; def: number; phy: number } };
  oyp: { archetype: string | null; confidence: number; matches_analyzed: number } | null;
  play_style_dna: Record<string, number>;
  stats_season: StatBlock;
  form_graph: { match_id: string; match_date: string; rating: number; is_motm: boolean }[];
  career: { matches: number; goals: number; assists: number };
  consistency_score: number;
  xp: number; xp_to_next: number;
  streak: number;
  recent_achievements: { id: string; code: string; name: string; rarity: string; unlocked_at: string }[];
  active_challenges: { id: string; title: string; type: string; target: number; progress: number; xp_reward: number }[];
};

const TABS = ["Season", "Career", "Form", "Impact"] as const;
type Tab = typeof TABS[number];

export default function PlayerProfile(): JSX.Element {
  const params = useParams<{ id?: string }>();
  const [data, setData] = useState<DashboardPayload | null>(null);
  const [tab, setTab] = useState<Tab>("Season");
  const [formTimeline, setFormTimeline] = useState<FormPoint[]>([]);

  useEffect(() => {
    const url = params.id ? `/v2/players/${params.id}` : "/v2/players/dashboard";
    fetch(url, { headers: authHeader() })
      .then((r) => r.json())
      .then((d: DashboardPayload) => setData(d));
  }, [params.id]);

  useEffect(() => {
    if (!data) return;
    fetch(`/v2/players/${data.profile.id}/form-timeline?days=30`, { headers: authHeader() })
      .then((r) => r.json())
      .then(setFormTimeline);
  }, [data?.profile.id]);

  const radarData = useMemo(() => {
    if (!data) return [];
    const a = data.fifa_card.attributes;
    return [
      { stat: "PAC", season: a.pac, career: a.pac - 4 },
      { stat: "SHO", season: a.sho, career: a.sho - 3 },
      { stat: "PAS", season: a.pas, career: a.pas - 2 },
      { stat: "DRI", season: a.dri, career: a.dri - 3 },
      { stat: "DEF", season: a.def, career: a.def - 2 },
      { stat: "PHY", season: a.phy, career: a.phy - 1 },
    ];
  }, [data]);

  if (!data) return <div className="min-h-screen bg-bg flex items-center justify-center text-ink-muted">Loading…</div>;

  return (
    <div className="min-h-screen bg-bg pb-24" data-testid="player-profile-page">
      {/* COVER + AVATAR */}
      <div className="relative h-[180px] overflow-hidden">
        <div className="absolute inset-0 bg-gradient-to-b from-[var(--city-accent)]/20 via-bg-surface to-bg" />
        <div className="absolute inset-0 city-pattern" />
        <button
          data-testid="edit-or-follow-btn"
          className="absolute right-4 top-4 px-4 h-9 rounded-full bg-bg-card border border-line text-xs uppercase tracking-widest font-mono hover:border-accent-green"
        >
          {!params.id ? "Edit" : "Follow"}
        </button>
        <div className="absolute -bottom-8 left-4 w-[72px] h-[72px] rounded-full overflow-hidden border-[3px]"
             style={{ borderColor: tierColor(data.fifa_card.tier) }}>
          <div className="w-full h-full bg-bg-elevated flex items-center justify-center font-display text-3xl">
            {data.profile.name?.[0]}
          </div>
        </div>
      </div>

      <div className="px-4 pt-12">
        <div className="font-display text-2xl font-bold tracking-tight">{data.profile.name.toUpperCase()}</div>
        <div className="font-mono text-[10px] uppercase tracking-widest text-ink-muted mt-1">
          {data.profile.city} · {data.fifa_card.position} · {data.profile.role.toUpperCase()}
        </div>
      </div>

      {/* FIFA CARD + STATS GRID */}
      <div className="px-4 mt-5 flex gap-4 items-start">
        <FIFACard player={{
          overall: data.fifa_card.overall, position: data.fifa_card.position,
          name: data.fifa_card.name, attributes: data.fifa_card.attributes,
          tier: data.fifa_card.tier, city: data.profile.city,
        }} size="md" showShareButton />
        <div className="flex-1 grid grid-cols-2 gap-2">
          <Stat label="Matches" value={data.stats_season.matches} />
          <Stat label="Goals" value={data.stats_season.goals} />
          <Stat label="Assists" value={data.stats_season.assists} />
          <Stat label="Streak 🔥" value={data.streak} />
        </div>
      </div>

      {/* OYP + DNA */}
      {data.oyp && (
        <div className="mx-4 mt-5 bg-accent-purple/10 border border-accent-purple/40 p-4" data-testid="oyp-block">
          <div className="font-mono text-[10px] uppercase tracking-widest text-accent-purple">⚡ {data.fifa_card.position} · {data.oyp.archetype}</div>
          <div className="grid grid-cols-3 gap-2 mt-3">
            {Object.entries(data.play_style_dna).slice(0, 3).map(([trait, score]) => (
              <div key={trait} className="bg-bg-card border border-line p-2">
                <div className="font-mono text-[9px] uppercase tracking-widest text-ink-muted">{trait}</div>
                <div className="font-mono font-bold text-lg">{score}</div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* TABS */}
      <div className="mt-6 px-4">
        <div className="flex gap-6 border-b border-line">
          {TABS.map((t) => (
            <button
              key={t}
              data-testid={`tab-${t.toLowerCase()}`}
              onClick={() => setTab(t)}
              className={`relative py-3 font-mono text-xs uppercase tracking-widest ${tab === t ? "text-ink" : "text-ink-muted"}`}
            >
              {t}
              {tab === t && <motion.div layoutId="profile-tab-underline" className="absolute -bottom-px left-0 right-0 h-0.5 bg-accent-green" />}
            </button>
          ))}
        </div>

        <AnimatePresence mode="wait">
          <motion.div key={tab} initial={{ opacity: 0, y: 6 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -6 }} transition={{ duration: 0.18 }} className="mt-4">
            {tab === "Season" && <StatsGrid stats={data.stats_season} position={data.fifa_card.position} />}
            {tab === "Career" && <StatsGrid stats={{ ...data.stats_season, ...data.career }} position={data.fifa_card.position} />}
            {tab === "Form" && (
              <div className="bg-bg-card border border-line p-3">
                <ResponsiveContainer width="100%" height={180}>
                  <LineChart data={formTimeline.slice().reverse()}>
                    <CartesianGrid stroke="rgba(255,255,255,0.06)" />
                    <XAxis dataKey="match_date" hide />
                    <YAxis domain={[40, 100]} stroke="#94A3B8" fontSize={10} />
                    <Tooltip contentStyle={{ background: "#1C2333", border: "1px solid #243046" }} />
                    <Line type="monotone" dataKey="rating" stroke="var(--city-accent)" strokeWidth={2} dot={{ r: 4 }} />
                  </LineChart>
                </ResponsiveContainer>
              </div>
            )}
            {tab === "Impact" && (
              <div className="bg-bg-card border border-line p-3">
                <ResponsiveContainer width="100%" height={180}>
                  <BarChart data={formTimeline.filter((p) => p.match_impact_index != null)}>
                    <CartesianGrid stroke="rgba(255,255,255,0.06)" />
                    <XAxis dataKey="match_date" hide />
                    <YAxis domain={[0, 100]} stroke="#94A3B8" fontSize={10} />
                    <Tooltip contentStyle={{ background: "#1C2333", border: "1px solid #243046" }} />
                    <Bar dataKey="match_impact_index">
                      {formTimeline.filter((p) => p.match_impact_index != null).map((p, i) => (
                        <Bar key={i} dataKey="match_impact_index" fill={impactColor(p.match_impact_index!)} />
                      ))}
                    </Bar>
                  </BarChart>
                </ResponsiveContainer>
              </div>
            )}
          </motion.div>
        </AnimatePresence>
      </div>

      {/* RADAR */}
      <div className="mx-4 mt-6 bg-bg-card border border-line p-3" data-testid="radar-block">
        <div className="font-mono text-[10px] uppercase tracking-widest text-ink-muted mb-2">ATTRIBUTE RADAR</div>
        <ResponsiveContainer width="100%" height={260}>
          <RadarChart data={radarData} margin={{ top: 8, right: 16, bottom: 8, left: 16 }}>
            <PolarGrid stroke="rgba(255,255,255,0.08)" />
            <PolarAngleAxis dataKey="stat" tick={{ fill: "#94A3B8", fontSize: 11 }} />
            <PolarRadiusAxis stroke="rgba(255,255,255,0.06)" tick={false} domain={[0, 99]} />
            <Radar name="Career" dataKey="career" stroke="rgba(255,255,255,0.5)" strokeDasharray="4 4" fill="rgba(255,255,255,0.06)" fillOpacity={0.3} isAnimationActive />
            <Radar name="Season" dataKey="season" stroke="var(--city-accent)" fill="var(--city-accent)" fillOpacity={0.35} isAnimationActive />
          </RadarChart>
        </ResponsiveContainer>
      </div>

      {/* CONSISTENCY GAUGE */}
      <div className="mx-4 mt-4 bg-bg-card border border-line p-4 text-center" data-testid="consistency-gauge">
        <div className="font-mono text-[10px] uppercase tracking-widest text-ink-muted">CONSISTENCY</div>
        <div className="font-display text-4xl font-bold mt-1" style={{ color: "var(--city-accent)" }}>{data.consistency_score}%</div>
        <div className="font-mono text-xs text-ink-muted mt-1">Top of {data.fifa_card.position} players in {data.profile.city}</div>
      </div>

      {/* ACHIEVEMENTS */}
      <div className="mt-6 px-4" data-testid="achievements-row">
        <div className="font-mono text-[10px] uppercase tracking-widest text-ink-muted mb-2">ACHIEVEMENTS</div>
        <div className="flex gap-2 overflow-x-auto pb-2">
          {data.recent_achievements.map((a, i) => (
            <div key={a.id} className={`min-w-[120px] p-3 border ${i < 3 ? "border-accent-gold" : "border-line"} bg-bg-card`}>
              <div className="font-mono text-[9px] uppercase tracking-widest" style={{ color: rarityColor(a.rarity) }}>{a.rarity}</div>
              <div className="font-display text-sm mt-1">{a.name}</div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

function authHeader(): HeadersInit {
  const t = localStorage.getItem("fb_token");
  return t ? { Authorization: `Bearer ${t}` } : {};
}

function Stat({ label, value }: { label: string; value: number }): JSX.Element {
  return (
    <div className="bg-bg-card border border-line p-3">
      <div className="font-mono text-[10px] uppercase tracking-widest text-ink-muted">{label}</div>
      <div className="font-mono font-bold text-xl mt-0.5">{value}</div>
    </div>
  );
}

function StatsGrid({ stats, position }: { stats: StatBlock; position: string }): JSX.Element {
  const items: [string, number][] = [
    ["Matches", stats.matches], ["Goals", stats.goals], ["Assists", stats.assists],
    ["Minutes", stats.minutes ?? 0],
  ];
  if (position === "GK") items.push(["Saves", stats.saves ?? 0], ["Clean Sheets", stats.clean_sheets ?? 0]);
  else if (["CB", "LB", "RB", "CDM"].includes(position)) items.push(["Tackles", stats.tackles ?? 0], ["Interceptions", stats.interceptions ?? 0]);
  else items.push(["Shots", stats.shots ?? 0], ["Key Passes", stats.key_passes ?? 0]);
  return (
    <div className="grid grid-cols-2 gap-2">
      {items.map(([l, v]) => <Stat key={l} label={l} value={v} />)}
    </div>
  );
}

function tierColor(tier: string): string {
  return ({ bronze: "#A0522D", silver: "#C0C0C0", gold: "#F59E0B", toty: "#00E5FF" } as const)[tier] ?? "#A0522D";
}
function rarityColor(r: string): string {
  return ({ legendary: "#F59E0B", epic: "#A78BFA", rare: "#38BDF8", common: "#94A3B8" } as const)[r] ?? "#94A3B8";
}
function impactColor(score: number): string {
  return score >= 60 ? "#00E676" : score >= 30 ? "#FFB830" : "#FF4D4D";
}
