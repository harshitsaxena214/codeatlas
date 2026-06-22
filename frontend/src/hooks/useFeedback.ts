"use client";

import { useMutation } from "@tanstack/react-query";
import { api, FeedbackCreate } from "@/lib/api";

/**
 * Hook for submitting feedback on AI responses.
 * Feeds back to Cognee's improve lifecycle.
 */
export function useFeedback(repoId: string) {
  return useMutation({
    mutationFn: (feedback: FeedbackCreate) =>
      api.submitFeedback(repoId, feedback),
  });
}
