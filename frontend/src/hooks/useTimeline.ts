"use client";

import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";

/**
 * Hook for fetching the project evolution timeline (Feature 8).
 */
export function useTimeline(repoId: string | undefined) {
  return useQuery({
    queryKey: ["timeline", repoId],
    queryFn: () => api.getTimeline(repoId!),
    enabled: !!repoId,
  });
}
