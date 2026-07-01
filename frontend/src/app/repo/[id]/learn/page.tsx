"use client";

import { useState } from "react";
import { useParams } from "next/navigation";
import { useMutation } from "@tanstack/react-query";
import {
  GraduationCap,
  Loader2,
  Clock,
  ExternalLink,
} from "lucide-react";
import { api, LearningPath } from "@/lib/api";
import { GlassCard } from "@/components/GlassCard";
import { FeedbackButtons } from "@/components/FeedbackButtons";

const interestOptions = [
  "Frontend",
  "Backend",
  "DevOps",
  "Testing",
  "Documentation",
  "AI/ML",
  "Security",
  "Performance",
  "Accessibility",
];

export default function LearningPathPage() {
  const params = useParams();
  const repoId = params.id as string;

  const [issueNumber, setIssueNumber] = useState("");
  const [selectedInterests, setSelectedInterests] = useState<string[]>([]);

  const mutation = useMutation({
    mutationFn: () =>
      api.getLearningPath(
        repoId,
        issueNumber ? parseInt(issueNumber, 10) : null,
        selectedInterests
      ),
  });

  const toggleInterest = (interest: string) => {
    setSelectedInterests((prev) =>
      prev.includes(interest)
        ? prev.filter((i) => i !== interest)
        : [...prev, interest]
    );
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    mutation.mutate();
  };

  const result = mutation.data as LearningPath | undefined;

  return (
    <div className="p-6 max-w-4xl mx-auto">
      <div className="flex items-center gap-3 mb-6 animate-fade-in">
        <div
          className="w-10 h-10 rounded-xl flex items-center justify-center"
          style={{
            background: "hsla(152, 69%, 50%, 0.15)",
            color: "var(--accent-green)",
          }}
        >
          <GraduationCap size={20} />
        </div>
        <div>
          <h1 className="text-xl font-bold" style={{ color: "var(--text-primary)" }}>
            Learning Path
          </h1>
          <p className="text-xs" style={{ color: "var(--text-secondary)" }}>
            Personalized learning journey to contribute to this repository
          </p>
        </div>
      </div>

      {!result && (
        <form onSubmit={handleSubmit} className="animate-fade-in-up">
          <GlassCard className="mb-4">
            <h3 className="text-sm font-semibold mb-3" style={{ color: "var(--text-primary)" }}>
              Target Issue (optional)
            </h3>
            <input
              type="number"
              value={issueNumber}
              onChange={(e) => setIssueNumber(e.target.value)}
              placeholder="Issue number, e.g. 42"
              className="input-field"
            />
          </GlassCard>

          <GlassCard className="mb-6">
            <h3 className="text-sm font-semibold mb-3" style={{ color: "var(--text-primary)" }}>
              Your Interests
            </h3>
            <div className="flex flex-wrap gap-2">
              {interestOptions.map((interest) => (
                <button
                  key={interest}
                  type="button"
                  onClick={() => toggleInterest(interest)}
                  className="badge py-2 px-3 text-sm cursor-pointer transition-all"
                  style={{
                    background: selectedInterests.includes(interest)
                      ? "hsla(152, 69%, 50%, 0.15)"
                      : "var(--bg-tertiary)",
                    color: selectedInterests.includes(interest)
                      ? "var(--accent-green)"
                      : "var(--text-secondary)",
                    border: `1px solid ${
                      selectedInterests.includes(interest)
                        ? "var(--accent-green)"
                        : "transparent"
                    }`,
                  }}
                >
                  {interest}
                </button>
              ))}
            </div>
          </GlassCard>

          <button
            type="submit"
            disabled={mutation.isPending}
            className="btn-primary w-full py-3 rounded-xl"
          >
            {mutation.isPending ? (
              <>
                <Loader2 size={16} className="animate-spin" />
                Generating path...
              </>
            ) : (
              <>
                <GraduationCap size={16} />
                Generate Learning Path
              </>
            )}
          </button>

          {mutation.error && (
            <div
              className="mt-4 p-3 rounded-lg text-sm"
              style={{ background: "hsla(0, 72%, 55%, 0.1)", color: "var(--accent-red)" }}
            >
              {(mutation.error as Error).message}
            </div>
          )}
        </form>
      )}

      {result && (
        <div className="animate-fade-in-up">
          {/* Title & Description */}
          <GlassCard className="mb-4">
            <h2
              className="text-lg font-bold mb-2 gradient-text"
            >
              {result.title}
            </h2>
            <p className="text-sm" style={{ color: "var(--text-secondary)" }}>
              {result.description}
            </p>
          </GlassCard>

          {/* Prerequisites */}
          {result.prerequisites.length > 0 && (
            <GlassCard className="mb-4">
              <h3 className="text-sm font-semibold mb-3" style={{ color: "var(--text-primary)" }}>
                Prerequisites
              </h3>
              <ul className="flex flex-col gap-1.5">
                {result.prerequisites.map((p, i) => (
                  <li key={i} className="flex items-start gap-2 text-sm" style={{ color: "var(--text-secondary)" }}>
                    <span style={{ color: "var(--accent-blue)" }}>•</span>
                    {p}
                  </li>
                ))}
              </ul>
            </GlassCard>
          )}

          {/* Key Concepts */}
          {result.key_concepts.length > 0 && (
            <GlassCard className="mb-4">
              <h3 className="text-sm font-semibold mb-3" style={{ color: "var(--text-primary)" }}>
                Key Concepts
              </h3>
              <div className="flex flex-wrap gap-1.5">
                {result.key_concepts.map((c) => (
                  <span key={c} className="badge badge-cyan text-xs">
                    {c}
                  </span>
                ))}
              </div>
            </GlassCard>
          )}

          {/* Steps */}
          <div className="flex flex-col gap-3">
            {result.steps.map((step, i) => (
              <div
                key={i}
                className="animate-fade-in-up"
                style={{ animationDelay: `${i * 75}ms` }}
              >
                <GlassCard hover padding="p-4">
                  <div className="flex items-start gap-3">
                    <div
                      className="w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0 text-xs font-bold"
                      style={{
                        background: "var(--gradient-primary)",
                        color: "white",
                      }}
                    >
                      {step.step_number}
                    </div>
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2 mb-1">
                        <h4 className="text-sm font-semibold" style={{ color: "var(--text-primary)" }}>
                          {step.title}
                        </h4>
                        <span className="badge badge-blue text-xs">
                          {step.resource_type}
                        </span>
                      </div>
                      <p className="text-xs mb-2" style={{ color: "var(--text-secondary)" }}>
                        {step.description}
                      </p>
                      <div className="flex items-center gap-3">
                        <span className="flex items-center gap-1 text-xs" style={{ color: "var(--text-tertiary)" }}>
                          <Clock size={10} /> {step.estimated_time}
                        </span>
                        {step.resource_url && (
                          <a
                            href={step.resource_url}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="flex items-center gap-1 text-xs"
                            style={{ color: "var(--accent-blue)" }}
                          >
                            <ExternalLink size={10} /> Open
                          </a>
                        )}
                      </div>
                    </div>
                  </div>
                </GlassCard>
              </div>
            ))}
          </div>

          <div className="mt-4 flex items-center justify-between">
            <FeedbackButtons
              repoId={repoId}
              feature="learning_path"
              query={`interests: ${selectedInterests.join(", ")}`}
              responseSummary={result.title}
            />
            <button
              onClick={() => mutation.reset()}
              className="btn-ghost text-sm"
            >
              Generate Again
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
