import logging
import json
import uuid
import asyncio
from datetime import datetime, timezone
from sqlalchemy import select
from app.database import async_session_factory
from app.models.repository import Repository, RepositoryAICache
from app.services.mentor_engine import MentorEngine
from app.services.github_fetcher import GitHubFetcher

logger = logging.getLogger(__name__)

async def generate_all_cached_features_task(repo_id: uuid.UUID, commit_sha: str | None = None):
    """Background task to generate and cache all AI features sequentially."""
    logger.info("Background Generation Started")
    
    # 1. Initialize Cache entry
    async with async_session_factory() as db:
        result = await db.execute(select(Repository).where(Repository.id == repo_id))
        repo = result.scalar_one_or_none()
        if not repo:
            logger.error(f"Repository {repo_id} not found. Aborting cache generation.")
            return
            
        owner, name = repo.owner, repo.name
        
        # If commit SHA not provided, fetch it
        if not commit_sha:
            try:
                fetcher = GitHubFetcher()
                commit_sha = await asyncio.to_thread(fetcher.fetch_latest_commit_sha, owner, name)
            except Exception as e:
                logger.warning(f"Could not fetch latest commit SHA: {e}")

        # Get or create cache entry
        result_cache = await db.execute(select(RepositoryAICache).where(RepositoryAICache.repo_id == repo_id))
        cache = result_cache.scalar_one_or_none()
        if not cache:
            cache = RepositoryAICache(repo_id=repo_id)
            db.add(cache)
        else:
            logger.info("Cache Invalidated")
        
        cache.status = "generating"
        cache.commit_sha = commit_sha
        cache.generated_at = None
        await db.commit()

    try:
        # Sequential Generation
        # --- Feature 1: Dashboard (Onboarding Guide) ---
        logger.info("Generating Dashboard")
        dashboard_data = await MentorEngine.generate_onboarding_guide(str(repo_id))
        async with async_session_factory() as db:
            result_cache = await db.execute(select(RepositoryAICache).where(RepositoryAICache.repo_id == repo_id))
            cache = result_cache.scalar_one()
            cache.dashboard = json.dumps(dashboard_data, default=str) if not isinstance(dashboard_data, str) else dashboard_data
            cache.generated_at = datetime.now(timezone.utc)
            await db.commit()
        logger.info("Saving Cache")

        # --- Feature 2: Timeline ---
        logger.info("Generating Timeline")
        timeline_data = await MentorEngine.generate_timeline(str(repo_id), focus=None)
        async with async_session_factory() as db:
            result_cache = await db.execute(select(RepositoryAICache).where(RepositoryAICache.repo_id == repo_id))
            cache = result_cache.scalar_one()
            timeline_cache = {"focus": None, "result": timeline_data}
            cache.timeline = json.dumps(timeline_cache, default=str)
            cache.generated_at = datetime.now(timezone.utc)
            await db.commit()
        logger.info("Saving Cache")

        # --- Feature 3: Architecture ---
        logger.info("Generating Architecture")
        architecture_data = await MentorEngine._lazy_architecture_analysis(str(repo_id), "Architecture overview", subsystem=None)
        async with async_session_factory() as db:
            result_cache = await db.execute(select(RepositoryAICache).where(RepositoryAICache.repo_id == repo_id))
            cache = result_cache.scalar_one()
            architecture_cache = {"subsystem": None, "result": architecture_data}
            cache.architecture = json.dumps(architecture_cache, default=str)
            cache.generated_at = datetime.now(timezone.utc)
            await db.commit()
        logger.info("Saving Cache")

        # --- Feature 4: Learning Path ---
        logger.info("Generating Learning Path")
        learning_path_data = await MentorEngine.generate_learning_path(str(repo_id), issue_number=None, interests=[])
        async with async_session_factory() as db:
            result_cache = await db.execute(select(RepositoryAICache).where(RepositoryAICache.repo_id == repo_id))
            cache = result_cache.scalar_one()
            learning_path_cache = {"issue_number": None, "interests": [], "result": learning_path_data}
            cache.learning_path = json.dumps(learning_path_cache, default=str)
            cache.generated_at = datetime.now(timezone.utc)
            await db.commit()
        logger.info("Saving Cache")

        # --- Feature 5: Maintainer Brain ---
        logger.info("Generating Maintainer Brain")
        maintainer_brain_data = await MentorEngine.maintainer_brain(str(repo_id))
        async with async_session_factory() as db:
            result_cache = await db.execute(select(RepositoryAICache).where(RepositoryAICache.repo_id == repo_id))
            cache = result_cache.scalar_one()
            cache.maintainer_brain = json.dumps(maintainer_brain_data, default=str) if not isinstance(maintainer_brain_data, str) else maintainer_brain_data
            cache.generated_at = datetime.now(timezone.utc)
            await db.commit()
        logger.info("Saving Cache")

        # --- Feature 6: Decision Explorer ---
        logger.info("Generating Decision Explorer")
        default_question = "What are the major architectural and design decisions made in this repository?"
        decision_explorer_data = await MentorEngine.explore_decision(str(repo_id), default_question)
        async with async_session_factory() as db:
            result_cache = await db.execute(select(RepositoryAICache).where(RepositoryAICache.repo_id == repo_id))
            cache = result_cache.scalar_one()
            decision_cache = {"question": default_question, "result": decision_explorer_data}
            cache.decision_explorer = json.dumps(decision_cache, default=str)
            cache.generated_at = datetime.now(timezone.utc)
            await db.commit()
        logger.info("Saving Cache")

        # --- Feature 7: Knowledge Graph Metadata ---
        logger.info("Generating Knowledge Graph Metadata")
        knowledge_graph_data = await MentorEngine.generate_knowledge_graph(str(repo_id))
        async with async_session_factory() as db:
            result_cache = await db.execute(select(RepositoryAICache).where(RepositoryAICache.repo_id == repo_id))
            cache = result_cache.scalar_one()
            cache.knowledge_graph = json.dumps(knowledge_graph_data, default=str) if not isinstance(knowledge_graph_data, str) else knowledge_graph_data
            cache.generated_at = datetime.now(timezone.utc)
            await db.commit()
        logger.info("Saving Cache")

        # Success - mark completed
        async with async_session_factory() as db:
            result_cache = await db.execute(select(RepositoryAICache).where(RepositoryAICache.repo_id == repo_id))
            cache = result_cache.scalar_one()
            cache.status = "completed"
            cache.generated_at = datetime.now(timezone.utc)
            await db.commit()
        logger.info("Background Generation Completed")

    except Exception as e:
        logger.error(f"Generation Failed: {e}", exc_info=True)
        async with async_session_factory() as db:
            result_cache = await db.execute(select(RepositoryAICache).where(RepositoryAICache.repo_id == repo_id))
            cache = result_cache.scalar_one_or_none()
            if cache:
                cache.status = "failed"
                await db.commit()

def trigger_background_generation(repo_id: uuid.UUID, commit_sha: str | None = None):
    """Spawns the background generation task on the current event loop."""
    asyncio.create_task(generate_all_cached_features_task(repo_id, commit_sha))
