"""
Ingestion router — manages the repository ingestion pipeline.
Supports Server-Sent Events (SSE) for real-time progress updates.

ARCHITECTURE:
  Stage 1 — Fast Profiling  (~10–20s): Fetches lightweight metadata + generates
             Repository DNA. Sets repo status = READY immediately so the
             Dashboard is available while Stage 2 runs in the background.

  Stage 2 — Memory Graph (~30–120s): Ingests issues, PRs, discussions,
             contributors, and releases into Cognee. Runs concurrently using
             asyncio.gather() for maximum throughput. Each step is isolated —
             a single failure does NOT kill the rest of the pipeline.

RELIABILITY IMPROVEMENTS:
  - DNA generation failure is non-fatal: raw metadata is stored as a minimal
    DNA record so the dashboard still works.
  - All Stage 2 memory writes are parallelized and individually wrapped in
    try/except — one bad step never blocks the others.
  - All GitHub fetches in Stage 1 are parallelized with asyncio.gather().
  - LLMService now uses a tiered provider strategy with automatic fallback.
"""
import uuid
import json
import asyncio
import logging
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete

from app.database import get_db, async_session_factory
from app.models.repository import Repository, RepositoryStatus
from app.models.ingestion_job import IngestionJob, IngestionStep, IngestionStatus
from app.schemas.ingestion import IngestionStatusResponse, IngestionJobResponse
from app.services.github_fetcher import GitHubFetcher
from app.services.cognee_memory import CogneeMemoryService

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/repositories", tags=["ingestion"])

# In-memory progress store for SSE (per repository)
_ingestion_progress: dict[str, list[dict]] = {}


def _emit_progress(
    repo_id: str,
    step: str,
    status: str,
    progress: int,
    message: str,
    items_processed: int = 0,
    items_total: int = 0,
):
    """Add a progress event to the in-memory store."""
    if repo_id not in _ingestion_progress:
        _ingestion_progress[repo_id] = []
    event = {
        "step": step,
        "status": status,
        "progress": progress,
        "message": message,
        "items_processed": items_processed,
        "items_total": items_total,
    }
    _ingestion_progress[repo_id].append(event)


# ═══════════════════════════════════════════════════════════════════════════════
#  INGESTION PIPELINE
# ═══════════════════════════════════════════════════════════════════════════════

