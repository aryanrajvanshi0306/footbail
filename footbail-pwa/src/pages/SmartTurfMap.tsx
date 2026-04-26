import { useState } from "react";
import { MapPin, Camera, Phone, Star, Wifi, X } from "lucide-react";

interface Turf {
  id: string; name: string; city: string; address: string;
  lat: number; lng: number; has_cameras: boolean;
  contact: string; rating: number; price: number;
}

const TURFS: Turf[] = [
  { id:"t1", name:"Juhu Beach Turf", city:"Mumbai", address:"Juhu, Mumbai 400049",
    lat:19.0883, lng:72.8264, has_cameras:true, contact:"+91 98765 43210", rating:4.8, price:1200 },
  { id:"t2", name:"Bandra Football Ground", city:"Mumbai", address:"Bandra (W), Mumbai 400050",
    lat:19.0596, lng:72.8295, has_cameras:false, contact:"+91 98765 11111", rating:4.3, price:900 },
  { id:"t3", name:"Powai Sports Complex", city:"Mumbai", address:"Powai, Mumbai 400076",
    lat:19.1176, lng:72.9060, has_cameras:true, contact:"+91 98765 22222", rating:4.6, price:1500 },
  { id:"t4", name:"Koregaon Park Turf", city:"Pune", address:"Koregaon Park, Pune 411001",
    lat:18.5362, lng:73.8941, has_cameras:true, contact:"+91 98765 33333", rating:4.7, price:1100 },
  { id:"t5", name:"Indiranagar FC Ground", city:"Bengaluru", address:"Indiranagar, Bengaluru 560038",
    lat:12.9784, lng:77.6408, has_cameras:false, contact:"+91 98765 44444", rating:4.4, price:1000 },
];

