"""
Repository router — CRUD operations for repositories.
"""
import uuid
import json
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import get_db
from app.models.repository import Repository, RepositoryStatus
from app.schemas.repository import RepositoryCreate, RepositoryResponse, RepositoryListItem, RepositoryDashboard
from app.services.github_fetcher import GitHubFetcher
from app.services.cognee_memory import CogneeMemoryService

router = APIRouter(prefix="/api/repositories", tags=["repositories"])


@router.post("/", response_model=RepositoryResponse)
async def create_repository(
    repo_data: RepositoryCreate,
    db: AsyncSession = Depends(get_db),
):
    """
    Add a new repository for analysis.
    Fetches metadata from GitHub and creates the database record.
    """
    # Check if already exists
    result = await db.execute(
        select(Repository).where(Repository.github_url == repo_data.github_url.rstrip("/"))
    )
    existing = result.scalar_one_or_none()
    if existing:
        return existing

    # Fetch metadata from GitHub
    fetcher = GitHubFetcher()
    try:
        owner, name = fetcher.parse_repo_url(repo_data.github_url)
        metadata = fetcher.fetch_repo_metadata(owner, name)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to fetch repository: {str(e)}")

    # Create repository record
    repo_id = uuid.uuid4()
    repo = Repository(
        id=repo_id,
        github_url=repo_data.github_url.rstrip("/"),
        owner=metadata["owner"],
        name=metadata["name"],
        description=metadata.get("description"),
        stars=metadata.get("stars", 0),
        forks=metadata.get("forks", 0),
        open_issues=metadata.get("open_issues", 0),
        language=metadata.get("language"),
        topics=json.dumps(metadata.get("topics", [])),
        default_branch=metadata.get("default_branch", "main"),
        cognee_dataset_name=f"repo_{repo_id}",
        status=RepositoryStatus.PENDING,
        user_id=uuid.UUID(repo_data.user_id) if repo_data.user_id else uuid.UUID("00000000-0000-0000-0000-000000000000"),
    )
    db.add(repo)
    await db.flush()
    await db.refresh(repo)

    return repo


@router.get("/", response_model=list[RepositoryListItem])
async def list_repositories(
    db: AsyncSession = Depends(get_db),
):
    """List all analyzed repositories."""
    result = await db.execute(
        select(Repository).order_by(Repository.created_at.desc())
    )
    return result.scalars().all()


@router.get("/{repo_id}", response_model=RepositoryResponse)
async def get_repository(
    repo_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    """Get a single repository by ID."""
    result = await db.execute(
        select(Repository).where(Repository.id == repo_id)
    )
    repo = result.scalar_one_or_none()
    if not repo:
        raise HTTPException(status_code=404, detail="Repository not found")
    return repo


@router.get("/{repo_id}/dashboard", response_model=RepositoryDashboard)
async def get_repository_dashboard(
    repo_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    """Get full dashboard data for a repository."""
    result = await db.execute(
        select(Repository).where(Repository.id == repo_id)
    )
    repo = result.scalar_one_or_none()
    if not repo:
        raise HTTPException(status_code=404, detail="Repository not found")

    # Get memory stats from Cognee
    memory_stats = await CogneeMemoryService.get_memory_stats(str(repo_id))

    topics = []
    try:
        topics = json.loads(repo.topics) if repo.topics else []
    except json.JSONDecodeError:
        pass

    return RepositoryDashboard(
        id=repo.id,
        owner=repo.owner,
        name=repo.name,
        description=repo.description,
        stars=repo.stars,
        forks=repo.forks,
        open_issues=repo.open_issues,
        language=repo.language,
        topics=topics,
        default_branch=repo.default_branch,
        status=repo.status,
        ingested_at=repo.ingested_at,
        memory_nodes=memory_stats.get("total_nodes", 0),
        memory_relationships=memory_stats.get("total_relationships", 0),
        contributor_count=repo.contributor_count,
        pr_count=repo.pr_count,
        discussion_count=repo.discussion_count,
        technology_stack=topics,
        contribution_opportunities=repo.contribution_opportunities,
        recent_activity=[],
    )


@router.post("/{repo_id}/refresh-metadata", response_model=RepositoryResponse)
async def refresh_repository_metadata(
    repo_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    """Re-fetch GitHub metadata (stars, forks, issues, etc.) for a repository."""
    result = await db.execute(
        select(Repository).where(Repository.id == repo_id)
    )
    repo = result.scalar_one_or_none()
    if not repo:
        raise HTTPException(status_code=404, detail="Repository not found")

    fetcher = GitHubFetcher()
    try:
        owner, name = fetcher.parse_repo_url(repo.github_url)
        metadata = fetcher.fetch_repo_metadata(owner, name)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to refresh from GitHub: {str(e)}")

    repo.description = metadata.get("description", repo.description)
    repo.stars = metadata.get("stars", repo.stars)
    repo.forks = metadata.get("forks", repo.forks)
    repo.open_issues = metadata.get("open_issues", repo.open_issues)
    repo.language = metadata.get("language", repo.language)
    repo.topics = json.dumps(metadata.get("topics", []))
    repo.default_branch = metadata.get("default_branch", repo.default_branch)

    await db.commit()
    await db.refresh(repo)
    return repo


@router.delete("/{repo_id}")
async def delete_repository(
    repo_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    """Delete a repository and its Cognee memory."""
    result = await db.execute(
        select(Repository).where(Repository.id == repo_id)
    )
    repo = result.scalar_one_or_none()
    if not repo:
        raise HTTPException(status_code=404, detail="Repository not found")

    # Forget Cognee memory
    try:
        await CogneeMemoryService.forget_dataset(str(repo_id))
    except Exception as e:
        pass  # Non-blocking

    # Delete related ingestion jobs and feedbacks to avoid foreign key constraints
    from sqlalchemy import delete
    from app.models.ingestion_job import IngestionJob
    from app.models.feedback import Feedback

    await db.execute(delete(IngestionJob).where(IngestionJob.repository_id == repo_id))
    await db.execute(delete(Feedback).where(Feedback.repository_id == repo_id))

    await db.delete(repo)
    return {"message": "Repository deleted"}
