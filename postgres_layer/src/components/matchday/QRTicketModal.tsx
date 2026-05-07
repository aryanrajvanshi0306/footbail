import { useEffect, useState } from "react";
import { QRCodeCanvas } from "qrcode.react";

interface TicketData {
  qr_token: string; turf_name: string; address: string;
  scheduled_at_ist: string; format: string; match_id: string;
}

interface Props { matchId: string; onClose: () => void; }

const DB_NAME = "footbail_ticket_cache";
const STORE = "tickets";

async function dbOpen(): Promise<IDBDatabase> {
  return new Promise((resolve, reject) => {
    const req = indexedDB.open(DB_NAME, 1);
    req.onupgradeneeded = () => req.result.createObjectStore(STORE, { keyPath: "match_id" });
    req.onsuccess = () => resolve(req.result);
    req.onerror = () => reject(req.error);
  });
}
async function dbPut(t: TicketData): Promise<void> {
  const db = await dbOpen();
  return new Promise((res, rej) => {
    const tx = db.transaction(STORE, "readwrite"); tx.objectStore(STORE).put(t);
    tx.oncomplete = () => res(); tx.onerror = () => rej(tx.error);
  });
}
async function dbGet(matchId: string): Promise<TicketData | null> {
  const db = await dbOpen();
  return new Promise((res) => {
    const tx = db.transaction(STORE, "readonly"); const r = tx.objectStore(STORE).get(matchId);
    r.onsuccess = () => res((r.result as TicketData) ?? null);
    r.onerror = () => res(null);
  });
}

export default function QRTicketModal({ matchId, onClose }: Props): JSX.Element {
  const [data, setData] = useState<TicketData | null>(null);
  const [offline, setOffline] = useState<boolean>(!navigator.onLine);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      // Read-first when offline
      if (!navigator.onLine) {
        const cached = await dbGet(matchId);
        if (cached && !cancelled) { setData(cached); setOffline(true); return; }
      }
      try {
        const r = await fetch(`/v2/matches/${matchId}/ticket`, { headers: { Authorization: `Bearer ${localStorage.getItem("fb_token") ?? ""}` } });
        const j: TicketData = await r.json();
        if (cancelled) return;
        setData(j);
        await dbPut(j);   // always write to Dexie/IndexedDB on first successful API load
      } catch {
        const cached = await dbGet(matchId);
        if (cached && !cancelled) { setData(cached); setOffline(true); }
      }
    })();
    return () => { cancelled = true; };
  }, [matchId]);

  return (
    <div className="fixed inset-0 z-50 bg-bg/80 flex items-center justify-center p-4" onClick={onClose} data-testid="qr-ticket-modal">
      {/* THE ONLY WHITE-BG SCREEN IN THE APP — required for QR scanner contrast */}
      <div className="bg-white text-black w-full max-w-sm rounded-xl p-5 relative" onClick={(e) => e.stopPropagation()}>
        {offline && <div className="bg-amber-100 text-amber-900 text-xs px-3 py-1 rounded-md mb-3">📵 Cached Ticket (Offline)</div>}
        <button data-testid="ticket-close" onClick={onClose} className="absolute top-2 right-2 text-black/60 text-xl leading-none">×</button>

        {data ? (
          <>
            <div className="text-center">
              <div className="text-[10px] uppercase tracking-widest text-black/60 font-mono">FOOTBAIL.IN · MATCH TICKET</div>
              <div className="mx-auto mt-3 inline-block p-2 bg-white border border-black/10">
                <QRCodeCanvas value={data.qr_token} size={220} level="H" includeMargin={false} bgColor="#ffffff" fgColor="#000000" />
              </div>
              <div className="font-bold text-lg mt-3">{data.turf_name}</div>
              <div className="text-sm text-black/70">{data.address}</div>
              <div className="font-mono text-xs mt-3">{new Date(data.scheduled_at_ist).toLocaleString("en-IN", { dateStyle: "medium", timeStyle: "short" })}</div>
              <div className="font-mono text-xs text-black/60">{data.format}</div>
            </div>
            <button data-testid="ticket-download"
              onClick={() => window.print()}
              className="w-full mt-4 h-11 bg-black text-white font-mono uppercase tracking-widest text-xs rounded-md">
              Download Ticket
            </button>
            <button data-testid="ticket-whatsapp"
              onClick={() => window.open(`https://wa.me/?text=${encodeURIComponent(`My footbAIl match at ${data.turf_name} on ${data.scheduled_at_ist}`)}`, "_blank")}
              className="w-full mt-2 h-11 bg-[#00E676] text-black font-mono uppercase tracking-widest text-xs font-bold rounded-md">
              Share via WhatsApp
            </button>
          </>
        ) : (
          <div className="text-center py-8 text-black/60">Loading ticket…</div>
        )}
      </div>
    </div>
  );
}
