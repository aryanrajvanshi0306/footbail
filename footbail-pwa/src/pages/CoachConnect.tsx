import { useQuery } from "@tanstack/react-query";
import { Loader2, MapPin, MessageCircle, Star, Award } from "lucide-react";
import { coachApi } from "../api/client";

const POSITIONS = ["All", "GK Coach", "Fitness", "Tactician", "Striker Coach", "Defence Coach"];

export default function CoachConnect() {
  const { data: coaches = [], isLoading } = useQuery({
    queryKey: ["coaches"],
    queryFn: coachApi.list,
    staleTime: 60_000,
  });

  const mockExtra = [
    { speciality: "Tactician", city: "Mumbai", rating: 4.8, sessions: 142, badges: ["FIFA C", "AIFF"] },
    { speciality: "Fitness Coach", city: "Pune", rating: 4.6, sessions: 89, badges: ["Sports Science"] },
    { speciality: "GK Coach", city: "Bengaluru", rating: 4.9, sessions: 210, badges: ["UEFA A"] },
    { speciality: "Striker Coach", city: "Delhi", rating: 4.7, sessions: 67, badges: ["AIFF Elite"] },
  ];

  return (
    <div className="p-6 max-w-6xl mx-auto animate-fade-in">
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-white">Coach Connect 📋</h1>
        <p className="text-sm text-[#6b7280] mt-0.5">Find certified coaches near you</p>
      </div>

      {/* Filter pills */}
      <div className="flex gap-2 overflow-x-auto pb-2 mb-6">
        {POSITIONS.map((pos) => (
          <button key={pos}
            className="flex-shrink-0 px-3 py-1.5 rounded-full text-sm border border-[#2a2a3d]
                       text-[#9ca3af] hover:border-[#00ff88] hover:text-[#00ff88] transition-colors">
            {pos}
          </button>
        ))}
      </div>

      {isLoading ? (
        <div className="flex justify-center py-16">
          <Loader2 size={32} className="text-[#00ff88] animate-spin" />
        </div>
      ) : (
        <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-4">
          {/* Real coaches from API */}
          {coaches.map((c, i) => {
            const extra = mockExtra[i % mockExtra.length]!;
            return (
              <div key={c.id}
                className="card hover:border-[#00ff88]/30 hover:bg-[#1a1a26]/80 transition-all group">
                <div className="flex items-start gap-3 mb-3">
                  <div className="w-12 h-12 rounded-full bg-[#00ff88]/10 border border-[#00ff88]/20
                                  flex items-center justify-center text-lg font-bold text-[#00ff88] flex-shrink-0">
                    {c.name[0]?.toUpperCase()}
                  </div>
                  <div className="min-w-0">
                    <p className="font-bold text-white text-sm truncate">{c.name}</p>
                    <p className="text-xs text-[#00ff88]">{extra.speciality}</p>
                    <div className="flex items-center gap-1 mt-0.5">
                      <MapPin size={11} className="text-[#6b7280]" />
                      <span className="text-xs text-[#6b7280]">{c.city ?? extra.city}</span>
                    </div>
                  </div>
                </div>

                <div className="flex items-center gap-3 mb-3">
                  <div className="flex items-center gap-1">
                    <Star size={13} className="text-[#f59e0b] fill-[#f59e0b]" />
                    <span className="text-sm font-bold text-white">{extra.rating}</span>
                  </div>
                  <span className="text-xs text-[#6b7280]">{extra.sessions} sessions</span>
                </div>

                <div className="flex flex-wrap gap-1 mb-4">
                  {extra.badges.map((b) => (
                    <span key={b} className="flex items-center gap-1 px-2 py-0.5 text-xs
                                             bg-[#2a2a3d] text-[#9ca3af] rounded-full">
                      <Award size={10} /> {b}
                    </span>
                  ))}
                </div>

                <button className="btn-secondary w-full text-sm py-2 flex items-center justify-center gap-2
                                   group-hover:border-[#00ff88] group-hover:text-[#00ff88]">
                  <MessageCircle size={14} /> Connect
                </button>
              </div>
            );
          })}

          {coaches.length === 0 && (
            <div className="col-span-3 text-center py-16 text-[#6b7280]">
              <p className="text-lg mb-1">No coaches registered yet</p>
              <p className="text-sm">Be the first to join as a coach</p>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
