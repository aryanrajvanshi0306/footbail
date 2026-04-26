import { useQuery } from "@tanstack/react-query";
import { dashboardApi, matchApi, footageApi, adminApi } from "../api/client";

export function useDashboard() {
  return useQuery({
    queryKey: ["dashboard"],
    queryFn: dashboardApi.get,
    staleTime: 60_000,
  });
}

export function useMatches(page = 1, city?: string) {
  return useQuery({
    queryKey: ["matches", page, city],
    queryFn: () => matchApi.list(page, city),
    staleTime: 30_000,
  });
}

export function useMyVideos() {
  return useQuery({
    queryKey: ["my-videos"],
    queryFn: footageApi.myVideos,
    staleTime: 30_000,
  });
}

export function useAdminMetrics() {
  return useQuery({
    queryKey: ["admin-metrics"],
    queryFn: adminApi.metrics,
    staleTime: 30_000,
  });
}

export function useAdminUsers() {
  return useQuery({
    queryKey: ["admin-users"],
    queryFn: () => adminApi.users(),
    staleTime: 60_000,
  });
}