async def _run_ingestion(repo_id: str, owner: str, name: str):
    """
    Background task: runs the full ingestion pipeline.

    Stage 1 — Fast Profiling  (parallel GitHub fetches → LLM DNA → READY)
    Stage 2 — Memory Graph    (parallel Cognee writes, each step isolated)
    """
    fetcher = GitHubFetcher()
    commit_sha = ""
    try:
        commit_sha = await asyncio.to_thread(fetcher.fetch_latest_commit_sha, owner, name)
    except Exception as e:
        logger.warning(f"Could not fetch latest commit SHA: {e}")

    async with async_session_factory() as db:
        try:
            # ── Initialise job records ───────────────────────────────────────
            result = await db.execute(select(Repository).where(Repository.id == uuid.UUID(repo_id)))
            repo = result.scalar_one()
            repo.status = RepositoryStatus.INGESTING

            await db.execute(delete(IngestionJob).where(IngestionJob.repository_id == uuid.UUID(repo_id)))
            await db.commit()

            steps = [
                IngestionStep.README,
                IngestionStep.ISSUES,
                IngestionStep.PULL_REQUESTS,
                IngestionStep.DISCUSSIONS,
                IngestionStep.CONTRIBUTORS,
                IngestionStep.RELEASES,
                IngestionStep.MEMORY_GRAPH,
            ]
            for step in steps:
                db.add(IngestionJob(
                    repository_id=uuid.UUID(repo_id),
                    step=step,
                    status=IngestionStatus.PENDING,
                ))
            await db.commit()

            # ── STAGE 1: FAST REPOSITORY PROFILING ──────────────────────────
            _emit_progress(repo_id, "readme", "running", 5, "Stage 1: Fetching repository data...")
            await _update_job_status(db, repo_id, IngestionStep.README, IngestionStatus.RUNNING, 5, 0, 1)

            # ── Parallel GitHub fetches ──────────────────────────────────────
            # All network I/O runs concurrently — dramatically faster for large repos
            (
                readme,
                top_level_struct,
                pkg_json,
                pyproject,
                go_mod,
                cargo_toml,
                composer_json,
                issues,
                prs,
                discussions,
                contributors,
                releases,
            ) = await asyncio.gather(
                asyncio.to_thread(fetcher.fetch_readme, owner, name),
                asyncio.to_thread(fetcher.fetch_top_level_structure, owner, name),
                asyncio.to_thread(fetcher.fetch_file_content, owner, name, "package.json"),
                asyncio.to_thread(fetcher.fetch_file_content, owner, name, "pyproject.toml"),
                asyncio.to_thread(fetcher.fetch_file_content, owner, name, "go.mod"),
                asyncio.to_thread(fetcher.fetch_file_content, owner, name, "Cargo.toml"),
                asyncio.to_thread(fetcher.fetch_file_content, owner, name, "composer.json"),
                asyncio.to_thread(fetcher.fetch_issues, owner, name, 20),
                asyncio.to_thread(fetcher.fetch_pull_requests, owner, name, 20),
                fetcher.fetch_discussions(owner, name, 20),
                asyncio.to_thread(fetcher.fetch_contributors, owner, name),
                asyncio.to_thread(fetcher.fetch_releases, owner, name, 20),
                return_exceptions=True,  # never let one fetch kill the whole gather
            )

            # Normalise: replace exceptions from fetch with empty defaults
            readme         = readme         if isinstance(readme, str)  else ""
            top_level_struct = top_level_struct if isinstance(top_level_struct, list) else []
            pkg_json       = pkg_json       if isinstance(pkg_json, str)  else ""
            pyproject      = pyproject      if isinstance(pyproject, str)  else ""
            go_mod         = go_mod         if isinstance(go_mod, str)    else ""
            cargo_toml     = cargo_toml     if isinstance(cargo_toml, str) else ""
            composer_json  = composer_json  if isinstance(composer_json, str) else ""
            issues         = issues         if isinstance(issues, list)   else []
            prs            = prs            if isinstance(prs, list)      else []
            discussions    = discussions    if isinstance(discussions, list) else []
            contributors   = contributors   if isinstance(contributors, list) else []
            releases       = releases       if isinstance(releases, list)  else []

            _emit_progress(repo_id, "readme", "running", 20, "Generating Repository DNA...")

            # ── DNA generation (LLM call via ingestion tier) ─────────────────
            from pydantic import BaseModel

            class RepositoryDNA(BaseModel):
                tech_stack: list[str]
                repository_type: str
                health: str
                complexity_score: int
                contribution_friendliness: str
                architecture_overview: str

            from app.services.llm_service import LLMService

            dna_prompt = (
                f"Analyze this repository.\n"
                f"README: {readme[:2000]}\n"
                f"Structure: {top_level_struct}\n"
                f"package.json: {pkg_json[:500]}\n"
                f"pyproject.toml: {pyproject[:500]}\n"
                f"go.mod: {go_mod[:500]}\n"
                f"Cargo.toml: {cargo_toml[:500]}\n"
                f"composer.json: {composer_json[:500]}\n"
                f"Generate the Repository DNA."
            )

            # Use the ingestion-tier provider (fast, high-RPM)
            dna_result = await LLMService.generate_for_ingestion(
                system_prompt="You are an expert software architect analyzing a repository.",
                user_prompt=dna_prompt,
                response_model=RepositoryDNA,
            )

            # ── DNA storage — graceful degradation if LLM failed ─────────────
            dna_stored = False
            if isinstance(dna_result, dict) and "error" not in dna_result:
                try:
                    await CogneeMemoryService.remember_dna(repo_id, owner, name, dna_result)
                    dna_stored = True
                except Exception as e:
                    logger.error(f"Cognee DNA store failed (non-fatal): {e}")
            else:
                # LLM failed → build a minimal DNA from raw metadata so dashboard works
                logger.warning(
                    f"DNA generation failed for {owner}/{name} "
                    f"(error: {dna_result.get('error') if isinstance(dna_result, dict) else dna_result}). "
                    f"Storing minimal fallback DNA."
                )
                # Infer tech stack from manifest files present
                tech_stack = []
                if pkg_json:    tech_stack.append("JavaScript/Node.js")
                if pyproject:   tech_stack.append("Python")
                if go_mod:      tech_stack.append("Go")
                if cargo_toml:  tech_stack.append("Rust")
                if composer_json: tech_stack.append("PHP")
                if not tech_stack and top_level_struct:
                    tech_stack = ["Unknown"]

                fallback_dna = {
                    "tech_stack": tech_stack,
                    "repository_type": "library",
                    "health": "unknown",
                    "complexity_score": 5,
                    "contribution_friendliness": "unknown",
                    "architecture_overview": (
                        f"Repository {owner}/{name}. "
                        f"Top-level structure: {', '.join(top_level_struct[:10])}."
                    ),
                }
                try:
                    await CogneeMemoryService.remember_dna(repo_id, owner, name, fallback_dna)
                    dna_stored = True
                except Exception as e:
                    logger.error(f"Fallback DNA store also failed: {e}")

            # Store README in Cognee memory
            if readme:
                try:
                    await CogneeMemoryService.remember_readme(repo_id, owner, name, readme)
                except Exception as e:
                    logger.error(f"README Cognee store failed (non-fatal): {e}")

            await _update_job_status(db, repo_id, IngestionStep.README, IngestionStatus.COMPLETED, 100, 1, 1)

            # ── Mark repository PROCESSING_MEMORY — DNA ready, memory graph starting ──
            # BUG FIX: Previously set READY here, which allowed Timeline/KG/Q&A to
            # open before any data was in Cognee. READY now means memory is available.
            result = await db.execute(select(Repository).where(Repository.id == uuid.UUID(repo_id)))
            repo = result.scalar_one()
            repo.status = RepositoryStatus.PROCESSING_MEMORY

            repo.contributor_count = len(contributors) if isinstance(contributors, list) else 0
            repo.pr_count = len(prs) if isinstance(prs, list) else 0
            repo.discussion_count = len(discussions) if isinstance(discussions, list) else 0

            # Count opportunities (good first issues / help wanted)
            opp_count = 0
            if isinstance(issues, list):
                for issue in issues:
                    labels = [lbl.lower() for lbl in issue.get("labels", [])]
                    if "good first issue" in labels or "help wanted" in labels:
                        opp_count += 1
            repo.contribution_opportunities = opp_count

            await db.commit()

            _emit_progress(repo_id, "memory_graph", "running", 40,
                           "Stage 1 complete. Building Memory Graph...")

            # ── STAGE 2: MEMORY GRAPH CONSTRUCTION (parallel, isolated) ──────
            # All Cognee memory writes run concurrently. Each is wrapped in
            # try/except so a single failure never blocks the others.
            logger.info(f"[Ingestion] Memory Graph Started — {owner}/{name}")
            _emit_progress(repo_id, "issues", "running", 40, "Building Memory Graph...")

            await _update_job_status(db, repo_id, IngestionStep.ISSUES,       IngestionStatus.RUNNING, 40, 0, len(issues))
            await _update_job_status(db, repo_id, IngestionStep.PULL_REQUESTS, IngestionStatus.RUNNING, 40, 0, len(prs))
            await _update_job_status(db, repo_id, IngestionStep.DISCUSSIONS,   IngestionStatus.RUNNING, 40, 0, len(discussions))
            await _update_job_status(db, repo_id, IngestionStep.CONTRIBUTORS,  IngestionStatus.RUNNING, 40, 0, len(contributors))
            await _update_job_status(db, repo_id, IngestionStep.RELEASES,      IngestionStatus.RUNNING, 40, 0, len(releases))

            async def _safe_remember_issues():
                if issues:
                    await CogneeMemoryService.remember_issues(repo_id, owner, name, issues)

            async def _safe_remember_prs():
                if prs:
                    await CogneeMemoryService.remember_pull_requests(repo_id, owner, name, prs)

            async def _safe_remember_discussions():
                if discussions:
                    await CogneeMemoryService.remember_discussions(repo_id, owner, name, discussions)

            async def _safe_remember_contributors():
                if contributors:
                    await CogneeMemoryService.remember_contributors(repo_id, owner, name, contributors)

            async def _safe_remember_releases():
                if releases:
                    await CogneeMemoryService.remember_releases(repo_id, owner, name, releases)

            # Fire all Cognee writes concurrently — return_exceptions so one
            # failure doesn't cancel the rest
            memory_results = await asyncio.gather(
                _safe_remember_issues(),
                _safe_remember_prs(),
                _safe_remember_discussions(),
                _safe_remember_contributors(),
                _safe_remember_releases(),
                return_exceptions=True,
            )

            # Log any per-step failures but continue — each step is independent
            step_names = ["issues", "pull_requests", "discussions", "contributors", "releases"]
            step_enums = [
                IngestionStep.ISSUES, IngestionStep.PULL_REQUESTS,
                IngestionStep.DISCUSSIONS, IngestionStep.CONTRIBUTORS, IngestionStep.RELEASES,
            ]
            step_counts = [len(issues), len(prs), len(discussions), len(contributors), len(releases)]

            memory_failed = False
            for i, (step_result, step_name, step_enum, count) in enumerate(
                zip(memory_results, step_names, step_enums, step_counts)
            ):
                if isinstance(step_result, Exception):
                    memory_failed = True
                    logger.error(f"[Ingestion] Memory Graph step '{step_name}' FAILED (non-fatal): {step_result}")
                    await _update_job_status(
                        db, repo_id, step_enum, IngestionStatus.FAILED, 0, 0, count,
                        error_message=str(step_result)[:500],
                    )
                else:
                    await _update_job_status(
                        db, repo_id, step_enum, IngestionStatus.COMPLETED, 100, count, count
                    )

            # ── Mark repository READY — memory graph is now populated ─────────
            # BUG FIX: READY is now set AFTER Stage 2 completes so all AI features
            # have real Cognee data available when the user opens them.
            result = await db.execute(select(Repository).where(Repository.id == uuid.UUID(repo_id)))
            repo = result.scalar_one()
            repo.status = RepositoryStatus.READY
            repo.ingested_at = datetime.now(timezone.utc)
            await db.commit()

            if memory_failed:
                logger.warning(f"[Ingestion] Memory Graph Completed with errors — {owner}/{name}")
            else:
                logger.info(f"[Ingestion] Memory Graph Completed — {owner}/{name}")

            # Finalise memory graph step
            _emit_progress(repo_id, "memory_graph", "completed", 100, "Memory Graph complete! Repository is ready.")
            _emit_progress(repo_id, "complete", "completed", 100, "Repository fully ingested and ready.")
            await _update_job_status(db, repo_id, IngestionStep.MEMORY_GRAPH, IngestionStatus.COMPLETED, 100, 1, 1)

            # Trigger Background AI Cache generation
            from app.services.ai_cache import trigger_background_generation
            trigger_background_generation(uuid.UUID(repo_id), commit_sha)

        except Exception as e:
            logger.error(f"Ingestion pipeline failed for {owner}/{name}: {e}", exc_info=True)
            try:
                await db.rollback()
                result = await db.execute(select(Repository).where(Repository.id == uuid.UUID(repo_id)))
                repo = result.scalar_one_or_none()
                if repo:
                    repo.status = RepositoryStatus.FAILED
                    await db.commit()
            except Exception as db_err:
                logger.error(f"Could not update repo status to FAILED: {db_err}")
            _emit_progress(repo_id, "error", "failed", 0, f"Pipeline failed: {str(e)[:200]}")


