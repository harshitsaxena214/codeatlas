"use client";

import Link from "next/link";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import {
  Star,
  GitFork,
  Code,
  ArrowRight,
  Trash2,
  Loader2,
} from "lucide-react";
import { api, RepositoryListItem } from "@/lib/api";

const statusColors: Record<string, { bg: string; text: string; label: string }> = {
  ready: {
    bg: "hsla(152, 69%, 50%, 0.12)",
    text: "var(--accent-green)",
    label: "Ready",
  },
  ingesting: {
    bg: "hsla(217, 91%, 60%, 0.12)",
    text: "var(--accent-blue)",
    label: "Ingesting…",
  },
  pending: {
    bg: "hsla(225, 10%, 55%, 0.12)",
    text: "var(--text-secondary)",
    label: "Pending",
  },
  failed: {
    bg: "hsla(0, 72%, 55%, 0.12)",
    text: "var(--accent-red)",
    label: "Failed",
  },
};

interface RepoCardProps {
  repo: RepositoryListItem;
}

/**
 * RepoCard — Repository summary card for list views.
 * Shows basic metadata, status badge, and hover actions.
 */
export function RepoCard({ repo }: RepoCardProps) {
  const queryClient = useQueryClient();
  const deleteMutation = useMutation({
    mutationFn: () => api.deleteRepository(repo.id),
    onSuccess: () =>
      queryClient.invalidateQueries({ queryKey: ["repositories"] }),
  });

  const status = statusColors[repo.status] || statusColors.pending;

  return (
    <div className="glass-card-hover p-5 relative group">
      <div className="flex items-start justify-between mb-3">
        <div className="flex-1 min-w-0">
          <Link
            href={
              repo.status === "ready"
                ? `/repo/${repo.id}`
                : `/analyze?repo=${repo.id}`
            }
            className="text-base font-semibold hover:opacity-80 transition-opacity"
            style={{ color: "var(--text-primary)" }}
          >
            {repo.owner}/
            <span className="gradient-text">{repo.name}</span>
          </Link>
        </div>
        <div
          className="badge text-xs ml-2 flex-shrink-0"
          style={{ background: status.bg, color: status.text }}
        >
          {status.label}
        </div>
      </div>

      {repo.description && (
        <p
          className="text-sm mb-4 line-clamp-2"
          style={{ color: "var(--text-secondary)" }}
        >
          {repo.description}
        </p>
      )}

      <div
        className="flex items-center gap-4 text-xs"
        style={{ color: "var(--text-tertiary)" }}
      >
        <span className="flex items-center gap-1">
          <Star size={12} />
          {repo.stars.toLocaleString()}
        </span>
        <span className="flex items-center gap-1">
          <GitFork size={12} />
          {repo.forks.toLocaleString()}
        </span>
        {repo.language && (
          <span className="flex items-center gap-1">
            <Code size={12} />
            {repo.language}
          </span>
        )}
      </div>

      {/* Actions on hover */}
      <div className="absolute top-3 right-3 opacity-0 group-hover:opacity-100 transition-opacity flex gap-1">
        {repo.status === "ready" && (
          <Link
            href={`/repo/${repo.id}`}
            className="p-1.5 rounded-md hover:bg-[var(--bg-tertiary)]"
            title="Open dashboard"
          >
            <ArrowRight
              size={14}
              style={{ color: "var(--text-secondary)" }}
            />
          </Link>
        )}
        <button
          onClick={() => deleteMutation.mutate()}
          className="p-1.5 rounded-md hover:bg-[hsla(0,72%,55%,0.1)]"
          title="Delete"
          disabled={deleteMutation.isPending}
        >
          {deleteMutation.isPending ? (
            <Loader2
              size={14}
              className="animate-spin"
              style={{ color: "var(--accent-red)" }}
            />
          ) : (
            <Trash2
              size={14}
              style={{ color: "var(--text-tertiary)" }}
            />
          )}
        </button>
      </div>
    </div>
  );
}
