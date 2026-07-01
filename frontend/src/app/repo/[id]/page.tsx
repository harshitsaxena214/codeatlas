"use client";

import { useParams, useRouter } from "next/navigation";
import { useQuery } from "@tanstack/react-query";
import Link from "next/link";
import {
  Star,
  GitFork,
  Bug,
  BrainCircuit,
  BookOpen,
  Target,
  Lightbulb,
  MessageSquare,
  GitPullRequest,
  Timer,
  GraduationCap,
  ArrowRight,
  Layers,
} from "lucide-react";
import { api } from "@/lib/api";
import { StatsCard } from "@/components/StatsCard";
import { GlassCard } from "@/components/GlassCard";
import { MemoryLifecycle } from "@/components/MemoryLifecycle";
import { PageSkeleton } from "@/components/LoadingSkeleton";

const featureCards = [
  {
    href: "onboarding",
    icon: BookOpen,
    title: "Onboarding Guide",
    description: "Step-by-step guide for new contributors",
    color: "var(--accent-green)",
  },
  {
    href: "find-issue",
    icon: Target,
    title: "Find My First Issue",
    description: "AI-matched issues based on your skills",
    color: "var(--accent-orange)",
  },
  {
    href: "maintainer-brain",
    icon: BrainCircuit,
    title: "Maintainer Brain",
    description: "Understand maintainer preferences",
    color: "var(--accent-purple)",
  },
  {
    href: "decisions",
    icon: Lightbulb,
    title: "Decision Explorer",
    description: "Discover why decisions were made",
    color: "var(--accent-yellow)",
  },
  {
    href: "ask",
    icon: MessageSquare,
    title: "Repository Q&A",
    description: "Ask anything about this repo",
    color: "var(--accent-cyan)",
  },
  {
    href: "architecture",
    icon: Layers,
    title: "Architecture Explorer",
    description: "Analyze high-level design",
    color: "var(--accent-purple)",
  },
  {
    href: "graph",
    icon: GitPullRequest,
    title: "Knowledge Graph",
    description: "Visualize entity relationships",
    color: "var(--accent-pink)",
  },
  {
    href: "timeline",
    icon: Timer,
    title: "Timeline",
    description: "Project evolution and milestones",
    color: "var(--accent-blue)",
  },
  {
    href: "learn",
    icon: GraduationCap,
    title: "Learning Path",
    description: "Personalized learning journey",
    color: "var(--accent-green)",
  },
];

