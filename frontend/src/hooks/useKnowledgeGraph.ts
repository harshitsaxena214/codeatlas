"use client";

import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";

/**
 * Hook for fetching knowledge graph data (Feature 7).
 * Returns nodes and edges formatted for React Flow.
 */
export function useKnowledgeGraph(repoId: string | undefined) {
  return useQuery({
    queryKey: ["knowledge-graph", repoId],
    queryFn: () => api.getKnowledgeGraph(repoId!),
    enabled: !!repoId,
  });
}
