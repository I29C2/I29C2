// frontend/src/app/admin/page.tsx
"use client";

import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import {
  Users,
  BarChart2,
  Activity,
  Shield,
  CheckCircle,
  XCircle,
  TrendingUp,
  AlertTriangle,
  RefreshCw,
  Server,
} from "lucide-react";
import { format } from "date-fns";
import {
  getAdminStats,
  getAdminUsers,
  updateUserPremium,
  getAdminPredictions,
  publishPrediction,
  rejectPrediction,
  type User,
  type Prediction,
} from "@/lib/api";
import { Card } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { StatsChart } from "@/components/StatsChart";
import { IntegrityBadge } from "@/components/IntegrityBadge";

// ─── Stat tiles ───────────────────────────────────────────────────────────────

interface StatTileProps {
  label: string;
  value: string | number;
  icon: React.ReactNode;
  sub?: string;
  color?: string;
}

function StatTile({ label, value, icon, sub, color = "text-white" }: StatTileProps) {
  return (
    <Card className="p-5">
      <div className="flex items-start justify-between">
        <div>
          <p className="text-xs text-slate-400 font-medium uppercase tracking-wide mb-1">
            {label}
          </p>
          <p className={`text-2xl font-bold ${color}`}>{value}</p>
          {sub && <p className="text-xs text-slate-500 mt-1">{sub}</p>}
        </div>
        <div className="w-10 h-10 rounded-xl bg-slate-700/50 flex items-center justify-center shrink-0">
          {icon}
        </div>
      </div>
    </Card>
  );
}

// ─── Users table ─────────────────────────────────────────────────────────────

function UserRow({ user }: { user: User }) {
  const queryClient = useQueryClient();
  const { mutate: togglePremium, isPending } = useMutation({
    mutationFn: () => updateUserPremium(user.id, !user.is_premium),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["admin-users"] }),
  });

  return (
    <tr className="border-t border-slate-700 hover:bg-slate-800/40 transition-colors">
      <td className="px-4 py-3">
        <div>
          <p className="text-sm font-medium text-white">{user.username}</p>
          <p className="text-xs text-slate-400">{user.email}</p>
        </div>
      </td>
      <td className="px-4 py-3">
        {user.is_premium ? (
          <Badge variant="warning">Premium</Badge>
        ) : (
          <Badge variant="default">Free</Badge>
        )}
      </td>
      <td className="px-4 py-3">
        {user.is_admin ? (
          <Badge variant="danger">Admin</Badge>
        ) : (
          <Badge variant="default">User</Badge>
        )}
      </td>
      <td className="px-4 py-3 text-xs text-slate-400">
        {user.created_at ? format(new Date(user.created_at), "d MMM yyyy") : "—"}
      </td>
      <td className="px-4 py-3">
        <Button
          variant={user.is_premium ? "danger" : "primary"}
          onClick={() => togglePremium()}
          disabled={isPending}
          className="text-xs py-1 px-3"
        >
          {isPending ? "..." : user.is_premium ? "Revoke Premium" : "Grant Premium"}
        </Button>
      </td>
    </tr>
  );
}

// ─── Prediction row ───────────────────────────────────────────────────────────

function PredictionRow({ pred }: { pred: Prediction }) {
  const queryClient = useQueryClient();
  const { mutate: publish, isPending: publishing } = useMutation({
    mutationFn: () => publishPrediction(pred.id),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["admin-predictions"] }),
  });
  const { mutate: reject, isPending: rejecting } = useMutation({
    mutationFn: () => rejectPrediction(pred.id),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["admin-predictions"] }),
  });

  return (
    <tr className="border-t border-slate-700 hover:bg-slate-800/40 transition-colors">
      <td className="px-4 py-3 text-sm text-white">
        <div>
          <p className="font-medium">
            {pred.match.home_team.name} vs {pred.match.away_team.name}
          </p>
          <p className="text-xs text-slate-400">{pred.match.league.name}</p>
        </div>
      </td>
      <td className="px-4 py-3">
        <span className="text-xs bg-slate-700 text-slate-200 px-2 py-0.5 rounded font-mono">
          {pred.market}
        </span>
      </td>
      <td className="px-4 py-3 text-sm text-white">{pred.predicted_outcome}</td>
      <td className="px-4 py-3 text-sm">
        <span
          className={
            pred.edge >= 0 ? "text-green-400 font-semibold" : "text-red-400"
          }
        >
          {pred.edge >= 0 ? "+" : ""}
          {pred.edge.toFixed(1)}%
        </span>
      </td>
      <td className="px-4 py-3">
        <IntegrityBadge score={pred.integrity_score} compact />
      </td>
      <td className="px-4 py-3">
        {pred.is_published ? (
          <Badge variant="success">Published</Badge>
        ) : (
          <div className="flex gap-2">
            <Button
              variant="primary"
              onClick={() => publish()}
              disabled={publishing || rejecting}
              className="text-xs py-1 px-2 flex items-center gap-1"
            >
              <CheckCircle className="w-3 h-3" />
              {publishing ? "..." : "Publish"}
            </Button>
            <Button
              variant="danger"
              onClick={() => reject()}
              disabled={publishing || rejecting}
              className="text-xs py-1 px-2 flex items-center gap-1"
            >
              <XCircle className="w-3 h-3" />
              {rejecting ? "..." : "Reject"}
            </Button>
          </div>
        )}
      </td>
    </tr>
  );
}

