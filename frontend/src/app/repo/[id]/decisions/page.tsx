"use client";

import { useState } from "react";
import { useParams } from "next/navigation";
import { useMutation } from "@tanstack/react-query";
import { Lightbulb, Loader2, Search } from "lucide-react";
import { api, DecisionExploration } from "@/lib/api";
import { GlassCard } from "@/components/GlassCard";
import { FeedbackButtons } from "@/components/FeedbackButtons";

export default function DecisionExplorerPage() {
  const params = useParams();
  const repoId = params.id as string;
  const [question, setQuestion] = useState("");

  const mutation = useMutation({
    mutationFn: (q: string) => api.exploreDecision(repoId, q),
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!question.trim()) return;
    mutation.mutate(question.trim());
  };

  const result = mutation.data as DecisionExploration | undefined;

  return (
    <div className="p-6 max-w-4xl mx-auto">
      <div className="flex items-center gap-3 mb-6 animate-fade-in">
        <div
          className="w-10 h-10 rounded-xl flex items-center justify-center"
          style={{ background: "hsla(45, 93%, 55%, 0.15)", color: "var(--accent-yellow)" }}
        >
          <Lightbulb size={20} />
        </div>
        <div>
          <h1 className="text-xl font-bold" style={{ color: "var(--text-primary)" }}>
            Decision Explorer
          </h1>
          <p className="text-xs" style={{ color: "var(--text-secondary)" }}>
            Understand why architectural and design decisions were made
          </p>
        </div>
      </div>

      <form onSubmit={handleSubmit} className="mb-6 animate-fade-in-up">
        <div className="flex gap-2">
          <div className="relative flex-1">
            <Search
              size={16}
              className="absolute left-3 top-1/2 -translate-y-1/2"
              style={{ color: "var(--text-tertiary)" }}
            />
            <input
              type="text"
              value={question}
              onChange={(e) => setQuestion(e.target.value)}
              placeholder="Why did this project switch to TypeScript?"
              className="input-field pl-10"
            />
          </div>
          <button
            type="submit"
            disabled={!question.trim() || mutation.isPending}
            className="btn-primary"
          >
            {mutation.isPending ? (
              <Loader2 size={16} className="animate-spin" />
            ) : (
              "Explore"
            )}
          </button>
        </div>
      </form>

      {mutation.error && (
        <div
          className="p-3 rounded-lg text-sm mb-4"
          style={{ background: "hsla(0, 72%, 55%, 0.1)", color: "var(--accent-red)" }}
        >
          {(mutation.error as Error).message}
        </div>
      )}

      {result && (
        <div className="animate-fade-in-up">
          <GlassCard className="mb-4">
            <h2 className="text-base font-semibold mb-2" style={{ color: "var(--text-primary)" }}>
              Decision Summary
            </h2>
            <p className="text-sm leading-relaxed" style={{ color: "var(--text-secondary)" }}>
              {result.decision_summary}
            </p>
          </GlassCard>

          <GlassCard className="mb-4">
            <h3 className="text-sm font-semibold mb-2" style={{ color: "var(--text-primary)" }}>
              Reasoning
            </h3>
            <p className="text-sm leading-relaxed" style={{ color: "var(--text-secondary)" }}>
              {result.reasoning}
            </p>
          </GlassCard>

          <GlassCard className="mb-4">
            <h3 className="text-sm font-semibold mb-2" style={{ color: "var(--text-primary)" }}>
              Outcome
            </h3>
            <p className="text-sm" style={{ color: "var(--text-secondary)" }}>
              {result.outcome}
            </p>
          </GlassCard>

          {result.alternatives_considered.length > 0 && (
            <GlassCard className="mb-4">
              <h3 className="text-sm font-semibold mb-3" style={{ color: "var(--text-primary)" }}>
                Alternatives Considered
              </h3>
              <ul className="flex flex-col gap-2">
                {result.alternatives_considered.map((alt, i) => (
                  <li key={i} className="flex items-start gap-2 text-sm" style={{ color: "var(--text-secondary)" }}>
                    <span style={{ color: "var(--text-tertiary)" }}>•</span>
                    {alt}
                  </li>
                ))}
              </ul>
            </GlassCard>
          )}

          {result.timeline.length > 0 && (
            <GlassCard className="mb-4">
              <h3 className="text-sm font-semibold mb-3" style={{ color: "var(--text-primary)" }}>
                Decision Timeline
              </h3>
              <div className="flex flex-col gap-3">
                {result.timeline.map((entry: Record<string, unknown>, i: number) => (
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
                        <span className="text-xs font-mono mr-2" style={{ color: "var(--text-tertiary)" }}>
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

          <FeedbackButtons
            repoId={repoId}
            feature="decision_explorer"
            query={result.question}
            responseSummary={result.decision_summary}
          />
        </div>
      )}
    </div>
  );
}
