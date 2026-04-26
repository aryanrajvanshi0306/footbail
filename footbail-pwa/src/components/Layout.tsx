import { type ReactNode, useState } from "react";
import { NavLink, useNavigate } from "react-router-dom";
import {
  BarChart3, Home, Map, Search, Shield, Trophy, Upload, Users, Video, LogOut, Menu, X,
} from "lucide-react";
import { useAuthStore } from "../stores/authStore";
import { useLogout } from "../hooks/useAuth";

const NAV: Record<string, { icon: typeof Home; label: string; href: string }[]> = {
  player: [
    { icon: Home,    label: "Dashboard",    href: "/dashboard" },
    { icon: Video,   label: "My Footage",   href: "/footage" },
    { icon: Upload,  label: "Upload",       href: "/upload" },
    { icon: Search,  label: "Find Match",   href: "/matches" },
    { icon: Users,   label: "Find Coach",   href: "/coaches" },
    { icon: Map,     label: "Turf Map",     href: "/turfs" },
  ],
  coach: [
    { icon: Home,    label: "Dashboard",    href: "/dashboard" },
    { icon: BarChart3, label: "Squad Stats", href: "/squad" },
    { icon: Video,   label: "Footage",      href: "/footage" },
    { icon: Search,  label: "Matches",      href: "/matches" },
    { icon: Map,     label: "Turf Map",     href: "/turfs" },
  ],
  referee: [
    { icon: Home,    label: "Dashboard",    href: "/dashboard" },
    { icon: Shield,  label: "VAR Panel",    href: "/var" },
    { icon: Search,  label: "Matches",      href: "/matches" },
  ],
  admin: [
    { icon: Home,    label: "Dashboard",    href: "/dashboard" },
    { icon: Users,   label: "Users",        href: "/admin/users" },
    { icon: Trophy,  label: "Matches",      href: "/matches" },
    { icon: Map,     label: "Turfs",        href: "/admin/turfs" },
    { icon: BarChart3, label: "Analytics",  href: "/admin/analytics" },
  ],
};

interface LayoutProps { children: ReactNode }

export default function Layout({ children }: LayoutProps) {
  const { user } = useAuthStore();
  const { mutate: logout } = useLogout();
  const [open, setOpen] = useState(false);
  const role = (user?.role ?? "player") as keyof typeof NAV;
  const navItems = NAV[role] ?? NAV.player;

  return (
    <div className="flex h-screen bg-[#0a0a0f] overflow-hidden">
      {/* ── Sidebar (desktop) ────────────────────────────────────────────── */}
      <aside className="hidden md:flex flex-col w-64 bg-[#13131a] border-r border-[#2a2a3d] flex-shrink-0">
        <div className="px-6 py-5 border-b border-[#2a2a3d]">
          <span className="text-2xl font-black text-[#00ff88] tracking-tight">
            foot<span className="text-white">bAIl</span>
          </span>
          <div className="mt-1 text-xs text-[#6b7280] capitalize">{role} portal</div>
        </div>

        <nav className="flex-1 px-3 py-4 space-y-1 overflow-y-auto">
          {navItems.map(({ icon: Icon, label, href }) => (
            <NavLink
              key={href}
              to={href}
              className={({ isActive }) =>
                `flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm font-medium transition-all
                 ${isActive
                   ? "bg-[#00ff88]/10 text-[#00ff88] border border-[#00ff88]/20"
                   : "text-[#9ca3af] hover:text-white hover:bg-[#1a1a26]"
                 }`
              }
            >
              <Icon size={18} />
              {label}
            </NavLink>
          ))}
        </nav>

        <div className="px-3 py-4 border-t border-[#2a2a3d]">
          <div className="px-3 py-2 mb-2">
            <p className="text-sm font-medium text-white truncate">{user?.name ?? "—"}</p>
            <p className="text-xs text-[#6b7280] truncate">{user?.phone ?? user?.email ?? ""}</p>
          </div>
          <button
            onClick={() => logout()}
            className="flex items-center gap-2 w-full px-3 py-2 text-sm text-[#ef4444]
                       hover:bg-[#ef4444]/10 rounded-xl transition-colors"
          >
            <LogOut size={16} /> Sign out
          </button>
        </div>
      </aside>

      {/* ── Mobile topbar ─────────────────────────────────────────────────── */}
      <div className="flex flex-col flex-1 overflow-hidden">
        <header className="md:hidden flex items-center justify-between px-4 py-3
                           bg-[#13131a] border-b border-[#2a2a3d] flex-shrink-0">
          <span className="text-xl font-black text-[#00ff88]">
            foot<span className="text-white">bAIl</span>
          </span>
          <button onClick={() => setOpen(!open)} className="text-white p-1">
            {open ? <X size={22} /> : <Menu size={22} />}
          </button>
        </header>

        {/* Mobile drawer */}
        {open && (
          <div className="md:hidden absolute inset-0 z-50 bg-black/60" onClick={() => setOpen(false)}>
            <aside
              className="w-72 h-full bg-[#13131a] border-r border-[#2a2a3d] flex flex-col"
              onClick={(e) => e.stopPropagation()}
            >
              <div className="px-6 py-5 border-b border-[#2a2a3d]">
                <span className="text-2xl font-black text-[#00ff88]">foot<span className="text-white">bAIl</span></span>
              </div>
              <nav className="flex-1 px-3 py-4 space-y-1">
                {navItems.map(({ icon: Icon, label, href }) => (
                  <NavLink
                    key={href} to={href} onClick={() => setOpen(false)}
                    className={({ isActive }) =>
                      `flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm font-medium transition-all
                       ${isActive ? "bg-[#00ff88]/10 text-[#00ff88]" : "text-[#9ca3af] hover:text-white hover:bg-[#1a1a26]"}`
                    }
                  >
                    <Icon size={18} />{label}
                  </NavLink>
                ))}
              </nav>
              <div className="px-3 py-4 border-t border-[#2a2a3d]">
                <button onClick={() => { logout(); setOpen(false); }}
                  className="flex items-center gap-2 w-full px-3 py-2 text-sm text-[#ef4444] hover:bg-[#ef4444]/10 rounded-xl">
                  <LogOut size={16} /> Sign out
                </button>
              </div>
            </aside>
          </div>
        )}

        {/* ── Main content ────────────────────────────────────────────────── */}
        <main className="flex-1 overflow-y-auto">{children}</main>
      </div>
    </div>
  );
}