// ─── Mock chart data ──────────────────────────────────────────────────────────

const MOCK_PERF_DATA = [
  { name: "Mon", accuracy: 62, roi: 3.1 },
  { name: "Tue", accuracy: 58, roi: -1.2 },
  { name: "Wed", accuracy: 71, roi: 8.4 },
  { name: "Thu", accuracy: 65, roi: 4.7 },
  { name: "Fri", accuracy: 69, roi: 6.2 },
  { name: "Sat", accuracy: 74, roi: 11.3 },
  { name: "Sun", accuracy: 68, roi: 5.9 },
];

const MOCK_ROI_DATA = [
  { name: "W1", value: 2.1 },
  { name: "W2", value: 5.8 },
  { name: "W3", value: 3.2 },
  { name: "W4", value: 8.7 },
  { name: "W5", value: 6.4 },
  { name: "W6", value: 11.2 },
  { name: "W7", value: 9.5 },
];

const MOCK_JOB_STATUS = [
  { name: "Data Ingestion", status: "running", last_run: "2 min ago" },
  { name: "Prediction Worker", status: "running", last_run: "5 min ago" },
  { name: "Integrity Scanner", status: "running", last_run: "8 min ago" },
  { name: "Alert Dispatcher", status: "idle", last_run: "1 hr ago" },
  { name: "Model Retrainer", status: "scheduled", last_run: "Yesterday 03:00" },
];

const MOCK_LOGS = [
  { ts: "10:42:31", level: "INFO", msg: "Generated 24 predictions for today" },
  { ts: "10:40:15", level: "INFO", msg: "Odds refresh completed — 312 markets updated" },
  { ts: "10:38:02", level: "WARN", msg: "High integrity risk detected: Fortuna Sittard vs AZ Alkmaar" },
  { ts: "10:35:44", level: "INFO", msg: "Telegram alerts dispatched: 8 value bets" },
  { ts: "10:30:00", level: "INFO", msg: "Scheduled jobs: all healthy" },
];

// ─── Page ─────────────────────────────────────────────────────────────────────

