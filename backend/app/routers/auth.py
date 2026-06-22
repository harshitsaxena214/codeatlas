"""
Authentication router — handles GitHub OAuth user sync.
"""
import uuid
from datetime import datetime, timezone, timedelta
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from jose import jwt

from app.database import get_db
from app.config import get_settings
from app.models.user import User
from app.schemas.user import GitHubUserSync, UserResponse

router = APIRouter(prefix="/api/auth", tags=["auth"])
settings = get_settings()


def create_access_token(data: dict) -> str:
    """Create a JWT access token."""
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


async def get_current_user(
    db: AsyncSession = Depends(get_db),
) -> User:
    """Dependency to get the current user. For MVP, uses github_id from header."""
    # In production, parse JWT from Authorization header
    # For MVP/hackathon, we accept github_id directly
    return None  # Placeholder — will be replaced with proper auth


@router.post("/github", response_model=UserResponse)
async def sync_github_user(
    user_data: GitHubUserSync,
    db: AsyncSession = Depends(get_db),
):
    """
    Sync GitHub user after OAuth sign-in.
    Creates or updates the user in PostgreSQL.
    Returns user data + JWT token.
    """
    # Check if user exists
    result = await db.execute(
        select(User).where(User.github_id == user_data.github_id)
    )
    user = result.scalar_one_or_none()

    if user:
        # Update existing user
        user.username = user_data.username
        user.email = user_data.email
        user.avatar_url = user_data.avatar_url
        if user_data.access_token:
            user.access_token = user_data.access_token
        user.updated_at = datetime.now(timezone.utc)
    else:
        # Create new user
        user = User(
            github_id=user_data.github_id,
            username=user_data.username,
            email=user_data.email,
            avatar_url=user_data.avatar_url,
            access_token=user_data.access_token,
        )
        db.add(user)

    await db.flush()
    await db.refresh(user)

    return user


@router.get("/me", response_model=UserResponse)
async def get_me(
    github_id: int,  # Query param for MVP
    db: AsyncSession = Depends(get_db),
):
    """Get current user info by GitHub ID."""
    result = await db.execute(
        select(User).where(User.github_id == github_id)
    )
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user
