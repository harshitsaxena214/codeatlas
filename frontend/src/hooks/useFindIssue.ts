"use client";

import { useMutation } from "@tanstack/react-query";
import { api } from "@/lib/api";

/**
 * Hook for finding the best first issue for a contributor (Feature 2).
 * Uses mutation since it takes user input (experience + interest).
 */
export function useFindIssue(repoId: string) {
  return useMutation({
    mutationFn: ({
      experience_level,
      interest,
    }: {
      experience_level: string;
      interest: string;
    }) => api.findFirstIssue(repoId, experience_level, interest),
  });
}

/**
 * Hook for analyzing a specific issue (Feature 3: Contribution Assistant).
 */
export function useAnalyzeIssue(repoId: string, issueNumber: number) {
  return useMutation({
    mutationFn: () => api.analyzeIssue(repoId, issueNumber),
  });
}