export default function AdminPage() {
  const [tab, setTab] = useState<"overview" | "users" | "predictions" | "jobs">(
    "overview"
  );
  const [userPage, setUserPage] = useState(1);
  const [predPage, setPredPage] = useState(1);

  const { data: stats, isLoading: statsLoading, refetch: refetchStats } = useQuery({
    queryKey: ["admin-stats"],
    queryFn: getAdminStats,
  });

  const { data: usersData, isLoading: usersLoading } = useQuery({
    queryKey: ["admin-users", userPage],
    queryFn: () => getAdminUsers(userPage, 20),
    enabled: tab === "users",
  });

  const { data: predsData, isLoading: predsLoading } = useQuery({
    queryKey: ["admin-predictions", predPage],
    queryFn: () => getAdminPredictions(predPage, 20),
    enabled: tab === "predictions",
  });

  const TABS = [
    { key: "overview", label: "Overview", icon: <BarChart2 className="w-4 h-4" /> },
    { key: "users", label: "Users", icon: <Users className="w-4 h-4" /> },
    { key: "predictions", label: "Predictions", icon: <Activity className="w-4 h-4" /> },
    { key: "jobs", label: "Jobs & Logs", icon: <Server className="w-4 h-4" /> },
  ] as const;

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 animate-fade-in">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-white flex items-center gap-2">
            <Shield className="w-6 h-6 text-blue-400" />
            Admin Dashboard
          </h1>
          <p className="text-slate-400 text-sm mt-0.5">
            Platform management and monitoring
          </p>
        </div>
        <Button
          variant="ghost"
          onClick={() => refetchStats()}
          className="flex items-center gap-2"
        >
          <RefreshCw className="w-4 h-4" />
          Refresh
        </Button>
      </div>

      {/* Tab nav */}
      <div className="flex gap-1 bg-slate-800 rounded-xl p-1 mb-6 w-fit">
        {TABS.map((t) => (
          <button
            key={t.key}
            onClick={() => setTab(t.key)}
            className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-all ${
              tab === t.key
                ? "bg-blue-600 text-white shadow"
                : "text-slate-400 hover:text-white"
            }`}
          >
            {t.icon}
            {t.label}
          </button>
        ))}
      </div>

      {/* ── Overview ──────────────────────────────────────────────────────────── */}
      {tab === "overview" && (
        <div className="space-y-6 animate-slide-up">
          {/* Stats grid */}
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
            <StatTile
              label="Total Users"
              value={statsLoading ? "..." : (stats?.total_users ?? 0)}
              icon={<Users className="w-5 h-5 text-blue-400" />}
              sub={`${stats?.premium_users ?? 0} premium`}
              color="text-blue-400"
            />
            <StatTile
              label="Picks Today"
              value={statsLoading ? "..." : (stats?.picks_today ?? 0)}
              icon={<Activity className="w-5 h-5 text-green-400" />}
              sub={`${stats?.value_bets_today ?? 0} value bets`}
              color="text-green-400"
            />
            <StatTile
              label="Model Accuracy"
              value={
                statsLoading
                  ? "..."
                  : `${((stats?.model_accuracy ?? 0) * 100).toFixed(1)}%`
              }
              icon={<TrendingUp className="w-5 h-5 text-amber-400" />}
              sub="Last 30 days"
              color="text-amber-400"
            />
            <StatTile
              label="ROI"
              value={
                statsLoading
                  ? "..."
                  : `+${(stats?.model_roi ?? 0).toFixed(1)}%`
              }
              icon={<BarChart2 className="w-5 h-5 text-purple-400" />}
              sub="Last 30 days"
              color="text-purple-400"
            />
          </div>

          {/* Model metrics */}
          <div className="grid md:grid-cols-2 gap-4">
            <StatTile
              label="Brier Score"
              value={statsLoading ? "..." : (stats?.brier_score ?? 0).toFixed(4)}
              icon={<Shield className="w-5 h-5 text-cyan-400" />}
              sub="Lower is better (0 = perfect)"
              color="text-cyan-400"
            />
            <StatTile
              label="Log Loss"
              value={statsLoading ? "..." : (stats?.log_loss ?? 0).toFixed(4)}
              icon={<AlertTriangle className="w-5 h-5 text-red-400" />}
              sub="Lower is better"
              color="text-red-400"
            />
          </div>

          {/* Charts */}
          <div className="grid md:grid-cols-2 gap-5">
            <StatsChart
              data={MOCK_PERF_DATA}
              type="bar"
              title="Daily Accuracy (7 days)"
              dataKey="accuracy"
            />
            <StatsChart
              data={MOCK_ROI_DATA}
              type="line"
              title="Weekly ROI Trend"
              dataKey="value"
            />
          </div>
        </div>
      )}

      {/* ── Users ─────────────────────────────────────────────────────────────── */}
      {tab === "users" && (
        <div className="animate-slide-up">
          <Card className="overflow-hidden">
            <div className="px-4 py-3 border-b border-slate-700 flex items-center justify-between">
              <h2 className="font-semibold text-white">
                User Management{" "}
                {usersData && (
                  <span className="text-slate-400 font-normal text-sm">
                    ({usersData.total} total)
                  </span>
                )}
              </h2>
            </div>
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="text-xs text-slate-400 uppercase tracking-wide border-b border-slate-700">
                    <th className="px-4 py-3 text-left">User</th>
                    <th className="px-4 py-3 text-left">Plan</th>
                    <th className="px-4 py-3 text-left">Role</th>
                    <th className="px-4 py-3 text-left">Joined</th>
                    <th className="px-4 py-3 text-left">Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {usersLoading ? (
                    <tr>
                      <td colSpan={5} className="px-4 py-8 text-center text-slate-400">
                        Loading users...
                      </td>
                    </tr>
                  ) : usersData?.items.length === 0 ? (
                    <tr>
                      <td colSpan={5} className="px-4 py-8 text-center text-slate-400">
                        No users found.
                      </td>
                    </tr>
                  ) : (
                    usersData?.items.map((user) => (
                      <UserRow key={user.id} user={user} />
                    ))
                  )}
                </tbody>
              </table>
            </div>
            {usersData && usersData.pages > 1 && (
              <div className="px-4 py-3 border-t border-slate-700 flex items-center justify-between text-sm text-slate-400">
                <span>
                  Page {userPage} of {usersData.pages}
                </span>
                <div className="flex gap-2">
                  <Button
                    variant="ghost"
                    onClick={() => setUserPage((p) => Math.max(1, p - 1))}
                    disabled={userPage === 1}
                    className="text-xs"
                  >
                    Previous
                  </Button>
                  <Button
                    variant="ghost"
                    onClick={() =>
                      setUserPage((p) => Math.min(usersData.pages, p + 1))
                    }
                    disabled={userPage === usersData.pages}
                    className="text-xs"
                  >
                    Next
                  </Button>
                </div>
              </div>
            )}
          </Card>
        </div>
      )}

      {/* ── Predictions ───────────────────────────────────────────────────────── */}
      {tab === "predictions" && (
        <div className="animate-slide-up">
          <Card className="overflow-hidden">
            <div className="px-4 py-3 border-b border-slate-700">
              <h2 className="font-semibold text-white">
                Active Predictions{" "}
                {predsData && (
                  <span className="text-slate-400 font-normal text-sm">
                    ({predsData.total} total)
                  </span>
                )}
              </h2>
            </div>
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="text-xs text-slate-400 uppercase tracking-wide border-b border-slate-700">
                    <th className="px-4 py-3 text-left">Match</th>
                    <th className="px-4 py-3 text-left">Market</th>
                    <th className="px-4 py-3 text-left">Prediction</th>
                    <th className="px-4 py-3 text-left">Edge</th>
                    <th className="px-4 py-3 text-left">Integrity</th>
                    <th className="px-4 py-3 text-left">Status</th>
                  </tr>
                </thead>
                <tbody>
                  {predsLoading ? (
                    <tr>
                      <td colSpan={6} className="px-4 py-8 text-center text-slate-400">
                        Loading predictions...
                      </td>
                    </tr>
                  ) : predsData?.items.length === 0 ? (
                    <tr>
                      <td colSpan={6} className="px-4 py-8 text-center text-slate-400">
                        No predictions found.
                      </td>
                    </tr>
                  ) : (
                    predsData?.items.map((pred) => (
                      <PredictionRow key={pred.id} pred={pred} />
                    ))
                  )}
                </tbody>
              </table>
            </div>
            {predsData && predsData.pages > 1 && (
              <div className="px-4 py-3 border-t border-slate-700 flex items-center justify-between text-sm text-slate-400">
                <span>
                  Page {predPage} of {predsData.pages}
                </span>
                <div className="flex gap-2">
                  <Button
                    variant="ghost"
                    onClick={() => setPredPage((p) => Math.max(1, p - 1))}
                    disabled={predPage === 1}
                    className="text-xs"
                  >
                    Previous
                  </Button>
                  <Button
                    variant="ghost"
                    onClick={() =>
                      setPredPage((p) => Math.min(predsData.pages, p + 1))
                    }
                    disabled={predPage === predsData.pages}
                    className="text-xs"
                  >
                    Next
                  </Button>
                </div>
              </div>
            )}
          </Card>
        </div>
      )}

      {/* ── Jobs & Logs ───────────────────────────────────────────────────────── */}
      {tab === "jobs" && (
        <div className="grid md:grid-cols-2 gap-5 animate-slide-up">
          {/* Worker status */}
          <Card className="overflow-hidden">
            <div className="px-4 py-3 border-b border-slate-700">
              <h2 className="font-semibold text-white flex items-center gap-2">
                <Server className="w-4 h-4 text-blue-400" />
                Worker Status
              </h2>
            </div>
            <div className="divide-y divide-slate-700">
              {MOCK_JOB_STATUS.map((job) => (
                <div
                  key={job.name}
                  className="px-4 py-3 flex items-center justify-between"
                >
                  <div>
                    <p className="text-sm font-medium text-white">{job.name}</p>
                    <p className="text-xs text-slate-500">Last: {job.last_run}</p>
                  </div>
                  <Badge
                    variant={
                      job.status === "running"
                        ? "success"
                        : job.status === "scheduled"
                        ? "info"
                        : "default"
                    }
                  >
                    {job.status}
                  </Badge>
                </div>
              ))}
            </div>
          </Card>

          {/* Recent logs */}
          <Card className="overflow-hidden">
            <div className="px-4 py-3 border-b border-slate-700">
              <h2 className="font-semibold text-white flex items-center gap-2">
                <Activity className="w-4 h-4 text-green-400" />
                Recent System Logs
              </h2>
            </div>
            <div className="divide-y divide-slate-700">
              {MOCK_LOGS.map((log, i) => (
                <div key={i} className="px-4 py-3 flex items-start gap-3 font-mono text-xs">
                  <span className="text-slate-500 shrink-0">{log.ts}</span>
                  <span
                    className={`font-semibold shrink-0 ${
                      log.level === "WARN"
                        ? "text-amber-400"
                        : log.level === "ERROR"
                        ? "text-red-400"
                        : "text-green-400"
                    }`}
                  >
                    {log.level}
                  </span>
                  <span className="text-slate-300">{log.msg}</span>
                </div>
              ))}
            </div>
          </Card>
        </div>
      )}
    </div>
  );
}
