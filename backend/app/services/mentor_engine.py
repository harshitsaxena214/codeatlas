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
        """Run multiple recall queries and combine results into context with a strict budget."""
        all_results = []
        logger.info(f"[Recall] Starting context recall for repo {repo_id} with {len(queries)} queries")
        
        # Always inject Repository DNA for base context
        dna_results = await CogneeMemoryService.recall(repo_id, "RepositoryDNA Tech Stack Architecture Overview")
        if dna_results:
            total_chars = sum(len(str(r)) for r in dna_results)
            logger.info(f"[Recall] DNA query returned {len(dna_results)} memories ({total_chars:,} chars)")
            for r in dna_results:
                text = str(r) if not isinstance(r, str) else r
                if text and text not in all_results:
                    all_results.append(text)
        else:
            logger.info("[Recall] DNA query returned no memories")

        for query in queries:
            results = await CogneeMemoryService.recall(repo_id, query)
            if results:
                total_chars = sum(len(str(r)) for r in results)
                logger.info(f"[Recall] Query {query!r} returned {len(results)} memories ({total_chars:,} chars)")
                for r in results:
                    text = str(r) if not isinstance(r, str) else r
                    if text and text not in all_results:
                        all_results.append(text)
            else:
                logger.info(f"[Recall] Query {query!r} returned no memories")

        logger.info(f"[Recall] Total unique memories collected: {len(all_results)}")

        # Context Budget constraint:
        # Max 20 memories OR ~4,000 tokens (~16,000 characters)
        budgeted_results = []
        token_count = 0
        max_memories = 20
        max_tokens = 4000

        for memory in all_results:
            if len(budgeted_results) >= max_memories:
                break
            
            # Simple word-based token approximation (1 word ≈ 1.3 tokens)
            words = memory.split()
            est_tokens = int(len(words) * 1.3) if words else 1
            
            if token_count + est_tokens > max_tokens:
                # Truncate memory to fit remaining budget
                remaining_tokens = max_tokens - token_count
                if remaining_tokens > 100:  # Only truncate if it yields a meaningful chunk
                    allowed_words = int(remaining_tokens / 1.3)
                    truncated_memory = " ".join(words[:allowed_words]) + "\n[Truncated due to context budget]"
                    budgeted_results.append(truncated_memory)
                    token_count += remaining_tokens
                break
            
            budgeted_results.append(memory)
            token_count += est_tokens

        logger.info(
            f"[Recall] Budgeted context: {len(budgeted_results)} memories kept. "
            f"Estimated context tokens: {token_count:,}"
        )
        return "\n\n---\n\n".join(budgeted_results) if budgeted_results else "No relevant memory found."

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
            user_prompt=f"Repository Memory Context:\n\n{context}\n\n=== END OF CONTEXT ===\n\nGenerate a comprehensive onboarding guide.",
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
                f"Repository Memory Context:\n\n{context}\n\n=== END OF CONTEXT ===\n\n"
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
                f"Repository Memory Context:\n\n{context}\n\n=== END OF CONTEXT ===\n\n"
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
            user_prompt=f"Repository Memory Context:\n\n{context}\n\n=== END OF CONTEXT ===\n\nAnalyze maintainer behavior and generate insights.",
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
                f"Repository Memory Context:\n\n{context}\n\n=== END OF CONTEXT ===\n\n"
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
                f"Repository Memory Context:\n\n{context}\n\n=== END OF CONTEXT ===\n\n"
                f"User Question: {question}"
            ),
            response_model=QAResponse,
        )
        return result

    @staticmethod
    async def generate_timeline(repo_id: str, focus: str | None = None) -> dict:
        """Feature 8: Project Evolution Timeline.

        Strategy:
          1. Build a structured timeline directly from the ingestion_jobs DB table
             so we always have well-typed events regardless of LLM output.
          2. Optionally call the LLM to enrich the summary text and add narrative
             events.  If the LLM returns parseable JSON we merge in any extra events;
             if it returns anything else we use that text as the summary.
          3. Always returns a valid ProjectTimeline-compatible dict.
        """
        from app.database import async_session_factory
        from sqlalchemy import select, text as sql_text
        from datetime import timezone

        # ── Step 1: Build timeline from ingestion_jobs ──────────────────────
        db_events: list[dict] = []
        try:
            async with async_session_factory() as db:
                rows = await db.execute(
                    sql_text(
                        """
                        SELECT step_name, started_at, completed_at, items_processed, status
                        FROM ingestion_jobs
                        WHERE repo_id = :repo_id
                        ORDER BY started_at ASC
                        """
                    ),
                    {"repo_id": repo_id},
                )
                for row in rows:
                    step = row.step_name or "Unknown Step"
                    started = row.started_at
                    completed = row.completed_at
                    items = row.items_processed or 0
                    status = row.status or ""

                    # Format date string
                    dt = completed or started
                    if dt:
                        try:
                            if hasattr(dt, "astimezone"):
                                date_str = dt.astimezone(timezone.utc).strftime("%Y-%m-%d")
                            else:
                                date_str = str(dt)[:10]
                        except Exception:
                            date_str = str(dt)[:10]
                    else:
                        date_str = "Unknown Date"

                    # Map step names to human-readable titles
                    step_titles = {
                        "metadata": "Repository Metadata Ingested",
                        "readme": "README & Documentation Processed",
                        "issues": f"Issues Ingested ({items} items)",
                        "pull_requests": f"Pull Requests Ingested ({items} items)",
                        "discussions": f"Discussions Ingested ({items} items)",
                        "releases": f"Releases Ingested ({items} items)",
                        "contributors": f"Contributors Indexed ({items} items)",
                        "memory": "Knowledge Graph Built",
                    }
                    # Match step by prefix
                    title = next(
                        (v for k, v in step_titles.items() if k in step.lower()),
                        f"{step.replace('_', ' ').title()} ({items} items)",
                    )

                    db_events.append({
                        "date": date_str,
                        "title": title,
                        "description": (
                            f"Ingestion step '{step}' completed with status '{status}'. "
                            f"{items} items processed."
                        ),
                        "event_type": "feature",
                        "source_url": None,
                        "source_id": None,
                        "related_items": [],
                    })
        except Exception as exc:
            logger.warning(f"[Timeline] Could not query ingestion_jobs: {exc}")

        # ── Step 2: LLM enrichment (optional, non-blocking on failure) ───────
        context = await MentorEngine._recall_context(repo_id, [
            "project evolution major milestones timeline",
            "significant features added over time",
            "architecture changes and breaking changes",
            "important discussions and decisions chronologically",
        ])

        user_prompt = (
            f"Repository Memory Context:\n\n{context}\n\n=== END OF CONTEXT ===\n\n"
            "Generate a project evolution timeline."
        )
        if focus:
            user_prompt += f" Focus heavily on: {focus}."

        llm_summary = ""
        llm_extra_events: list[dict] = []

        try:
            import asyncio as _asyncio
            result = await _asyncio.wait_for(
                LLMService.generate_for_query(
                    system_prompt=TIMELINE_SYSTEM_PROMPT,
                    user_prompt=user_prompt,
                    response_model=ProjectTimeline,
                    max_tokens=2048,
                ),
                timeout=60.0,
            )

            if isinstance(result, dict) and "events" in result:
                # LLM returned valid structured data — use its events and summary
                llm_extra_events = result.get("events", [])
                llm_summary = result.get("summary", "")
                logger.info(f"[Timeline] LLM returned {len(llm_extra_events)} structured events.")
            elif isinstance(result, str) and result.strip():
                # LLM returned narrative text — use it as the summary
                llm_summary = result.strip()
                logger.info("[Timeline] LLM returned raw text; using as summary narrative.")
            elif isinstance(result, dict) and "error" not in result:
                # Some other dict shape — stringify it
                import json as _json
                llm_summary = _json.dumps(result, default=str)[:1000]
        except Exception as exc:
            logger.warning(f"[Timeline] LLM call failed (non-fatal): {exc}")

        # ── Step 3: Merge and return ───────────────────────────────────
        # Prefer LLM events if we got structured data; otherwise use DB events.
        # Always ensure at least one event so the frontend never shows empty state.
        if llm_extra_events:
            merged_events = llm_extra_events
        elif db_events:
            merged_events = db_events
        else:
            merged_events = [{
                "date": "Unknown",
                "title": "Repository Ingested",
                "description": "The repository was successfully ingested into CodeAtlas.",
                "event_type": "feature",
                "source_url": None,
                "source_id": None,
                "related_items": [],
            }]

        summary = llm_summary or (
            f"Repository ingestion timeline with {len(merged_events)} recorded events."
        )

        return {"events": merged_events, "summary": summary}

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
                f"Repository Memory Context:\n\n{context}\n\n=== END OF CONTEXT ===\n\n"
                f"{interest_text}\n{issue_text}\n\n"
                f"Generate a personalized learning path."
            ),
            response_model=LearningPath,
        )
        return result

    @staticmethod
    def _synthesize_graph_from_text(text: str) -> dict:
        """Build a minimal KnowledgeGraphData dict from a plain-text description.

        Used as a last-resort fallback when the LLM returns a graph-completion
        object or free-form prose instead of JSON.  Extracts capitalized phrases
        and entity references to create nodes; creates simple edges between
        adjacent detected entities.

        Returns a valid KnowledgeGraphData-compatible dict.
        """
        import re

        # Extract possible entity names: capitalized words / short phrases
        candidates = re.findall(r'#\d+|"([^"]{3,60})"|\b([A-Z][A-Za-z0-9_/-]{2,40})\b', text)
        seen: set[str] = set()
        entities: list[str] = []
        for groups in candidates:
            for g in groups:
                if g and g not in seen:
                    seen.add(g)
                    entities.append(g)

        # Cap at 30 entities so the graph stays readable
        entities = entities[:30]

        nodes = [
            {
                "id": f"n{i}",
                "label": ent,
                "node_type": "feature",
                "metadata": {},
            }
            for i, ent in enumerate(entities)
        ]

        # Simple sequential edges between adjacent entities
        edges = [
            {
                "id": f"e{i}",
                "source": f"n{i}",
                "target": f"n{i + 1}",
                "label": "related_to",
                "metadata": {},
            }
            for i in range(len(entities) - 1)
        ]

        summary = text[:500].strip() if text else "Knowledge graph synthesized from repository data."
        return {"nodes": nodes, "edges": edges, "summary": summary}

    @staticmethod
    async def generate_knowledge_graph(repo_id: str) -> dict:
        """Feature 7: Knowledge Graph data for React Flow.

        Calls the LLM for structured KnowledgeGraphData JSON.
        If the LLM returns a graph-completion object, plain text, or any
        non-JSON response, falls back to _synthesize_graph_from_text so
        the endpoint NEVER fails.
        """
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
            user_prompt=f"Repository Memory Context:\n\n{context}\n\n=== END OF CONTEXT ===\n\nGenerate the knowledge graph.",
            response_model=KnowledgeGraphData,
        )

        # ── Happy path: LLM returned a valid KG dict ────────────────────────
        if isinstance(result, dict) and "nodes" in result and "edges" in result:
            logger.info(
                f"[KnowledgeGraph] LLM returned structured graph: "
                f"{len(result['nodes'])} nodes, {len(result['edges'])} edges."
            )
            return result

        # ── Fallback: result is a string (graph_completion text / plain text) ──
        if isinstance(result, str) and result.strip():
            logger.info("[KnowledgeGraph] LLM returned raw text; synthesizing graph from text.")
            return MentorEngine._synthesize_graph_from_text(result)

        # ── Fallback: result is some other dict (error dict or partial) ───────
        if isinstance(result, dict):
            # Try to coerce partial data
            nodes = result.get("nodes", [])
            edges = result.get("edges", [])
            summary = result.get("summary", str(result)[:300])
            if nodes:
                logger.info(f"[KnowledgeGraph] Partial KG dict returned: {len(nodes)} nodes.")
                return {"nodes": nodes, "edges": edges, "summary": summary}
            # No usable data — synthesize from whatever text is available
            raw_text = result.get("raw", "") or str(result)
            logger.info("[KnowledgeGraph] Empty/error dict; synthesizing fallback graph.")
            return MentorEngine._synthesize_graph_from_text(raw_text)

        # ── Ultimate fallback: return an empty valid graph ───────────────────
        logger.warning("[KnowledgeGraph] Unexpected result type; returning empty graph.")
        return {"nodes": [], "edges": [], "summary": "Knowledge graph could not be generated."}
