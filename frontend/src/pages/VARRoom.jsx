import React, { useEffect, useRef, useState } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import { toast } from 'sonner';
import { ChevronLeft, Power, Radio, AlertCircle, Goal, Square, ScanLine, Flag, BarChart3, Tv, X } from 'lucide-react';
import { api } from '../lib/api';
import { EVENT_META } from '../lib/constants';

/**
 * VAR Monitor / Match Control Room
 * - Click "Start Camera" → match goes live, recording begins (simulated)
 * - VAR controls: Kickoff, Foul, Goal, Yellow, Red, Offside (auto AI), Substitution, Complete
 * - Offside rechecking with confirm/overturn
 * - Live share toasts on goal/foul/yellow
 * - Match Complete → camera stops, shows analysis link
 */
export default function VARRoom() {
  const { id } = useParams();
  const nav = useNavigate();
  const [match, setMatch] = useState(null);
  const [events, setEvents] = useState([]);
  const [team, setTeam] = useState(null);
  const [pending, setPending] = useState(null); // pending offside review
  const [scanning, setScanning] = useState(false);
  const [matchTime, setMatchTime] = useState(0);
  const timerRef = useRef(null);

  const load = async () => {
    const r = await api.get(`/matches/${id}`);
    setMatch(r.data);
    setEvents(r.data.events || []);
    if (!team) setTeam(r.data.home_team);
  };

  useEffect(() => { load(); /* eslint-disable-next-line */ }, [id]);

  // Match clock
  useEffect(() => {
    if (match?.status === 'live') {
      timerRef.current = setInterval(() => setMatchTime((t) => t + 1), 1000);
    } else {
      clearInterval(timerRef.current);
    }
    return () => clearInterval(timerRef.current);
  }, [match?.status]);

  const minutes = Math.floor(matchTime / 60);

  const startCamera = async () => {
    setScanning(true);
    setTimeout(async () => {
      try {
        await api.post(`/matches/${id}/start`);
        toast.success('Turf camera ONLINE · Recording started');
        await load();
      } catch (e) {
        toast.error('Failed to start camera');
      } finally {
        setScanning(false);
      }
    }, 1500);
  };

  const completeMatch = async () => {
    if (!window.confirm('End the match? Camera will stop recording.')) return;
    await api.post(`/matches/${id}/complete`);
    toast.success('Match complete · Camera OFF · Analysis ready');
    await load();
  };

  const fireEvent = async (type, extra = {}) => {
    const body = { type, team, minute: minutes, ...extra };
    await api.post(`/matches/${id}/events`, body);
    const m = EVENT_META[type];
    if (['goal', 'foul', 'yellow_card', 'red_card'].includes(type)) {
      toast.success(`📡 LIVE SHARE · ${m.label} broadcasted to viewers`, { duration: 3000 });
    }
    load();
  };

  const checkOffside = async () => {
    setScanning(true);
    setTimeout(async () => {
      try {
        const r = await api.post(`/matches/${id}/offside-check`);
        setPending(r.data);
        toast.info(`AI: ${r.data.type.toUpperCase()} · Confidence ${(r.data.confidence * 100).toFixed(0)}%`);
        load();
      } finally {
        setScanning(false);
      }
    }, 1500);
  };

  if (!match) return <div className="p-8 text-ink-muted bg-black min-h-screen">Loading…</div>;

  const isLive = match.status === 'live';
  const isComplete = match.status === 'complete';

  return (
    <div className="min-h-screen bg-black text-white" data-testid="var-room-page">
      {/* TOP BAR */}
      <header className="border-b border-line">
        <div className="max-w-7xl mx-auto px-6 py-3 flex items-center gap-4">
          <Link to="/admin/match-control" data-testid="back-control" className="font-mono text-[10px] uppercase tracking-widest text-ink-muted hover:text-white flex items-center gap-1">
            <ChevronLeft className="w-3 h-3" /> Control
          </Link>
          <div className="flex-1 flex items-center justify-center gap-6">
            <div className="text-right font-display text-2xl">{match.home_team.toUpperCase()}</div>
            <div className="font-mono font-bold text-3xl text-accent-amber" data-testid="var-score">{match.score?.home || 0} : {match.score?.away || 0}</div>
            <div className="text-left font-display text-2xl">{match.away_team.toUpperCase()}</div>
          </div>
          <div className="flex items-center gap-2 font-mono text-xs uppercase tracking-widest">
            {isLive ? (
              <>
                <span className="w-2 h-2 bg-accent-green text-black font-bold rounded-full animate-pulse" />
                <span className="text-accent-green" data-testid="var-status">ON-AIR · {minutes}'</span>
              </>
            ) : isComplete ? (
              <span className="text-ink-muted" data-testid="var-status">FULL TIME</span>
            ) : (
              <span className="text-accent-amber" data-testid="var-status">STANDBY</span>
            )}
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-6 py-6 grid lg:grid-cols-[1.5fr_1fr] gap-6">
        {/* CAMERA FEED */}
        <div data-testid="var-camera-feed">
          <div className="font-mono text-[10px] uppercase tracking-widest text-ink-muted mb-2">PRIMARY · TURF CAM 01</div>
          <div className="relative aspect-video pitch-bg border border-line overflow-hidden">
            <div className="grain absolute inset-0" />

            {/* Pitch lines */}
            <svg className="absolute inset-0 w-full h-full opacity-40" viewBox="0 0 100 60" preserveAspectRatio="none">
              <rect x="2" y="2" width="96" height="56" fill="none" stroke="white" strokeWidth="0.3" />
              <line x1="50" y1="2" x2="50" y2="58" stroke="white" strokeWidth="0.3" />
              <circle cx="50" cy="30" r="6" fill="none" stroke="white" strokeWidth="0.3" />
              <rect x="2" y="18" width="12" height="24" fill="none" stroke="white" strokeWidth="0.3" />
              <rect x="86" y="18" width="12" height="24" fill="none" stroke="white" strokeWidth="0.3" />
            </svg>

            {/* Animated dots = players */}
            {isLive && (
              <>
                {[
                  [25, 30, '#FF3B30'], [38, 22, '#FF3B30'], [38, 38, '#FF3B30'], [50, 30, '#FF3B30'],
                  [62, 22, '#007AFF'], [62, 38, '#007AFF'], [75, 30, '#007AFF'], [88, 30, '#007AFF'],
                ].map(([x, y, c], i) => (
                  <div key={i} className="absolute w-3 h-3 rounded-full animate-pulse" style={{ left: `${x}%`, top: `${y}%`, transform: 'translate(-50%, -50%)', background: c, boxShadow: `0 0 8px ${c}` }} />
                ))}
                {/* Ball */}
                <div className="absolute w-2 h-2 bg-white rounded-full" style={{ left: '52%', top: '32%', boxShadow: '0 0 6px #fff' }} />
              </>
            )}

            {/* Scanning overlay */}
            {scanning && (
              <div className="absolute inset-0 overflow-hidden" data-testid="ai-scan-overlay">
                <div className="camera-scan absolute left-0 right-0 animate-scan" />
                <div className="absolute inset-0 flex items-center justify-center">
                  <div className="font-mono text-accent-green text-xs uppercase tracking-widest border border-accent-green px-3 py-1 bg-black/50">
                    <ScanLine className="w-3 h-3 inline mr-1" />AI Analysis · YOLO v9
                  </div>
                </div>
              </div>
            )}

            {/* Idle overlay */}
            {!isLive && !isComplete && !scanning && (
              <div className="absolute inset-0 bg-black/85 flex flex-col items-center justify-center">
                <div className="font-mono text-[10px] uppercase tracking-widest text-ink-muted mb-2">CAMERA IDLE</div>
                <button data-testid="start-camera-btn" onClick={startCamera} className="bg-accent-green text-black font-bold px-6 h-12 font-display text-xl tracking-widest uppercase hover:bg-[#00C853] flex items-center gap-2">
                  <Power className="w-5 h-5" /> Start Camera & Match
                </button>
                <div className="font-mono text-[10px] uppercase tracking-widest text-ink-muted mt-3">Camera will auto-start at turf · Live broadcast enabled</div>
              </div>
            )}

            {/* Complete overlay */}
            {isComplete && (
              <div className="absolute inset-0 bg-black/90 flex flex-col items-center justify-center" data-testid="camera-stopped">
                <div className="font-display text-5xl text-accent-amber">FULL TIME</div>
                <div className="font-mono text-xs uppercase tracking-widest text-ink-muted mt-2">Camera stopped · Recording archived</div>
                <button data-testid="goto-analysis-btn" onClick={() => nav(`/match/${id}/analysis`)} className="mt-4 bg-accent-amber text-black font-bold px-6 h-12 font-display text-xl tracking-widest uppercase hover:opacity-90 flex items-center gap-2">
                  <BarChart3 className="w-5 h-5" /> View Performance Analysis
                </button>
              </div>
            )}

            {/* HUD */}
            {isLive && (
              <div className="absolute top-2 left-2 flex items-center gap-2 font-mono text-[10px] uppercase tracking-widest" data-testid="live-hud">
                <span className="w-2 h-2 rounded-full bg-accent-green text-black font-bold animate-pulse" />
                <span className="text-accent-green">REC</span>
                <span className="text-ink-muted">|</span>
                <span>{minutes.toString().padStart(2, '0')}:{(matchTime % 60).toString().padStart(2, '0')}</span>
              </div>
            )}
            {isLive && (
              <div className="absolute top-2 right-2 font-mono text-[10px] uppercase tracking-widest text-accent-amber flex items-center gap-1">
                <Radio className="w-3 h-3" /> LIVE BROADCAST
              </div>
            )}
          </div>

          {/* MATCH CONTROLS */}
          {isLive && (
            <div className="mt-6" data-testid="var-controls">
              <div className="flex items-center gap-2 mb-3">
                <span className="font-mono text-[10px] uppercase tracking-widest text-ink-muted">ACTIVE TEAM</span>
                <button data-testid="pick-home-team" onClick={() => setTeam(match.home_team)} className={`px-3 py-1 font-mono text-[10px] uppercase tracking-widest border ${team === match.home_team ? 'border-accent-green bg-accent-green text-black font-bold' : 'border-line text-ink-muted'}`}>{match.home_team}</button>
                <button data-testid="pick-away-team" onClick={() => setTeam(match.away_team)} className={`px-3 py-1 font-mono text-[10px] uppercase tracking-widest border ${team === match.away_team ? 'border-brand-secondary bg-brand-secondary text-white' : 'border-line text-ink-muted'}`}>{match.away_team}</button>
              </div>

              <div className="grid grid-cols-3 md:grid-cols-4 gap-2">
                <ControlBtn testid="ctrl-kickoff" onClick={() => fireEvent('kickoff')} icon={Flag} label="KICKOFF" color="#32ADE6" />
                <ControlBtn testid="ctrl-goal" onClick={() => fireEvent('goal', { player_name: 'Top Scorer' })} icon={Goal} label="GOAL" color="#34C759" />
                <ControlBtn testid="ctrl-foul" onClick={() => fireEvent('foul', { notes: 'Physical foul logged from app' })} icon={AlertCircle} label="FOUL (PHYSICAL)" color="#FFCC00" />
                <ControlBtn testid="ctrl-yellow" onClick={() => fireEvent('yellow_card')} icon={Square} label="YELLOW" color="#FFCC00" />
                <ControlBtn testid="ctrl-red" onClick={() => fireEvent('red_card')} icon={Square} label="RED" color="#FF3B30" />
                <ControlBtn testid="ctrl-offside" onClick={checkOffside} icon={ScanLine} label="OFFSIDE (AI)" color="#FF3B30" pulse />
                <ControlBtn testid="ctrl-sub" onClick={() => fireEvent('substitution')} icon={Flag} label="SUB" color="#A1A1A1" />
                <ControlBtn testid="ctrl-complete" onClick={completeMatch} icon={Power} label="COMPLETE" color="#FF3B30" filled />
              </div>

              <div className="mt-3 text-xs text-ink-muted font-mono">
                ✓ Offside auto-detected by camera · Physical fouls input manually · Goals/Yellows live-shared to broadcast viewers
              </div>
            </div>
          )}
        </div>

        {/* RIGHT PANE — Events log + Offside review */}
        <div className="space-y-4">
          {pending && (
            <div className="bg-bg-card border-2 border-accent-green p-4 red-glow" data-testid="offside-review">
              <div className="font-mono text-[10px] uppercase tracking-widest text-accent-green mb-2">⚑ AI OFFSIDE REVIEW</div>
              <div className="font-display text-3xl">{pending.type.toUpperCase()}</div>
              <div className="text-xs text-ink-muted mt-1">{pending.notes}</div>
              <div className="font-mono text-xs mt-2">Confidence: <span className="text-accent-amber">{(pending.confidence * 100).toFixed(0)}%</span></div>
              <div className="grid grid-cols-2 gap-2 mt-3">
                <button data-testid="confirm-offside" onClick={() => { setPending(null); toast.success('AI decision confirmed'); }} className="bg-accent-green text-black font-bold h-10 font-mono uppercase tracking-widest text-xs text-white">CONFIRM</button>
                <button data-testid="overturn-offside" onClick={() => { setPending(null); toast.warning('AI decision overturned'); }} className="border border-line h-10 font-mono uppercase tracking-widest text-xs">OVERTURN</button>
              </div>
            </div>
          )}

          <div data-testid="var-events-log">
            <div className="flex items-center justify-between mb-2">
              <div className="font-mono text-[10px] uppercase tracking-widest text-ink-muted">EVENT LOG</div>
              {isLive && <button data-testid="open-broadcast" onClick={() => window.open(`/broadcast/${id}`, '_blank')} className="font-mono text-[10px] uppercase tracking-widest text-accent-amber hover:text-white flex items-center gap-1">
                <Tv className="w-3 h-3" /> Live Viewer
              </button>}
            </div>
            <div className="bg-bg-card border border-line max-h-[600px] overflow-y-auto">
              {events.length === 0 && <div className="p-4 text-ink-muted text-sm">No events.</div>}
              {[...events].reverse().map((e) => {
                const m = EVENT_META[e.type] || { label: e.type, color: '#A1A1A1', icon: '•' };
                return (
                  <div key={e.id} className="border-b border-line p-3 flex items-center gap-3 hover:bg-bg-elevated">
                    <div className="w-8 h-8 flex items-center justify-center font-mono font-bold flex-shrink-0" style={{ background: m.color, color: '#000' }}>{m.icon}</div>
                    <div className="flex-1 min-w-0">
                      <div className="font-mono text-xs uppercase tracking-widest flex items-center gap-2">
                        {m.label}
                        {e.auto_detected && <span className="text-[9px] text-accent-amber">AI</span>}
                      </div>
                      <div className="text-xs text-ink-muted truncate">{e.notes || `${e.team || ''} ${e.player_name || ''}`}</div>
                    </div>
                    {e.minute != null && <div className="font-mono text-xs text-accent-amber flex-shrink-0">{e.minute}'</div>}
                  </div>
                );
              })}
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}

function ControlBtn({ onClick, icon: Icon, label, color, filled, pulse, testid }) {
  return (
    <button
      data-testid={testid}
      onClick={onClick}
      className={`flex flex-col items-center justify-center gap-1 h-20 border-2 transition-all hover:scale-95 active:scale-90 ${pulse ? 'animate-pulse-red' : ''}`}
      style={{
        borderColor: color,
        background: filled ? color : 'transparent',
        color: filled ? '#000' : color,
      }}
    >
      <Icon className="w-5 h-5" />
      <span className="font-mono text-[10px] uppercase tracking-widest font-bold">{label}</span>
    </button>
  );
}
