/* ═══════════════════════════════════════════
   CodeAtlas — Typed API Client
   All backend endpoints with TypeScript types
   ═══════════════════════════════════════════ */

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export type RepositoryStatus =
  | "pending"
  | "ingesting"
  | "processing_memory"
  | "ready"
  | "failed";

// ─── Types ───

export interface Repository {
  id: string;
  github_url: string;
  owner: string;
  name: string;
  description: string | null;
  stars: number;
  forks: number;
  open_issues: number;
  language: string | null;
  topics: string | null;
  default_branch: string;
  cognee_dataset_name: string;
  status: RepositoryStatus;
  ingested_at: string | null;
  created_at: string;
  user_id: string;
}

export interface RepositoryListItem {
  id: string;
  github_url: string;
  owner: string;
  name: string;
  description: string | null;
  stars: number;
  forks: number;
  language: string | null;
  status: RepositoryStatus;
  created_at: string;
}

export interface RepositoryDashboard {
  id: string;
  owner: string;
  name: string;
  description: string | null;
  stars: number;
  forks: number;
  open_issues: number;
  language: string | null;
  topics: string[];
  default_branch: string;
  status: RepositoryStatus;
  ingested_at: string | null;
  memory_nodes: number;
  memory_relationships: number;
  contributor_count: number;
  pr_count: number;
  discussion_count: number;
  technology_stack: string[];
  contribution_opportunities: number;
  recent_activity: Record<string, unknown>[];
}

export interface IngestionJob {
  id: string;
  step: string;
  status: "pending" | "running" | "completed" | "failed";
  progress: number;
  items_processed: number;
  items_total: number;
  error_message: string | null;
  started_at: string | null;
  completed_at: string | null;
}

export interface IngestionStatus {
  repository_id: string;
  overall_status: string;
  overall_progress: number;
  jobs: IngestionJob[];
}

export interface IngestionProgressEvent {
  step: string;
  status: string;
  progress: number;
  message: string;
  items_processed: number;
  items_total: number;
}

export interface OnboardingStep {
  step_number: number;
  title: string;
  description: string;
  resource_type: string;
  resource_url?: string | null;
  resource_id?: string | null;
}

export interface OnboardingGuide {
  project_summary: string;
  what_it_solves: string;
  core_technologies: string[];
  key_maintainers: string[];
  project_culture: string;
  important_discussions: Record<string, unknown>[];
  important_prs: Record<string, unknown>[];
  reading_path: OnboardingStep[];
}

export interface RecommendedIssue {
  issue_number: number;
  title: string;
  url: string;
  why_it_matches: string;
  difficulty_score: number;
  relevant_files: string[];
  estimated_time: string;
  required_reading: Record<string, unknown>[];
  related_discussions: Record<string, unknown>[];
  related_prs: Record<string, unknown>[];
  labels: string[];
}

export interface FindIssueResponse {
  recommended_issues: RecommendedIssue[];
  reasoning: string;
}

export interface ContributionPlan {
  issue_number: number;
  issue_title: string;
  issue_url: string;
  summary: string;
  difficulty: string;
  difficulty_score: number;
  related_discussions: Record<string, unknown>[];
  related_prs: Record<string, unknown>[];
  related_decisions: Record<string, unknown>[];
  maintainer_expectations: string[];
  suggested_starting_point: string;
  estimated_effort: string;
  potential_challenges: string[];
  recommended_approach: string;
}

export interface MaintainerProfile {
  username: string;
  avatar_url?: string | null;
  review_count: number;
  preferences: string[];
  common_feedback: string[];
}

export interface MaintainerInsights {
  maintainer_profiles: MaintainerProfile[];
  preferences: string[];
  review_patterns: string[];
  contribution_expectations: string[];
  common_rejection_reasons: string[];
  do_list: string[];
  dont_list: string[];
}

export interface DecisionExploration {
  question: string;
  decision_summary: string;
  timeline: Record<string, unknown>[];
  related_discussions: Record<string, unknown>[];
  related_prs: Record<string, unknown>[];
  maintainer_comments: Record<string, unknown>[];
  alternatives_considered: string[];
  outcome: string;
  reasoning: string;
}

export interface ArchitectureResponse {
  subsystem: string;
  architecture_overview: string;
}

export interface QACitation {
  source_type: string;
  source_id: string;
  source_title: string;
  source_url?: string | null;
  relevant_excerpt: string;
}

export interface QAResponse {
  question: string;
  answer: string;
  citations: QACitation[];
  confidence: number;
  follow_up_questions: string[];
}

export interface GraphNode {
  id: string;
  label: string;
  node_type: string;
  metadata?: Record<string, unknown>;
}

export interface GraphEdge {
  id: string;
  source: string;
  target: string;
  label: string;
  metadata?: Record<string, unknown>;
}

export interface KnowledgeGraphData {
  nodes: GraphNode[];
  edges: GraphEdge[];
  summary: string;
}

export interface TimelineEvent {
  date: string;
  title: string;
  description: string;
  event_type: string;
  source_url?: string | null;
  source_id?: string | null;
  related_items: Record<string, unknown>[];
}

