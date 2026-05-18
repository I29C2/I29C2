// frontend/src/app/dashboard/page.tsx
"use client";

import { useQuery } from "@tanstack/react-query";
import {
  TrendingUp,
  Target,
  Activity,
  Award,
  Bell,
  ChevronRight,
  RefreshCw,
  Settings,
} from "lucide-react";
import Link from "next/link";
import { format } from "date-fns";
import { getValueBets, getDashboardStats, type ValueBet } from "@/lib/api";
import { PredictionCard } from "@/components/PredictionCard";
import { Card } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";

interface StatCardProps {
  label: string;
  value: string | number;
  sub?: string;
  icon: React.ReactNode;
  color?: string;
}

function StatCard({ label, value, sub, icon, color = "text-white" }: StatCardProps) {
  return (
    <Card className="p-5">
      <div className="flex items-start justify-between">
        <div>
          <p className="text-sm text-slate-400 mb-1">{label}</p>
          <p className={`text-2xl font-bold ${color}`}>{value}</p>
          {sub && <p className="text-xs text-slate-500 mt-1">{sub}</p>}
        </div>
        <div className="w-10 h-10 rounded-lg bg-slate-700/60 flex items-center justify-center">
          {icon}
        </div>
      </div>
    </Card>
  );
}

function ActiveAlert({ pick }: { pick: ValueBet }) {
  return (
    <div className="flex items-center gap-3 p-3 bg-slate-800/60 rounded-lg border border-slate-700">
      <div className="w-2 h-2 rounded-full bg-green-400 animate-pulse shrink-0" />
      <div className="flex-1 min-w-0">
        <p className="text-sm font-medium text-white truncate">
          {pick.match.home_team.name} vs {pick.match.away_team.name}
        </p>
        <p className="text-xs text-slate-400">
          {pick.market.toUpperCase()} · Edge: +{pick.edge.toFixed(1)}%
        </p>
      </div>
      <Badge variant="success" className="shrink-0">
        +{pick.edge.toFixed(1)}%
      </Badge>
    </div>
  );
}

