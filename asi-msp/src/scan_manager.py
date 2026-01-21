"""
Asynchronous scan management for long-running security scans.

Allows scans to run in the background without blocking API requests.
"""

import asyncio
import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional
from enum import Enum

from .logging_config import get_logger

logger = get_logger(__name__)


class ScanStatus(str, Enum):
    """Scan status enumeration."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class ScanJob:
    """Represents a background scan job."""

    def __init__(
        self,
        job_id: str,
        tool_name: str,
        target: str,
        arguments: Dict[str, Any],
        webhook_url: Optional[str] = None
    ):
        self.job_id = job_id
        self.tool_name = tool_name
        self.target = target
        self.arguments = arguments
        self.webhook_url = webhook_url
        self.status = ScanStatus.PENDING
        self.created_at = datetime.utcnow()
        self.started_at: Optional[datetime] = None
        self.completed_at: Optional[datetime] = None
        self.result: Optional[Dict[str, Any]] = None
        self.error: Optional[str] = None
        self.task: Optional[asyncio.Task] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "job_id": self.job_id,
            "tool_name": self.tool_name,
            "target": self.target,
            "arguments": self.arguments,
            "status": self.status.value,
            "created_at": self.created_at.isoformat(),
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "duration_seconds": (
                (self.completed_at - self.started_at).total_seconds()
                if self.completed_at and self.started_at else None
            ),
            "error": self.error
        }

    def get_summary(self) -> Dict[str, Any]:
        """Get job summary without full results."""
        summary = self.to_dict()
        if self.result:
            summary["has_results"] = True
            summary["result_size"] = len(str(self.result))
        return summary


class ScanManager:
    """Manages background scan jobs."""

    def __init__(self, results_dir: str = "/tmp/scans"):
        self.results_dir = Path(results_dir)
        self.results_dir.mkdir(parents=True, exist_ok=True)
        self.jobs: Dict[str, ScanJob] = {}
        logger.info(f"ScanManager initialized with results dir: {self.results_dir}")

    def create_job(
        self,
        tool_name: str,
        target: str,
        arguments: Dict[str, Any],
        webhook_url: Optional[str] = None
    ) -> str:
        """Create a new scan job and return job ID."""
        job_id = str(uuid.uuid4())
        job = ScanJob(job_id, tool_name, target, arguments, webhook_url)
        self.jobs[job_id] = job

        logger.info(f"Created scan job {job_id}: {tool_name} -> {target}")

        return job_id

    async def execute_job(
        self,
        job_id: str,
        tool_handler: callable
    ):
        """Execute a scan job in the background."""
        if job_id not in self.jobs:
            logger.error(f"Job {job_id} not found")
            return

        job = self.jobs[job_id]

        try:
            job.status = ScanStatus.RUNNING
            job.started_at = datetime.utcnow()

            logger.info(f"Starting scan job {job_id}: {job.tool_name}")

            # Execute the tool handler
            result = await tool_handler(**job.arguments)

            job.status = ScanStatus.COMPLETED
            job.completed_at = datetime.utcnow()
            job.result = result

            # Save results to file
            self._save_results(job_id, result)

            logger.info(
                f"Completed scan job {job_id} in "
                f"{(job.completed_at - job.started_at).total_seconds():.2f}s"
            )

            # Call webhook if configured
            if job.webhook_url:
                await self._call_webhook(job)

        except Exception as e:
            job.status = ScanStatus.FAILED
            job.completed_at = datetime.utcnow()
            job.error = str(e)

            logger.error(f"Scan job {job_id} failed: {e}", exc_info=True)

    def start_job(
        self,
        job_id: str,
        tool_handler: callable
    ) -> asyncio.Task:
        """Start a job as a background task."""
        if job_id not in self.jobs:
            raise ValueError(f"Job {job_id} not found")

        job = self.jobs[job_id]
        task = asyncio.create_task(self.execute_job(job_id, tool_handler))
        job.task = task

        return task

    def get_job(self, job_id: str) -> Optional[ScanJob]:
        """Get a job by ID."""
        return self.jobs.get(job_id)

    def get_job_status(self, job_id: str) -> Optional[Dict[str, Any]]:
        """Get job status summary."""
        job = self.get_job(job_id)
        if not job:
            return None
        return job.get_summary()

    def get_job_results(self, job_id: str) -> Optional[Dict[str, Any]]:
        """Get full job results."""
        job = self.get_job(job_id)
        if not job:
            return None

        if job.status != ScanStatus.COMPLETED:
            return {
                "job_id": job_id,
                "status": job.status.value,
                "message": "Job not completed yet"
            }

        # Try to load from file first
        results = self._load_results(job_id)
        if results:
            return {
                "job_id": job_id,
                "status": job.status.value,
                "tool": job.tool_name,
                "target": job.target,
                "completed_at": job.completed_at.isoformat(),
                "duration_seconds": (job.completed_at - job.started_at).total_seconds(),
                "results": results
            }

        # Fall back to in-memory results
        return {
            "job_id": job_id,
            "status": job.status.value,
            "tool": job.tool_name,
            "target": job.target,
            "completed_at": job.completed_at.isoformat() if job.completed_at else None,
            "duration_seconds": (
                (job.completed_at - job.started_at).total_seconds()
                if job.completed_at and job.started_at else None
            ),
            "results": job.result
        }

    def list_jobs(
        self,
        status: Optional[ScanStatus] = None,
        tool_name: Optional[str] = None,
        limit: int = 50
    ) -> list[Dict[str, Any]]:
        """List jobs with optional filters."""
        jobs = list(self.jobs.values())

        # Filter by status
        if status:
            jobs = [j for j in jobs if j.status == status]

        # Filter by tool
        if tool_name:
            jobs = [j for j in jobs if j.tool_name == tool_name]

        # Sort by creation time (newest first)
        jobs.sort(key=lambda j: j.created_at, reverse=True)

        # Limit results
        jobs = jobs[:limit]

        return [j.get_summary() for j in jobs]

    def cancel_job(self, job_id: str) -> bool:
        """Cancel a running job."""
        job = self.get_job(job_id)
        if not job:
            return False

        if job.status not in [ScanStatus.PENDING, ScanStatus.RUNNING]:
            return False

        if job.task and not job.task.done():
            job.task.cancel()

        job.status = ScanStatus.CANCELLED
        job.completed_at = datetime.utcnow()

        logger.info(f"Cancelled scan job {job_id}")
        return True

    def _save_results(self, job_id: str, results: Dict[str, Any]):
        """Save results to file."""
        try:
            results_file = self.results_dir / f"{job_id}.json"
            with open(results_file, 'w') as f:
                json.dump(results, f, indent=2)
            logger.info(f"Saved results for job {job_id} to {results_file}")
        except Exception as e:
            logger.error(f"Failed to save results for job {job_id}: {e}")

    def _load_results(self, job_id: str) -> Optional[Dict[str, Any]]:
        """Load results from file."""
        try:
            results_file = self.results_dir / f"{job_id}.json"
            if results_file.exists():
                with open(results_file, 'r') as f:
                    return json.load(f)
        except Exception as e:
            logger.error(f"Failed to load results for job {job_id}: {e}")
        return None

    async def _call_webhook(self, job: ScanJob):
        """Call webhook with job results."""
        if not job.webhook_url:
            return

        try:
            import aiohttp

            payload = {
                "job_id": job.job_id,
                "tool": job.tool_name,
                "target": job.target,
                "status": job.status.value,
                "completed_at": job.completed_at.isoformat(),
                "duration_seconds": (job.completed_at - job.started_at).total_seconds(),
                "results": job.result
            }

            async with aiohttp.ClientSession() as session:
                async with session.post(job.webhook_url, json=payload) as response:
                    if response.status == 200:
                        logger.info(f"Webhook called successfully for job {job.job_id}")
                    else:
                        logger.warning(
                            f"Webhook call failed for job {job.job_id}: "
                            f"HTTP {response.status}"
                        )

        except Exception as e:
            logger.error(f"Failed to call webhook for job {job.job_id}: {e}")

    def cleanup_old_jobs(self, max_age_hours: int = 24):
        """Clean up old completed jobs."""
        cutoff = datetime.utcnow().timestamp() - (max_age_hours * 3600)

        jobs_to_remove = [
            job_id for job_id, job in self.jobs.items()
            if job.status in [ScanStatus.COMPLETED, ScanStatus.FAILED, ScanStatus.CANCELLED]
            and job.completed_at
            and job.completed_at.timestamp() < cutoff
        ]

        for job_id in jobs_to_remove:
            # Remove results file
            results_file = self.results_dir / f"{job_id}.json"
            if results_file.exists():
                results_file.unlink()

            # Remove from memory
            del self.jobs[job_id]

        if jobs_to_remove:
            logger.info(f"Cleaned up {len(jobs_to_remove)} old jobs")


# Global scan manager instance
_scan_manager: Optional[ScanManager] = None


def get_scan_manager() -> ScanManager:
    """Get the global scan manager instance."""
    global _scan_manager
    if _scan_manager is None:
        _scan_manager = ScanManager()
    return _scan_manager
