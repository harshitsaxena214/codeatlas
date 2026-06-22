"use client";

import { useState } from "react";
import { useParams } from "next/navigation";
import { useMutation } from "@tanstack/react-query";
import { Layers, Loader2, Search } from "lucide-react";
import { api, ArchitectureResponse } from "@/lib/api";
import { GlassCard } from "@/components/GlassCard";
import { FeedbackButtons } from "@/components/FeedbackButtons";

export default function ArchitectureExplorerPage() {
  const params = useParams();
  const repoId = params.id as string;
  const [subsystem, setSubsystem] = useState("");

  const mutation = useMutation({
    mutationFn: (sub: string | null) => api.exploreArchitecture(repoId, sub),
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    mutation.mutate(subsystem.trim() || null);
  };

  const result = mutation.data as ArchitectureResponse | undefined;

  return (
    <div className="p-6 max-w-4xl mx-auto">
      <div className="flex items-center gap-3 mb-6 animate-fade-in">
        <div
          className="w-10 h-10 rounded-xl flex items-center justify-center"
          style={{ background: "hsla(280, 80%, 55%, 0.15)", color: "var(--accent-purple)" }}
        >
          <Layers size={20} />
        </div>
        <div>
          <h1 className="text-xl font-bold" style={{ color: "var(--text-primary)" }}>
            Architecture Explorer
          </h1>
          <p className="text-xs" style={{ color: "var(--text-secondary)" }}>
            Analyze high-level design and subsystems dynamically
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
              value={subsystem}
              onChange={(e) => setSubsystem(e.target.value)}
              placeholder="Subsystem name (e.g. Authentication, Database) or leave blank for general overview"
              className="input-field pl-10"
            />
          </div>
          <button
            type="submit"
            disabled={mutation.isPending}
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
              Architecture Overview: {result.subsystem}
            </h2>
            <div className="text-sm leading-relaxed whitespace-pre-wrap" style={{ color: "var(--text-secondary)" }}>
              {result.architecture_overview}
            </div>
          </GlassCard>

          <FeedbackButtons
            repoId={repoId}
            feature="architecture_explorer"
            query={result.subsystem || "General Architecture"}
            responseSummary={result.architecture_overview.slice(0, 200)}
          />
        </div>
      )}
    </div>
  );
}
