"""
Feedback router — handles the Cognee Improve lifecycle.
Users rate AI responses as helpful/not helpful, which feeds back into Cognee.
"""
import uuid
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import get_db
from app.models.feedback import Feedback
from app.models.repository import Repository
from app.schemas.feedback import FeedbackCreate, FeedbackResponse
from app.services.cognee_memory import CogneeMemoryService

router = APIRouter(prefix="/api/repositories", tags=["feedback"])


@router.post("/{repo_id}/feedback", response_model=FeedbackResponse)
async def submit_feedback(
    repo_id: uuid.UUID,
    feedback_data: FeedbackCreate,
    db: AsyncSession = Depends(get_db),
):
    """
    Submit feedback on an AI response.
    Feeds back to Cognee for retrieval improvement.
    """
    # Verify repository exists
    result = await db.execute(select(Repository).where(Repository.id == repo_id))
    repo = result.scalar_one_or_none()
    if not repo:
        raise HTTPException(status_code=404, detail="Repository not found")

    # Store feedback in PostgreSQL
    feedback = Feedback(
        repository_id=repo_id,
        user_id=uuid.UUID("00000000-0000-0000-0000-000000000000"),  # Default user for MVP
        feature=feedback_data.feature,
        query=feedback_data.query,
        response_summary=feedback_data.response_summary,
        rating=feedback_data.rating,
        comment=feedback_data.comment,
    )
    db.add(feedback)
    await db.flush()
    await db.refresh(feedback)

    # Feed back to Cognee for improvement
    try:
        await CogneeMemoryService.improve(
            str(repo_id),
            feedback_data.query,
            feedback_data.rating.value,
        )
    except Exception as e:
        pass  # Non-blocking

    return feedback


@router.get("/{repo_id}/feedback", response_model=list[FeedbackResponse])
async def list_feedback(
    repo_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    """List all feedback for a repository."""
    result = await db.execute(
        select(Feedback).where(Feedback.repository_id == repo_id)
        .order_by(Feedback.created_at.desc())
    )
    return result.scalars().all()
