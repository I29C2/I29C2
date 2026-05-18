// frontend/src/components/ui/Badge.tsx
import React from "react";
import clsx from "clsx";

export type BadgeVariant = "default" | "success" | "warning" | "danger" | "info";

interface BadgeProps {
  children: React.ReactNode;
  variant?: BadgeVariant;
  className?: string;
}

const VARIANT_CLASSES: Record<BadgeVariant, string> = {
  default: "bg-slate-700 text-slate-300 border-slate-600",
  success: "bg-green-500/20 text-green-400 border-green-500/30",
  warning: "bg-amber-500/20 text-amber-400 border-amber-500/30",
  danger:  "bg-red-500/20 text-red-400 border-red-500/30",
  info:    "bg-blue-500/20 text-blue-400 border-blue-500/30",
};

export function Badge({
  children,
  variant = "default",
  className,
}: BadgeProps) {
  return (
    <span
      className={clsx(
        "inline-flex items-center px-2 py-0.5 rounded-full text-xs font-semibold border",
        VARIANT_CLASSES[variant],
        className
      )}
    >
      {children}
    </span>
  );
}
