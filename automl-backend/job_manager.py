"""Job management for async pipeline operations."""
import uuid
import asyncio
from datetime import datetime
from typing import Dict, Any, Optional
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class JobStatus(str, Enum):
    """Job status enumeration."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class Job:
    """Represents an async job."""
    
    def __init__(self, job_id: str, job_type: str):
        self.job_id = job_id
        self.job_type = job_type
        self.status = JobStatus.PENDING
        self.progress = 0
        self.current_stage = "Initializing"
        self.created_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()
        self.completed_at: Optional[datetime] = None
        self.result: Optional[Dict[str, Any]] = None
        self.error: Optional[str] = None
    
    def update_progress(self, progress: int, stage: str):
        """Update job progress."""
        self.progress = min(100, max(0, progress))
        self.current_stage = stage
        self.updated_at = datetime.utcnow()
    
    def complete(self, result: Dict[str, Any]):
        """Mark job as completed."""
        self.status = JobStatus.COMPLETED
        self.result = result
        self.progress = 100
        self.completed_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()
    
    def fail(self, error: str):
        """Mark job as failed."""
        self.status = JobStatus.FAILED
        self.error = error
        self.completed_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()
    
    def start(self):
        """Mark job as running."""
        self.status = JobStatus.RUNNING
        self.updated_at = datetime.utcnow()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "job_id": self.job_id,
            "job_type": self.job_type,
            "status": self.status.value,
            "progress": self.progress,
            "current_stage": self.current_stage,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "error": self.error,
        }


class JobManager:
    """Manages async jobs."""
    
    def __init__(self, max_concurrent: int = 5, job_timeout: int = 3600):
        self.jobs: Dict[str, Job] = {}
        self.max_concurrent = max_concurrent
        self.job_timeout = job_timeout
        self._semaphore = asyncio.Semaphore(max_concurrent)
    
    def create_job(self, job_type: str) -> str:
        """Create a new job and return job_id."""
        job_id = str(uuid.uuid4())
        job = Job(job_id, job_type)
        self.jobs[job_id] = job
        logger.info(f"Created job {job_id} of type {job_type}")
        return job_id
    
    def get_job(self, job_id: str) -> Optional[Job]:
        """Retrieve job by ID."""
        return self.jobs.get(job_id)
    
    def update_job(self, job_id: str, progress: int, stage: str):
        """Update job progress."""
        if job_id in self.jobs:
            self.jobs[job_id].update_progress(progress, stage)
    
    def complete_job(self, job_id: str, result: Dict[str, Any]):
        """Mark job as completed."""
        if job_id in self.jobs:
            self.jobs[job_id].complete(result)
            logger.info(f"Job {job_id} completed successfully")
    
    def fail_job(self, job_id: str, error: str):
        """Mark job as failed."""
        if job_id in self.jobs:
            self.jobs[job_id].fail(error)
            logger.error(f"Job {job_id} failed: {error}")
    
    def start_job(self, job_id: str):
        """Mark job as running."""
        if job_id in self.jobs:
            self.jobs[job_id].start()
    
    def get_job_status(self, job_id: str) -> Dict[str, Any]:
        """Get job status."""
        job = self.get_job(job_id)
        if not job:
            return {"error": f"Job {job_id} not found"}
        return job.to_dict()
    
    def cleanup_old_jobs(self, retention_hours: int = 24):
        """Clean up old completed jobs."""
        now = datetime.utcnow()
        expired_jobs = []
        
        for job_id, job in self.jobs.items():
            if job.status == JobStatus.COMPLETED or job.status == JobStatus.FAILED:
                age_hours = (now - job.completed_at).total_seconds() / 3600
                if age_hours > retention_hours:
                    expired_jobs.append(job_id)
        
        for job_id in expired_jobs:
            del self.jobs[job_id]
            logger.info(f"Cleaned up job {job_id}")
    
    async def run_with_timeout(self, job_id: str, coro):
        """Run coroutine with timeout and semaphore."""
        async with self._semaphore:
            try:
                self.start_job(job_id)
                result = await asyncio.wait_for(coro, timeout=self.job_timeout)
                self.complete_job(job_id, result)
                return result
            except asyncio.TimeoutError:
                error_msg = f"Job {job_id} exceeded timeout of {self.job_timeout}s"
                self.fail_job(job_id, error_msg)
                raise
            except Exception as e:
                error_msg = f"Job {job_id} failed: {str(e)}"
                self.fail_job(job_id, error_msg)
                raise


# Global job manager instance
job_manager = JobManager()
