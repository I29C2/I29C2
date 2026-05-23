import { AlertTriangle, Lightbulb, Info, ArrowRight } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";
import { aiInsights } from "@/lib/mock-data";
import type { AiInsight } from "@/lib/mock-data";

const insightConfig = {
  warning: {
    icon: AlertTriangle,
    iconColor: "text-amber-500",
    iconBg: "bg-amber-50",
    borderColor: "border-l-amber-400",
  },
  opportunity: {
    icon: Lightbulb,
    iconColor: "text-emerald-600",
    iconBg: "bg-emerald-50",
    borderColor: "border-l-emerald-400",
  },
  info: {
    icon: Info,
    iconColor: "text-indigo-600",
    iconBg: "bg-indigo-50",
    borderColor: "border-l-indigo-400",
  },
} satisfies Record<AiInsight["type"], { icon: React.ElementType; iconColor: string; iconBg: string; borderColor: string }>;

export function AiInsightPanel() {
  const displayInsights = aiInsights.slice(0, 3);

  return (
    <Card className="border-zinc-100 shadow-sm">
      <CardHeader className="pb-3">
        <div className="flex items-center gap-2">
          <div className="flex h-6 w-6 items-center justify-center rounded-md bg-indigo-600">
            <span className="text-[10px] font-bold text-white">AI</span>
          </div>
          <CardTitle className="text-base font-semibold text-zinc-900">AI Insights</CardTitle>
        </div>
        <p className="text-xs text-zinc-500">Powered by your financial data — updated daily</p>
      </CardHeader>
      <CardContent className="space-y-3">
        {displayInsights.map((insight) => {
          const config = insightConfig[insight.type];
          const IconComponent = config.icon;

          return (
            <div
              key={insight.id}
              className={cn(
                "rounded-lg border border-zinc-100 border-l-4 bg-zinc-50/50 p-4",
                config.borderColor
              )}
            >
              <div className="flex items-start gap-3">
                <div
                  className={cn(
                    "mt-0.5 flex h-7 w-7 shrink-0 items-center justify-center rounded-md",
                    config.iconBg
                  )}
                >
                  <IconComponent className={cn("h-4 w-4", config.iconColor)} />
                </div>
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-semibold text-zinc-900">{insight.title}</p>
                  <p className="mt-1 text-xs leading-relaxed text-zinc-500">{insight.body}</p>
                  <button className="mt-2 flex items-center gap-1 text-xs font-medium text-indigo-600 hover:text-indigo-700 transition-colors">
                    {insight.action}
                    <ArrowRight className="h-3 w-3" />
                  </button>
                </div>
              </div>
            </div>
          );
        })}
      </CardContent>
    </Card>
  );
}
