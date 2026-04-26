/**
 * API Client — thin fetch wrapper around the footbAIl backend.
 * Automatically attaches Bearer token from localStorage.
 */

const BASE = import.meta.env.VITE_API_URL ?? "";

export class ApiError extends Error {
  constructor(
    public status: number,
    message: string,
    public body?: unknown,
  ) {
    super(message);
    this.name = "ApiError";
  }
}

function getToken(): string | null {
  return localStorage.getItem("footbail_access_token");
}

async function request<T>(
  method: string,
  path: string,
  body?: unknown,
  extraHeaders?: Record<string, string>,
): Promise<T> {
  const token = getToken();
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...extraHeaders,
  };
  if (token) headers["Authorization"] = `Bearer ${token}`;

  const res = await fetch(`${BASE}${path}`, {
    method,
    headers,
    body: body !== undefined ? JSON.stringify(body) : undefined,
  });

  if (!res.ok) {
    let errorBody: unknown;
    try {
      errorBody = await res.json();
    } catch {
      errorBody = await res.text();
    }
    const message =
      typeof errorBody === "object" &&
      errorBody !== null &&
      "detail" in errorBody
        ? String((errorBody as { detail: unknown }).detail)
        : res.statusText;
    throw new ApiError(res.status, message, errorBody);
  }

  if (res.status === 204) return undefined as T;
  return res.json() as Promise<T>;
}

export const api = {
  get: <T>(path: string) => request<T>("GET", path),
  post: <T>(path: string, body?: unknown) => request<T>("POST", path, body),
  put: <T>(path: string, body?: unknown) => request<T>("PUT", path, body),
  delete: <T>(path: string) => request<T>("DELETE", path),
};

// ─── Auth ────────────────────────────────────────────────────────────────────

export interface TokenPair {
  access_token: string;
  refresh_token: string;
  expires_in: number;
}

export interface OTPSendResponse {
  message: string;
  dev_otp?: string;
}

export interface MeResponse {
  user: User;
  role: string;
}

export interface User {
  id: string;
  name: string;
  phone: string | null;
  email: string | null;
  role: "player" | "coach" | "referee" | "admin";
  avatar_url: string | null;
  city: string | null;
  is_verified: boolean;
  created_at: string;
}

export const authApi = {
  sendOtp: (phone: string, role: string): Promise<OTPSendResponse> =>
    api.post("/auth/otp/send", { phone, role }),

  verifyOtp: (phone: string, otp: string, role: string): Promise<TokenPair> =>
    api.post("/auth/verify-otp", { phone, otp, role }),

  googleAuth: (code: string, role: string): Promise<TokenPair> =>
    api.post("/auth/google", { code, role }),

  refresh: (refresh_token: string): Promise<TokenPair> =>
    api.post("/auth/refresh", { refresh_token }),

  logout: (refresh_token: string): Promise<void> =>
    api.post("/auth/logout", { refresh_token }),

  me: (): Promise<MeResponse> => api.get("/auth/me"),
};

// ─── Dashboard ───────────────────────────────────────────────────────────────

export const dashboardApi = {
  get: (): Promise<unknown> => api.get("/players/dashboard"),
};

// ─── Matches ─────────────────────────────────────────────────────────────────

export interface MatchOut {
  id: string;
  home_team: string;
  away_team: string;
  scheduled_at: string;
  status: string;
  home_score: number;
  away_score: number;
  city: string | null;
  turf_id: string | null;
}

export interface MatchListOut {
  items: MatchOut[];
  total: number;
  page: number;
  limit: number;
}

export const matchApi = {
  list: (page = 1, city?: string): Promise<MatchListOut> =>
    api.get(`/matches?page=${page}${city ? `&city=${city}` : ""}`),

  get: (id: string): Promise<MatchOut> => api.get(`/matches/${id}`),

  create: (data: {
    home_team: string;
    away_team: string;
    scheduled_at: string;
    city?: string;
  }): Promise<MatchOut> => api.post("/matches", data),
};

// ─── Footage ─────────────────────────────────────────────────────────────────

export interface VideoOut {
  id: string;
  match_id: string | null;
  uploaded_by: string | null;
  title: string | null;
  status: string;
  processed_hls_url: string | null;
  thumbnail_url: string | null;
  ai_analysis: Record<string, unknown> | null;
  duration_sec: number | null;
  created_at: string;
}

export interface UploadUrlResponse {
  upload_url: string;
  object_key: string;
  video_id: string;
}

export const footageApi = {
  getUploadUrl: (
    filename: string,
    content_type: string,
    match_id?: string,
  ): Promise<UploadUrlResponse> =>
    api.post("/footage/upload-url", { filename, content_type, match_id }),

  confirm: (
    video_id: string,
    object_key: string,
    file_size_bytes?: number,
  ): Promise<VideoOut> =>
    api.post("/footage/confirm", { video_id, object_key, file_size_bytes }),

  myVideos: (): Promise<VideoOut[]> => api.get("/footage/my"),

  stream: (id: string): Promise<{ hls_url: string }> =>
    api.get(`/footage/${id}/stream`),
};

// ─── Admin ───────────────────────────────────────────────────────────────────

export const adminApi = {
  metrics: (): Promise<unknown> => api.get("/admin/metrics"),
  users: (page = 1): Promise<User[]> => api.get(`/admin/users?page=${page}`),
};

// ─── Coaches ─────────────────────────────────────────────────────────────────

export const coachApi = {
  list: (): Promise<User[]> => api.get("/coaches"),
};

// ─── Direct S3 upload with progress ──────────────────────────────────────────

export function uploadToS3WithProgress(
  url: string,
  file: File,
  onProgress: (pct: number) => void,
): Promise<void> {
  return new Promise((resolve, reject) => {
    const xhr = new XMLHttpRequest();
    xhr.open("PUT", url, true);
    xhr.setRequestHeader("Content-Type", file.type);

    xhr.upload.addEventListener("progress", (e) => {
      if (e.lengthComputable) {
        onProgress(Math.round((e.loaded / e.total) * 100));
      }
    });

    xhr.addEventListener("load", () => {
      if (xhr.status >= 200 && xhr.status < 300) resolve();
      else reject(new Error(`S3 upload failed: ${xhr.status}`));
    });

    xhr.addEventListener("error", () => reject(new Error("Network error during upload")));
    xhr.send(file);
  });
}
