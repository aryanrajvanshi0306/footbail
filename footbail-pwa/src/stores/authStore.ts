/**
 * Auth Store — Zustand
 * Persists tokens in localStorage; exposes typed actions.
 */
import { create } from "zustand";
import { persist } from "zustand/middleware";
import type { User } from "../api/client";

interface AuthState {
  user: User | null;
  accessToken: string | null;
  refreshToken: string | null;
  isAuthenticated: boolean;

  setTokens: (access: string, refresh: string) => void;
  setUser: (user: User) => void;
  logout: () => void;
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      user: null,
      accessToken: null,
      refreshToken: null,
      isAuthenticated: false,

      setTokens: (access, refresh) => {
        localStorage.setItem("footbail_access_token", access);
        localStorage.setItem("footbail_refresh_token", refresh);
        set({ accessToken: access, refreshToken: refresh, isAuthenticated: true });
      },

      setUser: (user) => set({ user }),

      logout: () => {
        localStorage.removeItem("footbail_access_token");
        localStorage.removeItem("footbail_refresh_token");
        set({ user: null, accessToken: null, refreshToken: null, isAuthenticated: false });
      },
    }),
    {
      name: "footbail-auth",
      partialize: (s) => ({
        accessToken: s.accessToken,
        refreshToken: s.refreshToken,
        isAuthenticated: s.isAuthenticated,
        user: s.user,
      }),
    },
  ),
);
