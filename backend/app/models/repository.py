"""Repository model — stores analyzed GitHub repositories."""
import uuid
import enum
from datetime import datetime, timezone
from sqlalchemy import String, Integer, DateTime, Enum, Text, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


class RepositoryStatus(str, enum.Enum):
    PENDING = "pending"
    INGESTING = "ingesting"
    PROCESSING_MEMORY = "processing_memory"  # Stage 2: memory graph building
    READY = "ready"
    FAILED = "failed"


class Repository(Base):
    __tablename__ = "repositories"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    github_url: Mapped[str] = mapped_column(String(512), unique=True, nullable=False, index=True)
    owner: Mapped[str] = mapped_column(String(255), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    stars: Mapped[int] = mapped_column(Integer, default=0)
    forks: Mapped[int] = mapped_column(Integer, default=0)
    open_issues: Mapped[int] = mapped_column(Integer, default=0)
    language: Mapped[str | None] = mapped_column(String(100), nullable=True)
    topics: Mapped[str | None] = mapped_column(Text, nullable=True)  # JSON string of topics
    default_branch: Mapped[str] = mapped_column(String(100), default="main")

    # Cached dashboard counts
    contributor_count: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    pr_count: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    discussion_count: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    contribution_opportunities: Mapped[int] = mapped_column(Integer, default=0, server_default="0")

    # Cognee integration
    cognee_dataset_name: Mapped[str] = mapped_column(String(255), nullable=False)

    # Status tracking
    status: Mapped[RepositoryStatus] = mapped_column(
        Enum(RepositoryStatus), default=RepositoryStatus.PENDING
    )
    ingested_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    # Foreign keys
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False
    )

    # Relationships
    user = relationship("User", back_populates="repositories")
    ingestion_jobs = relationship("IngestionJob", back_populates="repository", lazy="selectin")
    feedbacks = relationship("Feedback", back_populates="repository", lazy="selectin")
    ai_cache = relationship("RepositoryAICache", back_populates="repository", uselist=False, cascade="all, delete-orphan", lazy="selectin")

    def __repr__(self) -> str:
        return f"<Repository(owner={self.owner}, name={self.name}, status={self.status})>"


class RepositoryAICache(Base):
    __tablename__ = "repository_ai_caches"

    repo_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("repositories.id", ondelete="CASCADE"), primary_key=True
    )
    dashboard: Mapped[str | None] = mapped_column(Text, nullable=True)
    timeline: Mapped[str | None] = mapped_column(Text, nullable=True)
    architecture: Mapped[str | None] = mapped_column(Text, nullable=True)
    learning_path: Mapped[str | None] = mapped_column(Text, nullable=True)
    maintainer_brain: Mapped[str | None] = mapped_column(Text, nullable=True)
    decision_explorer: Mapped[str | None] = mapped_column(Text, nullable=True)
    knowledge_graph: Mapped[str | None] = mapped_column(Text, nullable=True)
    generated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    commit_sha: Mapped[str | None] = mapped_column(String(255), nullable=True)
    status: Mapped[str] = mapped_column(String(50), default="pending")

    # Relationships
    repository = relationship("Repository", back_populates="ai_cache")

