"""Mentor feature schemas — structured outputs for all AI features."""
from pydantic import BaseModel


# ─── Feature 1: Onboarding Guide ───

class OnboardingStep(BaseModel):
    step_number: int
    title: str
    description: str
    resource_type: str  # "readme", "discussion", "pr", "issue"
    resource_url: str | None = None
    resource_id: str | None = None

class OnboardingGuide(BaseModel):
    project_summary: str
    what_it_solves: str
    core_technologies: list[str]
    key_maintainers: list[str]
    project_culture: str
    important_discussions: list[dict]
    important_prs: list[dict]
    reading_path: list[OnboardingStep]


# ─── Feature 2: Find My First Issue ───

class FindIssueRequest(BaseModel):
    experience_level: str  # beginner, intermediate, advanced
    interest: str  # frontend, backend, devops, documentation, ai, testing

class RecommendedIssue(BaseModel):
    issue_number: int
    title: str
    url: str
    why_it_matches: str
    difficulty_score: int  # 1-10
    relevant_files: list[str]
    estimated_time: str
    required_reading: list[dict]
    related_discussions: list[dict]
    related_prs: list[dict]
    labels: list[str]

class FindIssueResponse(BaseModel):
    recommended_issues: list[RecommendedIssue]
    reasoning: str


# ─── Feature 3: Contribution Assistant ───

class AnalyzeIssueRequest(BaseModel):
    issue_number: int

class ContributionPlan(BaseModel):
    issue_number: int
    issue_title: str
    issue_url: str
    summary: str
    difficulty: str  # beginner, intermediate, advanced
    difficulty_score: int
    related_discussions: list[dict]
    related_prs: list[dict]
    related_decisions: list[dict]
    maintainer_expectations: list[str]
    suggested_starting_point: str
    estimated_effort: str
    potential_challenges: list[str]
    recommended_approach: str


# ─── Feature 4: Maintainer Brain ───

class MaintainerProfile(BaseModel):
    username: str
    avatar_url: str | None = None
    review_count: int
    preferences: list[str]
    common_feedback: list[str]

class MaintainerInsights(BaseModel):
    maintainer_profiles: list[MaintainerProfile]
    preferences: list[str]
    review_patterns: list[str]
    contribution_expectations: list[str]
    common_rejection_reasons: list[str]
    do_list: list[str]
    dont_list: list[str]


# ─── Feature 5: Decision Explorer ───

class ExploreDecisionRequest(BaseModel):
    question: str

class DecisionExploration(BaseModel):
    question: str
    decision_summary: str
    timeline: list[dict]
    related_discussions: list[dict]
    related_prs: list[dict]
    maintainer_comments: list[dict]
    alternatives_considered: list[str]
    outcome: str
    reasoning: str


# ─── Feature 6: Repository Q&A ───

class QARequest(BaseModel):
    question: str

class QACitation(BaseModel):
    source_type: str  # issue, pr, discussion, readme
    source_id: str
    source_title: str
    source_url: str | None = None
    relevant_excerpt: str

class QAResponse(BaseModel):
    question: str
    answer: str
    citations: list[QACitation]
    confidence: float  # 0.0 - 1.0
    follow_up_questions: list[str]


# ─── Feature 8: Timeline ───

class TimelineEvent(BaseModel):
    date: str
    title: str
    description: str
    event_type: str  # issue, pr, discussion, decision, feature
    source_url: str | None = None
    source_id: str | None = None
    related_items: list[dict]

class ProjectTimeline(BaseModel):
    events: list[TimelineEvent]
    summary: str


# ─── Feature 9: Learning Path ───

class LearningPathRequest(BaseModel):
    issue_number: int | None = None
    interests: list[str] = []

class LearningStep(BaseModel):
    step_number: int
    title: str
    description: str
    resource_type: str
    resource_url: str | None = None
    estimated_time: str

class LearningPath(BaseModel):
    title: str
    description: str
    prerequisites: list[str]
    steps: list[LearningStep]
    key_concepts: list[str]


# ─── Feature 7: Knowledge Graph ───

class GraphNode(BaseModel):
    id: str
    label: str
    node_type: str  # issue, pr, discussion, feature, maintainer, technology, decision, opportunity
    metadata: dict = {}

class GraphEdge(BaseModel):
    id: str
    source: str
    target: str
    label: str  # resolved_by, reviewed_by, mentions, etc.
    metadata: dict = {}

class KnowledgeGraphData(BaseModel):
    nodes: list[GraphNode]
    edges: list[GraphEdge]
    summary: str


# ─── Memory Lifecycle ───

class ForgetRequest(BaseModel):
    entity_type: str | None = None  # if None, forget entire dataset
    entity_id: str | None = None

class MemoryStats(BaseModel):
    total_nodes: int
    total_relationships: int
    entity_counts: dict  # { "Issue": 42, "PR": 31, ... }

# ─── Feature 10: Architecture Explorer ───

class ArchitectureRequest(BaseModel):
    subsystem: str | None = None

class ArchitectureResponse(BaseModel):
    subsystem: str
    architecture_overview: str

