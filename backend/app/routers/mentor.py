"""
Mentor router — API endpoints for all AI mentor features.
"""
import uuid
import json
import logging
from typing import Any
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import get_db
from app.models.repository import Repository, RepositoryStatus, RepositoryAICache
from app.services.mentor_engine import MentorEngine
from app.schemas.mentor import (
    FindIssueRequest, AnalyzeIssueRequest, ExploreDecisionRequest,
    QARequest, LearningPathRequest, ArchitectureRequest, ArchitectureResponse
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/repositories", tags=["mentor"])


# ─── Feature-level fallbacks ────────────────────────────────────────────────
# These defaults are returned whenever the LLM tier fails or produces an
# unparseable response.  They keep the frontend from displaying raw error text.
_FEATURE_FALLBACKS: dict[str, Any] = {
    "onboarding": {
        "project_summary": "Summary unavailable — please try again shortly.",
        "what_it_solves": "",
        "core_technologies": [],
        "key_maintainers": [],
        "project_culture": "",
        "important_discussions": [],
        "important_prs": [],
        "reading_path": [],
    },
    "find_issue": {"recommended_issues": [], "reasoning": "Unable to generate recommendations right now."},
    "contribution": {
        "issue_number": 0, "issue_title": "", "issue_url": "",
        "summary": "Analysis unavailable — please retry.",
        "difficulty": "unknown", "difficulty_score": 0,
        "related_discussions": [], "related_prs": [], "related_decisions": [],
        "maintainer_expectations": [], "suggested_starting_point": "",
        "estimated_effort": "", "potential_challenges": [], "recommended_approach": "",
    },
    "maintainer_brain": {
        "maintainer_profiles": [], "preferences": [],
        "review_patterns": [], "contribution_expectations": [],
        "common_rejection_reasons": [], "do_list": [], "dont_list": [],
    },
    "decision": {
        "question": "", "decision_summary": "Decision data unavailable.",
        "timeline": [], "related_discussions": [], "related_prs": [],
        "maintainer_comments": [], "alternatives_considered": [],
        "outcome": "", "reasoning": "",
    },
    "qa": {
        "question": "", "answer": "Unable to answer right now — please retry.",
        "citations": [], "confidence": 0.0, "follow_up_questions": [],
    },
    "graph": {"nodes": [], "edges": [], "summary": "Knowledge graph unavailable — please retry."},
    "timeline": {
        "events": [],
        "summary": "Timeline unavailable — please retry.",
    },
    "learning_path": {
        "title": "Learning Path", "description": "Unavailable right now.",
        "prerequisites": [], "steps": [], "key_concepts": [],
    },
}


def _sanitize_result(result: Any, feature: str) -> Any:
    """Guard against LLM error dicts propagating to the frontend.

    If `result` is a dict with an 'error' key (provider failure / quota) or
    is a plain string, return the appropriate feature fallback instead so the
    frontend always receives a correctly-shaped object.
    """
    # Raw string — LLM returned prose instead of JSON
    if isinstance(result, str):
        logger.warning(f"[{feature}] LLM returned raw text; substituting fallback.")
        fallback = dict(_FEATURE_FALLBACKS.get(feature, {}))
        # Embed the text where it makes sense
        if feature == "timeline":
            fallback["summary"] = result[:500]
        elif feature == "graph":
            fallback["summary"] = result[:500]
        elif feature == "qa":
            fallback["answer"] = result[:2000]
        return fallback

    # Error dict from the provider pipeline
    if isinstance(result, dict) and "error" in result and result["error"]:
        error_msg = str(result["error"])
        logger.warning(f"[{feature}] Provider error: {error_msg}; substituting fallback.")
        fallback = dict(_FEATURE_FALLBACKS.get(feature, {}))
        # Surface the error as a human-readable note in the appropriate field
        if feature == "onboarding":
            fallback["project_summary"] = f"Could not generate guide: {error_msg}"
        elif feature == "timeline":
            fallback["summary"] = f"Could not generate timeline: {error_msg}"
        elif feature == "graph":
            fallback["summary"] = f"Could not generate graph: {error_msg}"
        elif feature == "qa":
            fallback["answer"] = f"Could not answer: {error_msg}"
        elif feature == "maintainer_brain":
            fallback["preferences"] = [f"Error: {error_msg}"]
        elif feature == "decision":
            fallback["decision_summary"] = f"Could not analyze: {error_msg}"
        return fallback

    return result


async def _get_ready_repo(repo_id: uuid.UUID, db: AsyncSession) -> Repository:
    """Helper to get a repository that has been fully ingested."""
    result = await db.execute(select(Repository).where(Repository.id == repo_id))
    repo = result.scalar_one_or_none()
    if not repo:
        raise HTTPException(status_code=404, detail="Repository not found")
    if repo.status != RepositoryStatus.READY:
        raise HTTPException(
            status_code=400,
            detail=f"Repository is not ready. Current status: {repo.status.value}. Please complete ingestion first."
        )
    return repo


@router.get("/{repo_id}/onboarding")
async def get_onboarding_guide(
    repo_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    """Feature 1: Generate a contributor onboarding guide."""
    await _get_ready_repo(repo_id, db)
    
    # Check cache
    cache_res = await db.execute(select(RepositoryAICache).where(RepositoryAICache.repo_id == repo_id))
    cache = cache_res.scalar_one_or_none()
    if cache and cache.dashboard:
        try:
            logger.info("Cache Hit")
            cached = json.loads(cache.dashboard)
            if not (isinstance(cached, dict) and "error" in cached):
                return cached
        except Exception as e:
            logger.warning(f"Failed to read dashboard cache: {e}")

    logger.info("Cache Miss")
    logger.info("Generating Dashboard")
    result = await MentorEngine.generate_onboarding_guide(str(repo_id))
    result = _sanitize_result(result, "onboarding")
    
    # Save cache
    if not cache:
        cache = RepositoryAICache(repo_id=repo_id)
        db.add(cache)
    cache.dashboard = json.dumps(result, default=str)
    logger.info("Saving Cache")
    await db.commit()
    return result


@router.post("/{repo_id}/find-first-issue")
async def find_first_issue(
    repo_id: uuid.UUID,
    request: FindIssueRequest,
    db: AsyncSession = Depends(get_db),
):
    """Feature 2: Find My First Issue — personalized issue recommendations."""
    await _get_ready_repo(repo_id, db)
    result = await MentorEngine.find_first_issue(
        str(repo_id), request.experience_level, request.interest
    )
    return _sanitize_result(result, "find_issue")


@router.post("/{repo_id}/analyze-issue")
async def analyze_issue(
    repo_id: uuid.UUID,
    request: AnalyzeIssueRequest,
    db: AsyncSession = Depends(get_db),
):
    """Feature 3: Contribution Assistant — analyze an issue for contribution."""
    await _get_ready_repo(repo_id, db)
    result = await MentorEngine.analyze_issue(str(repo_id), request.issue_number)
    return _sanitize_result(result, "contribution")


@router.get("/{repo_id}/maintainer-brain")
async def get_maintainer_brain(
    repo_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    """Feature 4: Maintainer Brain — analyze maintainer patterns and preferences."""
    await _get_ready_repo(repo_id, db)
    
    # Check cache
    cache_res = await db.execute(select(RepositoryAICache).where(RepositoryAICache.repo_id == repo_id))
    cache = cache_res.scalar_one_or_none()
    if cache and cache.maintainer_brain:
        try:
            logger.info("Cache Hit")
            cached = json.loads(cache.maintainer_brain)
            if not (isinstance(cached, dict) and "error" in cached):
                return cached
        except Exception as e:
            logger.warning(f"Failed to read maintainer brain cache: {e}")

    logger.info("Cache Miss")
    result = await MentorEngine.maintainer_brain(str(repo_id))
    result = _sanitize_result(result, "maintainer_brain")
    
    # Save cache
    if not cache:
        cache = RepositoryAICache(repo_id=repo_id)
        db.add(cache)
    cache.maintainer_brain = json.dumps(result, default=str)
    logger.info("Saving Cache")
    await db.commit()
    return result


@router.post("/{repo_id}/explore-decision")
async def explore_decision(
    repo_id: uuid.UUID,
    request: ExploreDecisionRequest,
    db: AsyncSession = Depends(get_db),
):
    """Feature 5: Decision Explorer — understand why decisions were made."""
    await _get_ready_repo(repo_id, db)
    
    # Check cache
    cache_res = await db.execute(select(RepositoryAICache).where(RepositoryAICache.repo_id == repo_id))
    cache = cache_res.scalar_one_or_none()
    if cache and cache.decision_explorer:
        try:
            dec_cache = json.loads(cache.decision_explorer)
            if dec_cache.get("question") == request.question:
                cached_result = dec_cache["result"]
                if not (isinstance(cached_result, dict) and "error" in cached_result):
                    logger.info("Cache Hit")
                    return cached_result
        except Exception as e:
            logger.warning(f"Failed to read decision explorer cache: {e}")

    logger.info("Cache Miss")
    result = await MentorEngine.explore_decision(
        str(repo_id), request.question
    )
    result = _sanitize_result(result, "decision")
    result["question"] = result.get("question") or request.question
    
    # Save cache
    if not cache:
        cache = RepositoryAICache(repo_id=repo_id)
        db.add(cache)
    dec_cache = {"question": request.question, "result": result}
    cache.decision_explorer = json.dumps(dec_cache, default=str)
    logger.info("Saving Cache")
    await db.commit()
    return result


@router.post("/{repo_id}/ask")
async def ask_question(
    repo_id: uuid.UUID,
    request: QARequest,
    db: AsyncSession = Depends(get_db),
):
    """Feature 6: Repository Q&A — ask questions about the repository."""
    await _get_ready_repo(repo_id, db)
    result = await MentorEngine.answer_question(str(repo_id), request.question)
    result = _sanitize_result(result, "qa")
    if isinstance(result, dict):
        result["question"] = result.get("question") or request.question
    return result


@router.get("/{repo_id}/graph")
async def get_knowledge_graph(
    repo_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    """Feature 7: Knowledge Graph — get nodes and edges for visualization."""
    await _get_ready_repo(repo_id, db)
    
    # Check cache
    cache_res = await db.execute(select(RepositoryAICache).where(RepositoryAICache.repo_id == repo_id))
    cache = cache_res.scalar_one_or_none()
    if cache and cache.knowledge_graph:
        try:
            logger.info("Cache Hit")
            cached = json.loads(cache.knowledge_graph)
            if not (isinstance(cached, dict) and "error" in cached):
                return cached
        except Exception as e:
            logger.warning(f"Failed to read knowledge graph cache: {e}")

    logger.info("Cache Miss")
    result = await MentorEngine.generate_knowledge_graph(str(repo_id))
    result = _sanitize_result(result, "graph")
    
    # Save cache
    if not cache:
        cache = RepositoryAICache(repo_id=repo_id)
        db.add(cache)
    cache.knowledge_graph = json.dumps(result, default=str)
    logger.info("Saving Cache")
    await db.commit()
    return result


@router.get("/{repo_id}/timeline")
async def get_timeline(
    repo_id: uuid.UUID,
    focus: str | None = None,
    db: AsyncSession = Depends(get_db),
):
    """Feature 8: Project Evolution Timeline."""
    await _get_ready_repo(repo_id, db)
    
    # Check cache
    cache_res = await db.execute(select(RepositoryAICache).where(RepositoryAICache.repo_id == repo_id))
    cache = cache_res.scalar_one_or_none()
    if cache and cache.timeline:
        try:
            timeline_cache = json.loads(cache.timeline)
            if timeline_cache.get("focus") == focus:
                cached_result = timeline_cache["result"]
                if not (isinstance(cached_result, dict) and "error" in cached_result):
                    logger.info("Cache Hit")
                    return cached_result
        except Exception as e:
            logger.warning(f"Failed to read timeline cache: {e}")

    logger.info("Cache Miss")
    logger.info("Generating Timeline")
    result = await MentorEngine.generate_timeline(str(repo_id), focus)
    result = _sanitize_result(result, "timeline")
    
    # Save cache
    if not cache:
        cache = RepositoryAICache(repo_id=repo_id)
        db.add(cache)
    timeline_cache = {"focus": focus, "result": result}
    cache.timeline = json.dumps(timeline_cache, default=str)
    logger.info("Saving Cache")
    await db.commit()
    return result


@router.post("/{repo_id}/learning-path")
async def get_learning_path(
    repo_id: uuid.UUID,
    request: LearningPathRequest,
    db: AsyncSession = Depends(get_db),
):
    """Feature 9: Personalized Learning Path."""
    await _get_ready_repo(repo_id, db)
    
    # Check cache
    cache_res = await db.execute(select(RepositoryAICache).where(RepositoryAICache.repo_id == repo_id))
    cache = cache_res.scalar_one_or_none()
    if cache and cache.learning_path:
        try:
            lp_cache = json.loads(cache.learning_path)
            if lp_cache.get("issue_number") == request.issue_number and lp_cache.get("interests") == request.interests:
                cached_result = lp_cache["result"]
                if not (isinstance(cached_result, dict) and "error" in cached_result):
                    logger.info("Cache Hit")
                    return cached_result
        except Exception as e:
            logger.warning(f"Failed to read learning path cache: {e}")

    logger.info("Cache Miss")
    result = await MentorEngine.generate_learning_path(
        str(repo_id), request.issue_number, request.interests
    )
    result = _sanitize_result(result, "learning_path")
    
    # Save cache
    if not cache:
        cache = RepositoryAICache(repo_id=repo_id)
        db.add(cache)
    lp_cache = {"issue_number": request.issue_number, "interests": request.interests, "result": result}
    cache.learning_path = json.dumps(lp_cache, default=str)
    logger.info("Saving Cache")
    await db.commit()
    return result


@router.post("/{repo_id}/architecture", response_model=ArchitectureResponse)
async def explore_architecture(
    repo_id: uuid.UUID,
    request: ArchitectureRequest,
    db: AsyncSession = Depends(get_db),
):
    """Feature 10: Architecture Explorer."""
    await _get_ready_repo(repo_id, db)
    
    # Check cache
    cache_res = await db.execute(select(RepositoryAICache).where(RepositoryAICache.repo_id == repo_id))
    cache = cache_res.scalar_one_or_none()
    if cache and cache.architecture:
        try:
            arch_cache = json.loads(cache.architecture)
            if arch_cache.get("subsystem") == request.subsystem:
                logger.info("Cache Hit")
                return ArchitectureResponse(
                    subsystem=request.subsystem or "General Architecture",
                    architecture_overview=arch_cache["result"]
                )
        except Exception as e:
            logger.warning(f"Failed to read architecture cache: {e}")

    logger.info("Cache Miss")
    logger.info("Generating Architecture")
    overview = await MentorEngine._lazy_architecture_analysis(
        str(repo_id), "Architecture overview", request.subsystem
    )
    
    # Save cache
    if not cache:
        cache = RepositoryAICache(repo_id=repo_id)
        db.add(cache)
    arch_cache = {"subsystem": request.subsystem, "result": overview}
    cache.architecture = json.dumps(arch_cache, default=str)
    logger.info("Saving Cache")
    await db.commit()
    
    return ArchitectureResponse(
        subsystem=request.subsystem or "General Architecture",
        architecture_overview=overview
    )


@router.post("/{repo_id}/refresh-cache")
async def refresh_cache(
    repo_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    """Manual cache refresh endpoint. Invalidates cache and triggers background generation."""
    await _get_ready_repo(repo_id, db)
    
    # Check if cache entry exists
    result = await db.execute(select(RepositoryAICache).where(RepositoryAICache.repo_id == repo_id))
    cache = result.scalar_one_or_none()
    if cache:
        logger.info("Cache Invalidated")
        
    # Trigger background generation
    from app.services.ai_cache import trigger_background_generation
    trigger_background_generation(repo_id)
    
    return {"message": "Background Cache Generation Started"}
