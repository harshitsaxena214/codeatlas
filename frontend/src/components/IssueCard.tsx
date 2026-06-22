"use client";

import Link from "next/link";
import { ExternalLink, Gauge, Clock, FileCode } from "lucide-react";
import { RecommendedIssue } from "@/lib/api";

interface IssueCardProps {
  issue: RecommendedIssue;
  repoId: string;
  index?: number;
}

/**
 * IssueCard — Displays a recommended issue with difficulty, time estimate, and relevant files.
 * Links to the Contribution Assistant for detailed analysis.
 */
export function IssueCard({ issue, repoId, index = 0 }: IssueCardProps) {
  const difficultyColor =
    issue.difficulty_score <= 3
      ? "var(--accent-green)"
      : issue.difficulty_score <= 6
        ? "var(--accent-yellow)"
        : "var(--accent-red)";

  return (
    <div
      className="glass-card-hover p-5 animate-fade-in-up"
      style={{ animationDelay: `${index * 100}ms` }}
    >
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
          <ExternalLink
            size={14}
            style={{ color: "var(--text-secondary)" }}
          />
        </a>
      </div>

      <p className="text-sm mb-3" style={{ color: "var(--text-secondary)" }}>
        {issue.why_it_matches}
      </p>

      <div className="grid grid-cols-3 gap-3 mb-3">
        <div
          className="flex items-center gap-1.5 text-xs"
          style={{ color: "var(--text-tertiary)" }}
        >
          <Gauge size={12} style={{ color: difficultyColor }} />
          Difficulty: {issue.difficulty_score}/10
        </div>
        <div
          className="flex items-center gap-1.5 text-xs"
          style={{ color: "var(--text-tertiary)" }}
        >
          <Clock size={12} />
          {issue.estimated_time}
        </div>
        <div
          className="flex items-center gap-1.5 text-xs"
          style={{ color: "var(--text-tertiary)" }}
        >
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
  );
}
