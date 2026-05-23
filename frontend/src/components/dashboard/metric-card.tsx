import { TrendingUp, TrendingDown, Minus } from "lucide-react";
import { Card, CardContent } from "@/components/ui/card";
import { cn, formatCurrency } from "@/lib/utils";

interface MetricCardProps {
  title: string;
  value: number;
  previousValue?: number;
  currency?: string;
  icon: React.ElementType;
  iconColor?: string;
  iconBg?: string;
  format?: "currency" | "number" | "count";
  suffix?: string;
  description?: string;
}

export function MetricCard({
  title,
  value,
  previousValue,
  currency = "RON",
  icon: Icon,
  iconColor = "text-indigo-600",
  iconBg = "bg-indigo-50",
  format = "currency",
  suffix,
  description,
}: MetricCardProps) {
  const percentChange =
    previousValue !== undefined && previousValue !== 0
      ? Math.round(((value - previousValue) / previousValue) * 100)
      : null;

  const isPositive = percentChange !== null && percentChange > 0;
  const isNegative = percentChange !== null && percentChange < 0;
  const isNeutral = percentChange === 0;

  function formatValue(v: number): string {
    if (format === "currency") return formatCurrency(v, currency);
    if (format === "count") return v.toLocaleString("ro-RO");
    return v.toLocaleString("ro-RO") + (suffix ? ` ${suffix}` : "");
  }

  return (
    <Card className="border-zinc-100 shadow-sm">
      <CardContent className="p-5">
        <div className="flex items-start justify-between">
          <div className="space-y-3 flex-1 min-w-0">
            <p className="text-xs font-medium uppercase tracking-wider text-zinc-500">{title}</p>
            <p className="text-2xl font-bold text-zinc-900 truncate">{formatValue(value)}</p>

            {description && (
              <p className="text-xs text-zinc-500">{description}</p>
            )}

            {percentChange !== null && (
              <div className="flex items-center gap-1.5">
                <span
                  className={cn(
                    "flex items-center gap-0.5 text-xs font-semibold",
                    isPositive && "text-emerald-600",
                    isNegative && "text-red-500",
                    isNeutral && "text-zinc-400"
                  )}
                >
                  {isPositive && <TrendingUp className="h-3 w-3" />}
                  {isNegative && <TrendingDown className="h-3 w-3" />}
                  {isNeutral && <Minus className="h-3 w-3" />}
                  {isPositive && "+"}
                  {percentChange}%
                </span>
                <span className="text-xs text-zinc-400">vs last month</span>
              </div>
            )}
          </div>

          <div className={cn("flex h-10 w-10 shrink-0 items-center justify-center rounded-lg", iconBg)}>
            <Icon className={cn("h-5 w-5", iconColor)} />
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
