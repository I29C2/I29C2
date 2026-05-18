// frontend/src/components/PredictionCard.tsx
"use client";

import React from "react";
import Link from "next/link";
import clsx from "clsx";
import { format, parseISO } from "date-fns";
import { TrendingUp, ChevronRight, Wallet } from "lucide-react";
import { type Prediction } from "@/lib/api";
import { Card } from "@/components/ui/Card";
import { Badge, type BadgeVariant } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { IntegrityBadge } from "@/components/IntegrityBadge";

interface PredictionCardProps {
  prediction: Prediction;
  className?: string;
}

const CONFIDENCE_CONFIG: Record<
  string,
  { variant: BadgeVariant; label: string; bar: string }
> = {
  very_high: {
    variant: "success",
    label: "Very High",
    bar: "bg-green-500",
  },
  high: {
    variant: "info",
    label: "High",
    bar: "bg-blue-500",
  },
  medium: {
    variant: "warning",
    label: "Medium",
    bar: "bg-amber-500",
  },
  low: {
    variant: "default",
    label: "Low",
    bar: "bg-slate-500",
  },
};

function ProbabilityBar({
  probability,
  barColor,
}: {
  probability: number;
  barColor: string;
}) {
  const pct = Math.min(100, Math.max(0, probability * 100));
  return (
    <div className="flex items-center gap-2">
      <div className="flex-1 h-1.5 bg-slate-700 rounded-full overflow-hidden">
        <div
          className={clsx("h-full rounded-full transition-all", barColor)}
          style={{ width: `${pct}%` }}
        />
      </div>
      <span className="text-xs font-bold text-white tabular-nums">
        {pct.toFixed(1)}%
      </span>
    </div>
  );
}

function formatTime(dateStr: string): string {
  try {
    return format(parseISO(dateStr), "HH:mm");
  } catch {
    return dateStr;
  }
}

export function PredictionCard({
  prediction,
  className,
}: PredictionCardProps) {
  const {
    match,
    market,
    predicted_outcome,
    probability,
    market_odds,
    fair_odds,
    edge,
    confidence,
    bankroll_suggestion,
    integrity_score,
  } = prediction;

  const confKey = confidence ?? "medium";
  const conf = CONFIDENCE_CONFIG[confKey] ?? CONFIDENCE_CONFIG.medium;
  const edgePositive = edge >= 0;

  return (
    <Card
      className={clsx(
        "p-5 flex flex-col gap-4 hover:border-blue-500/30 transition-all duration-200",
        className
      )}
    >
      {/* Match header */}
      <div className="flex items-start justify-between gap-3">
        <div className="flex-1 min-w-0">
          <p className="text-xs text-slate-400 mb-1 flex items-center gap-1.5">
            <span className="truncate">🏆 {match.league.name}</span>
            <span className="text-slate-600">·</span>
            <span className="shrink-0">{formatTime(match.match_date)}</span>
          </p>
          <h3 className="font-bold text-white text-sm leading-tight">
            {match.home_team.name}
            <span className="text-slate-500 font-normal mx-1.5">vs</span>
            {match.away_team.name}
          </h3>
        </div>
        <span className="text-xs bg-slate-700 text-slate-300 px-2 py-0.5 rounded font-mono shrink-0">
          {market.toUpperCase()}
        </span>
      </div>

      {/* Prediction */}
      <div className="flex items-center gap-3">
        <div className="w-8 h-8 rounded-lg bg-blue-600/20 flex items-center justify-center shrink-0">
          <TrendingUp className="w-4 h-4 text-blue-400" />
        </div>
        <div className="flex-1">
          <p className="text-xs text-slate-400 mb-0.5">Prediction</p>
          <p className="text-sm font-bold text-white">{predicted_outcome}</p>
        </div>
        <Badge variant={conf.variant}>{conf.label}</Badge>
      </div>

      {/* Probability bar */}
      <div>
        <p className="text-xs text-slate-400 mb-1.5">AI Probability</p>
        <ProbabilityBar probability={probability} barColor={conf.bar} />
      </div>

      {/* Stats grid */}
      <div className="grid grid-cols-3 gap-3">
        <div className="bg-slate-900/50 rounded-lg p-2.5 text-center">
          <p className="text-xs text-slate-400 mb-0.5">Market Odds</p>
          <p className="text-sm font-bold text-white">{market_odds.toFixed(2)}</p>
        </div>
        <div className="bg-slate-900/50 rounded-lg p-2.5 text-center">
          <p className="text-xs text-slate-400 mb-0.5">Fair Odds</p>
          <p className="text-sm font-bold text-slate-300">
            {fair_odds > 0 ? fair_odds.toFixed(2) : "—"}
          </p>
        </div>
        <div
          className={clsx(
            "rounded-lg p-2.5 text-center",
            edgePositive
              ? "bg-green-500/10 border border-green-500/20"
              : "bg-red-500/10 border border-red-500/20"
          )}
        >
          <p className="text-xs text-slate-400 mb-0.5">Edge</p>
          <p
            className={clsx(
              "text-sm font-bold",
              edgePositive ? "text-green-400" : "text-red-400"
            )}
          >
            {edgePositive ? "+" : ""}
            {edge.toFixed(1)}%
          </p>
        </div>
      </div>

      {/* Bankroll suggestion */}
      <div className="flex items-center gap-2 bg-slate-900/40 rounded-lg px-3 py-2">
        <Wallet className="w-3.5 h-3.5 text-amber-400 shrink-0" />
        <span className="text-xs text-slate-400">
          Suggested stake:{" "}
          <span className="text-amber-400 font-semibold">
            {bankroll_suggestion.toFixed(1)}% of bankroll
          </span>
        </span>
      </div>

      {/* Integrity badge */}
      <IntegrityBadge score={integrity_score} />

      {/* CTA */}
      <Link href={`/matches/${match.id}`} className="block">
        <Button
          variant="ghost"
          className="w-full flex items-center justify-center gap-2 text-blue-400 border-blue-500/30 hover:bg-blue-500/10"
        >
          Get Full Analysis
          <ChevronRight className="w-4 h-4" />
        </Button>
      </Link>
    </Card>
  );
}
