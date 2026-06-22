"""
Mentor router — API endpoints for all AI mentor features.
"""
import uuid
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import get_db
from app.models.repository import Repository, RepositoryStatus
from app.services.mentor_engine import MentorEngine
from app.schemas.mentor import (
    FindIssueRequest, AnalyzeIssueRequest, ExploreDecisionRequest,
    QARequest, LearningPathRequest, ArchitectureRequest, ArchitectureResponse
)

router = APIRouter(prefix="/api/repositories", tags=["mentor"])


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
    result = await MentorEngine.generate_onboarding_guide(str(repo_id))
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
    return result


@router.post("/{repo_id}/analyze-issue")
async def analyze_issue(
    repo_id: uuid.UUID,
    request: AnalyzeIssueRequest,
    db: AsyncSession = Depends(get_db),
):
    """Feature 3: Contribution Assistant — analyze an issue for contribution."""
    await _get_ready_repo(repo_id, db)
    result = await MentorEngine.analyze_issue(str(repo_id), request.issue_number)
    return result


@router.get("/{repo_id}/maintainer-brain")
async def get_maintainer_brain(
    repo_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    """Feature 4: Maintainer Brain — analyze maintainer patterns and preferences."""
    await _get_ready_repo(repo_id, db)
    result = await MentorEngine.maintainer_brain(str(repo_id))
    return result


@router.post("/{repo_id}/explore-decision")
async def explore_decision(
    repo_id: uuid.UUID,
    request: ExploreDecisionRequest,
    db: AsyncSession = Depends(get_db),
):
    """Feature 5: Decision Explorer — understand why decisions were made."""
    await _get_ready_repo(repo_id, db)
    result = await MentorEngine.explore_decision(str(repo_id), request.question)
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
    return result


@router.get("/{repo_id}/graph")
async def get_knowledge_graph(
    repo_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    """Feature 7: Knowledge Graph — get nodes and edges for visualization."""
    await _get_ready_repo(repo_id, db)
    result = await MentorEngine.generate_knowledge_graph(str(repo_id))
    return result


@router.get("/{repo_id}/timeline")
async def get_timeline(
    repo_id: uuid.UUID,
    focus: str | None = None,
    db: AsyncSession = Depends(get_db),
):
    """Feature 8: Project Evolution Timeline."""
    await _get_ready_repo(repo_id, db)
    result = await MentorEngine.generate_timeline(str(repo_id), focus)
    return result


@router.post("/{repo_id}/learning-path")
async def get_learning_path(
    repo_id: uuid.UUID,
    request: LearningPathRequest,
    db: AsyncSession = Depends(get_db),
):
    """Feature 9: Personalized Learning Path."""
    await _get_ready_repo(repo_id, db)
    result = await MentorEngine.generate_learning_path(
        str(repo_id), request.issue_number, request.interests
    )
    return result


@router.post("/{repo_id}/architecture", response_model=ArchitectureResponse)
async def explore_architecture(
    repo_id: uuid.UUID,
    request: ArchitectureRequest,
    db: AsyncSession = Depends(get_db),
):
    """Feature 10: Architecture Explorer."""
    await _get_ready_repo(repo_id, db)
    # Using the existing lazy architecture analysis internal method
    overview = await MentorEngine._lazy_architecture_analysis(
        str(repo_id), "Architecture overview", request.subsystem
    )
    return ArchitectureResponse(
        subsystem=request.subsystem or "General Architecture",
        architecture_overview=overview
    )
