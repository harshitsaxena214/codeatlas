"use client";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import Link from "next/link";
import { useRouter } from "next/navigation";
import {
  Star,
  GitFork,
  Code,
  ArrowRight,
  Plus,
  Trash2,
  Sparkles,
  Loader2,
} from "lucide-react";
import { api, RepositoryListItem } from "@/lib/api";
import { CardSkeleton } from "@/components/LoadingSkeleton";

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

function RepoCard({ repo }: { repo: RepositoryListItem }) {
  const queryClient = useQueryClient();
  const deleteMutation = useMutation({
    mutationFn: () => api.deleteRepository(repo.id),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["repositories"] }),
  });

  const status = statusColors[repo.status] || statusColors.pending;

  return (
    <div className="glass-card-hover p-5 relative group">
      <div className="flex items-start justify-between mb-3">
        <div className="flex-1 min-w-0">
          <Link
            href={repo.status === "ready" ? `/repo/${repo.id}` : `/analyze?repo=${repo.id}`}
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

      <div className="flex items-center gap-4 text-xs" style={{ color: "var(--text-tertiary)" }}>
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
            <ArrowRight size={14} style={{ color: "var(--text-secondary)" }} />
          </Link>
        )}
        <button
          onClick={() => deleteMutation.mutate()}
          className="p-1.5 rounded-md hover:bg-[hsla(0,72%,55%,0.1)]"
          title="Delete"
          disabled={deleteMutation.isPending}
        >
          {deleteMutation.isPending ? (
            <Loader2 size={14} className="animate-spin" style={{ color: "var(--accent-red)" }} />
          ) : (
            <Trash2 size={14} style={{ color: "var(--text-tertiary)" }} />
          )}
        </button>
      </div>
    </div>
  );
}

export default function DashboardPage() {
  const router = useRouter();
  const { data: repos, isLoading } = useQuery({
    queryKey: ["repositories"],
    queryFn: api.listRepositories,
  });

  return (
    <div className="min-h-screen" style={{ background: "var(--bg-primary)" }}>
      {/* Header */}
      <header
        className="flex items-center justify-between px-6 py-4"
        style={{ borderBottom: "1px solid var(--border)" }}
      >
        <Link href="/" className="flex items-center gap-2.5">
          <div
            className="w-8 h-8 rounded-lg flex items-center justify-center"
            style={{ background: "var(--gradient-primary)" }}
          >
            <Sparkles size={16} color="white" />
          </div>
          <span className="text-lg font-bold" style={{ color: "var(--text-primary)" }}>
            CodeAtlas
          </span>
        </Link>
        <button
          onClick={() => router.push("/analyze")}
          className="btn-primary text-sm"
        >
          <Plus size={14} />
          Analyze Repo
        </button>
      </header>

      <div className="max-w-5xl mx-auto px-6 py-10">
        <h1
          className="text-2xl font-bold mb-1 animate-fade-in"
          style={{ color: "var(--text-primary)" }}
        >
          Your Repositories
        </h1>
        <p
          className="text-sm mb-8 animate-fade-in delay-100"
          style={{ color: "var(--text-secondary)" }}
        >
          Repositories you&apos;ve analyzed with CodeAtlas
        </p>

        {isLoading ? (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {Array.from({ length: 4 }).map((_, i) => (
              <CardSkeleton key={i} />
            ))}
          </div>
        ) : repos && repos.length > 0 ? (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {repos.map((repo, i) => (
              <div
                key={repo.id}
                className="animate-fade-in-up"
                style={{ animationDelay: `${i * 75}ms` }}
              >
                <RepoCard repo={repo} />
              </div>
            ))}
          </div>
        ) : (
          <div className="flex flex-col items-center justify-center py-20 text-center">
            <div
              className="w-16 h-16 rounded-2xl flex items-center justify-center mb-4"
              style={{ background: "var(--bg-tertiary)" }}
            >
              <Sparkles size={28} style={{ color: "var(--text-tertiary)" }} />
            </div>
            <h3
              className="text-lg font-semibold mb-2"
              style={{ color: "var(--text-primary)" }}
            >
              No repositories yet
            </h3>
            <p
              className="text-sm mb-6"
              style={{ color: "var(--text-secondary)" }}
            >
              Analyze your first GitHub repository to get started
            </p>
            <button
              onClick={() => router.push("/analyze")}
              className="btn-primary"
            >
              <Plus size={14} />
              Analyze a Repository
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