export default function SmartTurfMap() {
  const [selected, setSelected] = useState<Turf | null>(null);
  const [cityFilter, setCityFilter] = useState("All");

  const cities = ["All", ...Array.from(new Set(TURFS.map((t) => t.city)))];
  const filtered = cityFilter === "All" ? TURFS : TURFS.filter((t) => t.city === cityFilter);

  return (
    <div className="p-6 max-w-7xl mx-auto animate-fade-in">
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-white">Smart Turf Map 📍</h1>
        <p className="text-sm text-[#6b7280] mt-0.5">AI-enabled turfs with camera integration</p>
      </div>

      {/* City filter */}
      <div className="flex gap-2 overflow-x-auto pb-2 mb-6">
        {cities.map((c) => (
          <button key={c}
            onClick={() => setCityFilter(c)}
            className={`flex-shrink-0 px-4 py-1.5 rounded-full text-sm font-medium transition-all border
              ${cityFilter === c
                ? "bg-[#00ff88] text-black border-[#00ff88]"
                : "border-[#2a2a3d] text-[#9ca3af] hover:border-[#00ff88]/40"}`}>
            {c}
          </button>
        ))}
      </div>

      <div className="grid lg:grid-cols-2 gap-6">
        {/* SVG Map (simplified India outline + pins) */}
        <div className="card relative overflow-hidden" style={{ minHeight: 420 }}>
          <h2 className="text-xs font-semibold text-[#6b7280] uppercase tracking-wider mb-3">
            Map View
          </h2>
          <svg viewBox="0 0 400 500" className="w-full h-full" style={{ maxHeight: 380 }}>
            {/* India outline approximation */}
            <path
              d="M200,30 L280,60 L310,90 L330,140 L340,190 L320,240 L290,280 L270,320
                 L250,360 L220,400 L200,440 L180,420 L160,390 L140,350 L120,300
                 L100,260 L90,210 L100,160 L120,120 L150,80 L180,50 Z"
              fill="#1a1a26" stroke="#2a2a3d" strokeWidth="2"
            />

            {/* Grid lines */}
            {[100,150,200,250,300,350].map((y) => (
              <line key={y} x1="80" y1={y} x2="340" y2={y} stroke="#2a2a3d" strokeWidth="0.5" />
            ))}
            {[120,160,200,240,280,320].map((x) => (
              <line key={x} x1={x} y1="40" x2={x} y2="440" stroke="#2a2a3d" strokeWidth="0.5" />
            ))}

            {/* Turf pins — mapped to approximate SVG coords */}
            {[
              { ...TURFS[0]!, sx:190, sy:285 },
              { ...TURFS[1]!, sx:185, sy:295 },
              { ...TURFS[2]!, sx:200, sy:270 },
              { ...TURFS[3]!, sx:195, sy:315 },
              { ...TURFS[4]!, sx:200, sy:350 },
            ].filter((t) => cityFilter === "All" || t.city === cityFilter).map((turf) => (
              <g key={turf.id} onClick={() => setSelected(TURFS.find((t) => t.id === turf.id) ?? null)}
                className="cursor-pointer">
                <circle cx={turf.sx} cy={turf.sy} r="12" fill="#00ff88" opacity="0.15" />
                <circle
                  cx={turf.sx} cy={turf.sy} r="6"
                  fill={selected?.id === turf.id ? "#00ff88" : "#00cc6a"}
                  stroke={turf.has_cameras ? "#fff" : "none"}
                  strokeWidth="1.5"
                  className="transition-all hover:r-8"
                />
                <text x={turf.sx} y={turf.sy - 14} textAnchor="middle"
                  fontSize="8" fill="#d1d5db" fontFamily="Inter">
                  {turf.name.split(" ")[0]}
                </text>
              </g>
            ))}
          </svg>

          {/* Legend */}
          <div className="absolute bottom-4 left-4 flex items-center gap-4 text-xs text-[#6b7280]">
            <span className="flex items-center gap-1">
              <span className="w-2.5 h-2.5 rounded-full bg-[#00ff88] border border-white" />
              AI Camera
            </span>
            <span className="flex items-center gap-1">
              <span className="w-2.5 h-2.5 rounded-full bg-[#00cc6a]" />
              Standard
            </span>
          </div>
        </div>

        {/* Turf list */}
        <div className="space-y-3 overflow-y-auto" style={{ maxHeight: 480 }}>
          {filtered.map((t) => (
            <div
              key={t.id}
              onClick={() => setSelected(selected?.id === t.id ? null : t)}
              className={`card cursor-pointer transition-all hover:border-[#00ff88]/40
                ${selected?.id === t.id ? "border-[#00ff88]/60 bg-[#00ff88]/5" : ""}`}
            >
              <div className="flex items-start justify-between gap-2">
                <div className="min-w-0">
                  <div className="flex items-center gap-2 mb-1">
                    <p className="font-bold text-white text-sm truncate">{t.name}</p>
                    {t.has_cameras && (
                      <span className="flex items-center gap-0.5 text-xs text-[#3b82f6] flex-shrink-0">
                        <Camera size={11} /> AI
                      </span>
                    )}
                  </div>
                  <div className="flex items-center gap-1 text-xs text-[#6b7280]">
                    <MapPin size={11} /> {t.address}
                  </div>
                </div>
                <div className="text-right flex-shrink-0">
                  <div className="flex items-center gap-1 justify-end">
                    <Star size={12} className="text-[#f59e0b] fill-[#f59e0b]" />
                    <span className="text-sm font-bold text-white">{t.rating}</span>
                  </div>
                  <p className="text-xs text-[#00ff88] mt-0.5">₹{t.price}/hr</p>
                </div>
              </div>

              {selected?.id === t.id && (
                <div className="mt-3 pt-3 border-t border-[#2a2a3d] animate-slide-up">
                  <div className="flex flex-wrap gap-2">
                    <a href={`tel:${t.contact}`}
                      className="flex items-center gap-1 text-xs text-[#00ff88] hover:underline">
                      <Phone size={12} /> {t.contact}
                    </a>
                    {t.has_cameras && (
                      <span className="flex items-center gap-1 text-xs text-[#3b82f6]">
                        <Wifi size={12} /> Live streaming enabled
                      </span>
                    )}
                  </div>
                  <a
                    href={`https://maps.google.com/?q=${t.lat},${t.lng}`}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="btn-primary text-xs px-3 py-1.5 mt-3 inline-block"
                  >
                    Open in Maps
                  </a>
                </div>
              )}
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
