import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { toast } from 'sonner';
import { ArrowRight, Check } from 'lucide-react';
import { api } from '../lib/api';
import { fmtINR } from '../lib/constants';

const TEAMS = ['FC Powai', 'Andheri United', 'BKC Strikers', 'Bandra Boys', 'Mumbai XI'];

export default function CreateMatch() {
  const nav = useNavigate();
  const [step, setStep] = useState(1);
  const [data, setData] = useState({ home_team: '', away_team: '', turf_id: '', slot: '', format: '5v5' });
  const [turfs, setTurfs] = useState([]);

  useEffect(() => { api.get('/turfs').then((r) => setTurfs(r.data)); }, []);

  const slots = [];
  for (let day = 0; day < 7; day++) {
    for (const hour of ['18:00', '19:30', '21:00']) {
      const d = new Date();
      d.setDate(d.getDate() + day);
      const [h, m] = hour.split(':');
      d.setHours(parseInt(h), parseInt(m), 0, 0);
      slots.push({ iso: d.toISOString(), label: `${d.toLocaleDateString('en-IN', { weekday: 'short', day: '2-digit', month: 'short' })} · ${hour}` });
    }
  }

  const set = (k, v) => setData((s) => ({ ...s, [k]: v }));

  const create = async () => {
    try {
      const r = await api.post('/matches', {
        home_team: data.home_team,
        away_team: data.away_team,
        turf_id: data.turf_id,
        scheduled_at: data.slot,
        format: data.format,
      });
      toast.success('Match scheduled');
      nav(`/matches/${r.data.id}`);
    } catch (e) {
      toast.error(e.response?.data?.detail || 'Failed');
    }
  };

  const STEPS = ['Team', 'Opponent', 'Slot', 'Pay', 'Confirm'];

  return (
    <div className="px-4 pt-4 pb-24" data-testid="create-match-page">
      <div className="font-mono text-[10px] uppercase tracking-widest text-ink-muted">Step {step}/5</div>
      <div className="font-display text-3xl mb-1">CREATE MATCH</div>
      <div className="flex gap-1 mb-6">
        {STEPS.map((s, i) => (
          <div key={s} className={`flex-1 h-1 ${i < step ? 'bg-brand-primary' : 'bg-line'}`} />
        ))}
      </div>

      {step === 1 && (
        <div className="space-y-2" data-testid="step-team">
          <div className="font-mono text-xs uppercase tracking-widest text-ink-muted mb-2">Your Team</div>
          {TEAMS.map((t) => (
            <button
              key={t}
              data-testid={`pick-home-${t}`}
              onClick={() => { set('home_team', t); setStep(2); }}
              className={`w-full text-left p-4 border ${data.home_team === t ? 'border-brand-primary bg-brand-primary/10' : 'border-line hover:border-ink-muted'}`}
            >
              <span className="font-display text-xl">{t.toUpperCase()}</span>
            </button>
          ))}
        </div>
      )}

      {step === 2 && (
        <div className="space-y-2" data-testid="step-opp">
          <div className="font-mono text-xs uppercase tracking-widest text-ink-muted mb-2">Opponent</div>
          {TEAMS.filter((t) => t !== data.home_team).map((t) => (
            <button
              key={t}
              data-testid={`pick-away-${t}`}
              onClick={() => { set('away_team', t); setStep(3); }}
              className={`w-full text-left p-4 border ${data.away_team === t ? 'border-brand-primary bg-brand-primary/10' : 'border-line hover:border-ink-muted'}`}
            >
              <span className="font-display text-xl">{t.toUpperCase()}</span>
            </button>
          ))}
        </div>
      )}

      {step === 3 && (
        <div className="space-y-3" data-testid="step-slot">
          <div className="font-mono text-xs uppercase tracking-widest text-ink-muted">Pick Turf</div>
          <div className="grid gap-2">
            {turfs.map((t) => (
              <button
                key={t.id}
                data-testid={`pick-turf-${t.id}`}
                onClick={() => set('turf_id', t.id)}
                className={`text-left p-3 border ${data.turf_id === t.id ? 'border-brand-primary bg-brand-primary/10' : 'border-line hover:border-ink-muted'}`}
              >
                <div className="font-display text-lg">{t.name.toUpperCase()}</div>
                <div className="font-mono text-[10px] uppercase tracking-widest text-ink-muted">{t.address} · {fmtINR(t.price_per_slot)} / slot</div>
              </button>
            ))}
          </div>
          <div className="font-mono text-xs uppercase tracking-widest text-ink-muted mt-4">Slot</div>
          <div className="grid grid-cols-2 gap-2 max-h-72 overflow-y-auto">
            {slots.map((s) => (
              <button
                key={s.iso}
                data-testid={`slot-${s.iso}`}
                onClick={() => set('slot', s.iso)}
                className={`p-2 border text-xs font-mono ${data.slot === s.iso ? 'border-brand-primary bg-brand-primary/10' : 'border-line hover:border-ink-muted'}`}
              >
                {s.label}
              </button>
            ))}
          </div>
          <button
            data-testid="step3-next"
            disabled={!data.turf_id || !data.slot}
            onClick={() => setStep(4)}
            className="w-full mt-4 bg-brand-primary h-12 font-display text-xl tracking-widest uppercase disabled:opacity-40 hover:bg-[#D63026]"
          >
            Next →
          </button>
        </div>
      )}

      {step === 4 && (
        <div className="space-y-3" data-testid="step-pay">
          <div className="bg-bg-card border border-line p-4">
            <div className="font-mono text-[10px] uppercase tracking-widest text-ink-muted">Payment</div>
            <div className="font-display text-3xl mt-1">{fmtINR(turfs.find((t) => t.id === data.turf_id)?.price_per_slot || 0)}</div>
            <div className="text-sm text-ink-muted">UPI / Card / Netbanking via Razorpay (mocked in MVP)</div>
          </div>
          <button data-testid="mock-pay-btn" onClick={() => setStep(5)} className="w-full bg-brand-accent text-black h-12 font-display text-xl tracking-widest uppercase hover:opacity-90">
            Pay Now (Mock)
          </button>
        </div>
      )}

      {step === 5 && (
        <div className="space-y-3" data-testid="step-confirm">
          <div className="bg-bg-card border border-line p-4 space-y-2">
            <Row k="MATCH" v={`${data.home_team} vs ${data.away_team}`} />
            <Row k="TURF" v={turfs.find((t) => t.id === data.turf_id)?.name} />
            <Row k="SLOT" v={new Date(data.slot).toLocaleString('en-IN')} />
            <Row k="FORMAT" v={data.format} />
          </div>
          <button data-testid="confirm-create-btn" onClick={create} className="w-full bg-brand-primary h-12 font-display text-xl tracking-widest uppercase hover:bg-[#D63026] flex items-center justify-center gap-2">
            <Check className="w-5 h-5" /> Confirm Match
          </button>
        </div>
      )}
    </div>
  );
}

const Row = ({ k, v }) => (
  <div className="flex justify-between items-center">
    <span className="font-mono text-[10px] uppercase tracking-widest text-ink-muted">{k}</span>
    <span className="font-mono text-sm">{v}</span>
  </div>
);
