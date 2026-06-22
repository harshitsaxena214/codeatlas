"use client";

import { useParams } from "next/navigation";
import { useQuery } from "@tanstack/react-query";
import { BrainCircuit, User, CheckCircle, XCircle } from "lucide-react";
import { api } from "@/lib/api";
import { GlassCard } from "@/components/GlassCard";
import { FeedbackButtons } from "@/components/FeedbackButtons";
import { PageSkeleton } from "@/components/LoadingSkeleton";

export default function MaintainerBrainPage() {
  const params = useParams();
  const repoId = params.id as string;

  const { data: insights, isLoading, error } = useQuery({
    queryKey: ["maintainer-brain", repoId],
    queryFn: () => api.getMaintainerBrain(repoId),
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
  if (!insights) return null;

  return (
    <div className="p-6 max-w-4xl mx-auto">
      {/* Header */}
      <div className="flex items-center gap-3 mb-6 animate-fade-in">
        <div
          className="w-10 h-10 rounded-xl flex items-center justify-center"
          style={{ background: "hsla(270, 76%, 65%, 0.15)", color: "var(--accent-purple)" }}
        >
          <BrainCircuit size={20} />
        </div>
        <div>
          <h1 className="text-xl font-bold" style={{ color: "var(--text-primary)" }}>
            Maintainer Brain
          </h1>
          <p className="text-xs" style={{ color: "var(--text-secondary)" }}>
            Understand how maintainers think and what they expect
          </p>
        </div>
      </div>

      {/* Maintainer Profiles */}
      {insights.maintainer_profiles.length > 0 && (
        <div className="mb-6">
          <h2 className="text-sm font-semibold mb-3" style={{ color: "var(--text-primary)" }}>
            Key Maintainers
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            {insights.maintainer_profiles.map((profile, i) => (
              <GlassCard
                key={profile.username}
                className="animate-fade-in-up"
                hover
              >
                <div style={{ animationDelay: `${i * 100}ms` }}>
                  <div className="flex items-center gap-3 mb-3">
                    <div
                      className="w-9 h-9 rounded-full flex items-center justify-center"
                      style={{ background: "var(--bg-tertiary)" }}
                    >
                      <User size={16} style={{ color: "var(--text-secondary)" }} />
                    </div>
                    <div>
                      <div className="text-sm font-semibold" style={{ color: "var(--text-primary)" }}>
                        @{profile.username}
                      </div>
                      <div className="text-xs" style={{ color: "var(--text-tertiary)" }}>
                        {profile.review_count} reviews
                      </div>
                    </div>
                  </div>
                  {profile.preferences.length > 0 && (
                    <div className="flex flex-wrap gap-1 mb-2">
                      {profile.preferences.map((p) => (
                        <span key={p} className="badge badge-purple text-xs">
                          {p}
                        </span>
                      ))}
                    </div>
                  )}
                  {profile.common_feedback.length > 0 && (
                    <ul className="flex flex-col gap-1">
                      {profile.common_feedback.slice(0, 3).map((fb, j) => (
                        <li key={j} className="text-xs" style={{ color: "var(--text-secondary)" }}>
                          • {fb}
                        </li>
                      ))}
                    </ul>
                  )}
                </div>
              </GlassCard>
            ))}
          </div>
        </div>
      )}

      {/* Do / Don't lists */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
        <GlassCard className="animate-fade-in-up delay-300">
          <h3 className="text-sm font-semibold mb-3 flex items-center gap-2" style={{ color: "var(--accent-green)" }}>
            <CheckCircle size={16} /> DO
          </h3>
          <ul className="flex flex-col gap-2">
            {insights.do_list.map((item, i) => (
              <li key={i} className="flex items-start gap-2 text-sm" style={{ color: "var(--text-secondary)" }}>
                <span style={{ color: "var(--accent-green)" }}>✓</span>
                {item}
              </li>
            ))}
          </ul>
        </GlassCard>

        <GlassCard className="animate-fade-in-up delay-400">
          <h3 className="text-sm font-semibold mb-3 flex items-center gap-2" style={{ color: "var(--accent-red)" }}>
            <XCircle size={16} /> DON&apos;T
          </h3>
          <ul className="flex flex-col gap-2">
            {insights.dont_list.map((item, i) => (
              <li key={i} className="flex items-start gap-2 text-sm" style={{ color: "var(--text-secondary)" }}>
                <span style={{ color: "var(--accent-red)" }}>✗</span>
                {item}
              </li>
            ))}
          </ul>
        </GlassCard>
      </div>

      {/* Review Patterns */}
      {insights.review_patterns.length > 0 && (
        <GlassCard className="mb-4 animate-fade-in-up delay-500">
          <h3 className="text-sm font-semibold mb-3" style={{ color: "var(--text-primary)" }}>
            Review Patterns
          </h3>
          <ul className="flex flex-col gap-2">
            {insights.review_patterns.map((pattern, i) => (
              <li key={i} className="text-sm" style={{ color: "var(--text-secondary)" }}>
                • {pattern}
              </li>
            ))}
          </ul>
        </GlassCard>
      )}

      {/* Common Rejection Reasons */}
      {insights.common_rejection_reasons.length > 0 && (
        <GlassCard className="mb-4 animate-fade-in-up delay-600">
          <h3 className="text-sm font-semibold mb-3" style={{ color: "var(--text-primary)" }}>
            Common Rejection Reasons
          </h3>
          <ul className="flex flex-col gap-2">
            {insights.common_rejection_reasons.map((reason, i) => (
              <li key={i} className="flex items-start gap-2 text-sm" style={{ color: "var(--text-secondary)" }}>
                <span style={{ color: "var(--accent-orange)" }}>⚠</span>
                {reason}
              </li>
            ))}
          </ul>
        </GlassCard>
      )}

      <FeedbackButtons
        repoId={repoId}
        feature="maintainer_brain"
        query="maintainer insights"
        responseSummary={insights.preferences.join(", ")}
      />
    </div>
  );
}
