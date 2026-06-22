"use client";

import { GlassCard } from "@/components/GlassCard";

interface DecisionCardProps {
  summary: string;
  reasoning: string;
  outcome: string;
  alternatives: string[];
  timeline?: Record<string, unknown>[];
  className?: string;
}

/**
 * DecisionCard — Displays a decision exploration result with summary,
 * reasoning, outcome, alternatives, and optional timeline.
 */
export function DecisionCard({
  summary,
  reasoning,
  outcome,
  alternatives,
  timeline,
  className = "",
}: DecisionCardProps) {
  return (
    <div className={`flex flex-col gap-4 ${className}`}>
      <GlassCard>
        <h2
          className="text-base font-semibold mb-2"
          style={{ color: "var(--text-primary)" }}
        >
          Decision Summary
        </h2>
        <p
          className="text-sm leading-relaxed"
          style={{ color: "var(--text-secondary)" }}
        >
          {summary}
        </p>
      </GlassCard>

      <GlassCard>
        <h3
          className="text-sm font-semibold mb-2"
          style={{ color: "var(--text-primary)" }}
        >
          Reasoning
        </h3>
        <p
          className="text-sm leading-relaxed"
          style={{ color: "var(--text-secondary)" }}
        >
          {reasoning}
        </p>
      </GlassCard>

      <GlassCard>
        <h3
          className="text-sm font-semibold mb-2"
          style={{ color: "var(--text-primary)" }}
        >
          Outcome
        </h3>
        <p className="text-sm" style={{ color: "var(--text-secondary)" }}>
          {outcome}
        </p>
      </GlassCard>

      {alternatives.length > 0 && (
        <GlassCard>
          <h3
            className="text-sm font-semibold mb-3"
            style={{ color: "var(--text-primary)" }}
          >
            Alternatives Considered
          </h3>
          <ul className="flex flex-col gap-2">
            {alternatives.map((alt, i) => (
              <li
                key={i}
                className="flex items-start gap-2 text-sm"
                style={{ color: "var(--text-secondary)" }}
              >
                <span style={{ color: "var(--text-tertiary)" }}>•</span>
                {alt}
              </li>
            ))}
          </ul>
        </GlassCard>
      )}

      {timeline && timeline.length > 0 && (
        <GlassCard>
          <h3
            className="text-sm font-semibold mb-3"
            style={{ color: "var(--text-primary)" }}
          >
            Decision Timeline
          </h3>
          <div className="flex flex-col gap-3">
            {timeline.map((entry, i) => (
              <div
                key={i}
                className="flex items-start gap-3 text-sm"
                style={{ color: "var(--text-secondary)" }}
              >
                <div
                  className="w-2 h-2 rounded-full mt-1.5 flex-shrink-0"
                  style={{ background: "var(--accent-yellow)" }}
                />
                <div>
                  {Boolean(entry.date) && (
                    <span
                      className="text-xs font-mono mr-2"
                      style={{ color: "var(--text-tertiary)" }}
                    >
                      {String(entry.date)}
                    </span>
                  )}
                  {String(entry.description || entry.title || "")}
                </div>
              </div>
            ))}
          </div>
        </GlassCard>
      )}
    </div>
  );
}
