import { TrendingUp, TrendingDown } from "lucide-react";

interface StatCardProps {
  val: string;
  label: string;
  delta?: string | null;
  color?: string;
}

export default function StatCard({ val, label, delta, color }: StatCardProps) {
  const isUp = delta?.startsWith("+");
  const isDown = delta?.startsWith("-");

  return (
    <div className="card hover:border-[#00ff88]/30 hover:bg-[#1a1a26]/80 transition-all duration-200">
      <p
        className="text-3xl font-black font-mono mb-1"
        style={{ color: color ?? "var(--g, #00ff88)" }}
      >
        {val}
      </p>
      <p className="text-xs text-[#6b7280] uppercase tracking-widest font-semibold">{label}</p>
      {delta && (
        <div
          className={`flex items-center gap-1 mt-2 text-xs font-medium
            ${isUp ? "text-[#00ff88]" : isDown ? "text-[#ef4444]" : "text-[#6b7280]"}`}
        >
          {isUp && <TrendingUp size={12} />}
          {isDown && <TrendingDown size={12} />}
          {delta}
        </div>
      )}
    </div>
  );
}
