"use client";

import { useEffect, useRef, useState, useCallback } from "react";
import { useMutation, useQuery } from "@tanstack/react-query";
import { api, IngestionProgressEvent } from "@/lib/api";

/**
 * Hook for starting the ingestion pipeline.
 */
export function useStartIngestion() {
  return useMutation({
    mutationFn: (id: string) => api.startIngestion(id),
  });
}

/**
 * Hook for polling ingestion status.
 */
export function useIngestionStatus(repoId: string | undefined, enabled = true) {
  return useQuery({
    queryKey: ["ingestion-status", repoId],
    queryFn: () => api.getIngestionStatus(repoId!),
    enabled: !!repoId && enabled,
    refetchInterval: 2000, // Poll every 2 seconds while active
  });
}

/**
 * Hook for SSE-based real-time ingestion progress streaming.
 * Returns the accumulated events, current progress, and completion state.
 */
export function useIngestionStream(
  repoId: string | undefined,
  onComplete?: () => void
) {
  const [events, setEvents] = useState<IngestionProgressEvent[]>([]);
  const [progress, setProgress] = useState(0);
  const [isComplete, setIsComplete] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const eventSourceRef = useRef<EventSource | null>(null);
  const onCompleteRef = useRef(onComplete);

  useEffect(() => {
    onCompleteRef.current = onComplete;
  }, [onComplete]);

  useEffect(() => {
    if (!repoId) return;

    const apiBase = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
    const es = new EventSource(
      `${apiBase}/api/repositories/${repoId}/ingestion-stream`
    );
    eventSourceRef.current = es;

    es.onmessage = (event) => {
      try {
        const data: IngestionProgressEvent = JSON.parse(event.data);
        setEvents((prev) => [...prev, data]);
        setProgress(data.progress);

        if (data.step === "complete") {
          setIsComplete(true);
          es.close();
          onCompleteRef.current?.();
        } else if (data.step === "error") {
          setError(data.message);
          es.close();
        }
      } catch {
        // ignore parse errors
      }
    };

    es.onerror = () => {
      es.close();
    };

    return () => {
      es.close();
    };
  }, [repoId]);

  const reset = useCallback(() => {
    setEvents([]);
    setProgress(0);
    setIsComplete(false);
    setError(null);
  }, []);

  return { events, progress, isComplete, error, reset };
}

/**
 * Hook for forgetting (deleting) all Cognee memory for a repository.
 */
export function useForgetMemory() {
  return useMutation({
    mutationFn: (id: string) => api.forgetMemory(id),
  });
}
