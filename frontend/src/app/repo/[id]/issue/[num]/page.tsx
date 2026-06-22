"use client";

import { useParams } from "next/navigation";
import { useQuery } from "@tanstack/react-query";
import { Wrench, ExternalLink, Gauge, Clock, AlertTriangle } from "lucide-react";
import { api } from "@/lib/api";
import { GlassCard } from "@/components/GlassCard";
import { FeedbackButtons } from "@/components/FeedbackButtons";
import { PageSkeleton } from "@/components/LoadingSkeleton";

export default function ContributionAssistantPage() {
  const params = useParams();
  const repoId = params.id as string;
  const issueNum = parseInt(params.num as string, 10);

  const { data: plan, isLoading, error } = useQuery({
    queryKey: ["analyze-issue", repoId, issueNum],
    queryFn: () => api.analyzeIssue(repoId, issueNum),
    enabled: !!repoId && !isNaN(issueNum),
  });

  if (isLoading) return <PageSkeleton />;
  if (error)
    return (
      <div className="p-6">
        <GlassCard>
          <p style={{ color: "var(--accent-red)" }}>
            {(error as Error).message}
          </p>
        </GlassCard>
      </div>
    );
  if (!plan) return null;

  const difficultyColor =
    plan.difficulty_score <= 3
      ? "var(--accent-green)"
      : plan.difficulty_score <= 6
        ? "var(--accent-yellow)"
        : "var(--accent-red)";

  return (
    <div className="p-6 max-w-4xl mx-auto">
      {/* Header */}
      <div className="flex items-center gap-3 mb-6 animate-fade-in">
        <div
          className="w-10 h-10 rounded-xl flex items-center justify-center"
          style={{ background: "hsla(217, 91%, 60%, 0.15)", color: "var(--accent-blue)" }}
        >
          <Wrench size={20} />
        </div>
        <div className="flex-1">
          <div className="flex items-center gap-2">
            <h1 className="text-xl font-bold" style={{ color: "var(--text-primary)" }}>
              Contribution Plan
            </h1>
            <span className="text-sm font-mono" style={{ color: "var(--text-tertiary)" }}>
              #{plan.issue_number}
            </span>
          </div>
          <p className="text-xs" style={{ color: "var(--text-secondary)" }}>
            {plan.issue_title}
          </p>
        </div>
        <a
          href={plan.issue_url}
          target="_blank"
          rel="noopener noreferrer"
          className="btn-ghost text-xs"
        >
          <ExternalLink size={12} /> GitHub
        </a>
      </div>

      {/* Summary */}
      <GlassCard className="mb-4 animate-fade-in-up delay-100">
        <p className="text-sm leading-relaxed" style={{ color: "var(--text-secondary)" }}>
          {plan.summary}
        </p>
      </GlassCard>

      {/* Difficulty & Effort */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 mb-4">
        <GlassCard className="animate-fade-in-up delay-200" padding="p-4">
          <div className="flex items-center gap-2 mb-1">
            <Gauge size={14} style={{ color: difficultyColor }} />
            <span className="text-xs" style={{ color: "var(--text-secondary)" }}>
              Difficulty
            </span>
          </div>
          <div className="text-lg font-bold" style={{ color: difficultyColor }}>
            {plan.difficulty_score}/10
          </div>
          <div className="text-xs" style={{ color: "var(--text-tertiary)" }}>
            {plan.difficulty}
          </div>
        </GlassCard>

        <GlassCard className="animate-fade-in-up delay-300" padding="p-4">
          <div className="flex items-center gap-2 mb-1">
            <Clock size={14} style={{ color: "var(--accent-blue)" }} />
            <span className="text-xs" style={{ color: "var(--text-secondary)" }}>
              Estimated Effort
            </span>
          </div>
          <div className="text-lg font-bold" style={{ color: "var(--text-primary)" }}>
            {plan.estimated_effort}
          </div>
        </GlassCard>

        <GlassCard className="animate-fade-in-up delay-400" padding="p-4">
          <div className="flex items-center gap-2 mb-1">
            <AlertTriangle size={14} style={{ color: "var(--accent-orange)" }} />
            <span className="text-xs" style={{ color: "var(--text-secondary)" }}>
              Challenges
            </span>
          </div>
          <div className="text-lg font-bold" style={{ color: "var(--text-primary)" }}>
            {plan.potential_challenges.length}
          </div>
        </GlassCard>
      </div>

      {/* Starting Point */}
      <GlassCard className="mb-4 animate-fade-in-up delay-400">
        <h3 className="text-sm font-semibold mb-2" style={{ color: "var(--text-primary)" }}>
          Suggested Starting Point
        </h3>
        <p className="text-sm" style={{ color: "var(--text-secondary)" }}>
          {plan.suggested_starting_point}
        </p>
      </GlassCard>

      {/* Recommended Approach */}
      <GlassCard className="mb-4 animate-fade-in-up delay-500">
        <h3 className="text-sm font-semibold mb-2" style={{ color: "var(--text-primary)" }}>
          Recommended Approach
        </h3>
        <p className="text-sm leading-relaxed" style={{ color: "var(--text-secondary)" }}>
          {plan.recommended_approach}
        </p>
      </GlassCard>

      {/* Maintainer Expectations */}
      {plan.maintainer_expectations.length > 0 && (
        <GlassCard className="mb-4 animate-fade-in-up delay-600">
          <h3 className="text-sm font-semibold mb-3" style={{ color: "var(--text-primary)" }}>
            Maintainer Expectations
          </h3>
          <ul className="flex flex-col gap-2">
            {plan.maintainer_expectations.map((exp, i) => (
              <li key={i} className="flex items-start gap-2 text-sm" style={{ color: "var(--text-secondary)" }}>
                <span style={{ color: "var(--accent-green)" }}>✓</span>
                {exp}
              </li>
            ))}
          </ul>
        </GlassCard>
      )}

      {/* Challenges */}
      {plan.potential_challenges.length > 0 && (
        <GlassCard className="mb-4 animate-fade-in-up delay-700">
          <h3 className="text-sm font-semibold mb-3" style={{ color: "var(--text-primary)" }}>
            Potential Challenges
          </h3>
          <ul className="flex flex-col gap-2">
            {plan.potential_challenges.map((ch, i) => (
              <li key={i} className="flex items-start gap-2 text-sm" style={{ color: "var(--text-secondary)" }}>
                <span style={{ color: "var(--accent-orange)" }}>⚠</span>
                {ch}
              </li>
            ))}
          </ul>
        </GlassCard>
      )}

      <FeedbackButtons
        repoId={repoId}
        feature="contribution_assistant"
        query={`Issue #${plan.issue_number}`}
        responseSummary={plan.summary}
      />
    </div>
  );
}
