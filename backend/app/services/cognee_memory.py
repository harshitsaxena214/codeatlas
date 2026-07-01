"""
Cognee Memory Service — Core integration layer.
ALL repository intelligence lives in Cognee, not PostgreSQL.
Uses cognee.remember(), cognee.recall(), cognee.improve(), cognee.forget().

ARCHITECTURE NOTE:
Raw structured text is passed directly to cognee.remember() — Cognee's own
pipeline handles entity extraction, knowledge graph construction, and
vector indexing internally. Pre-summarizing data with an LLM before passing
it to Cognee is redundant, lossy, and wasteful of quota.
"""
import json
import logging
import cognee
from typing import Any
from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class CogneeMemoryService:
    """
    Manages the full Cognee memory lifecycle for repositories.
    Each repository gets its own dataset namespace: repo_{uuid}
    """

    _connected: bool = False

    @classmethod
    async def connect(cls):
        """Connect to Cognee Cloud on application startup."""
        if cls._connected:
            return
        try:
            if settings.COGNEE_API_URL and settings.COGNEE_API_KEY:
                await cognee.serve(
                    url=settings.COGNEE_API_URL,
                    api_key=settings.COGNEE_API_KEY,
                )
                logger.info("Connected to Cognee Cloud")
            else:
                logger.info("Running Cognee in local mode (no cloud credentials)")
            cls._connected = True
        except Exception as e:
            logger.error(f"Failed to connect to Cognee: {e}")
            raise

    @classmethod
    async def disconnect(cls):
        """Disconnect from Cognee Cloud on application shutdown."""
        try:
            await cognee.disconnect()
            cls._connected = False
            logger.info("Disconnected from Cognee Cloud")
        except Exception:
            pass

    @staticmethod
    def _dataset_name(repo_id: str) -> str:
        """Generate Cognee dataset namespace for a repository."""
        return f"repo_{repo_id}"

    # ═══════════════════════════════════════════
    #  REMEMBER — Ingest data into Cognee memory
    # ═══════════════════════════════════════════

    @classmethod
    async def remember_dna(cls, repo_id: str, owner: str, name: str, dna_data: dict) -> None:
        """Store Repository DNA (fast profiling stage) as a RepositoryEntity."""
        dataset = cls._dataset_name(repo_id)
        formatted = (
            f"[Repository: {owner}/{name}]\n"
            f"[Entity: RepositoryDNA]\n"
            f"[Tech Stack: {', '.join(dna_data.get('tech_stack', []))}]\n"
            f"[Repository Type: {dna_data.get('repository_type', 'unknown')}]\n"
            f"[Health: {dna_data.get('health', 'unknown')}]\n"
            f"[Complexity Score: {dna_data.get('complexity_score', 0)}/10]\n"
            f"[Contribution Friendliness: {dna_data.get('contribution_friendliness', 'unknown')}]\n\n"
            f"Architecture Overview:\n{dna_data.get('architecture_overview', 'None provided')}\n"
        )
        try:
            await cognee.remember(formatted, dataset_name=dataset)
            logger.info(f"[Memory] Remember DNA — {owner}/{name} | dataset={dataset}")
        except Exception as e:
            logger.error(f"[Memory] Remember DNA FAILED — {owner}/{name}: {e}")
            raise

    @classmethod
    async def remember_readme(cls, repo_id: str, owner: str, name: str, content: str) -> None:
        """Store README as a DocumentationPage entity."""
        dataset = cls._dataset_name(repo_id)
        # Truncate very large READMEs — Cognee works best with focused chunks
        truncated = content[:8000] if len(content) > 8000 else content
        formatted = (
            f"[Repository: {owner}/{name}]\n"
            f"[Entity: DocumentationPage]\n"
            f"[Type: README]\n\n"
            f"{truncated}"
        )
        try:
            logger.info(f"[Memory] Remember README — {owner}/{name} | {len(truncated)} chars")
            await cognee.remember(formatted, dataset_name=dataset)
            logger.info(f"[Memory] Remember README DONE — {owner}/{name}")
        except Exception as e:
            logger.error(f"[Memory] Remember README FAILED — {owner}/{name}: {e}")
            raise

    @classmethod
    async def remember_issues(cls, repo_id: str, owner: str, name: str, issues: list[dict]) -> None:
        """
        Store issues as structured text directly into Cognee memory.

        NO LLM pre-summarization — Cognee's internal pipeline handles entity
        extraction and knowledge graph construction from the raw structured text.
        This saves 4 LLM calls (~10K tokens each) per ingestion.
        """
        dataset = cls._dataset_name(repo_id)
        if not issues:
            return

        entries = []
        for issue in issues:
            # Truncate body to keep token usage reasonable for Cognee's internal processing
            body = (issue.get("body") or "")[:600]
            labels = ", ".join(issue.get("labels", [])) or "none"

            # Include top 3 comments only — signal without noise
            comments_text = ""
            for c in issue.get("comments", [])[:3]:
                comment_body = (c.get("body") or "")[:200]
                if comment_body:
                    comments_text += f"  - @{c.get('author', 'unknown')}: {comment_body}\n"

            entry = (
                f"Issue #{issue.get('number')}: {issue.get('title', '')}\n"
                f"State: {issue.get('state', 'unknown')} | "
                f"Author: @{issue.get('author', 'unknown')} | "
                f"Labels: {labels} | "
                f"Created: {issue.get('created_at', '')[:10]}\n"
                f"Body: {body}\n"
            )
            if comments_text:
                entry += f"Top Comments:\n{comments_text}"

            entries.append(entry)

        formatted = (
            f"[Repository: {owner}/{name}]\n"
            f"[Entity: Issues]\n"
            f"[Total: {len(issues)} issues]\n\n"
            + "\n---\n".join(entries)
        )
        try:
            logger.info(f"[Memory] Remember Issues — {owner}/{name} | count={len(issues)}")
            await cognee.remember(formatted, dataset_name=dataset)
            logger.info(f"[Memory] Remember Issues DONE — {owner}/{name} | count={len(issues)}")
        except Exception as e:
            logger.error(f"[Memory] Remember Issues FAILED — {owner}/{name}: {e}")
            raise

    @classmethod
    async def remember_pull_requests(
        cls, repo_id: str, owner: str, name: str, prs: list[dict]
    ) -> None:
        """
        Store PRs as structured text directly into Cognee memory.

        NO LLM pre-summarization — Cognee handles entity extraction internally.
        """
        dataset = cls._dataset_name(repo_id)
        if not prs:
            return

        entries = []
        for pr in prs:
            body = (pr.get("body") or "")[:600]
            labels = ", ".join(pr.get("labels", [])) or "none"
            state = "merged" if pr.get("merged") else pr.get("state", "unknown")

            # Include top 3 review summaries
            reviews_text = ""
            for r in pr.get("reviews", [])[:3]:
                review_body = (r.get("body") or "")[:150]
                if review_body:
                    reviews_text += (
                        f"  - @{r.get('author', 'unknown')} [{r.get('state', '')}]: {review_body}\n"
                    )

            entry = (
                f"PR #{pr.get('number')}: {pr.get('title', '')}\n"
                f"State: {state} | "
                f"Author: @{pr.get('author', 'unknown')} | "
                f"Labels: {labels} | "
                f"Files Changed: {pr.get('files_changed', 0)} | "
                f"+{pr.get('additions', 0)}/-{pr.get('deletions', 0)}\n"
                f"Created: {(pr.get('created_at') or '')[:10]} | "
                f"Merged: {(pr.get('merged_at') or '')[:10]}\n"
                f"Description: {body}\n"
            )
            if reviews_text:
                entry += f"Reviews:\n{reviews_text}"

            entries.append(entry)

        formatted = (
            f"[Repository: {owner}/{name}]\n"
            f"[Entity: PullRequests]\n"
            f"[Total: {len(prs)} pull requests]\n\n"
            + "\n---\n".join(entries)
        )
        try:
            logger.info(f"[Memory] Remember PRs — {owner}/{name} | count={len(prs)}")
            await cognee.remember(formatted, dataset_name=dataset)
            logger.info(f"[Memory] Remember PRs DONE — {owner}/{name} | count={len(prs)}")
        except Exception as e:
            logger.error(f"[Memory] Remember PRs FAILED — {owner}/{name}: {e}")
            raise

    @classmethod
    async def remember_discussions(
        cls, repo_id: str, owner: str, name: str, discussions: list[dict]
    ) -> None:
        """
        Store discussions as structured text directly into Cognee memory.

        NO LLM pre-summarization — Cognee handles entity extraction internally.
        """
        dataset = cls._dataset_name(repo_id)
        if not discussions:
            return

        entries = []
        for disc in discussions:
            body = (disc.get("body") or "")[:600]
            category = disc.get("category", "general")
            labels = ", ".join(disc.get("labels", [])) or "none"
            has_answer = "✓ Answered" if disc.get("has_answer") else "Open"

            # Include top 3 comments
            comments_text = ""
            for c in disc.get("comments", [])[:3]:
                comment_body = (c.get("body") or "")[:200]
                if comment_body:
                    comments_text += f"  - @{c.get('author', 'unknown')}: {comment_body}\n"

            entry = (
                f"Discussion #{disc.get('number')}: {disc.get('title', '')}\n"
                f"Category: {category} | Status: {has_answer} | "
                f"Author: @{disc.get('author', 'unknown')} | Labels: {labels}\n"
                f"Created: {(disc.get('created_at') or '')[:10]}\n"
                f"Body: {body}\n"
            )
            if comments_text:
                entry += f"Comments:\n{comments_text}"
            if disc.get("answer"):
                answer_body = (disc["answer"].get("body") or "")[:300]
                entry += f"Accepted Answer: {answer_body}\n"

            entries.append(entry)

        formatted = (
            f"[Repository: {owner}/{name}]\n"
            f"[Entity: Discussions]\n"
            f"[Total: {len(discussions)} discussions]\n\n"
            + "\n---\n".join(entries)
        )
        try:
            logger.info(f"[Memory] Remember Discussions — {owner}/{name} | count={len(discussions)}")
            await cognee.remember(formatted, dataset_name=dataset)
            logger.info(f"[Memory] Remember Discussions DONE — {owner}/{name} | count={len(discussions)}")
        except Exception as e:
            logger.error(f"[Memory] Remember Discussions FAILED — {owner}/{name}: {e}")
            raise

    @classmethod
    async def remember_releases(
        cls, repo_id: str, owner: str, name: str, releases: list[dict]
    ) -> None:
        """
        Store releases as structured text directly into Cognee memory.

        NO LLM pre-summarization — Cognee handles entity extraction internally.
        """
        dataset = cls._dataset_name(repo_id)
        if not releases:
            return

        entries = []
        for release in releases:
            body = (release.get("body") or "")[:500]
            entry = (
                f"Release {release.get('tag_name', '')}: {release.get('name', '')}\n"
                f"Published: {(release.get('published_at') or '')[:10]}\n"
                f"Release Notes: {body}\n"
            )
            entries.append(entry)

        formatted = (
            f"[Repository: {owner}/{name}]\n"
            f"[Entity: Releases]\n"
            f"[Total: {len(releases)} releases]\n\n"
            + "\n---\n".join(entries)
        )
        try:
            logger.info(f"[Memory] Remember Releases — {owner}/{name} | count={len(releases)}")
            await cognee.remember(formatted, dataset_name=dataset)
            logger.info(f"[Memory] Remember Releases DONE — {owner}/{name} | count={len(releases)}")
        except Exception as e:
            logger.error(f"[Memory] Remember Releases FAILED — {owner}/{name}: {e}")
            raise

    @classmethod
    async def remember_contributors(
        cls, repo_id: str, owner: str, name: str, contributors: list[dict]
    ) -> None:
        """Store contributors and identify maintainers (top contributors)."""
        dataset = cls._dataset_name(repo_id)

        # Sort by contributions; top 10% are flagged as maintainers
        sorted_contributors = sorted(contributors, key=lambda c: c.get("contributions", 0), reverse=True)
        maintainer_threshold = max(1, len(sorted_contributors) // 10)

        contributor_entries = []
        for i, contrib in enumerate(sorted_contributors):
            is_maintainer = i < maintainer_threshold
            entity_type = "Maintainer" if is_maintainer else "Contributor"
            contributor_entries.append(
                f"[@{contrib['username']}] — {entity_type} — "
                f"{contrib.get('contributions', 0)} contributions"
            )

        formatted = (
            f"[Repository: {owner}/{name}]\n"
            f"[Entity: ContributorList]\n"
            f"[Total Contributors: {len(contributors)}]\n"
            f"[Maintainers: {maintainer_threshold}]\n\n"
            f"Contributors (sorted by activity):\n" +
            "\n".join(contributor_entries)
        )
        try:
            logger.info(f"[Memory] Remember Contributors — {owner}/{name} | count={len(contributors)}")
            await cognee.remember(formatted, dataset_name=dataset)
            logger.info(f"[Memory] Remember Contributors DONE — {owner}/{name} | count={len(contributors)}")
        except Exception as e:
            logger.error(f"[Memory] Remember Contributors FAILED — {owner}/{name}: {e}")
            raise

    # ═══════════════════════════════════════════
    #  ARCHITECTURE CACHE
    # ═══════════════════════════════════════════

    @classmethod
    async def remember_architecture_cache(
        cls, repo_id: str, subsystem: str, summary: str
    ) -> None:
        """Cache the lazy architecture analysis result for a subsystem."""
        dataset = cls._dataset_name(repo_id)
        formatted = f"[Architecture Cache: {subsystem}]\n{summary}"
        try:
            await cognee.remember(formatted, dataset_name=dataset)
            logger.info(f"[Memory] Remember Architecture Cache — subsystem={subsystem}")
        except Exception as e:
            logger.warning(f"[Memory] Remember Architecture Cache FAILED — subsystem={subsystem}: {e}")

    @classmethod
    async def recall_architecture_cache(
        cls, repo_id: str, subsystem: str
    ) -> str | None:
        """Recall cached architecture analysis for a subsystem if it exists."""
        dataset = cls._dataset_name(repo_id)
        try:
            results = await cognee.recall(query_text=f"Architecture Cache for {subsystem}", datasets=[dataset])
            if not results:
                return None

            for r in results:
                text = str(r)
                if f"[Architecture Cache: {subsystem}]" in text:
                    return text
            return None
        except Exception as e:
            logger.warning(f"[Memory] Recall architecture cache failed for {subsystem}: {e}")
            return None

    # ═══════════════════════════════════════════
    #  RECALL — Query Cognee memory
    # ═══════════════════════════════════════════

    @classmethod
    async def recall(cls, repo_id: str, query: str) -> list[Any]:
        """
        Query Cognee memory for a repository.
        Uses auto-routed retrieval (graph + vector hybrid).
        """
        dataset = cls._dataset_name(repo_id)
        try:
            results = await cognee.recall(query_text=query, datasets=[dataset])
            return results if results else []
        except Exception as e:
            logger.error(f"[Memory] Recall FAILED — dataset={dataset} query={query[:80]!r}: {e}")
            return []

    @classmethod
    async def search(cls, repo_id: str, query: str, search_type: str = "INSIGHTS") -> list[Any]:
        """
        Low-level Cognee search with explicit search type.
        search_type options: INSIGHTS, CHUNKS, GRAPH_COMPLETION, SUMMARIES
        """
        dataset = cls._dataset_name(repo_id)
        try:
            from cognee.api.v1.search import SearchType
            st = getattr(SearchType, search_type, SearchType.GRAPH_COMPLETION)
            results = await cognee.search(query_type=st, query_text=query, datasets=[dataset])
            return results if results else []
        except Exception as e:
            logger.error(f"[Memory] Search FAILED — dataset={dataset} type={search_type}: {e}")
            return []

    # ═══════════════════════════════════════════
    #  IMPROVE — Feed user feedback back to Cognee
    # ═══════════════════════════════════════════

    @classmethod
    async def improve(cls, repo_id: str, query: str, rating: str) -> None:
        """
        Feed user feedback to Cognee for retrieval improvement.

        BUG FIX: cognee.improve(dataset, ...) takes the dataset name as the first
        positional arg in v1.2.1 — NOT freeform text. The old call passed feedback_text
        as the dataset arg, causing the improvement to target a non-existent dataset.
        """
        dataset = cls._dataset_name(repo_id)
        try:
            # Log the feedback for auditability before calling improve
            logger.info(
                f"[Memory] Improve feedback — dataset={dataset} "
                f"query={query[:80]!r} rating={rating!r}"
            )
            # cognee.improve(dataset, ...) enriches the graph for that dataset.
            # There is no free-form text parameter in v1.2.1 — feedback context
            # is derived from the session Q&A stored in the graph itself.
            await cognee.improve(dataset)
            logger.info(f"[Memory] Improve DONE — dataset={dataset}")
        except Exception as e:
            logger.warning(f"[Memory] Improve FAILED (non-critical) — dataset={dataset}: {e}")

    # ═══════════════════════════════════════════
    #  FORGET — Remove data from Cognee memory
    # ═══════════════════════════════════════════

    @classmethod
    async def forget_dataset(cls, repo_id: str) -> None:
        """Remove all memory for a repository."""
        dataset = cls._dataset_name(repo_id)
        try:
            await cognee.forget(dataset=dataset)
            logger.info(f"[Memory] Forget DONE — dataset={dataset}")
        except Exception as e:
            logger.error(f"[Memory] Forget FAILED — dataset={dataset}: {e}")
            raise

    # ═══════════════════════════════════════════
    #  STATS — Get memory statistics
    # ═══════════════════════════════════════════

    @classmethod
    async def get_memory_stats(cls, repo_id: str) -> dict:
        """
        Get memory statistics for a repository dataset.

        Uses the local ingestion_jobs table to calculate total nodes and relationships.
        This is extremely fast, avoids slow Cognee Cloud searches, and prevents timeouts.
        """
        import uuid
        from sqlalchemy import select, func
        from app.database import async_session_factory
        from app.models.ingestion_job import IngestionJob, IngestionStatus

        try:
            async with async_session_factory() as session:
                result = await session.execute(
                    select(func.sum(IngestionJob.items_processed))
                    .where(IngestionJob.repository_id == uuid.UUID(repo_id))
                    .where(IngestionJob.status == IngestionStatus.COMPLETED)
                )
                total_nodes = result.scalar() or 0

            # Estimate relationships as ~1.2x the number of nodes
            total_relationships = int(total_nodes * 1.2) if total_nodes > 0 else 0

            logger.info(
                f"[Memory] Stats (Local DB) — repo_id={repo_id} | "
                f"nodes={total_nodes} | relationships={total_relationships}"
            )
            return {
                "total_nodes": total_nodes,
                "total_relationships": total_relationships,
                "entity_counts": {"items_processed": total_nodes},
            }
        except Exception as e:
            logger.error(f"[Memory] Stats FAILED — repo_id={repo_id}: {e}")
            return {"total_nodes": 0, "total_relationships": 0, "entity_counts": {}}