export default function RepoDashboard() {
  const params = useParams();
  const router = useRouter();
  const repoId = params.id as string;

  const { data: dashboard, isLoading } = useQuery({
    queryKey: ["dashboard", repoId],
    queryFn: () => api.getRepositoryDashboard(repoId),
    enabled: !!repoId,
  });

  if (isLoading || !dashboard) return <PageSkeleton />;

  return (
    <div className="p-6 max-w-6xl mx-auto">
      {/* Header */}
      <div className="mb-8 animate-fade-in">
        <div className="flex items-center gap-2 mb-1">
          <span className="text-sm" style={{ color: "var(--text-secondary)" }}>
            {dashboard.owner}
          </span>
          <span style={{ color: "var(--text-tertiary)" }}>/</span>
          <h1 className="text-2xl font-bold gradient-text">
            {dashboard.name}
          </h1>
        </div>
        {dashboard.description && (
          <p
            className="text-sm mt-1 max-w-2xl"
            style={{ color: "var(--text-secondary)" }}
          >
            {dashboard.description}
          </p>
        )}
        {dashboard.topics.length > 0 && (
          <div className="flex flex-wrap gap-1.5 mt-3">
            {dashboard.topics.slice(0, 8).map((topic) => (
              <span key={topic} className="badge badge-blue text-xs">
                {topic}
              </span>
            ))}
          </div>
        )}
      </div>

      {/* Stats */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mb-8">
        <StatsCard
          label="Stars"
          value={dashboard.stars}
          icon={Star}
          color="var(--accent-yellow)"
          delay={0}
        />
        <StatsCard
          label="Forks"
          value={dashboard.forks}
          icon={GitFork}
          color="var(--accent-blue)"
          delay={100}
        />
        <StatsCard
          label="Open Issues"
          value={dashboard.open_issues}
          icon={Bug}
          color="var(--accent-orange)"
          delay={200}
        />
        <StatsCard
          label="Memory Nodes"
          value={dashboard.memory_nodes}
          icon={BrainCircuit}
          color="var(--accent-purple)"
          delay={300}
        />
      </div>

      {/* Memory Lifecycle Controls */}
      <div className="mb-8 animate-fade-in-up delay-400">
        <MemoryLifecycle
          repoId={repoId}
          status={dashboard.status}
          onReIngest={() => router.push(`/analyze?repo=${repoId}`)}
          onForgetComplete={() => router.push("/dashboard")}
        />
      </div>

      {/* Feature cards */}
      <h2
        className="text-lg font-semibold mb-4"
        style={{ color: "var(--text-primary)" }}
      >
        AI Features
      </h2>
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-3">
        {featureCards.map((feature, i) => (
          <Link
            key={feature.href}
            href={`/repo/${repoId}/${feature.href}`}
            className="glass-card-hover p-4 flex flex-col animate-fade-in-up group"
            style={{ animationDelay: `${i * 50}ms` }}
          >
            <div className="flex items-center justify-between mb-3">
              <div
                className="w-9 h-9 rounded-xl flex items-center justify-center"
                style={{
                  background: `${feature.color}15`,
                  color: feature.color,
                }}
              >
                <feature.icon size={18} />
              </div>
              <ArrowRight
                size={14}
                className="opacity-0 group-hover:opacity-100 transition-opacity"
                style={{ color: "var(--text-tertiary)" }}
              />
            </div>
            <h3
              className="text-sm font-semibold mb-1"
              style={{ color: "var(--text-primary)" }}
            >
              {feature.title}
            </h3>
            <p className="text-xs" style={{ color: "var(--text-secondary)" }}>
              {feature.description}
            </p>
          </Link>
        ))}
      </div>

      {/* Quick info */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mt-8">
        <GlassCard className="animate-fade-in-up delay-200">
          <h3
            className="text-sm font-semibold mb-3"
            style={{ color: "var(--text-primary)" }}
          >
            Repository Info
          </h3>
          <div className="flex flex-col gap-2 text-sm">
            <div className="flex justify-between">
              <span style={{ color: "var(--text-secondary)" }}>Language</span>
              <span style={{ color: "var(--text-primary)" }}>
                {dashboard.language || "N/A"}
              </span>
            </div>
            <div className="flex justify-between">
              <span style={{ color: "var(--text-secondary)" }}>Branch</span>
              <span className="font-mono text-xs" style={{ color: "var(--text-primary)" }}>
                {dashboard.default_branch}
              </span>
            </div>
            <div className="flex justify-between">
              <span style={{ color: "var(--text-secondary)" }}>Status</span>
              <span
                className="badge text-xs"
                style={{
                  background: "hsla(152, 69%, 50%, 0.12)",
                  color: "var(--accent-green)",
                }}
              >
                {dashboard.status}
              </span>
            </div>
            {dashboard.ingested_at && (
              <div className="flex justify-between">
                <span style={{ color: "var(--text-secondary)" }}>Analyzed</span>
                <span style={{ color: "var(--text-primary)" }}>
                  {new Date(dashboard.ingested_at).toLocaleDateString()}
                </span>
              </div>
            )}
          </div>
        </GlassCard>

        <GlassCard className="animate-fade-in-up delay-300">
          <h3
            className="text-sm font-semibold mb-3"
            style={{ color: "var(--text-primary)" }}
          >
            Memory Stats
          </h3>
          <div className="flex flex-col gap-2 text-sm">
            <div className="flex justify-between">
              <span style={{ color: "var(--text-secondary)" }}>Knowledge Nodes</span>
              <span style={{ color: "var(--text-primary)" }}>
                {dashboard.memory_nodes}
              </span>
            </div>
            <div className="flex justify-between">
              <span style={{ color: "var(--text-secondary)" }}>Relationships</span>
              <span style={{ color: "var(--text-primary)" }}>
                {dashboard.memory_relationships}
              </span>
            </div>
            <div className="flex justify-between">
              <span style={{ color: "var(--text-secondary)" }}>Contributors</span>
              <span style={{ color: "var(--text-primary)" }}>
                {dashboard.contributor_count}
              </span>
            </div>
          </div>
        </GlassCard>
      </div>
    </div>
  );
}
