"use client";

import { useQuery, useMutation } from "@tanstack/react-query";
import { api } from "@/lib/api";

/**
 * Hook for the Maintainer Brain feature (Feature 4).
 */
export function useMaintainerBrain(repoId: string | undefined) {
  return useQuery({
    queryKey: ["maintainer-brain", repoId],
    queryFn: () => api.getMaintainerBrain(repoId!),
    enabled: !!repoId,
  });
}

/**
 * Hook for Decision Explorer (Feature 5).
 * Uses mutation since it takes a user question.
 */
export function useExploreDecision(repoId: string) {
  return useMutation({
    mutationFn: (question: string) => api.exploreDecision(repoId, question),
  });
}

/**
 * Hook for Repository Q&A (Feature 6).
 * Uses mutation since it takes a user question.
 */
export function useAskQuestion(repoId: string) {
  return useMutation({
    mutationFn: (question: string) => api.askQuestion(repoId, question),
  });
}

/**
 * Hook for Contribution Assistant issue analysis (Feature 3).
 */
export function useContributionPlan(
  repoId: string | undefined,
  issueNumber: number | undefined
) {
  return useQuery({
    queryKey: ["analyze-issue", repoId, issueNumber],
    queryFn: () => api.analyzeIssue(repoId!, issueNumber!),
    enabled: !!repoId && issueNumber !== undefined && !isNaN(issueNumber),
  });
}

/**
 * Hook for generating a learning path (Feature 9).
 */
export function useLearningPath(repoId: string) {
  return useMutation({
    mutationFn: ({
      issue_number,
      interests,
    }: {
      issue_number?: number | null;
      interests: string[];
    }) => api.getLearningPath(repoId, issue_number, interests),
  });
}
