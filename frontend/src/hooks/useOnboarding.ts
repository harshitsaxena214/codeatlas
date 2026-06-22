"use client";

import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";

/**
 * Hook for fetching the contributor onboarding guide (Feature 1).
 */
export function useOnboarding(repoId: string | undefined) {
  return useQuery({
    queryKey: ["onboarding", repoId],
    queryFn: () => api.getOnboarding(repoId!),
    enabled: !!repoId,
  });
}