export default function DashboardPage() {
  const {
    data: betsData,
    isLoading: betsLoading,
    refetch,
    isFetching,
  } = useQuery({
    queryKey: ["value-bets"],
    queryFn: () => getValueBets(1, 6),
  });

  const { data: stats, isLoading: statsLoading } = useQuery({
    queryKey: ["dashboard-stats"],
    queryFn: getDashboardStats,
  });

  const valueBets = betsData?.items ?? [];
  const today = format(new Date(), "EEEE, d MMMM yyyy");

  const displayStats = stats ?? {
    active_picks: betsData?.total ?? 0,
    win_rate: 0,
    avg_edge: 0,
    current_streak: 0,
  };

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 animate-fade-in">
      {/* Header */}
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-2xl font-bold text-white">Dashboard</h1>
          <p className="text-slate-400 text-sm mt-0.5">{today}</p>
        </div>
        <div className="flex items-center gap-3">
          <Button
            variant="ghost"
            onClick={() => refetch()}
            disabled={isFetching}
            className="flex items-center gap-2"
          >
            <RefreshCw
              className={`w-4 h-4 ${isFetching ? "animate-spin" : ""}`}
            />
            Refresh
          </Button>
          <Link href="/settings">
            <Button variant="secondary" className="flex items-center gap-2">
              <Settings className="w-4 h-4" />
              Settings
            </Button>
          </Link>
        </div>
      </div>

      {/* Stats row */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
        <StatCard
          label="Active Picks"
          value={statsLoading ? "..." : displayStats.active_picks}
          sub="Today"
          icon={<Target className="w-5 h-5 text-blue-400" />}
          color="text-blue-400"
        />
        <StatCard
          label="Win Rate"
          value={
            statsLoading
              ? "..."
              : `${(displayStats.win_rate * 100).toFixed(1)}%`
          }
          sub="Last 30 days"
          icon={<Award className="w-5 h-5 text-green-400" />}
          color="text-green-400"
        />
        <StatCard
          label="Avg Edge"
          value={
            statsLoading
              ? "..."
              : `+${displayStats.avg_edge.toFixed(1)}%`
          }
          sub="Value bets"
          icon={<TrendingUp className="w-5 h-5 text-amber-400" />}
          color="text-amber-400"
        />
        <StatCard
          label="Streak"
          value={
            statsLoading ? "..." : `${displayStats.current_streak}W`
          }
          sub="Current"
          icon={<Activity className="w-5 h-5 text-purple-400" />}
          color="text-purple-400"
        />
      </div>

      <div className="grid lg:grid-cols-3 gap-6">
        {/* Value Bets — main column */}
        <div className="lg:col-span-2 space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="text-lg font-bold text-white">Today's Value Bets</h2>
            <span className="text-sm text-slate-400">
              {betsData?.total ?? 0} found
            </span>
          </div>

          {betsLoading ? (
            <div className="space-y-4">
              {[...Array(3)].map((_, i) => (
                <div
                  key={i}
                  className="h-48 rounded-xl bg-slate-800 animate-pulse"
                />
              ))}
            </div>
          ) : valueBets.length === 0 ? (
            <Card className="p-8 text-center">
              <p className="text-slate-400">
                No value bets found for today. Check back soon.
              </p>
            </Card>
          ) : (
            <div className="space-y-4">
              {valueBets.map((bet) => (
                <PredictionCard key={bet.id} prediction={bet} />
              ))}
              {(betsData?.total ?? 0) > 6 && (
                <Link href="/picks" className="block">
                  <Button variant="ghost" className="w-full flex items-center justify-center gap-2">
                    View All {betsData?.total} Picks
                    <ChevronRight className="w-4 h-4" />
                  </Button>
                </Link>
              )}
            </div>
          )}
        </div>

        {/* Right sidebar */}
        <div className="space-y-5">
          {/* Active Alerts */}
          <Card className="p-5">
            <div className="flex items-center justify-between mb-4">
              <h3 className="font-semibold text-white flex items-center gap-2">
                <Bell className="w-4 h-4 text-amber-400" />
                Active Alerts
              </h3>
              <Badge variant="warning">{valueBets.slice(0, 3).length}</Badge>
            </div>
            <div className="space-y-2">
              {valueBets.slice(0, 3).length === 0 ? (
                <p className="text-sm text-slate-400 text-center py-2">
                  No active alerts
                </p>
              ) : (
                valueBets
                  .slice(0, 3)
                  .map((bet) => <ActiveAlert key={bet.id} pick={bet} />)
              )}
            </div>
          </Card>

          {/* Quick Settings */}
          <Card className="p-5">
            <h3 className="font-semibold text-white mb-4">Quick Settings</h3>
            <div className="space-y-3 text-sm">
              <div className="flex items-center justify-between">
                <span className="text-slate-400">Edge Threshold</span>
                <span className="text-white font-medium">5%</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-slate-400">Notifications</span>
                <span className="text-green-400 font-medium">On</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-slate-400">Max Stake</span>
                <span className="text-white font-medium">3% bankroll</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-slate-400">Markets</span>
                <span className="text-white font-medium">All</span>
              </div>
              <Link href="/settings" className="block mt-2">
                <Button variant="ghost" className="w-full text-xs">
                  Edit Settings
                </Button>
              </Link>
            </div>
          </Card>

          {/* Premium upsell */}
          <div className="rounded-xl bg-gradient-to-br from-blue-900/40 to-slate-800 border border-blue-500/30 p-5 text-center">
            <p className="text-amber-400 text-sm font-semibold mb-2">
              ⭐ Premium
            </p>
            <p className="text-white font-semibold mb-2">
              Unlock All Competitions
            </p>
            <p className="text-slate-400 text-xs mb-4">
              Access all 30+ leagues and unlimited daily picks.
            </p>
            <Link href="/register">
              <Button variant="primary" className="w-full text-sm">
                Upgrade Now
              </Button>
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
}
