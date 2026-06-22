"use client";

import { useState } from "react";
import { useParams } from "next/navigation";
import { useMutation } from "@tanstack/react-query";
import Link from "next/link";
import {
  Target,
  ExternalLink,
  Loader2,
  Gauge,
  Clock,
  FileCode,
} from "lucide-react";
import { api, FindIssueResponse } from "@/lib/api";
import { GlassCard } from "@/components/GlassCard";
import { FeedbackButtons } from "@/components/FeedbackButtons";

const experienceLevels = [
  { value: "beginner", label: "Beginner", desc: "New to open source" },
  { value: "intermediate", label: "Intermediate", desc: "Some contributions" },
  { value: "advanced", label: "Advanced", desc: "Experienced contributor" },
];

const interests = [
  { value: "frontend", label: "Frontend" },
  { value: "backend", label: "Backend" },
  { value: "devops", label: "DevOps" },
  { value: "documentation", label: "Documentation" },
  { value: "testing", label: "Testing" },
  { value: "ai", label: "AI / ML" },
];

export default function FindIssuePage() {
  const params = useParams();
  const repoId = params.id as string;

  const [experience, setExperience] = useState("");
  const [interest, setInterest] = useState("");

  const mutation = useMutation({
    mutationFn: () => api.findFirstIssue(repoId, experience, interest),
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!experience || !interest) return;
    mutation.mutate();
  };

  const result = mutation.data as FindIssueResponse | undefined;

  return (
    <div className="p-6 max-w-4xl mx-auto">
      {/* Header */}
      <div className="flex items-center gap-3 mb-6 animate-fade-in">
        <div
          className="w-10 h-10 rounded-xl flex items-center justify-center"
          style={{
            background: "hsla(25, 95%, 55%, 0.15)",
            color: "var(--accent-orange)",
          }}
        >
          <Target size={20} />
        </div>
        <div>
          <h1 className="text-xl font-bold" style={{ color: "var(--text-primary)" }}>
            Find My First Issue
          </h1>
          <p className="text-xs" style={{ color: "var(--text-secondary)" }}>
            AI-matched issues based on your profile
          </p>
        </div>
      </div>

      {/* Form */}
      {!result && (
        <form onSubmit={handleSubmit} className="animate-fade-in-up">
          <GlassCard className="mb-4">
            <h3 className="text-sm font-semibold mb-3" style={{ color: "var(--text-primary)" }}>
              Your Experience Level
            </h3>
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-2">
              {experienceLevels.map((level) => (
                <button
                  key={level.value}
                  type="button"
                  onClick={() => setExperience(level.value)}
                  className="p-3 rounded-lg text-left transition-all"
                  style={{
                    background:
                      experience === level.value
                        ? "hsla(25, 95%, 55%, 0.1)"
                        : "var(--bg-secondary)",
                    border: `1px solid ${
                      experience === level.value
                        ? "var(--accent-orange)"
                        : "var(--border)"
                    }`,
                  }}
                >
                  <div className="text-sm font-medium" style={{ color: "var(--text-primary)" }}>
                    {level.label}
                  </div>
                  <div className="text-xs" style={{ color: "var(--text-secondary)" }}>
                    {level.desc}
                  </div>
                </button>
              ))}
            </div>
          </GlassCard>

          <GlassCard className="mb-6">
            <h3 className="text-sm font-semibold mb-3" style={{ color: "var(--text-primary)" }}>
              Your Interest Area
            </h3>
            <div className="flex flex-wrap gap-2">
              {interests.map((item) => (
                <button
                  key={item.value}
                  type="button"
                  onClick={() => setInterest(item.value)}
                  className="badge py-2 px-4 text-sm cursor-pointer transition-all"
                  style={{
                    background:
                      interest === item.value
                        ? "hsla(25, 95%, 55%, 0.15)"
                        : "var(--bg-tertiary)",
                    color:
                      interest === item.value
                        ? "var(--accent-orange)"
                        : "var(--text-secondary)",
                    border: `1px solid ${
                      interest === item.value
                        ? "var(--accent-orange)"
                        : "transparent"
                    }`,
                  }}
                >
                  {item.label}
                </button>
              ))}
            </div>
          </GlassCard>

          <button
            type="submit"
            disabled={!experience || !interest || mutation.isPending}
            className="btn-primary w-full py-3 rounded-xl"
          >
            {mutation.isPending ? (
              <>
                <Loader2 size={16} className="animate-spin" />
                Finding issues...
              </>
            ) : (
              <>
                <Target size={16} />
                Find My Issue
              </>
            )}
          </button>

          {mutation.error && (
            <div
              className="mt-4 p-3 rounded-lg text-sm"
              style={{
                background: "hsla(0, 72%, 55%, 0.1)",
                color: "var(--accent-red)",
              }}
            >
              {(mutation.error as Error).message}
            </div>
          )}
        </form>
      )}

      {/* Results */}
      {result && (
        <div className="animate-fade-in-up">
          {result.reasoning && (
            <GlassCard className="mb-4">
              <p className="text-sm" style={{ color: "var(--text-secondary)" }}>
                {result.reasoning}
              </p>
            </GlassCard>
          )}

          <div className="flex flex-col gap-4">
            {result.recommended_issues?.map((issue, i) => (
              <GlassCard
                key={issue.issue_number}
                className="animate-fade-in-up"
                hover
              >
                <div style={{ animationDelay: `${i * 100}ms` }}>
                  <div className="flex items-start justify-between mb-3">
                    <div className="flex-1">
                      <div className="flex items-center gap-2 mb-1">
                        <span
                          className="text-xs font-mono"
                          style={{ color: "var(--text-tertiary)" }}
                        >
                          #{issue.issue_number}
                        </span>
                        <h3
                          className="text-sm font-semibold"
                          style={{ color: "var(--text-primary)" }}
                        >
                          {issue.title}
                        </h3>
                      </div>
                      <div className="flex flex-wrap gap-1.5 mt-1">
                        {issue.labels.map((label) => (
                          <span key={label} className="badge badge-blue text-xs">
                            {label}
                          </span>
                        ))}
                      </div>
                    </div>
                    <a
                      href={issue.url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="p-1.5 rounded-md hover:bg-[var(--bg-tertiary)]"
                    >
                      <ExternalLink size={14} style={{ color: "var(--text-secondary)" }} />
                    </a>
                  </div>

                  <p className="text-sm mb-3" style={{ color: "var(--text-secondary)" }}>
                    {issue.why_it_matches}
                  </p>

                  <div className="grid grid-cols-3 gap-3 mb-3">
                    <div className="flex items-center gap-1.5 text-xs" style={{ color: "var(--text-tertiary)" }}>
                      <Gauge size={12} />
                      Difficulty: {issue.difficulty_score}/10
                    </div>
                    <div className="flex items-center gap-1.5 text-xs" style={{ color: "var(--text-tertiary)" }}>
                      <Clock size={12} />
                      {issue.estimated_time}
                    </div>
                    <div className="flex items-center gap-1.5 text-xs" style={{ color: "var(--text-tertiary)" }}>
                      <FileCode size={12} />
                      {issue.relevant_files.length} files
                    </div>
                  </div>

                  {issue.relevant_files.length > 0 && (
                    <div className="flex flex-wrap gap-1 mt-2">
                      {issue.relevant_files.slice(0, 5).map((f) => (
                        <code
                          key={f}
                          className="text-xs px-2 py-0.5 rounded"
                          style={{
                            background: "var(--bg-secondary)",
                            color: "var(--accent-cyan)",
                          }}
                        >
                          {f}
                        </code>
                      ))}
                    </div>
                  )}

                  <div className="mt-3">
                    <Link
                      href={`/repo/${repoId}/issue/${issue.issue_number}`}
                      className="btn-ghost text-xs"
                      style={{ color: "var(--accent-blue)" }}
                    >
                      Get Contribution Plan →
                    </Link>
                  </div>
                </div>
              </GlassCard>
            ))}
          </div>

          <div className="mt-4 flex items-center justify-between">
            <FeedbackButtons
              repoId={repoId}
              feature="find_issue"
              query={`${experience} ${interest}`}
              responseSummary={result.reasoning}
            />
            <button
              onClick={() => mutation.reset()}
              className="btn-ghost text-sm"
            >
              Search Again
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
