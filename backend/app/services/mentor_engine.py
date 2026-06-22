"""
Mentor Engine — Orchestrates Cognee recall + LLM to generate mentoring outputs.
Every feature follows: User Request → Cognee Recall → LLM Synthesis → Structured Response
"""
import logging
from typing import Any
from app.services.cognee_memory import CogneeMemoryService
from app.services.llm_service import LLMService
from app.schemas.mentor import (
    OnboardingGuide, FindIssueResponse, ContributionPlan,
    MaintainerInsights, DecisionExploration, QAResponse,
    LearningPath, ProjectTimeline, KnowledgeGraphData,
)

logger = logging.getLogger(__name__)

# ─── System prompts for each feature ───

ONBOARDING_SYSTEM_PROMPT = """You are Open Source Mentor, an AI that helps developers understand and contribute to open-source repositories.

Generate a comprehensive onboarding guide based on the repository memory provided.

The guide should:
1. Summarize what the project does and why it matters
2. List core technologies
3. Identify key maintainers
4. Highlight the most important discussions and PRs
5. Describe the project culture and contribution norms
6. Create a step-by-step reading path for new contributors

Base your response ENTIRELY on the repository memory context provided. Do not fabricate information."""

FIND_ISSUE_SYSTEM_PROMPT = """You are Open Source Mentor, an AI that matches developers to their ideal first contribution.

Based on the repository memory, find the best open issues for a contributor with the given experience level and interest area.

For each recommended issue, provide:
- Why it matches the user's profile
- A difficulty score (1-10)
- Relevant files to look at
- Estimated completion time
- Required reading (related discussions, PRs)
- Labels

Rank issues by how suitable they are as a FIRST contribution. Prioritize issues that:
- Have clear requirements
- Are well-scoped
- Have supportive maintainer history
- Match the user's stated interests

Base your response ENTIRELY on the repository memory context provided."""

CONTRIBUTION_SYSTEM_PROMPT = """You are Open Source Mentor, an AI contribution assistant.

Analyze the given issue and generate a detailed contribution plan.

Include:
- Issue summary and context
- Difficulty assessment
- Related discussions and PRs
- What maintainers expect
- Suggested starting point
- Estimated effort
- Potential challenges
- Recommended implementation approach

Base your response ENTIRELY on the repository memory context provided."""

MAINTAINER_BRAIN_SYSTEM_PROMPT = """You are Open Source Mentor, analyzing maintainer behavior patterns.

Based on repository history (PR reviews, discussion comments, issue responses), generate insights about:
- Individual maintainer profiles and preferences
- Review patterns and expectations
- Common reasons for PR rejection
- What maintainers value in contributions
- DO and DON'T lists for contributors

Base your response ENTIRELY on the repository memory context provided."""

DECISION_EXPLORER_SYSTEM_PROMPT = """You are Open Source Mentor, a repository historian.

Answer the user's question about WHY a decision was made in this project.

Provide:
- A clear summary of the decision
- Timeline of events
- Related discussions and PRs
- Key maintainer comments
- Alternative solutions that were considered
- The final outcome and reasoning

Base your response ENTIRELY on the repository memory context provided."""

QA_SYSTEM_PROMPT = """You are Open Source Mentor, answering questions about an open-source repository.

Answer the user's question using ONLY the repository memory context provided.

For each answer:
- Provide clear, specific information
- Cite sources (issue numbers, PR numbers, discussion numbers)
- Include relevant excerpts
- Suggest follow-up questions
- Rate your confidence (0.0-1.0) based on available evidence

NEVER fabricate information. If the memory doesn't contain enough data, say so."""

TIMELINE_SYSTEM_PROMPT = """You are Open Source Mentor, generating a project evolution timeline.

Based on the repository memory, create a chronological timeline of significant events:
- Major features added
- Architecture decisions
- Breaking changes
- Important discussions
- Milestone PRs

Each event should connect to specific issues, discussions, or PRs from the repository history.

Base your response ENTIRELY on the repository memory context provided."""

LEARNING_PATH_SYSTEM_PROMPT = """You are Open Source Mentor, creating personalized learning paths.

Generate a learning path that prepares a developer to contribute to this repository.

Consider:
- The user's stated interests
- The specific issue they want to work on (if any)
- Repository technologies
- Key concepts they need to understand

The path should reference actual discussions, PRs, and issues from the repository.

Base your response ENTIRELY on the repository memory context provided."""


