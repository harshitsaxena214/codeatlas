"use client";

import { useParams } from "next/navigation";
import { useQuery } from "@tanstack/react-query";
import { BookOpen, ExternalLink } from "lucide-react";
import { api } from "@/lib/api";
import { GlassCard } from "@/components/GlassCard";
import { FeedbackButtons } from "@/components/FeedbackButtons";
import { PageSkeleton } from "@/components/LoadingSkeleton";

export default function OnboardingPage() {
  const params = useParams();
  const repoId = params.id as string;

  const { data: guide, isLoading, error } = useQuery({
    queryKey: ["onboarding", repoId],
    queryFn: () => api.getOnboarding(repoId),
    enabled: !!repoId,
  });

  if (isLoading) return <PageSkeleton />;
  if (error)
    return (
      <div className="p-6">
        <GlassCard>
          <p style={{ color: "var(--accent-red)" }}>
            Failed to load onboarding guide: {(error as Error).message}
          </p>
        </GlassCard>
      </div>
    );
  if (!guide) return null;

  return (
    <div className="p-6 max-w-4xl mx-auto">
      {/* Header */}
      <div className="flex items-center gap-3 mb-6 animate-fade-in">
        <div
          className="w-10 h-10 rounded-xl flex items-center justify-center"
          style={{
            background: "hsla(152, 69%, 50%, 0.15)",
            color: "var(--accent-green)",
          }}
        >
          <BookOpen size={20} />
        </div>
        <div>
          <h1 className="text-xl font-bold" style={{ color: "var(--text-primary)" }}>
            Onboarding Guide
          </h1>
          <p className="text-xs" style={{ color: "var(--text-secondary)" }}>
            Everything you need to start contributing
          </p>
        </div>
      </div>

      {/* Project Summary */}
      <GlassCard className="mb-4 animate-fade-in-up delay-100">
        <h2 className="text-base font-semibold mb-2" style={{ color: "var(--text-primary)" }}>
          Project Summary
        </h2>
        <p className="text-sm leading-relaxed" style={{ color: "var(--text-secondary)" }}>
          {guide.project_summary}
        </p>
      </GlassCard>

      {/* What it solves */}
      <GlassCard className="mb-4 animate-fade-in-up delay-200">
        <h2 className="text-base font-semibold mb-2" style={{ color: "var(--text-primary)" }}>
          What Problem Does It Solve?
        </h2>
        <p className="text-sm leading-relaxed" style={{ color: "var(--text-secondary)" }}>
          {guide.what_it_solves}
        </p>
      </GlassCard>

      {/* Core Technologies & Maintainers */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
        <GlassCard className="animate-fade-in-up delay-300">
          <h3 className="text-sm font-semibold mb-3" style={{ color: "var(--text-primary)" }}>
            Core Technologies
          </h3>
          <div className="flex flex-wrap gap-1.5">
            {guide.core_technologies.map((tech) => (
              <span key={tech} className="badge badge-cyan text-xs">
                {tech}
              </span>
            ))}
          </div>
        </GlassCard>

        <GlassCard className="animate-fade-in-up delay-400">
          <h3 className="text-sm font-semibold mb-3" style={{ color: "var(--text-primary)" }}>
            Key Maintainers
          </h3>
          <div className="flex flex-wrap gap-1.5">
            {guide.key_maintainers.map((m) => (
              <span key={m} className="badge badge-purple text-xs">
                @{m}
              </span>
            ))}
          </div>
        </GlassCard>
      </div>

      {/* Project Culture */}
      <GlassCard className="mb-4 animate-fade-in-up delay-500">
        <h2 className="text-base font-semibold mb-2" style={{ color: "var(--text-primary)" }}>
          Project Culture
        </h2>
        <p className="text-sm leading-relaxed" style={{ color: "var(--text-secondary)" }}>
          {guide.project_culture}
        </p>
      </GlassCard>

      {/* Reading Path */}
      {guide.reading_path.length > 0 && (
        <GlassCard className="mb-4 animate-fade-in-up delay-600">
          <h2 className="text-base font-semibold mb-4" style={{ color: "var(--text-primary)" }}>
            Suggested Reading Path
          </h2>
          <div className="flex flex-col gap-3">
            {guide.reading_path.map((step, i) => (
              <div
                key={i}
                className="flex items-start gap-3 p-3 rounded-lg"
                style={{ background: "var(--bg-secondary)" }}
              >
                <div
                  className="w-7 h-7 rounded-full flex items-center justify-center flex-shrink-0 text-xs font-bold"
                  style={{
                    background: "var(--gradient-primary)",
                    color: "white",
                  }}
                >
                  {step.step_number}
                </div>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2">
                    <h4 className="text-sm font-medium" style={{ color: "var(--text-primary)" }}>
                      {step.title}
                    </h4>
                    <span className="badge badge-blue text-xs">{step.resource_type}</span>
                  </div>
                  <p className="text-xs mt-1" style={{ color: "var(--text-secondary)" }}>
                    {step.description}
                  </p>
                  {step.resource_url && (
                    <a
                      href={step.resource_url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="inline-flex items-center gap-1 text-xs mt-1.5"
                      style={{ color: "var(--accent-blue)" }}
                    >
                      View Resource <ExternalLink size={10} />
                    </a>
                  )}
                </div>
              </div>
            ))}
          </div>
        </GlassCard>
      )}

      {/* Feedback */}
      <div className="mt-4">
        <FeedbackButtons
          repoId={repoId}
          feature="onboarding"
          query="onboarding guide"
          responseSummary={guide.project_summary}
        />
      </div>
    </div>
  );
}