# ═══════════════════════════════════════════════════════════════════════════════
#  HELPERS
# ═══════════════════════════════════════════════════════════════════════════════

async def _update_job_status(
    db: AsyncSession,
    repo_id: str,
    step: IngestionStep,
    status: IngestionStatus,
    progress: int,
    items_processed: int,
    items_total: int,
    error_message: str | None = None,
):
    """Update an ingestion job's status in the database."""
    result = await db.execute(
        select(IngestionJob).where(
            IngestionJob.repository_id == uuid.UUID(repo_id),
            IngestionJob.step == step,
        )
    )
    job = result.scalar_one_or_none()
    if job:
        job.status = status
        job.progress = progress
        job.items_processed = items_processed
        job.items_total = items_total
        job.error_message = error_message
        if status == IngestionStatus.RUNNING:
            job.started_at = datetime.now(timezone.utc)
        if status in (IngestionStatus.COMPLETED, IngestionStatus.FAILED):
            job.completed_at = datetime.now(timezone.utc)
        await db.commit()


# ═══════════════════════════════════════════════════════════════════════════════
#  API ENDPOINTS
# ═══════════════════════════════════════════════════════════════════════════════

@router.post("/{repo_id}/ingest")
async def start_ingestion(
    repo_id: uuid.UUID,
    background_tasks: BackgroundTasks,
    force: bool = Query(
        default=False,
        description="Force re-ingestion even if the repository is already READY.",
    ),
    db: AsyncSession = Depends(get_db),
):
    """
    Start the ingestion pipeline for a repository.

    Set `?force=true` to re-ingest a repository that was already analysed.
    Without the flag, calling this endpoint on a READY repository is a no-op
    that returns a 200 immediately.
    """
    result = await db.execute(select(Repository).where(Repository.id == repo_id))
    repo = result.scalar_one_or_none()
    if not repo:
        raise HTTPException(status_code=404, detail="Repository not found")

    if repo.status == RepositoryStatus.INGESTING:
        raise HTTPException(status_code=409, detail="Ingestion already in progress")

    # Skip re-ingestion for already-ready repos unless forced
    if repo.status == RepositoryStatus.READY and not force:
        return {
            "message": "Repository already analysed. Pass ?force=true to re-ingest.",
            "repository_id": str(repo_id),
            "skipped": True,
        }

    # Clear previous SSE progress events
    _ingestion_progress.pop(str(repo_id), None)

    background_tasks.add_task(_run_ingestion, str(repo_id), repo.owner, repo.name)

    return {"message": "Ingestion started", "repository_id": str(repo_id)}


