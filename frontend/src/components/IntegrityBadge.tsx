// frontend/src/components/IntegrityBadge.tsx
"use client";

import React, { useState } from "react";
import clsx from "clsx";
import { Shield, AlertTriangle, Info } from "lucide-react";
import { type IntegrityScore } from "@/lib/api";

interface IntegrityBadgeProps {
  score: IntegrityScore;
  compact?: boolean;
  className?: string;
}

const RISK_CONFIG = {
  low: {
    bg: "bg-green-500/20",
    border: "border-green-500/30",
    text: "text-green-400",
    icon: <Shield className="w-3 h-3" />,
    label: "Low Risk",
    tooltip: "bg-green-900/90 border-green-500/30",
  },
  medium: {
    bg: "bg-amber-500/20",
    border: "border-amber-500/30",
    text: "text-amber-400",
    icon: <AlertTriangle className="w-3 h-3" />,
    label: "Medium Risk",
    tooltip: "bg-amber-900/90 border-amber-500/30",
  },
  high: {
    bg: "bg-orange-500/20",
    border: "border-orange-500/30",
    text: "text-orange-400",
    icon: <AlertTriangle className="w-3 h-3" />,
    label: "High Risk",
    tooltip: "bg-orange-900/90 border-orange-500/30",
  },
  critical: {
    bg: "bg-red-500/20",
    border: "border-red-500/30",
    text: "text-red-400",
    icon: <AlertTriangle className="w-3 h-3" />,
    label: "Critical",
    tooltip: "bg-red-900/90 border-red-500/30",
  },
} as const;

export function IntegrityBadge({
  score,
  compact = false,
  className,
}: IntegrityBadgeProps) {
  const [showTooltip, setShowTooltip] = useState(false);
  const riskLevel = (score.risk_level ?? "low") as keyof typeof RISK_CONFIG;
  const config = RISK_CONFIG[riskLevel] ?? RISK_CONFIG.low;

  if (compact) {
    return (
      <span
        className={clsx(
          "inline-flex items-center gap-1 text-xs font-semibold px-2 py-0.5 rounded-full border",
          config.bg,
          config.border,
          config.text,
          className
        )}
      >
        {config.icon}
        {config.label}
      </span>
    );
  }

  return (
    <div className={clsx("relative inline-block", className)}>
      <button
        type="button"
        onMouseEnter={() => setShowTooltip(true)}
        onMouseLeave={() => setShowTooltip(false)}
        onFocus={() => setShowTooltip(true)}
        onBlur={() => setShowTooltip(false)}
        className={clsx(
          "flex items-center gap-2 px-3 py-1.5 rounded-lg border text-sm font-medium transition-opacity hover:opacity-90 focus:outline-none focus:ring-2 focus:ring-blue-500/40",
          config.bg,
          config.border,
          config.text
        )}
      >
        {config.icon}
        <span>Integrity: {config.label}</span>
        <span className="font-mono text-xs opacity-70">
          ({score.score}/100)
        </span>
        <Info className="w-3 h-3 opacity-60" />
      </button>

      {showTooltip && (
        <div
          className={clsx(
            "absolute z-50 bottom-full left-0 mb-2 w-64 rounded-xl border p-4 shadow-xl text-sm",
            config.tooltip
          )}
          onMouseEnter={() => setShowTooltip(true)}
          onMouseLeave={() => setShowTooltip(false)}
        >
          <p className={clsx("font-semibold mb-2 flex items-center gap-1.5", config.text)}>
            {config.icon}
            Integrity Assessment
          </p>

          {score.contributing_factors.length > 0 && (
            <div className="mb-3">
              <p className="text-slate-400 text-xs font-medium mb-1">
                Contributing Factors:
              </p>
              <ul className="space-y-0.5">
                {score.contributing_factors.map((factor, i) => (
                  <li key={i} className="text-xs text-slate-300 flex items-start gap-1.5">
                    <span className="mt-0.5 shrink-0">•</span>
                    {factor}
                  </li>
                ))}
              </ul>
            </div>
          )}

          {score.recommendation && (
            <div className="pt-2 border-t border-white/10">
              <p className="text-xs text-slate-400 font-medium mb-1">
                Recommendation:
              </p>
              <p className="text-xs text-slate-200">{score.recommendation}</p>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
