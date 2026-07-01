"use client";

import { useEffect, useRef, useState } from "react";
import { LucideIcon } from "lucide-react";

interface StatsCardProps {
  label: string;
  value: number;
  icon: LucideIcon;
  color: string;
  suffix?: string;
  delay?: number;
}

export function StatsCard({
  label,
  value,
  icon: Icon,
  color,
  suffix = "",
  delay = 0,
}: StatsCardProps) {
  const [displayed, setDisplayed] = useState(0);
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    let active = true;
    const timeout = setTimeout(() => {
      const duration = 1200;
      const start = performance.now();

      const tick = (now: number) => {
        if (!active) return;
        const elapsed = now - start;
        const progress = Math.min(elapsed / duration, 1);
        const eased = 1 - Math.pow(1 - progress, 3);
        setDisplayed(Math.round(eased * value));
        if (progress < 1) requestAnimationFrame(tick);
      };

      requestAnimationFrame(tick);
    }, delay);

    return () => {
      active = false;
      clearTimeout(timeout);
    };
  }, [value, delay]);

  return (
    <div
      ref={ref}
      className="glass-card p-4 flex items-center gap-4 animate-fade-in-up"
      style={{ animationDelay: `${delay}ms` }}
    >
      <div
        className="w-10 h-10 rounded-xl flex items-center justify-center flex-shrink-0"
        style={{ background: `${color}20`, color }}
      >
        <Icon size={20} />
      </div>
      <div>
        <div className="text-2xl font-bold" style={{ color: "var(--text-primary)" }}>
          {displayed.toLocaleString()}
          {suffix}
        </div>
        <div className="text-xs" style={{ color: "var(--text-secondary)" }}>
          {label}
        </div>
      </div>
    </div>
  );
}
