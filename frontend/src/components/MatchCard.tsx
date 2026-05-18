// frontend/src/components/MatchCard.tsx
import React from "react";
import Link from "next/link";
import { format, parseISO } from "date-fns";
import { Clock, ChevronRight } from "lucide-react";
import clsx from "clsx";
import { type Match } from "@/lib/api";
import { Card } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";

interface MatchCardProps {
  match: Match;
  className?: string;
}

const STATUS_VARIANTS = {
  scheduled: { variant: "info" as const, label: "Upcoming" },
  live:      { variant: "success" as const, label: "LIVE" },
  finished:  { variant: "default" as const, label: "FT" },
  postponed: { variant: "warning" as const, label: "PPD" },
  cancelled: { variant: "danger" as const, label: "CXL" },
};

function formatMatchTime(dateStr: string): string {
  try {
    return format(parseISO(dateStr), "HH:mm");
  } catch {
    return dateStr;
  }
}

function formatMatchDate(dateStr: string): string {
  try {
    return format(parseISO(dateStr), "EEE d MMM");
  } catch {
    return "";
  }
}

export function MatchCard({ match, className }: MatchCardProps) {
  const statusInfo = STATUS_VARIANTS[match.status] ?? STATUS_VARIANTS.scheduled;

  const isLive = match.status === "live";
  const isFinished = match.status === "finished";
  const showScore = isLive || isFinished;

  return (
    <Link href={`/matches/${match.id}`}>
      <Card
        className={clsx(
          "p-4 hover:border-blue-500/40 transition-all duration-200 group",
          isLive && "border-green-500/30",
          className
        )}
      >
        <div className="flex items-start justify-between mb-3">
          <div className="flex items-center gap-2">
            <span className="text-xs text-slate-400 font-medium">
              🏆 {match.league.name}
            </span>
          </div>
          <div className="flex items-center gap-2">
            {isLive ? (
              <div className="flex items-center gap-1.5">
                <span className="w-2 h-2 rounded-full bg-green-400 animate-pulse" />
                <span className="text-xs text-green-400 font-semibold">
                  {match.minute ? `${match.minute}'` : "LIVE"}
                </span>
              </div>
            ) : (
              <Badge variant={statusInfo.variant}>{statusInfo.label}</Badge>
            )}
          </div>
        </div>

        {/* Teams and score */}
        <div className="flex items-center justify-between">
          <div className="flex-1">
            {/* Home team */}
            <div className="flex items-center justify-between mb-2">
              <span className="text-sm font-semibold text-white">
                {match.home_team.name}
              </span>
              {showScore && (
                <span
                  className={clsx(
                    "text-lg font-bold ml-4",
                    isLive ? "text-green-400" : "text-white"
                  )}
                >
                  {match.home_score ?? 0}
                </span>
              )}
            </div>
            {/* Away team */}
            <div className="flex items-center justify-between">
              <span className="text-sm font-semibold text-white">
                {match.away_team.name}
              </span>
              {showScore && (
                <span
                  className={clsx(
                    "text-lg font-bold ml-4",
                    isLive ? "text-green-400" : "text-white"
                  )}
                >
                  {match.away_score ?? 0}
                </span>
              )}
            </div>
          </div>

          {!showScore && (
            <div className="ml-4 text-right">
              <div className="flex items-center gap-1 text-slate-400">
                <Clock className="w-3.5 h-3.5" />
                <span className="text-sm font-medium">
                  {formatMatchTime(match.match_date)}
                </span>
              </div>
              <p className="text-xs text-slate-500 mt-0.5">
                {formatMatchDate(match.match_date)}
              </p>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="mt-3 pt-3 border-t border-slate-700 flex items-center justify-between">
          <span className="text-xs text-slate-500">
            {match.league.country}
          </span>
          <span className="text-xs text-blue-400 flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
            View Analysis <ChevronRight className="w-3 h-3" />
          </span>
        </div>
      </Card>
    </Link>
  );
}
