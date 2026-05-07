import React, { useState } from 'react';
import { CreditCard, ShieldCheck, Loader2, X, BadgeCheck } from 'lucide-react';
import { toast } from 'sonner';
import { api } from '../lib/api';
import { fmtINR } from '../lib/constants';

/**
 * RazorpayMockCheckout
 * --------------------
 * Drop-in modal that simulates the full Razorpay payment flow.
 * Steps: create_order → user clicks "Pay" → server-signed signature → verify → success
 *
 * In production, replace `confirm()` body with real Razorpay Checkout JS.
 *
 * Props:
 *   open (bool), onClose(), amountPaise (int)
 *   matchId? turfId? notes? — passed to /api/payments/razorpay/order
 *   onSuccess(booking) — called when verify returns 200
 */
export default function RazorpayMockCheckout({ open, onClose, amountPaise, matchId, turfId, notes, onSuccess }) {
  const [step, setStep] = useState('idle'); // idle | creating | review | paying | success | error
  const [order, setOrder] = useState(null);
  const [booking, setBooking] = useState(null);
  const [err, setErr] = useState('');

  if (!open) return null;

  const startOrder = async () => {
    setStep('creating'); setErr('');
    try {
      const r = await api.post('/payments/razorpay/order', { amount_paise: amountPaise, match_id: matchId, turf_id: turfId, notes: notes || {} });
      setOrder(r.data);
      setStep('review');
    } catch (e) {
      setErr(e.response?.data?.detail || 'Failed to create order');
      setStep('error');
    }
  };

  const confirm = async () => {
    setStep('paying');
    try {
      // DEV-mock branch: ask server to issue a verifiable signature on the spot.
      // (Real flow would receive signature from Razorpay Checkout JS success handler.)
      const sig = await api.post('/payments/razorpay/dev-sign', { order_id: order.order_id });
      const r = await api.post('/payments/razorpay/verify', {
        razorpay_order_id: sig.data.razorpay_order_id,
        razorpay_payment_id: sig.data.razorpay_payment_id,
        razorpay_signature: sig.data.razorpay_signature,
        booking_id: order.booking_id,
      });
      setBooking(r.data);
      setStep('success');
      onSuccess?.(r.data);
      toast.success('Payment successful — your slot is locked');
    } catch (e) {
      setErr(e.response?.data?.detail || 'Payment failed');
      setStep('error');
    }
  };

  return (
    <div className="fixed inset-0 z-[60] flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm" data-testid="razorpay-modal" onClick={(e) => e.target === e.currentTarget && step !== 'paying' && onClose?.()}>
      <div className="relative w-full max-w-md bg-bg-surface border border-line rounded-xl overflow-hidden">
        {/* Header */}
        <div className="px-5 py-4 border-b border-line flex items-center gap-3">
          <div className="w-10 h-10 rounded-lg bg-[#0c2541] border border-[#3395ff]/40 flex items-center justify-center">
            <span className="font-bold text-[#3395ff] text-sm">R</span>
          </div>
          <div className="flex-1">
            <div className="font-display text-lg leading-none">Razorpay Test Mode</div>
            <div className="font-mono text-[10px] uppercase tracking-widest text-ink-muted mt-0.5">100% secure — encrypted</div>
          </div>
          {step !== 'paying' && (
            <button data-testid="razorpay-close-btn" onClick={onClose} className="text-ink-muted hover:text-white"><X className="w-5 h-5"/></button>
          )}
        </div>

        {/* Body */}
        <div className="p-5">
          <div className="bg-bg-card border border-line p-4 rounded-lg mb-4">
            <div className="font-mono text-[10px] uppercase tracking-widest text-ink-muted">You're paying</div>
            <div className="font-display text-4xl font-bold mt-1" data-testid="razorpay-amount">{fmtINR(amountPaise)}</div>
            {(matchId || turfId) && (
              <div className="text-xs text-ink-muted mt-1">
                {matchId && <span>Match · {matchId.slice(0, 8)}</span>}
                {turfId && <span>Turf · {turfId.slice(0, 8)}</span>}
              </div>
            )}
          </div>

          {step === 'idle' && (
            <button data-testid="razorpay-start-btn" onClick={startOrder} className="w-full bg-accent-green text-black h-12 font-display text-xl tracking-widest uppercase hover:bg-[#00C853] transition-colors font-bold">
              Continue to Payment
            </button>
          )}

          {step === 'creating' && (
            <div className="flex items-center justify-center py-6 text-ink-muted">
              <Loader2 className="w-5 h-5 animate-spin mr-2" />
              <span className="font-mono text-xs uppercase tracking-widest">Creating order…</span>
            </div>
          )}

          {step === 'review' && order && (
            <>
              <div className="bg-bg-card border border-line p-3 rounded-lg mb-3 font-mono text-xs space-y-1">
                <div className="flex justify-between"><span className="text-ink-muted">Order</span><span data-testid="razorpay-order-id">{order.order_id}</span></div>
                <div className="flex justify-between"><span className="text-ink-muted">Mode</span>
                  <span className={order.dev_mode ? 'text-accent-amber' : 'text-accent-green'}>{order.dev_mode ? 'TEST · DEV-MOCK' : 'TEST'}</span>
                </div>
                <div className="flex justify-between"><span className="text-ink-muted">Method</span><span>UPI · QR · Card</span></div>
              </div>
              <button data-testid="razorpay-pay-btn" onClick={confirm} className="w-full bg-[#3395ff] text-white h-12 font-display text-lg tracking-widest uppercase hover:bg-[#1f7be5] transition-colors font-bold flex items-center justify-center gap-2">
                <CreditCard className="w-5 h-5"/> Pay {fmtINR(amountPaise)}
              </button>
              <div className="mt-3 flex items-center justify-center gap-1.5 text-[10px] font-mono uppercase tracking-widest text-ink-muted">
                <ShieldCheck className="w-3 h-3"/> HMAC-SHA256 verified
              </div>
            </>
          )}

          {step === 'paying' && (
            <div className="flex flex-col items-center justify-center py-8">
              <Loader2 className="w-8 h-8 animate-spin text-accent-green mb-3" />
              <div className="font-mono text-xs uppercase tracking-widest text-ink-muted">Processing payment…</div>
            </div>
          )}

          {step === 'success' && booking && (
            <div data-testid="razorpay-success" className="text-center py-4">
              <div className="w-16 h-16 mx-auto bg-accent-green text-black rounded-full flex items-center justify-center mb-3">
                <BadgeCheck className="w-9 h-9"/>
              </div>
              <div className="font-display text-2xl">PAYMENT CONFIRMED</div>
              <div className="font-mono text-xs uppercase tracking-widest text-ink-muted mt-1">QR ticket: {booking.qr_token?.slice(0,8)}…</div>
              <button data-testid="razorpay-done-btn" onClick={onClose} className="mt-4 w-full bg-accent-green text-black h-11 font-display text-lg tracking-widest uppercase hover:bg-[#00C853] transition-colors font-bold">
                Done
              </button>
            </div>
          )}

          {step === 'error' && (
            <div data-testid="razorpay-error" className="text-center py-4">
              <div className="text-accent-red font-mono text-sm">{err}</div>
              <button onClick={() => setStep('idle')} className="mt-3 text-xs font-mono uppercase tracking-widest text-accent-green hover:underline">
                Try again
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
