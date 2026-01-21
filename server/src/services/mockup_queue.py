"""
Asynchronous Mockup Generation Queue

This service handles mockup generation as background jobs to prevent
blocking the upload workflow and allow for better resource management.

Features:
- Async job queue with Redis backend
- Retry logic for failed mockups
- Progress tracking
- Batch processing
"""

import os
import logging
import asyncio
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone
from enum import Enum
from dataclasses import dataclass, field
import uuid

# Try to import Redis for queue management
try:
    import redis.asyncio as redis
    from rq import Queue
    from rq.job import Job
    REDIS_AVAILABLE = True
except ImportError:
    redis = None
    Queue = None
    Job = None
    REDIS_AVAILABLE = False
    logging.warning("Redis/RQ not available - mockup queue will use fallback mode")


class MockupJobStatus(str, Enum):
    """Status of a mockup generation job"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    RETRYING = "retrying"


@dataclass
class MockupJob:
    """Represents a mockup generation job"""
    job_id: str
    user_id: str
    design_ids: List[str]
    product_template_id: str
    mockup_id: str
    status: MockupJobStatus = MockupJobStatus.PENDING
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    retry_count: int = 0
    max_retries: int = 3
    result: Optional[Dict[str, Any]] = None


class MockupQueue:
    """
    Manages asynchronous mockup generation jobs

    Uses Redis + RQ if available, falls back to in-memory queue
    """

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.redis_client: Optional[redis.Redis] = None
        self.queue: Optional[Queue] = None
        self.jobs: Dict[str, MockupJob] = {}  # In-memory fallback
        self._lock = asyncio.Lock()

        # Initialize Redis connection if available
        if REDIS_AVAILABLE:
            self._init_redis()
        else:
            self.logger.warning("Using in-memory queue - jobs will not persist across restarts")

    def _init_redis(self):
        """Initialize Redis connection"""
        try:
            redis_host = os.getenv('REDIS_HOST', 'localhost')
            redis_port = int(os.getenv('REDIS_PORT', '6379'))
            redis_password = os.getenv('REDIS_PASSWORD')
            redis_db = int(os.getenv('REDIS_DB', '0'))

            self.redis_client = redis.Redis(
                host=redis_host,
                port=redis_port,
                password=redis_password,
                db=redis_db,
                decode_responses=False
            )

            # Test connection
            asyncio.create_task(self._test_redis_connection())

            self.logger.info(f"✅ Redis connection initialized: {redis_host}:{redis_port}")
        except Exception as e:
            self.logger.error(f"❌ Failed to initialize Redis: {e}")
            self.redis_client = None

    async def _test_redis_connection(self):
        """Test Redis connection"""
        try:
            if self.redis_client:
                await self.redis_client.ping()
                self.logger.info("✅ Redis connection test successful")
        except Exception as e:
            self.logger.error(f"❌ Redis connection test failed: {e}")
            self.redis_client = None

    async def enqueue_mockup_job(
        self,
        user_id: str,
        design_ids: List[str],
        product_template_id: str,
        mockup_id: str,
        priority: str = "normal"
    ) -> str:
        """
        Enqueue a new mockup generation job

        Args:
            user_id: User ID
            design_ids: List of design IDs to generate mockups for
            product_template_id: Product template ID
            mockup_id: Mockup ID
            priority: Job priority (high, normal, low)

        Returns:
            Job ID
        """
        job_id = str(uuid.uuid4())

        job = MockupJob(
            job_id=job_id,
            user_id=user_id,
            design_ids=design_ids,
            product_template_id=product_template_id,
            mockup_id=mockup_id
        )

        async with self._lock:
            self.jobs[job_id] = job

        # If Redis is available, also enqueue there
        if self.redis_client:
            await self._enqueue_redis_job(job, priority)
        else:
            # Process immediately in fallback mode
            asyncio.create_task(self._process_job_async(job_id))

        self.logger.info(f"📋 Enqueued mockup job {job_id} for {len(design_ids)} designs")
        return job_id

    async def _enqueue_redis_job(self, job: MockupJob, priority: str):
        """Enqueue job in Redis"""
        try:
            # Store job data in Redis
            job_key = f"mockup_job:{job.job_id}"
            job_data = {
                "user_id": job.user_id,
                "design_ids": ",".join(job.design_ids),
                "product_template_id": job.product_template_id,
                "mockup_id": job.mockup_id,
                "status": job.status.value,
                "created_at": job.created_at.isoformat()
            }

            await self.redis_client.hset(job_key, mapping=job_data)
            await self.redis_client.expire(job_key, 86400)  # 24 hours TTL

            # Add to processing queue based on priority
            queue_name = f"mockup_queue:{priority}"
            await self.redis_client.rpush(queue_name, job.job_id)

            self.logger.info(f"📋 Job {job.job_id} added to Redis queue: {queue_name}")
        except Exception as e:
            self.logger.error(f"❌ Failed to enqueue Redis job: {e}")

    async def get_job_status(self, job_id: str) -> Optional[MockupJob]:
        """Get status of a mockup job"""
        async with self._lock:
            return self.jobs.get(job_id)

    async def _process_job_async(self, job_id: str):
        """Process a mockup job asynchronously"""
        try:
            async with self._lock:
                job = self.jobs.get(job_id)

            if not job:
                self.logger.error(f"❌ Job {job_id} not found")
                return

            # Update status
            job.status = MockupJobStatus.PROCESSING
            job.started_at = datetime.now(timezone.utc)

            self.logger.info(f"🎨 Processing mockup job {job_id} for {len(job.design_ids)} designs")

            # Import mockup service (avoid circular imports)
            from server.src.routes.mockups import service as mockup_service
            from server.src.database.core import get_db

            # Get database session
            db = next(get_db())

            try:
                # Call the actual mockup generation service
                # This runs the existing mockup generation logic
                result = await mockup_service.generate_mockups_async(
                    db=db,
                    user_id=job.user_id,
                    design_ids=job.design_ids,
                    product_template_id=job.product_template_id,
                    mockup_id=job.mockup_id
                )

                # Update job with success
                job.status = MockupJobStatus.COMPLETED
                job.completed_at = datetime.now(timezone.utc)
                job.result = result

                self.logger.info(f"✅ Mockup job {job_id} completed successfully")

            except Exception as e:
                # Handle failure
                job.error_message = str(e)

                if job.retry_count < job.max_retries:
                    job.retry_count += 1
                    job.status = MockupJobStatus.RETRYING
                    self.logger.warning(f"⚠️ Mockup job {job_id} failed, retrying ({job.retry_count}/{job.max_retries}): {e}")

                    # Retry after delay
                    await asyncio.sleep(5 * job.retry_count)  # Exponential backoff
                    await self._process_job_async(job_id)
                else:
                    job.status = MockupJobStatus.FAILED
                    job.completed_at = datetime.now(timezone.utc)
                    self.logger.error(f"❌ Mockup job {job_id} failed after {job.max_retries} retries: {e}")

            finally:
                db.close()

        except Exception as e:
            self.logger.error(f"❌ Error processing job {job_id}: {e}")

    async def get_pending_jobs(self, user_id: Optional[str] = None) -> List[MockupJob]:
        """Get list of pending jobs, optionally filtered by user"""
        async with self._lock:
            jobs = list(self.jobs.values())

        if user_id:
            jobs = [j for j in jobs if j.user_id == user_id]

        return [j for j in jobs if j.status == MockupJobStatus.PENDING]

    async def get_job_progress(self, job_id: str) -> Dict[str, Any]:
        """Get detailed progress information for a job"""
        job = await self.get_job_status(job_id)

        if not job:
            return {"error": "Job not found"}

        progress = {
            "job_id": job.job_id,
            "status": job.status.value,
            "created_at": job.created_at.isoformat(),
            "design_count": len(job.design_ids),
            "retry_count": job.retry_count,
        }

        if job.started_at:
            progress["started_at"] = job.started_at.isoformat()
            elapsed = (datetime.now(timezone.utc) - job.started_at).total_seconds()
            progress["elapsed_seconds"] = elapsed

        if job.completed_at:
            progress["completed_at"] = job.completed_at.isoformat()
            duration = (job.completed_at - job.started_at).total_seconds() if job.started_at else 0
            progress["duration_seconds"] = duration

        if job.error_message:
            progress["error"] = job.error_message

        if job.result:
            progress["result"] = job.result

        return progress


# Global queue instance
mockup_queue = MockupQueue()


async def enqueue_mockup_generation(
    user_id: str,
    design_ids: List[str],
    product_template_id: str,
    mockup_id: str,
    priority: str = "normal"
) -> str:
    """
    Convenience function to enqueue mockup generation

    Returns job_id for tracking
    """
    return await mockup_queue.enqueue_mockup_job(
        user_id=user_id,
        design_ids=design_ids,
        product_template_id=product_template_id,
        mockup_id=mockup_id,
        priority=priority
    )


async def get_mockup_job_status(job_id: str) -> Optional[Dict[str, Any]]:
    """Get status of a mockup generation job"""
    return await mockup_queue.get_job_progress(job_id)
