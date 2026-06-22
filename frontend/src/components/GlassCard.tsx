"use client";

import { ReactNode } from "react";

interface GlassCardProps {
  children: ReactNode;
  className?: string;
  hover?: boolean;
  padding?: string;
  onClick?: () => void;
}

export function GlassCard({
  children,
  className = "",
  hover = false,
  padding = "p-5",
  onClick,
}: GlassCardProps) {
  return (
    <div
      className={`${hover ? "glass-card-hover" : "glass-card"} ${padding} ${className}`}
      onClick={onClick}
      role={onClick ? "button" : undefined}
      tabIndex={onClick ? 0 : undefined}
    >
      {children}
    </div>
  );
}
