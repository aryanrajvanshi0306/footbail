import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useNavigate } from "react-router-dom";
import { authApi } from "../api/client";
import { useAuthStore } from "../stores/authStore";

// ─── Current user ─────────────────────────────────────────────────────────

export function useMe() {
  const { isAuthenticated } = useAuthStore();
  return useQuery({
    queryKey: ["me"],
    queryFn: authApi.me,
    enabled: isAuthenticated,
    staleTime: 5 * 60 * 1000,
    retry: false,
  });
}

// ─── OTP send ─────────────────────────────────────────────────────────────

export function useSendOtp() {
  return useMutation({
    mutationFn: ({ phone, role }: { phone: string; role: string }) =>
      authApi.sendOtp(phone, role),
  });
}

// ─── OTP verify ───────────────────────────────────────────────────────────

export function useVerifyOtp() {
  const { setTokens, setUser } = useAuthStore();
  const qc = useQueryClient();

  return useMutation({
    mutationFn: ({
      phone,
      otp,
      role,
    }: {
      phone: string;
      otp: string;
      role: string;
    }) => authApi.verifyOtp(phone, otp, role),

    onSuccess: async (tokens) => {
      setTokens(tokens.access_token, tokens.refresh_token);
      const me = await authApi.me();
      setUser(me.user);
      qc.setQueryData(["me"], me);
    },
  });
}

// ─── Logout ───────────────────────────────────────────────────────────────

export function useLogout() {
  const { logout, refreshToken } = useAuthStore();
  const qc = useQueryClient();
  const navigate = useNavigate();

  return useMutation({
    mutationFn: async () => {
      if (refreshToken) {
        try {
          await authApi.logout(refreshToken);
        } catch {
          // ignore revocation errors
        }
      }
    },
    onSettled: () => {
      logout();
      qc.clear();
      navigate("/login");
    },
  });
}
