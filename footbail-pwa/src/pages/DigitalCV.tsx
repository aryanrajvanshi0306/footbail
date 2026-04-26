import { useParams } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { Loader2, Star, Target, Award, TrendingUp } from "lucide-react";
import { api } from "../api/client";
import { useAuthStore } from "../stores/authStore";

interface Profile {
  user_id: string; position: string | null; dominant_foot: string | null;
  jersey_number: number | null; rating: number | null;
  total_goals: number; total_assists: number; total_matches: number;
  bio: string | null; highlight_video_url: string | null;
}

export default function DigitalCV() {
  const { playerId } = useParams<{ playerId: string }>();
  const { user } = useAuthStore();
  const id = playerId ?? user?.id;

  const { data: profile, isLoading } = useQuery<Profile>({
    queryKey: ["profile", id],
    queryFn: () => api.get(`/players/${id}/profile`),
    enabled: !!id,
  });

  if (isLoading) return (
    <div className="flex items-center justify-center h-64">
      <Loader2 size={32} className="text-[#00ff88] animate-spin" />
    </div>
  );

  const statsGrid = [
    { icon: Target, label: "Goals", val: profile?.total_goals ?? 0, color: "text-[#00ff88]" },
    { icon: TrendingUp, label: "Assists", val: profile?.total_assists ?? 0, color: "text-[#3b82f6]" },
    { icon: Award, label: "Matches", val: profile?.total_matches ?? 0, color: "text-[#f59e0b]" },
    { icon: Star, label: "Rating", val: profile?.rating?.toFixed(1) ?? "—", color: "text-purple-400" },
  ];

  return (
    <div className="p-6 max-w-3xl mx-auto animate-fade-in">
      <h1 className="text-2xl font-bold text-white mb-6">Digital CV 📄</h1>

      {!profile ? (
        <div className="card text-center py-12">
          <p className="text-[#6b7280]">No profile found. Update your profile to generate your CV.</p>
        </div>
      ) : (
        <div className="space-y-6">
          {/* Header card */}
          <div className="card flex flex-col sm:flex-row items-center sm:items-start gap-6">
            <div className="w-20 h-20 rounded-full bg-[#00ff88]/10 border-2 border-[#00ff88]/30
                            flex items-center justify-center text-3xl font-black text-[#00ff88] flex-shrink-0">
              {user?.name?.[0]?.toUpperCase() ?? "?"}
            </div>
            <div className="text-center sm:text-left">
              <h2 className="text-xl font-bold text-white">{user?.name ?? "—"}</h2>
              <p className="text-[#00ff88] font-semibold">{profile.position ?? "Footballer"}</p>
              {profile.jersey_number && (
                <p className="text-[#6b7280] text-sm"># {profile.jersey_number}</p>
              )}
              {profile.dominant_foot && (
                <p className="text-[#6b7280] text-sm">Dominant foot: {profile.dominant_foot}</p>
              )}
              {profile.bio && (
                <p className="text-[#9ca3af] text-sm mt-2 leading-relaxed">{profile.bio}</p>
              )}
            </div>
          </div>

          {/* Stats */}
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
            {statsGrid.map(({ icon: Icon, label, val, color }) => (
              <div key={label} className="card text-center">
                <Icon size={20} className={`${color} mx-auto mb-2`} />
                <p className={`text-2xl font-black ${color}`}>{val}</p>
                <p className="text-xs text-[#6b7280] uppercase tracking-wider mt-0.5">{label}</p>
              </div>
            ))}
          </div>

          {/* Highlight video */}
          {profile.highlight_video_url && (
            <div className="card">
              <h3 className="text-sm font-semibold text-[#6b7280] uppercase tracking-wider mb-3">
                Highlight Reel
              </h3>
              <video src={profile.highlight_video_url} controls className="w-full rounded-lg" />
            </div>
          )}

          <div className="card border-[#00ff88]/20 bg-[#00ff88]/5 text-center">
            <p className="text-xs text-[#00ff88] font-semibold uppercase tracking-wider mb-1">
              Powered by footbAIl
            </p>
            <p className="text-[#6b7280] text-xs">
              Share your Digital CV: footbail.in/cv/{id?.slice(0, 8)}
            </p>
          </div>
        </div>
      )}
    </div>
  );
}
