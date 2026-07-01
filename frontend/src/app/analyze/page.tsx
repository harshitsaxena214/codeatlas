"use client";

import { useState, Suspense } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { useMutation } from "@tanstack/react-query";
import Link from "next/link";
import {
  Sparkles,
  Zap,
  ArrowRight,
  Code,
  Loader2,
  AlertCircle,
} from "lucide-react";
import { useSession } from "next-auth/react";
import { api } from "@/lib/api";
import { IngestionProgress } from "@/components/IngestionProgress";

function AnalyzeContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const existingRepoId = searchParams.get("repo");

  const [url, setUrl] = useState("");
  const [repoId, setRepoId] = useState<string | null>(existingRepoId);
  const [phase, setPhase] = useState<"input" | "ingesting" | "done">(
    existingRepoId ? "ingesting" : "input"
  );

  const { data: session } = useSession();

  const createMutation = useMutation({
    mutationFn: (github_url: string) => api.createRepository(github_url, session?.user?.backendId),
    onSuccess: (repo) => {
      setRepoId(repo.id);
      if (repo.status === "ready") {
        router.push(`/repo/${repo.id}`);
        return;
      }
      startIngestion.mutate(repo.id);
    },
  });

  const startIngestion = useMutation({
    mutationFn: (id: string) => api.startIngestion(id),
    onSuccess: () => {
      setPhase("ingesting");
    },
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!url.trim()) return;
    createMutation.mutate(url.trim());
  };

  const handleIngestionComplete = () => {
    setPhase("done");
    setTimeout(() => {
      if (repoId) router.push(`/repo/${repoId}`);
    }, 1500);
  };

  const isLoading = createMutation.isPending || startIngestion.isPending;
  const error = createMutation.error || startIngestion.error;

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
        <Link href="/dashboard" className="btn-ghost text-sm">
          Dashboard
        </Link>
      </header>

      <div className="max-w-xl mx-auto px-6 py-16">
        {phase === "input" && (
          <div className="animate-fade-in-up">
            <div className="text-center mb-10">
              <div
                className="w-14 h-14 rounded-2xl flex items-center justify-center mx-auto mb-4"
                style={{ background: "var(--gradient-primary)" }}
              >
                <Zap size={24} color="white" />
              </div>
              <h1
                className="text-2xl font-bold mb-2"
                style={{ color: "var(--text-primary)" }}
              >
                Analyze a Repository
              </h1>
              <p className="text-sm" style={{ color: "var(--text-secondary)" }}>
                Paste a GitHub repository URL to begin AI-powered analysis
              </p>
            </div>

            <form onSubmit={handleSubmit} className="flex flex-col gap-4">
              <div className="relative">
                <Code
                  size={18}
                  className="absolute left-4 top-1/2 -translate-y-1/2"
                  style={{ color: "var(--text-tertiary)" }}
                />
                <input
                  type="url"
                  value={url}
                  onChange={(e) => setUrl(e.target.value)}
                  placeholder="https://github.com/owner/repository"
                  className="input-field pl-12 py-3.5 text-base"
                  autoFocus
                  required
                />
              </div>
              <button
                type="submit"
                disabled={isLoading || !url.trim()}
                className="btn-primary py-3.5 text-base rounded-xl"
              >
                {isLoading ? (
                  <>
                    <Loader2 size={18} className="animate-spin" />
                    Analyzing...
                  </>
                ) : (
                  <>
                    <Zap size={18} />
                    Start Analysis
                  </>
                )}
              </button>
            </form>

            {error && (
              <div
                className="mt-4 p-3 rounded-lg flex items-center gap-2 text-sm"
                style={{
                  background: "hsla(0, 72%, 55%, 0.1)",
                  color: "var(--accent-red)",
                }}
              >
                <AlertCircle size={16} />
                {(error as Error).message}
              </div>
            )}

            {/* Example repos */}
            <div className="mt-10">
              <p
                className="text-xs font-medium mb-3"
                style={{ color: "var(--text-tertiary)" }}
              >
                TRY THESE
              </p>
              <div className="flex flex-wrap gap-2">
                {[
                  "https://github.com/facebook/react",
                  "https://github.com/vercel/next.js",
                  "https://github.com/topoteretes/cognee",
                ].map((example) => (
                  <button
                    key={example}
                    onClick={() => setUrl(example)}
                    className="badge text-xs py-1.5 px-3 cursor-pointer transition-all"
                    style={{
                      background: "var(--bg-tertiary)",
                      color: "var(--text-secondary)",
                      border: "1px solid var(--border)",
                    }}
                  >
                    {example.replace("https://github.com/", "")}
                  </button>
                ))}
              </div>
            </div>
          </div>
        )}

        {phase === "ingesting" && repoId && (
          <div className="animate-fade-in-up">
            <IngestionProgress
              repoId={repoId}
              onComplete={handleIngestionComplete}
            />
          </div>
        )}

        {phase === "done" && (
          <div className="text-center animate-scale-in">
            <div
              className="w-16 h-16 rounded-full flex items-center justify-center mx-auto mb-4"
              style={{
                background: "hsla(152, 69%, 50%, 0.15)",
                color: "var(--accent-green)",
              }}
            >
              <Sparkles size={28} />
            </div>
            <h2
              className="text-xl font-bold mb-2"
              style={{ color: "var(--text-primary)" }}
            >
              Analysis Complete!
            </h2>
            <p className="text-sm mb-6" style={{ color: "var(--text-secondary)" }}>
              Redirecting to your repository dashboard...
            </p>
            {repoId && (
              <Link
                href={`/repo/${repoId}`}
                className="btn-primary"
              >
                Open Dashboard
                <ArrowRight size={14} />
              </Link>
            )}
          </div>
        )}
      </div>
    </div>
  );
}

export default function AnalyzePage() {
  return (
    <Suspense fallback={<div className="flex h-screen items-center justify-center"><Loader2 className="animate-spin text-zinc-500" /></div>}>
      <AnalyzeContent />
    </Suspense>
  );
}