@router.get("/{repo_id}/ingestion-status")
async def get_ingestion_status(
    repo_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    """Get current ingestion status."""
    result = await db.execute(select(Repository).where(Repository.id == repo_id))
    repo = result.scalar_one_or_none()
    if not repo:
        raise HTTPException(status_code=404, detail="Repository not found")

    result = await db.execute(
        select(IngestionJob).where(IngestionJob.repository_id == repo_id)
    )
    jobs = result.scalars().all()

    total_progress = int(sum(j.progress for j in jobs) / len(jobs)) if jobs else 0

    return IngestionStatusResponse(
        repository_id=repo_id,
        overall_status=repo.status.value,
        overall_progress=total_progress,
        jobs=[IngestionJobResponse.model_validate(j) for j in jobs],
    )


@router.get("/{repo_id}/ingestion-stream")
async def stream_ingestion_progress(repo_id: uuid.UUID):
    """SSE endpoint for real-time ingestion progress."""
    rid = str(repo_id)

    async def event_generator():
        last_index = 0
        max_wait = 600   # 10-minute timeout
        waited = 0

        while waited < max_wait:
            events = _ingestion_progress.get(rid, [])
            while last_index < len(events):
                event = events[last_index]
                yield f"data: {json.dumps(event)}\n\n"
                last_index += 1

                if event.get("step") in ("complete", "error"):
                    return

            await asyncio.sleep(0.5)
            waited += 0.5

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.delete("/{repo_id}/memory")
async def forget_memory(
    repo_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    """Delete all Cognee memory for a repository (Forget lifecycle)."""
    result = await db.execute(select(Repository).where(Repository.id == repo_id))
    repo = result.scalar_one_or_none()
    if not repo:
        raise HTTPException(status_code=404, detail="Repository not found")

    await CogneeMemoryService.forget_dataset(str(repo_id))

    repo.status = RepositoryStatus.PENDING
    repo.ingested_at = None
    await db.commit()

    return {"message": "Memory cleared"}
