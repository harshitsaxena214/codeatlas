"use client";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api";

/**
 * Hook for fetching a single repository by ID.
 */
export function useRepository(repoId: string | undefined) {
  return useQuery({
    queryKey: ["repository", repoId],
    queryFn: () => api.getRepository(repoId!),
    enabled: !!repoId,
  });
}

/**
 * Hook for fetching repository dashboard data (extended stats).
 */
export function useRepositoryDashboard(repoId: string | undefined) {
  return useQuery({
    queryKey: ["dashboard", repoId],
    queryFn: () => api.getRepositoryDashboard(repoId!),
    enabled: !!repoId,
  });
}

/**
 * Hook for listing all analyzed repositories.
 */
export function useRepositories() {
  return useQuery({
    queryKey: ["repositories"],
    queryFn: api.listRepositories,
  });
}

/**
 * Hook for creating a new repository.
 */
export function useCreateRepository() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (github_url: string) => api.createRepository(github_url),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["repositories"] });
    },
  });
}

/**
 * Hook for deleting a repository.
 */
export function useDeleteRepository() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => api.deleteRepository(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["repositories"] });
    },
  });
}