class MentorEngine:
    """Orchestrates Cognee recall + LLM to generate mentoring outputs."""

    @staticmethod
    async def _recall_context(repo_id: str, queries: list[str]) -> str:
        """Run multiple recall queries and combine results into context."""
        all_results = []
        
        # Always inject Repository DNA for base context
        dna_results = await CogneeMemoryService.recall(repo_id, "RepositoryDNA Tech Stack Architecture Overview")
        if dna_results:
            for r in dna_results:
                text = str(r) if not isinstance(r, str) else r
                if text and text not in all_results:
                    all_results.append(text)

        for query in queries:
            results = await CogneeMemoryService.recall(repo_id, query)
            if results:
                for r in results:
                    text = str(r) if not isinstance(r, str) else r
                    if text and text not in all_results:
                        all_results.append(text)

        return "\n\n---\n\n".join(all_results) if all_results else "No relevant memory found."

    @staticmethod
    async def generate_onboarding_guide(repo_id: str) -> dict:
        """Feature 1: Contributor Onboarding Guide."""
        context = await MentorEngine._recall_context(repo_id, [
            "project overview README summary what does this project do",
            "most important discussions and architectural decisions",
            "key maintainers and their contribution expectations",
            "important pull requests and features",
            "project culture contribution guidelines",
        ])

        result = await LLMService.generate_for_query(
            system_prompt=ONBOARDING_SYSTEM_PROMPT,
            user_prompt=f"Repository Memory Context:\n\n{context}\n\nGenerate a comprehensive onboarding guide.",
            response_model=OnboardingGuide,
        )
        return result

    @staticmethod
    async def find_first_issue(repo_id: str, experience_level: str, interest: str) -> dict:
        """Feature 2: Find My First Issue."""
        context = await MentorEngine._recall_context(repo_id, [
            f"open issues suitable for {experience_level} contributors in {interest}",
            "issues labeled good-first-issue help-wanted beginner",
            "maintainer preferences for new contributor PRs",
            f"recent {interest} related issues and discussions",
            "contributor journey patterns first contributions",
        ])

        result = await LLMService.generate_for_query(
            system_prompt=FIND_ISSUE_SYSTEM_PROMPT,
            user_prompt=(
                f"Repository Memory Context:\n\n{context}\n\n"
                f"Find the best first issues for a contributor with:\n"
                f"- Experience Level: {experience_level}\n"
                f"- Interest Area: {interest}"
            ),
            response_model=FindIssueResponse,
        )
        return result

    @staticmethod
    async def analyze_issue(repo_id: str, issue_number: int) -> dict:
        """Feature 3: Contribution Assistant."""
        context = await MentorEngine._recall_context(repo_id, [
            f"issue #{issue_number} details context discussion",
            f"pull requests related to issue #{issue_number}",
            f"discussions about the topic of issue #{issue_number}",
            "maintainer expectations for pull request submissions",
            f"architecture decisions related to issue #{issue_number}",
        ])

        result = await LLMService.generate_for_query(
            system_prompt=CONTRIBUTION_SYSTEM_PROMPT,
            user_prompt=(
                f"Repository Memory Context:\n\n{context}\n\n"
                f"Generate a contribution plan for Issue #{issue_number}."
            ),
            response_model=ContributionPlan,
        )
        return result

    @staticmethod
    async def maintainer_brain(repo_id: str) -> dict:
        """Feature 4: Maintainer Brain."""
        context = await MentorEngine._recall_context(repo_id, [
            "maintainer review comments and feedback patterns",
            "PR rejections and reasons for rejection",
            "maintainer preferences coding style expectations",
            "commonly requested changes in code reviews",
            "contribution guidelines and best practices",
        ])

        result = await LLMService.generate_for_query(
            system_prompt=MAINTAINER_BRAIN_SYSTEM_PROMPT,
            user_prompt=f"Repository Memory Context:\n\n{context}\n\nAnalyze maintainer behavior and generate insights.",
            response_model=MaintainerInsights,
        )
        return result

    @staticmethod
    async def explore_decision(repo_id: str, question: str) -> dict:
        """Feature 5: Decision Explorer."""
        context = await MentorEngine._recall_context(repo_id, [
            question,
            f"discussions about {question}",
            f"pull requests related to {question}",
            f"architecture decisions about {question}",
            f"alternatives considered for {question}",
        ])

        result = await LLMService.generate_for_query(
            system_prompt=DECISION_EXPLORER_SYSTEM_PROMPT,
            user_prompt=(
                f"Repository Memory Context:\n\n{context}\n\n"
                f"User Question: {question}"
            ),
            response_model=DecisionExploration,
        )
        return result

    @staticmethod
    async def _lazy_architecture_analysis(repo_id: str, question: str, subsystem: str | None = None) -> str:
        """Fetch files dynamically for Category B architecture questions with caching."""
        subsystem_name = subsystem or "General Architecture"
        
        # 1. Check Architecture Cache in Cognee
        cached_summary = await CogneeMemoryService.recall_architecture_cache(repo_id, subsystem_name)
        if cached_summary:
            return f"Cached Architecture ({subsystem_name}):\n{cached_summary}"
            
        from app.database import async_session_factory
        from sqlalchemy import select
        from app.models.repository import Repository
        from app.services.github_fetcher import GitHubFetcher
        
        async with async_session_factory() as db:
            result = await db.execute(select(Repository).where(Repository.id == __import__("uuid").UUID(repo_id)))
            repo = result.scalar_one_or_none()
            if not repo:
                return "Repository not found."

        fetcher = GitHubFetcher()
        # 2. Fetch top level structure
        structure = await __import__("asyncio").to_thread(fetcher.fetch_top_level_structure, repo.owner, repo.name)
        
        # 3. Smart File Discovery Ranking
        priority_files = ["README.md", "package.json", "next.config.ts", "vite.config.ts", 
                          "middleware.ts", "auth.ts", "session.ts", "database.ts", "prisma.ts", 
                          "main.ts", "app.ts", "server.ts", "routes.ts", "pyproject.toml", "main.py"]
        
        files_to_fetch = []
        for item in structure:
            if item.startswith("[file] "):
                filename = item.replace("[file] ", "")
                if any(filename.endswith(pf) or filename == pf for pf in priority_files):
                    files_to_fetch.append(filename)
                    
        # Limit to top 5 files to avoid token limits
        files_to_fetch = files_to_fetch[:5]
        
        file_contents = []
        for f in files_to_fetch:
            content = await __import__("asyncio").to_thread(fetcher.fetch_file_content, repo.owner, repo.name, f)
            if content:
                # Truncate content to avoid blowing up context
                file_contents.append(f"--- {f} ---\n{content[:2000]}")
                
        raw_context = "\n\n".join(file_contents) if file_contents else "No relevant architecture files found."
        
        # 4. Generate Architecture Summary and Cache it
        summary_prompt = (
            f"Analyze the following repository files for the subsystem '{subsystem_name}'.\n"
            f"Question: {question}\n\n"
            f"Generate a structured Architecture Summary including:\n"
            f"- Summary of how it works\n"
            f"- Important Files\n"
            f"- Related context\n\n"
            f"Files:\n{raw_context}"
        )
        
        # Architecture analysis benefits from large context — use query tier (Gemini Flash)
        generated_summary = await LLMService.generate_for_query(
            system_prompt="You are an expert software architect analyzing source code.",
            user_prompt=summary_prompt,
            temperature=0.3
        )
        
        final_summary = str(generated_summary)
        await CogneeMemoryService.remember_architecture_cache(repo_id, subsystem_name, final_summary)
        
        return f"Newly Analyzed Architecture ({subsystem_name}):\n{final_summary}"

    @staticmethod
    async def answer_question(repo_id: str, question: str) -> dict:
        """Feature 6: Repository Q&A (Refactored for Lazy Analysis)."""
        from pydantic import BaseModel
        class IntentClassification(BaseModel):
            category: str  # 'MEMORY' or 'ARCHITECTURE'
            subsystem: str | None = None # e.g., 'Authentication', 'Routing', 'Database', 'API Layer'
            
        # Intent classification is a tiny cheap call — use ingestion tier (high RPM)
        intent_result = await LLMService.generate_for_ingestion(
            system_prompt="You classify questions. 'MEMORY' for history, 'ARCHITECTURE' for code/systems. If ARCHITECTURE, provide the subsystem name.",
            user_prompt=f"Question: {question}",
            response_model=IntentClassification,
            temperature=0.1,
            max_tokens=64,
        )
        
        category = "MEMORY"
        subsystem = None
        if isinstance(intent_result, dict):
            category = intent_result.get("category", "MEMORY")
            subsystem = intent_result.get("subsystem")

        if category == "ARCHITECTURE":
            # Category B: Lazy Architecture Analysis
            arch_context = await MentorEngine._lazy_architecture_analysis(repo_id, question, subsystem)
            context = f"Architecture Analysis Context:\n{arch_context}"
        else:
            # Category A: Memory Questions
            context = await MentorEngine._recall_context(repo_id, [
                question,
                f"issues and discussions about {question}",
                f"pull requests related to {question}",
            ])

        result = await LLMService.generate_for_query(
            system_prompt=QA_SYSTEM_PROMPT,
            user_prompt=(
                f"Repository Context:\n\n{context}\n\n"
                f"User Question: {question}"
            ),
            response_model=QAResponse,
        )
        return result

    @staticmethod
    async def generate_timeline(repo_id: str, focus: str | None = None) -> dict:
        """Feature 8: Project Evolution Timeline."""
        context = await MentorEngine._recall_context(repo_id, [
            "project evolution major milestones timeline",
            "significant features added over time",
            "architecture changes and breaking changes",
            "important discussions and decisions chronologically",
        ])
        
        user_prompt = f"Repository Memory Context:\n\n{context}\n\nGenerate a project evolution timeline."
        if focus:
            user_prompt += f" Focus heavily on: {focus}."

        result = await LLMService.generate_for_query(
            system_prompt=TIMELINE_SYSTEM_PROMPT,
            user_prompt=user_prompt,
            response_model=ProjectTimeline,
        )
        return result

    @staticmethod
    async def generate_learning_path(
        repo_id: str, issue_number: int | None, interests: list[str]
    ) -> dict:
        """Feature 9: Personalized Learning Path."""
        queries = [
            "repository technologies and key concepts",
            "important discussions for understanding the codebase",
            "recommended reading for new contributors",
        ]
        if issue_number:
            queries.append(f"concepts needed to work on issue #{issue_number}")
        if interests:
            queries.append(f"resources related to {', '.join(interests)}")

        context = await MentorEngine._recall_context(repo_id, queries)

        interest_text = f"Interests: {', '.join(interests)}" if interests else "No specific interests"
        issue_text = f"Target Issue: #{issue_number}" if issue_number else "No specific issue"

        result = await LLMService.generate_for_query(
            system_prompt=LEARNING_PATH_SYSTEM_PROMPT,
            user_prompt=(
                f"Repository Memory Context:\n\n{context}\n\n"
                f"{interest_text}\n{issue_text}\n\n"
                f"Generate a personalized learning path."
            ),
            response_model=LearningPath,
        )
        return result

    @staticmethod
    async def generate_knowledge_graph(repo_id: str) -> dict:
        """Feature 7: Knowledge Graph data for React Flow."""
        context = await MentorEngine._recall_context(repo_id, [
            "all entities: issues, PRs, discussions, features, technologies",
            "all relationships between entities",
            "maintainers and their contributions",
            "architecture decisions and feature implementations",
        ])

        result = await LLMService.generate_for_query(
            system_prompt=(
                "You are Open Source Mentor. Generate a knowledge graph of the repository.\n"
                "Create nodes for: Issues, PRs, Discussions, Features, Technologies, "
                "Maintainers, Architecture Decisions, and Contribution Opportunities.\n"
                "Create edges showing relationships like: resolved_by, reviewed_by, "
                "mentions, implemented_by, originated_from, authored, referenced_in, "
                "discussed_in, related_to.\n"
                "Each node needs: id, label, node_type.\n"
                "Each edge needs: id, source, target, label.\n"
                "Base your response ENTIRELY on the repository memory context provided."
            ),
            user_prompt=f"Repository Memory Context:\n\n{context}\n\nGenerate the knowledge graph.",
            response_model=KnowledgeGraphData,
        )
        return result
