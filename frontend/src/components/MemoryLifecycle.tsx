"use client";

import { useState } from "react";
import {
  BrainCircuit,
  Search,
  RefreshCcw,
  Trash2,
  ThumbsUp,
  Loader2,
  Sparkles,
} from "lucide-react";
import { useForgetMemory } from "@/hooks/useIngestion";
import { GlassCard } from "@/components/GlassCard";
import type { RepositoryStatus } from "@/lib/api";

interface MemoryLifecycleProps {
  repoId: string;
  status: RepositoryStatus;
  onReIngest?: () => void;
  onForgetComplete?: () => void;
}

/**
 * MemoryLifecycle — UI controls for Cognee's memory lifecycle:
 * Remember (ingest), Recall (query), Improve (feedback), Forget (delete).
 */
export function MemoryLifecycle({
  repoId,
  status,
  onReIngest,
  onForgetComplete,
}: MemoryLifecycleProps) {
  const [showForgetConfirm, setShowForgetConfirm] = useState(false);
  const forgetMutation = useForgetMemory();

  const handleForget = async () => {
    try {
      await forgetMutation.mutateAsync(repoId);
      setShowForgetConfirm(false);
      onForgetComplete?.();
    } catch {
      // Error handled by mutation state
    }
  };

  const lifecycleSteps = [
    {
      icon: Sparkles,
      label: "Remember",
      description: "Ingest repo data into Cognee knowledge graph",
      color: "var(--accent-blue)",
      status: status === "ready" || status === "processing_memory"
        ? "complete"
        : status === "ingesting"
          ? "active"
          : "pending",
    },
    {
      icon: Search,
      label: "Recall",
      description: "Query memory for contextual AI responses",
      color: "var(--accent-cyan)",
      status: status === "ready" ? "complete" : status === "processing_memory" ? "active" : "pending",
    },
    {
      icon: ThumbsUp,
      label: "Improve",
      description: "Feed user ratings back to improve retrieval",
      color: "var(--accent-green)",
      status: status === "ready" ? "active" : "pending",
    },
    {
      icon: Trash2,
      label: "Forget",
      description: "Remove all memory for this repository",
      color: "var(--accent-red)",
      status: "available",
    },
  ];

  return (
    <GlassCard>
      <div className="flex items-center gap-2 mb-4">
        <BrainCircuit size={16} style={{ color: "var(--accent-purple)" }} />
        <h3
          className="text-sm font-semibold"
          style={{ color: "var(--text-primary)" }}
        >
          Memory Lifecycle
        </h3>
        <span
          className="badge text-xs ml-auto"
          style={{
            background:
              status === "ready"
                ? "hsla(152, 69%, 50%, 0.12)"
                : status === "ingesting"
                  ? "hsla(217, 91%, 60%, 0.12)"
                  : status === "processing_memory"
                    ? "hsla(190, 80%, 55%, 0.12)"
                    : status === "failed"
                      ? "hsla(0, 72%, 55%, 0.12)"
                      : "hsla(225, 10%, 55%, 0.12)",
            color:
              status === "ready"
                ? "var(--accent-green)"
                : status === "ingesting"
                  ? "var(--accent-blue)"
                  : status === "processing_memory"
                    ? "var(--accent-cyan)"
                    : status === "failed"
                      ? "var(--accent-red)"
                      : "var(--text-secondary)",
          }}
        >
          {status}
        </span>
      </div>

      {/* Lifecycle visual */}
      <div className="flex items-center gap-2 mb-4">
        {lifecycleSteps.map((step, i) => (
          <div key={step.label} className="flex items-center gap-2">
            <div
              className="w-8 h-8 rounded-lg flex items-center justify-center flex-shrink-0"
              style={{
                background:
                  step.status === "complete"
                    ? `${step.color}20`
                    : step.status === "active"
                      ? `${step.color}15`
                      : "var(--bg-tertiary)",
                color:
                  step.status === "complete" || step.status === "active"
                    ? step.color
                    : "var(--text-tertiary)",
                border:
                  step.status === "active"
                    ? `1px solid ${step.color}40`
                    : "1px solid transparent",
              }}
              title={`${step.label}: ${step.description}`}
            >
              <step.icon size={14} />
            </div>
            {i < lifecycleSteps.length - 1 && (
              <div
                className="w-6 h-px"
                style={{
                  background:
                    step.status === "complete"
                      ? step.color
                      : "var(--border)",
                }}
              />
            )}
          </div>
        ))}
      </div>

      <div className="text-xs mb-4" style={{ color: "var(--text-secondary)" }}>
        {lifecycleSteps.map((step) => (
          <div key={step.label} className="flex items-center gap-2 py-0.5">
            <span className="font-medium w-16" style={{ color: step.color }}>
              {step.label}
            </span>
            <span>{step.description}</span>
          </div>
        ))}
      </div>

      {/* Action buttons */}
      <div className="flex gap-2">
        {status === "ready" && onReIngest && (
          <button
            onClick={onReIngest}
            className="btn-secondary text-xs py-1.5 px-3"
          >
            <RefreshCcw size={12} />
            Re-Ingest
          </button>
        )}

        {!showForgetConfirm ? (
          <button
            onClick={() => setShowForgetConfirm(true)}
            className="btn-ghost text-xs py-1.5 px-3"
            style={{ color: "var(--accent-red)" }}
            disabled={status === "pending"}
          >
            <Trash2 size={12} />
            Forget All
          </button>
        ) : (
          <div className="flex items-center gap-2">
            <span className="text-xs" style={{ color: "var(--accent-red)" }}>
              Delete all memory?
            </span>
            <button
              onClick={handleForget}
              disabled={forgetMutation.isPending}
              className="btn-ghost text-xs py-1 px-2"
              style={{
                color: "white",
                background: "var(--accent-red)",
                borderRadius: "var(--radius-sm)",
              }}
            >
              {forgetMutation.isPending ? (
                <Loader2 size={12} className="animate-spin" />
              ) : (
                "Confirm"
              )}
            </button>
            <button
              onClick={() => setShowForgetConfirm(false)}
              className="btn-ghost text-xs py-1 px-2"
            >
              Cancel
            </button>
          </div>
        )}
      </div>

      {forgetMutation.error && (
        <div
          className="mt-2 text-xs"
          style={{ color: "var(--accent-red)" }}
        >
          Failed to forget: {(forgetMutation.error as Error).message}
        </div>
      )}
    </GlassCard>
  );
}
