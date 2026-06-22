"""IngestionJob model — tracks each step of the repository ingestion pipeline."""
import uuid
import enum
from datetime import datetime, timezone
from sqlalchemy import String, Integer, DateTime, Enum, Text, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


class IngestionStep(str, enum.Enum):
    README = "readme"
    ISSUES = "issues"
    PULL_REQUESTS = "pull_requests"
    DISCUSSIONS = "discussions"
    CONTRIBUTORS = "contributors"
    RELEASES = "releases"
    MEMORY_GRAPH = "memory_graph"


class IngestionStatus(str, enum.Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class IngestionJob(Base):
    __tablename__ = "ingestion_jobs"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    repository_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("repositories.id"), nullable=False
    )
    step: Mapped[IngestionStep] = mapped_column(Enum(IngestionStep), nullable=False)
    status: Mapped[IngestionStatus] = mapped_column(
        Enum(IngestionStatus), default=IngestionStatus.PENDING
    )
    progress: Mapped[int] = mapped_column(Integer, default=0)  # 0-100
    items_processed: Mapped[int] = mapped_column(Integer, default=0)
    items_total: Mapped[int] = mapped_column(Integer, default=0)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationships
    repository = relationship("Repository", back_populates="ingestion_jobs")

    def __repr__(self) -> str:
        return f"<IngestionJob(step={self.step}, status={self.status}, progress={self.progress})>"
