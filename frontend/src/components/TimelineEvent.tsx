"use client";

import { ExternalLink } from "lucide-react";
import { TimelineEvent as TimelineEventType } from "@/lib/api";
import { GlassCard } from "@/components/GlassCard";

const eventTypeColors: Record<string, { bg: string; dot: string }> = {
  issue: {
    bg: "hsla(25, 95%, 55%, 0.1)",
    dot: "var(--accent-orange)",
  },
  pr: {
    bg: "hsla(152, 69%, 50%, 0.1)",
    dot: "var(--accent-green)",
  },
  discussion: {
    bg: "hsla(190, 80%, 55%, 0.1)",
    dot: "var(--accent-cyan)",
  },
  decision: {
    bg: "hsla(45, 93%, 55%, 0.1)",
    dot: "var(--accent-yellow)",
  },
  feature: {
    bg: "hsla(217, 91%, 60%, 0.1)",
    dot: "var(--accent-blue)",
  },
  default: {
    bg: "hsla(225, 10%, 55%, 0.1)",
    dot: "var(--text-secondary)",
  },
};

interface TimelineEventProps {
  event: TimelineEventType;
  index?: number;
}

/**
 * TimelineEvent — A single event in the project evolution timeline.
 * Shows date, type badge, title, description, and optional source link.
 */
export function TimelineEventCard({ event, index = 0 }: TimelineEventProps) {
  const colors =
    eventTypeColors[event.event_type.toLowerCase()] || eventTypeColors.default;

  return (
    <div
      className="relative animate-fade-in-up"
      style={{ animationDelay: `${index * 75}ms` }}
    >
      {/* Dot */}
      <div
        className="absolute -left-5 top-1.5 w-3 h-3 rounded-full ring-4"
        style={{
          background: colors.dot,
          boxShadow: "0 0 0 4px var(--bg-primary)",
        }}
      />

      <GlassCard padding="p-4" hover>
        <div className="flex items-center gap-2 mb-1">
          <span
            className="text-xs font-mono"
            style={{ color: "var(--text-tertiary)" }}
          >
            {event.date}
          </span>
          <span
            className="badge text-xs capitalize"
            style={{
              background: colors.bg,
              color: colors.dot,
            }}
          >
            {event.event_type}
          </span>
        </div>
        <h3
          className="text-sm font-semibold mb-1"
          style={{ color: "var(--text-primary)" }}
        >
          {event.title}
        </h3>
        <p
          className="text-xs leading-relaxed"
          style={{ color: "var(--text-secondary)" }}
        >
          {event.description}
        </p>
        {event.source_url && (
          <a
            href={event.source_url}
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center gap-1 text-xs mt-2"
            style={{ color: "var(--accent-blue)" }}
          >
            View Source <ExternalLink size={10} />
          </a>
        )}
      </GlassCard>
    </div>
  );
}
