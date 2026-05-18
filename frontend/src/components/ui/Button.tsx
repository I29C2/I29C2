// frontend/src/components/ui/Button.tsx
import React from "react";
import clsx from "clsx";

export type ButtonVariant = "primary" | "secondary" | "ghost" | "danger";

interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: ButtonVariant;
  children: React.ReactNode;
  className?: string;
}

const VARIANT_CLASSES: Record<ButtonVariant, string> = {
  primary:
    "bg-blue-600 hover:bg-blue-500 text-white border-transparent disabled:opacity-50",
  secondary:
    "bg-slate-700 hover:bg-slate-600 text-white border-slate-600 disabled:opacity-50",
  ghost:
    "bg-transparent hover:bg-slate-800 text-slate-300 hover:text-white border-slate-700 disabled:opacity-50",
  danger:
    "bg-red-600/20 hover:bg-red-600/30 text-red-400 border-red-500/30 disabled:opacity-50",
};

export function Button({
  variant = "primary",
  children,
  className,
  disabled,
  ...props
}: ButtonProps) {
  return (
    <button
      disabled={disabled}
      className={clsx(
        "inline-flex items-center justify-center px-4 py-2 rounded-lg text-sm font-medium border transition-all duration-200 focus:outline-none focus:ring-2 focus:ring-blue-500/40",
        VARIANT_CLASSES[variant],
        disabled && "cursor-not-allowed",
        className
      )}
      {...props}
    >
      {children}
    </button>
  );
}
