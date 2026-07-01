"use client";

import { useState } from "react";
import { useParams } from "next/navigation";
import { useQuery } from "@tanstack/react-query";
import { Timer, ExternalLink } from "lucide-react";
import { api } from "@/lib/api";
import { GlassCard } from "@/components/GlassCard";
import { FeedbackButtons } from "@/components/FeedbackButtons";
import { PageSkeleton } from "@/components/LoadingSkeleton";

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

export default function TimelinePage() {
  const params = useParams();
  const repoId = params.id as string;
  const [focus, setFocus] = useState<string | undefined>(undefined);

  const { data: timeline, isLoading, error } = useQuery({
    queryKey: ["timeline", repoId, focus],
    queryFn: () => api.getTimeline(repoId, focus),
    enabled: !!repoId,
  });

  if (isLoading) return <PageSkeleton />;
  if (error)
    return (
      <div className="p-6">
        <GlassCard>
          <p style={{ color: "var(--accent-red)" }}>{(error as Error).message}</p>
        </GlassCard>
      </div>
    );
  if (!timeline) return null;

  return (
    <div className="p-6 max-w-3xl mx-auto">
      <div className="flex items-center gap-3 mb-6 animate-fade-in">
        <div
          className="w-10 h-10 rounded-xl flex items-center justify-center"
          style={{ background: "hsla(217, 91%, 60%, 0.15)", color: "var(--accent-blue)" }}
        >
          <Timer size={20} />
        </div>
        <div>
          <h1 className="text-xl font-bold" style={{ color: "var(--text-primary)" }}>
            Project Timeline
          </h1>
          <p className="text-xs" style={{ color: "var(--text-secondary)" }}>
            Key milestones and evolution
          </p>
        </div>
      </div>

      {timeline.summary && (
        <GlassCard className="mb-6 animate-fade-in-up">
          <p className="text-sm" style={{ color: "var(--text-secondary)" }}>
            {timeline.summary}
          </p>
        </GlassCard>
      )}

      {/* Filter Toggle */}
      <div className="flex gap-2 mb-6 animate-fade-in-up delay-100">
        <button
          onClick={() => setFocus(undefined)}
          className={`px-3 py-1.5 rounded-md text-xs font-medium transition-colors ${
            !focus ? "bg-[var(--accent-blue)] text-white" : "bg-[var(--bg-tertiary)] text-[var(--text-secondary)] hover:bg-[var(--bg-tertiary-hover)]"
          }`}
        >
          General Timeline
        </button>
        <button
          onClick={() => setFocus("architecture")}
          className={`px-3 py-1.5 rounded-md text-xs font-medium transition-colors ${
            focus === "architecture" ? "bg-[var(--accent-purple)] text-white" : "bg-[var(--bg-tertiary)] text-[var(--text-secondary)] hover:bg-[var(--bg-tertiary-hover)]"
          }`}
        >
          Architecture Focus
        </button>
      </div>

      {/* Timeline */}
      <div className="relative pl-8">
        {/* Vertical line */}
        <div
          className="absolute left-3 top-0 bottom-0 w-px"
          style={{ background: "var(--border)" }}
        />

        <div className="flex flex-col gap-6">
          {timeline.events.map((event, i) => {
            const colors =
              eventTypeColors[event.event_type.toLowerCase()] ||
              eventTypeColors.default;

            return (
              <div
                key={i}
                className="relative animate-fade-in-up"
                style={{ animationDelay: `${i * 75}ms` }}
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
          })}
        </div>
      </div>

      <div className="mt-6">
        <FeedbackButtons
          repoId={repoId}
          feature="timeline"
          query="project timeline"
          responseSummary={timeline.summary}
        />
      </div>
    </div>
  );
}
