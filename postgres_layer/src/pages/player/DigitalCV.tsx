import { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import { Radar, RadarChart, PolarGrid, PolarAngleAxis, ResponsiveContainer } from "recharts";
import FIFACard from "../../components/player/FIFACard";

type CV = {
  profile: { id: string; name: string; city: string; avatar_url: string | null; bio: string | null; aiff_player_id: string | null };
  fifa_card: { overall: number; position: string; tier: string; attributes: { pac: number; sho: number; pas: number; dri: number; def: number; phy: number } };
  oyp: { archetype: string; confidence: number } | null;
  dna: Record<string, number>;
  stats: { matches: number; goals: number; assists: number; minutes: number; clean_sheets: number };
  radar_data: { pac: number; sho: number; pas: number; dri: number; def: number; phy: number };
  form_indicator: { streak_days: number; consistency: number };
  top_achievements: { code: string; name: string; rarity: string; unlocked_at: string }[];
  club_history: { club_id: string; name: string; city: string; logo_url: string | null; role: string; jersey_number: number | null }[];
  public_clips: { id: string; type: string; title: string | null; thumbnail_url: string | null; clip_url: string | null; share_count: number }[];
};

export default function DigitalCV(): JSX.Element {
  const { id } = useParams<{ id: string }>();
  const [data, setData] = useState<CV | null>(null);
  const [pdfUrl, setPdfUrl] = useState<string | null>(null);
  useEffect(() => { fetch(`/v2/cv/${id}`).then((r) => r.json()).then(setData); }, [id]);
  if (!data) return <div className="min-h-screen bg-bg flex items-center justify-center text-ink-muted">Loading…</div>;

  const { profile, fifa_card, stats } = data;
  const radar = [
    { stat: "PAC", v: data.radar_data.pac }, { stat: "SHO", v: data.radar_data.sho },
    { stat: "PAS", v: data.radar_data.pas }, { stat: "DRI", v: data.radar_data.dri },
    { stat: "DEF", v: data.radar_data.def }, { stat: "PHY", v: data.radar_data.phy },
  ];

  const downloadPdf = async (): Promise<void> => {
    const r = await fetch(`/v2/cv/${id}/generate-pdf`, { headers: { Authorization: `Bearer ${localStorage.getItem("fb_token") ?? ""}` } });
    if (r.ok) { const j: { pdf_url: string } = await r.json(); setPdfUrl(j.pdf_url); window.open(j.pdf_url, "_blank"); }
  };

  const waShare = (): void => {
    const url = window.location.href;
    const text = `Check out ${profile.name}'s digital football CV on footbAIl.in — ${url}`;
    window.open(`https://wa.me/?text=${encodeURIComponent(text)}`, "_blank");
  };

  return (
    <div className="min-h-screen bg-bg pb-12" data-testid="digital-cv-page">
      {/* HERO */}
      <div className="relative h-[150px] overflow-hidden">
        <div className="absolute inset-0 bg-gradient-to-b from-[var(--city-accent)]/30 via-bg-surface to-bg" />
        <div className="absolute inset-0 city-pattern" />
        <div className="absolute -bottom-10 left-1/2 -translate-x-1/2 w-20 h-20 rounded-full overflow-hidden border-[3px] border-[var(--city-accent)] bg-bg-elevated flex items-center justify-center font-display text-3xl">
          {profile.avatar_url ? <img src={profile.avatar_url} alt="" className="w-full h-full object-cover" /> : profile.name[0]}
        </div>
      </div>
      <div className="text-center pt-14 px-4">
        <div className="font-display text-3xl font-bold tracking-tight">{profile.name.toUpperCase()}</div>
        <div className="font-mono text-[10px] uppercase tracking-widest text-ink-muted mt-1">
          {profile.city} · {fifa_card.position}
          {profile.aiff_player_id && <span className="ml-2 px-2 py-0.5 bg-accent-amber/20 text-accent-amber rounded-full">AIFF #{profile.aiff_player_id}</span>}
        </div>
      </div>

      {/* ROW 1: card + career stats */}
      <div className="px-4 mt-6 flex gap-4 items-start" data-testid="cv-row-1">
        <FIFACard player={{ ...fifa_card, name: profile.name, city: profile.city, oyp_label: data.oyp?.archetype ?? undefined }} size="lg" />
        <div className="flex-1 grid grid-cols-2 gap-2">
          {[["Matches", stats.matches], ["Goals", stats.goals], ["Assists", stats.assists],
            ["Minutes", stats.minutes], ["Clean Sheets", stats.clean_sheets], ["Streak 🔥", data.form_indicator.streak_days]]
            .map(([l, v]) => (
            <div key={l as string} className="bg-bg-card border border-line p-3">
              <div className="font-mono text-[10px] uppercase tracking-widest text-ink-muted">{l as string}</div>
              <div className="font-mono font-bold text-xl mt-0.5">{v as number}</div>
            </div>
          ))}
        </div>
      </div>

      {/* OYP + DNA + RADAR */}
      <div className="mx-4 mt-6 bg-accent-purple/10 border border-accent-purple/40 p-4" data-testid="cv-oyp-banner">
        <div className="font-mono text-[10px] uppercase tracking-widest text-accent-purple">⚡ {data.oyp?.archetype ?? "Computing…"}</div>
        <div className="grid grid-cols-[280px_1fr] gap-4 mt-3 items-center">
          <div className="bg-bg-card border border-line p-2" style={{ height: 280 }}>
            <ResponsiveContainer width="100%" height="100%">
              <RadarChart data={radar}>
                <PolarGrid stroke="rgba(255,255,255,0.08)" />
                <PolarAngleAxis dataKey="stat" tick={{ fill: "#94A3B8", fontSize: 11 }} />
                <Radar dataKey="v" stroke="var(--city-accent)" fill="var(--city-accent)" fillOpacity={0.4} />
              </RadarChart>
            </ResponsiveContainer>
          </div>
          <div className="grid grid-cols-2 gap-2">
            {Object.entries(data.dna).slice(0, 4).map(([k, v]) => (
              <div key={k} className="bg-bg-card border border-line p-2">
                <div className="font-mono text-[9px] uppercase tracking-widest text-ink-muted">{k}</div>
                <div className="font-mono font-bold text-lg">{v}</div>
              </div>
            ))}
            <div className="col-span-2 bg-bg-elevated border border-line p-2">
              <div className="font-mono text-[10px] uppercase tracking-widest text-ink-muted">Form</div>
              <div className="font-mono text-sm">{data.form_indicator.consistency}% · {data.form_indicator.streak_days}-day streak</div>
            </div>
          </div>
        </div>
      </div>

      {/* TOP 6 ACHIEVEMENTS */}
      <div className="mx-4 mt-6" data-testid="cv-achievements">
        <div className="font-mono text-[10px] uppercase tracking-widest text-ink-muted mb-2">TOP ACHIEVEMENTS</div>
        <div className="grid grid-cols-2 gap-2">
          {data.top_achievements.map((a) => (
            <div key={a.code} className="bg-bg-card border border-line p-3">
              <div className="font-mono text-[9px] uppercase tracking-widest" style={{ color: rarityColor(a.rarity) }}>{a.rarity}</div>
              <div className="font-display text-sm mt-1">{a.name}</div>
            </div>
          ))}
        </div>
      </div>

      {/* CLUB HISTORY */}
      <div className="mx-4 mt-6" data-testid="cv-club-history">
        <div className="font-mono text-[10px] uppercase tracking-widest text-ink-muted mb-2">CLUB HISTORY</div>
        <div className="space-y-2">
          {data.club_history.map((c) => (
            <div key={c.club_id} className="bg-bg-card border border-line p-3 flex items-center gap-3">
              <div className="w-9 h-9 bg-bg-elevated flex items-center justify-center font-mono font-bold">{c.name[0]}</div>
              <div className="flex-1">
                <div className="font-bold">{c.name}</div>
                <div className="font-mono text-[10px] uppercase tracking-widest text-ink-muted">{c.city} · {c.role}{c.jersey_number ? ` · #${c.jersey_number}` : ""}</div>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* SHARE */}
      <div className="mx-4 mt-6 grid grid-cols-2 gap-2" data-testid="cv-share-row">
        <button onClick={waShare} className="bg-accent-green text-black font-bold h-12 font-mono uppercase tracking-widest text-xs rounded-md">Share to WhatsApp</button>
        <button onClick={downloadPdf} className="border border-line h-12 font-mono uppercase tracking-widest text-xs rounded-md hover:border-ink">{pdfUrl ? "Re-download PDF" : "Download PDF"}</button>
      </div>
    </div>
  );
}

function rarityColor(r: string): string {
  return ({ legendary: "#F59E0B", epic: "#A78BFA", rare: "#38BDF8", common: "#94A3B8" } as const)[r] ?? "#94A3B8";
}
