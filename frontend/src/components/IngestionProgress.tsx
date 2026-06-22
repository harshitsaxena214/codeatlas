"use client";

import { useEffect, useRef, useState } from "react";
import {
  FileText,
  Bug,
  GitPullRequest,
  MessageSquare,
  Users,
  BrainCircuit,
  Check,
  X,
  Loader2,
} from "lucide-react";
import { IngestionProgressEvent } from "@/lib/api";

const stepConfig: Record<
  string,
  { icon: typeof FileText; label: string; color: string }
> = {
  readme: {
    icon: FileText,
    label: "README",
    color: "var(--accent-blue)",
  },
  issues: {
    icon: Bug,
    label: "Issues",
    color: "var(--accent-orange)",
  },
  pull_requests: {
    icon: GitPullRequest,
    label: "Pull Requests",
    color: "var(--accent-green)",
  },
  discussions: {
    icon: MessageSquare,
    label: "Discussions",
    color: "var(--accent-cyan)",
  },
  contributors: {
    icon: Users,
    label: "Contributors",
    color: "var(--accent-purple)",
  },
  memory_graph: {
    icon: BrainCircuit,
    label: "Memory Graph",
    color: "var(--accent-pink)",
  },
};

interface IngestionProgressProps {
  repoId: string;
  onComplete?: () => void;
}

export function IngestionProgress({ repoId, onComplete }: IngestionProgressProps) {
  const [events, setEvents] = useState<IngestionProgressEvent[]>([]);
  const [progress, setProgress] = useState(0);
  const [isComplete, setIsComplete] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const eventSourceRef = useRef<EventSource | null>(null);

  useEffect(() => {
    const apiBase = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
    const es = new EventSource(
      `${apiBase}/api/repositories/${repoId}/ingestion-stream`
    );
    eventSourceRef.current = es;

    es.onmessage = (event) => {
      try {
        const data: IngestionProgressEvent = JSON.parse(event.data);
        setEvents((prev) => [...prev, data]);
        setProgress(data.progress);

        if (data.step === "complete") {
          setIsComplete(true);
          es.close();
          onComplete?.();
        } else if (data.step === "error") {
          setError(data.message);
          es.close();
        }
      } catch {
        // ignore parse errors
      }
    };

    es.onerror = () => {
      es.close();
    };

    return () => {
      es.close();
    };
  }, [repoId, onComplete]);

  // Build step statuses from events
  const stepStatuses: Record<string, { status: string; message: string }> = {};
  for (const ev of events) {
    if (ev.step in stepConfig) {
      stepStatuses[ev.step] = { status: ev.status, message: ev.message };
    }
  }

  return (
    <div className="glass-card p-6">
      {/* Overall progress */}
      <div className="flex items-center justify-between mb-2">
        <h3
          className="text-sm font-medium"
          style={{ color: "var(--text-primary)" }}
        >
          {isComplete
            ? "🎉 Analysis Complete!"
            : error
              ? "❌ Analysis Failed"
              : "Analyzing Repository..."}
        </h3>
        <span
          className="text-xs font-mono"
          style={{ color: "var(--text-secondary)" }}
        >
          {progress}%
        </span>
      </div>

      <div className="progress-bar mb-6">
        <div className="progress-bar-fill" style={{ width: `${progress}%` }} />
      </div>

      {/* Step list */}
      <div className="flex flex-col gap-3">
        {Object.entries(stepConfig).map(([key, config]) => {
          const stepStatus = stepStatuses[key];
          const Icon = config.icon;
          const StatusIcon = stepStatus
            ? stepStatus.status === "completed"
              ? Check
              : stepStatus.status === "failed"
                ? X
                : Loader2
            : null;

          return (
            <div key={key} className="flex items-center gap-3">
              <div
                className="w-8 h-8 rounded-lg flex items-center justify-center flex-shrink-0"
                style={{
                  background: stepStatus
                    ? `${config.color}20`
                    : "var(--bg-tertiary)",
                  color: stepStatus ? config.color : "var(--text-tertiary)",
                }}
              >
                <Icon size={16} />
              </div>
              <div className="flex-1 min-w-0">
                <div
                  className="text-sm font-medium"
                  style={{
                    color: stepStatus
                      ? "var(--text-primary)"
                      : "var(--text-tertiary)",
                  }}
                >
                  {config.label}
                </div>
                {stepStatus && (
                  <div
                    className="text-xs truncate"
                    style={{ color: "var(--text-secondary)" }}
                  >
                    {stepStatus.message}
                  </div>
                )}
              </div>
              {StatusIcon && (
                <StatusIcon
                  size={16}
                  className={
                    stepStatus?.status === "running" ? "animate-spin" : ""
                  }
                  style={{
                    color:
                      stepStatus?.status === "completed"
                        ? "var(--accent-green)"
                        : stepStatus?.status === "failed"
                          ? "var(--accent-red)"
                          : "var(--accent-blue)",
                  }}
                />
              )}
            </div>
          );
        })}
      </div>

      {error && (
        <div
          className="mt-4 p-3 rounded-lg text-sm"
          style={{
            background: "hsla(0, 72%, 55%, 0.1)",
            color: "var(--accent-red)",
          }}
        >
          {error}
        </div>
      )}
    </div>
  );
}
