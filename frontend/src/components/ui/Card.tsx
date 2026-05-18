// frontend/src/components/ui/Card.tsx
import React from "react";
import clsx from "clsx";

interface CardProps {
  children: React.ReactNode;
  className?: string;
  onClick?: () => void;
}

export function Card({ children, className, onClick }: CardProps) {
  return (
    <div
      className={clsx(
        "bg-slate-800 border border-slate-700 rounded-xl",
        onClick && "cursor-pointer hover:border-slate-500 transition-colors",
        className
      )}
      onClick={onClick}
    >
      {children}
    </div>
  );
}