export interface ProjectTimeline {
  events: TimelineEvent[];
  summary: string;
}

export interface LearningStep {
  step_number: number;
  title: string;
  description: string;
  resource_type: string;
  resource_url?: string | null;
  estimated_time: string;
}

export interface LearningPath {
  title: string;
  description: string;
  prerequisites: string[];
  steps: LearningStep[];
  key_concepts: string[];
}

export interface FeedbackCreate {
  feature: string;
  query: string;
  response_summary: string;
  rating: "helpful" | "not_helpful";
  comment?: string;
}

// ─── API Functions ───

async function apiFetch<T>(
  path: string,
  options?: RequestInit
): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    headers: {
      "Content-Type": "application/json",
      ...options?.headers,
    },
    ...options,
  });
  if (!res.ok) {
    const error = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(error.detail || `API Error: ${res.status}`);
  }
  const data = await res.json();
  if (data && typeof data === "object" && "error" in data && data.error) {
    throw new Error(String(data.error));
  }
  return data;
}

// ─── Repository APIs ───

export const api = {
  // Repositories
  createRepository: (github_url: string, user_id?: string) =>
    apiFetch<Repository>("/api/repositories/", {
      method: "POST",
      body: JSON.stringify({ github_url, user_id }),
    }),

  listRepositories: () =>
    apiFetch<RepositoryListItem[]>("/api/repositories/"),

  getRepository: (id: string) =>
    apiFetch<Repository>(`/api/repositories/${id}`),

  getRepositoryDashboard: (id: string) =>
    apiFetch<RepositoryDashboard>(`/api/repositories/${id}/dashboard`),

  deleteRepository: (id: string) =>
    apiFetch<{ message: string }>(`/api/repositories/${id}`, {
      method: "DELETE",
    }),

  // Ingestion
  startIngestion: (id: string) =>
    apiFetch<{ message: string; repository_id: string }>(
      `/api/repositories/${id}/ingest`,
      { method: "POST" }
    ),

  getIngestionStatus: (id: string) =>
    apiFetch<IngestionStatus>(`/api/repositories/${id}/ingestion-status`),

  streamIngestion: (id: string): EventSource =>
    new EventSource(`${API_BASE}/api/repositories/${id}/ingestion-stream`),

  forgetMemory: (id: string) =>
    apiFetch<{ message: string }>(`/api/repositories/${id}/memory`, {
      method: "DELETE",
    }),

  // Mentor Features
  getOnboarding: (id: string) =>
    apiFetch<OnboardingGuide>(`/api/repositories/${id}/onboarding`),

  findFirstIssue: (id: string, experience_level: string, interest: string) =>
    apiFetch<FindIssueResponse>(`/api/repositories/${id}/find-first-issue`, {
      method: "POST",
      body: JSON.stringify({ experience_level, interest }),
    }),

  analyzeIssue: (id: string, issue_number: number) =>
    apiFetch<ContributionPlan>(`/api/repositories/${id}/analyze-issue`, {
      method: "POST",
      body: JSON.stringify({ issue_number }),
    }),

  getMaintainerBrain: (id: string) =>
    apiFetch<MaintainerInsights>(`/api/repositories/${id}/maintainer-brain`),

  exploreDecision: (id: string, question: string) =>
    apiFetch<DecisionExploration>(
      `/api/repositories/${id}/explore-decision`,
      {
        method: "POST",
        body: JSON.stringify({ question }),
      }
    ),

  askQuestion: (id: string, question: string) =>
    apiFetch<QAResponse>(`/api/repositories/${id}/ask`, {
      method: "POST",
      body: JSON.stringify({ question }),
    }),

  getKnowledgeGraph: (id: string) =>
    apiFetch<KnowledgeGraphData>(`/api/repositories/${id}/graph`),

  exploreArchitecture: (id: string, subsystem?: string | null) =>
    apiFetch<ArchitectureResponse>(`/api/repositories/${id}/architecture`, {
      method: "POST",
      body: JSON.stringify({ subsystem: subsystem || null }),
    }),

  getTimeline: (id: string, focus?: string) => {
    const url = new URL(`/api/repositories/${id}/timeline`, window.location.origin);
    if (focus) url.searchParams.append("focus", focus);
    return apiFetch<ProjectTimeline>(url.pathname + url.search);
  },

  getLearningPath: (
    id: string,
    issue_number?: number | null,
    interests?: string[]
  ) =>
    apiFetch<LearningPath>(`/api/repositories/${id}/learning-path`, {
      method: "POST",
      body: JSON.stringify({ issue_number, interests: interests || [] }),
    }),

  // Feedback
  submitFeedback: (id: string, feedback: FeedbackCreate) =>
    apiFetch<Record<string, unknown>>(
      `/api/repositories/${id}/feedback`,
      {
        method: "POST",
        body: JSON.stringify(feedback),
      }
    ),

  // Health
  healthCheck: () => apiFetch<{ status: string }>("/api/health"),
};
