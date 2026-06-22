"use client";

import { useState } from "react";
import { ThumbsUp, ThumbsDown, Check } from "lucide-react";
import { api } from "@/lib/api";

interface FeedbackButtonsProps {
  repoId: string;
  feature: string;
  query: string;
  responseSummary: string;
}

export function FeedbackButtons({
  repoId,
  feature,
  query,
  responseSummary,
}: FeedbackButtonsProps) {
  const [submitted, setSubmitted] = useState<"helpful" | "not_helpful" | null>(
    null
  );
  const [loading, setLoading] = useState(false);

  const handleFeedback = async (rating: "helpful" | "not_helpful") => {
    if (submitted || loading) return;
    setLoading(true);
    try {
      await api.submitFeedback(repoId, {
        feature,
        query,
        response_summary: responseSummary.slice(0, 500),
        rating,
      });
      setSubmitted(rating);
    } catch {
      // Non-blocking
    }
    setLoading(false);
  };

  if (submitted) {
    return (
      <div
        className="flex items-center gap-2 text-xs py-1"
        style={{ color: "var(--accent-green)" }}
      >
        <Check size={14} />
        Thanks for the feedback!
      </div>
    );
  }

  return (
    <div className="flex items-center gap-2">
      <span className="text-xs" style={{ color: "var(--text-tertiary)" }}>
        Was this helpful?
      </span>
      <button
        onClick={() => handleFeedback("helpful")}
        disabled={loading}
        className="p-1.5 rounded-md transition-all hover:bg-[hsla(152,69%,50%,0.1)]"
        style={{ color: "var(--text-secondary)" }}
        title="Helpful"
      >
        <ThumbsUp size={14} />
      </button>
      <button
        onClick={() => handleFeedback("not_helpful")}
        disabled={loading}
        className="p-1.5 rounded-md transition-all hover:bg-[hsla(0,72%,55%,0.1)]"
        style={{ color: "var(--text-secondary)" }}
        title="Not helpful"
      >
        <ThumbsDown size={14} />
      </button>
    </div>
  );
}
