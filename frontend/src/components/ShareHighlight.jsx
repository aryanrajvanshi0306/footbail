import React, { useRef, useState } from 'react';
import html2canvas from 'html2canvas';
import { Share2, Download } from 'lucide-react';
import { toast } from 'sonner';
import { getCityTheme } from '../lib/cityTheme';

/**
 * Share Highlight Reel — generates a 9:16 vertical share card as PNG.
 * Viral loop: every share surfaces footbAIl branding + player stats to IG/WhatsApp.
 */
export default function ShareHighlight({ match, motm, userCity = 'Mumbai', goalCount = 1 }) {
  const cardRef = useRef(null);
  const [busy, setBusy] = useState(false);
  const theme = getCityTheme(userCity);

  const generate = async () => {
    if (!cardRef.current) return;
    setBusy(true);
    try {
      const canvas = await html2canvas(cardRef.current, {
        backgroundColor: '#0A0F1E',
        scale: 2,
        useCORS: true,
        logging: false,
      });
      const blob = await new Promise((res) => canvas.toBlob(res, 'image/png', 0.95));
      const url = URL.createObjectURL(blob);
      // Try Web Share API (mobile)
      if (navigator.share && navigator.canShare?.({ files: [new File([blob], 'footbail-motm.png', { type: 'image/png' })] })) {
        try {
          await navigator.share({
            title: `${motm.name} · MOTM`,
            text: `${motm.name} cooked at ${match.turf_name}. ${motm.rating} rating. Built on footbAIl.`,
            files: [new File([blob], 'footbail-motm.png', { type: 'image/png' })],
          });
          toast.success('Shared');
        } catch (_) { /* cancelled */ }
      } else {
        // Fallback: download
        const a = document.createElement('a');
        a.href = url;
        a.download = `footbail-motm-${match.id.slice(0, 6)}.png`;
        document.body.appendChild(a); a.click(); a.remove();
        toast.success('Reel saved to downloads');
      }
      setTimeout(() => URL.revokeObjectURL(url), 8000);
    } catch (e) {
      console.error(e);
      toast.error('Could not generate reel');
    } finally {
      setBusy(false);
    }
  };

  return (
    <div data-testid="share-highlight-block">
      {/* Live preview */}
      <div className="flex gap-3 items-start">
        <div
          ref={cardRef}
          data-testid="share-card-preview"
          className="relative overflow-hidden flex-shrink-0"
          style={{
            width: 270, height: 480, // 9:16 aspect, scaled down
            background: `radial-gradient(ellipse at top, ${theme.accent}22 0%, #0A0F1E 60%, #000 100%)`,
            borderRadius: 16,
            border: `1px solid ${theme.accent}`,
          }}
        >
          {/* Grain */}
          <div className="absolute inset-0" style={{
            backgroundImage: `url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='120' height='120'%3E%3Cfilter id='n'%3E%3CfeTurbulence baseFrequency='0.85' numOctaves='2'/%3E%3CfeColorMatrix values='0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0.18 0'/%3E%3C/filter%3E%3Crect width='120' height='120' filter='url(%23n)'/%3E%3C/svg%3E")`,
            mixBlendMode: 'overlay',
          }} />
          {/* Header */}
          <div className="relative z-10 flex items-center justify-between px-5 pt-5">
            <div className="flex items-center gap-2">
              <div style={{ width: 28, height: 28, background: theme.accent, borderRadius: 8, color: '#0A0F1E' }} className="flex items-center justify-center font-display font-bold">f</div>
              <div className="font-mono text-[10px] tracking-[0.3em] uppercase" style={{ color: theme.accent }}>MOTM</div>
            </div>
            <div className="font-mono text-[9px] uppercase tracking-widest text-ink-muted">{theme.subtitle}</div>
          </div>

          {/* Rating — HUGE */}
          <div className="relative z-10 mt-2 text-center">
            <div className="font-display text-[92px] leading-none" style={{ color: theme.accent, fontWeight: 800 }}>
              {motm.rating}
            </div>
            <div className="font-mono text-[10px] tracking-[0.4em] uppercase text-ink-muted mt-1">MATCH RATING</div>
          </div>

          {/* Player name */}
          <div className="relative z-10 text-center mt-4 px-5">
            <div className="font-display text-2xl tracking-wide font-bold text-ink">{motm.name.toUpperCase()}</div>
            <div className="font-mono text-[11px] tracking-[0.3em] uppercase mt-1" style={{ color: theme.accent }}>{motm.position}</div>
          </div>

          {/* Stat row */}
          <div className="relative z-10 mt-4 mx-5 grid grid-cols-3 gap-2" style={{ borderTop: '1px solid rgba(255,255,255,0.12)', paddingTop: 12 }}>
            <StatPill label="GOALS" value={motm.goals} />
            <StatPill label="ASSISTS" value={motm.assists} />
            <StatPill label="TEAM" value={goalCount > 0 ? 'WIN' : '—'} />
          </div>

          {/* Match strip */}
          <div className="relative z-10 mx-5 mt-4 px-3 py-2.5" style={{ background: 'rgba(255,255,255,0.04)', border: '1px solid rgba(255,255,255,0.08)', borderRadius: 10 }}>
            <div className="font-mono text-[9px] tracking-widest uppercase text-ink-muted truncate">{match.turf_name}</div>
            <div className="font-mono text-xs mt-1 text-ink truncate">
              {match.home_team} <span className="font-bold" style={{ color: theme.accent }}>{match.score?.home ?? 0}–{match.score?.away ?? 0}</span> {match.away_team}
            </div>
          </div>

          {/* Footer wordmark */}
          <div className="absolute bottom-3 left-0 right-0 text-center z-10">
            <div className="font-display text-[10px] tracking-[0.4em] uppercase text-ink-muted">
              made with <span className="font-bold text-ink">footb<span style={{ color: theme.accent }}>AI</span>l</span>
            </div>
          </div>
        </div>

        {/* Actions */}
        <div className="flex-1 space-y-2">
          <div className="font-mono text-[10px] uppercase tracking-widest text-accent-purple">VIRAL KIT</div>
          <div className="text-sm text-ink leading-relaxed">Drop this in your story — the {theme.subtitle.toLowerCase()} vibes sell themselves.</div>
          <button
            data-testid="share-highlight-btn"
            disabled={busy}
            onClick={generate}
            className="w-full h-11 font-display font-bold text-sm tracking-wider uppercase flex items-center justify-center gap-2 disabled:opacity-50 transition-all hover:scale-[0.98] active:scale-95"
            style={{ background: theme.accent, color: '#0A0F1E', borderRadius: 10 }}
          >
            <Share2 className="w-4 h-4" /> {busy ? 'Rendering…' : 'Share Reel'}
          </button>
          <button
            data-testid="download-highlight-btn"
            disabled={busy}
            onClick={generate}
            className="w-full h-10 font-mono text-[10px] tracking-widest uppercase flex items-center justify-center gap-2 border border-line hover:border-ink-muted transition-colors"
            style={{ borderRadius: 10 }}
          >
            <Download className="w-3.5 h-3.5" /> PNG
          </button>
        </div>
      </div>
    </div>
  );
}

function StatPill({ label, value }) {
  return (
    <div style={{ borderRadius: 8, background: 'rgba(255,255,255,0.05)', padding: '8px 6px' }} className="text-center">
      <div className="font-mono text-[9px] tracking-widest uppercase text-ink-muted">{label}</div>
      <div className="font-display text-xl text-ink font-bold">{value ?? '—'}</div>
    </div>
  );
}
