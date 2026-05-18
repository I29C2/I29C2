// frontend/src/lib/api.ts
import axios, { AxiosInstance, InternalAxiosRequestConfig } from "axios";

// ─── Types ────────────────────────────────────────────────────────────────────

export interface Team {
  id: string;
  name: string;
  logo_url?: string;
}

export interface League {
  id: string;
  name: string;
  country: string;
  logo_url?: string;
  current_season?: string;
  total_matches?: number;
  predictions_made?: number;
  accuracy_rate?: number;
  roi?: number;
  is_active?: boolean;
}

export interface Match {
  id: string;
  home_team: Team;
  away_team: Team;
  league: League;
  match_date: string;
  status: "scheduled" | "live" | "finished" | "postponed" | "cancelled";
  home_score?: number | null;
  away_score?: number | null;
  minute?: number | null;
}

export interface IntegrityScore {
  score: number;
  risk_level: "low" | "medium" | "high" | "critical";
  contributing_factors: string[];
  recommendation: string;
}

export interface Prediction {
  id: string;
  match: Match;
  market: string;
  predicted_outcome: string;
  probability: number;
  market_odds: number;
  fair_odds: number;
  edge: number;
  confidence: "low" | "medium" | "high" | "very_high";
  bankroll_suggestion: number;
  integrity_score: IntegrityScore;
  is_published: boolean;
  created_at: string;
}

export interface ValueBet extends Prediction {
  // Value bets are just predictions with positive edge
}

export interface User {
  id: string;
  email: string;
  username: string;
  is_premium: boolean;
  is_admin: boolean;
  telegram_id?: string;
  created_at: string;
  subscription_expires_at?: string | null;
}

export interface AuthTokens {
  access_token: string;
  token_type: string;
}

export interface AdminStats {
  total_users: number;
  premium_users: number;
  picks_today: number;
  value_bets_today: number;
  avg_edge: number;
  model_accuracy: number;
  model_roi: number;
  brier_score: number;
  log_loss: number;
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  pages: number;
  per_page: number;
}

export interface DashboardStats {
  active_picks: number;
  win_rate: number;
  avg_edge: number;
  current_streak: number;
  recent_roi: number;
}

// ─── Axios instance ───────────────────────────────────────────────────────────

const baseURL =
  process.env.NEXT_PUBLIC_API_URL || "/api/v1";

const apiClient: AxiosInstance = axios.create({
  baseURL,
  headers: {
    "Content-Type": "application/json",
  },
  timeout: 15000,
});

// Request interceptor — attach JWT if available
apiClient.interceptors.request.use(
  (config: InternalAxiosRequestConfig) => {
    if (typeof window !== "undefined") {
      const token = localStorage.getItem("betbot_token");
      if (token && config.headers) {
        config.headers.Authorization = `Bearer ${token}`;
      }
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Response interceptor — handle 401 globally
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401 && typeof window !== "undefined") {
      localStorage.removeItem("betbot_token");
      window.location.href = "/login";
    }
    return Promise.reject(error);
  }
);

// ─── Auth ─────────────────────────────────────────────────────────────────────

export async function loginUser(
  email: string,
  password: string
): Promise<AuthTokens> {
  const params = new URLSearchParams();
  params.set("username", email);
  params.set("password", password);
  const { data } = await apiClient.post<AuthTokens>("/auth/token", params, {
    headers: { "Content-Type": "application/x-www-form-urlencoded" },
  });
  return data;
}

export async function registerUser(
  email: string,
  username: string,
  password: string
): Promise<User> {
  const { data } = await apiClient.post<User>("/auth/register", {
    email,
    username,
    password,
  });
  return data;
}

// ─── Matches ──────────────────────────────────────────────────────────────────

export async function getTodaysMatches(): Promise<Match[]> {
  const { data } = await apiClient.get<Match[] | PaginatedResponse<Match>>(
    "/matches/today"
  );
  return Array.isArray(data) ? data : data.items;
}

export async function getMatch(id: string): Promise<Match> {
  const { data } = await apiClient.get<Match>(`/matches/${id}`);
  return data;
}

// ─── Predictions / Value Bets ─────────────────────────────────────────────────

export async function getValueBets(
  page = 1,
  perPage = 10
): Promise<PaginatedResponse<ValueBet>> {
  const { data } = await apiClient.get<PaginatedResponse<ValueBet>>(
    "/predictions/value-bets",
    { params: { page, per_page: perPage } }
  );
  return data;
}

export async function getPrediction(matchId: string): Promise<Prediction> {
  const { data } = await apiClient.get<Prediction>(
    `/predictions/match/${matchId}`
  );
  return data;
}

// ─── Leagues ──────────────────────────────────────────────────────────────────

export async function getLeagues(): Promise<League[]> {
  const { data } = await apiClient.get<League[] | PaginatedResponse<League>>(
    "/leagues"
  );
  return Array.isArray(data) ? data : data.items;
}

// ─── Dashboard ────────────────────────────────────────────────────────────────

export async function getDashboardStats(): Promise<DashboardStats> {
  const { data } = await apiClient.get<DashboardStats>("/users/me/stats");
  return data;
}

// ─── Admin ────────────────────────────────────────────────────────────────────

export async function getAdminStats(): Promise<AdminStats> {
  const { data } = await apiClient.get<AdminStats>("/admin/stats");
  return data;
}

export async function getAdminUsers(
  page = 1,
  perPage = 20
): Promise<PaginatedResponse<User>> {
  const { data } = await apiClient.get<PaginatedResponse<User>>(
    "/admin/users",
    { params: { page, per_page: perPage } }
  );
  return data;
}

export async function updateUserPremium(
  userId: string,
  isPremium: boolean
): Promise<User> {
  const { data } = await apiClient.patch<User>(`/admin/users/${userId}`, {
    is_premium: isPremium,
  });
  return data;
}

export async function getAdminPredictions(
  page = 1,
  perPage = 20
): Promise<PaginatedResponse<Prediction>> {
  const { data } = await apiClient.get<PaginatedResponse<Prediction>>(
    "/admin/predictions",
    { params: { page, per_page: perPage } }
  );
  return data;
}

export async function publishPrediction(id: string): Promise<Prediction> {
  const { data } = await apiClient.post<Prediction>(
    `/admin/predictions/${id}/publish`
  );
  return data;
}

export async function rejectPrediction(id: string): Promise<Prediction> {
  const { data } = await apiClient.post<Prediction>(
    `/admin/predictions/${id}/reject`
  );
  return data;
}

export default apiClient;
