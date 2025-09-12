"""
Print Job service layer for background job processing
"""

import logging
from typing import List, Optional, Dict, Any
from uuid import UUID
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_

from server.src.entities.print_job import PrintJob, PrintJobType, PrintJobStatus
from server.src.entities.event import Event, EventTypes
from . import model

logger = logging.getLogger(__name__)

class PrintJobService:
    
    @staticmethod
    def create_print_job(
        db: Session,
        org_id: UUID,
        job_data: model.PrintJobCreate,
        user_id: Optional[UUID] = None
    ) -> PrintJob:
        """Create a new print job"""
        try:
            job = PrintJob(
                org_id=org_id,
                created_by=user_id,
                job_type=PrintJobType(job_data.job_type.value),
                status=PrintJobStatus.QUEUED,
                template_name=job_data.template_name,
                config=job_data.config,
                input_data=job_data.input_data,
                retry_count=0
            )
            db.add(job)
            db.flush()
            
            # Log event
            event = Event.create_event(
                event_type=EventTypes.SYSTEM_INFO,
                org_id=org_id,
                user_id=user_id,
                entity_type="PrintJob",
                entity_id=job.id,
                payload={
                    "action": "job_created",
                    "job_type": job_data.job_type.value,
                    "template_name": job_data.template_name
                }
            )
            db.add(event)
            
            db.commit()
            db.refresh(job)
            
            logger.info(f"Created print job: {job.id} - {job.job_type.value}")
            return job
            
        except Exception as e:
            db.rollback()
            logger.error(f"Error creating print job: {e}")
            raise

    @staticmethod
    def get_job_by_id(db: Session, job_id: UUID) -> Optional[PrintJob]:
        """Get print job by ID"""
        return db.query(PrintJob).filter(PrintJob.id == job_id).first()

    @staticmethod
    def search_jobs(
        db: Session,
        org_id: UUID,
        search_params: model.PrintJobSearch,
        skip: int = 0,
        limit: int = 100
    ) -> tuple[List[PrintJob], int]:
        """Search print jobs with filters"""
        query = db.query(PrintJob).filter(PrintJob.org_id == org_id)
        
        # Apply filters
        if search_params.job_type:
            query = query.filter(PrintJob.job_type == PrintJobType(search_params.job_type.value))
        
        if search_params.status:
            query = query.filter(PrintJob.status == PrintJobStatus(search_params.status.value))
        
        if search_params.template_name:
            query = query.filter(PrintJob.template_name.ilike(f"%{search_params.template_name}%"))
        
        if search_params.created_by:
            query = query.filter(PrintJob.created_by == search_params.created_by)
        
        if search_params.created_after:
            query = query.filter(PrintJob.created_at >= search_params.created_after)
        
        if search_params.created_before:
            query = query.filter(PrintJob.created_at <= search_params.created_before)
        
        # Order by creation date descending
        query = query.order_by(PrintJob.created_at.desc())
        
        total = query.count()
        jobs = query.offset(skip).limit(limit).all()
        return jobs, total

    @staticmethod
    def update_job_status(
        db: Session,
        job_id: UUID,
        status: PrintJobStatus,
        error_message: Optional[str] = None,
        output_files: Optional[List[UUID]] = None
    ) -> Optional[PrintJob]:
        """Update job status and related fields"""
        try:
            job = db.query(PrintJob).filter(PrintJob.id == job_id).first()
            if not job:
                return None
            
            old_status = job.status
            job.status = status
            
            if error_message:
                job.error_message = error_message
            
            if output_files:
                job.output_files = output_files
            
            # Update timestamps
            now = datetime.utcnow()
            if status == PrintJobStatus.PROCESSING and not job.started_at:
                job.started_at = now
            elif status in [PrintJobStatus.COMPLETED, PrintJobStatus.FAILED, PrintJobStatus.CANCELLED]:
                job.completed_at = now
            
            # Log event
            event = Event.create_event(
                event_type=EventTypes.SYSTEM_INFO if status == PrintJobStatus.COMPLETED else EventTypes.SYSTEM_WARNING,
                org_id=job.org_id,
                user_id=job.created_by,
                entity_type="PrintJob",
                entity_id=job_id,
                payload={
                    "action": "status_changed",
                    "old_status": old_status.value,
                    "new_status": status.value,
                    "error_message": error_message
                }
            )
            db.add(event)
            
            db.commit()
            db.refresh(job)
            
            logger.info(f"Updated job {job_id} status: {old_status.value} -> {status.value}")
            return job
            
        except Exception as e:
            db.rollback()
            logger.error(f"Error updating job status {job_id}: {e}")
            raise

    @staticmethod
    def retry_failed_job(db: Session, job_id: UUID, user_id: Optional[UUID] = None) -> Optional[PrintJob]:
        """Retry a failed job"""
        try:
            job = db.query(PrintJob).filter(PrintJob.id == job_id).first()
            if not job or job.status != PrintJobStatus.FAILED:
                return None
            
            job.status = PrintJobStatus.QUEUED
            job.retry_count = int(job.retry_count) + 1
            job.error_message = None
            job.started_at = None
            job.completed_at = None
            
            # Log event
            event = Event.create_event(
                event_type=EventTypes.SYSTEM_INFO,
                org_id=job.org_id,
                user_id=user_id,
                entity_type="PrintJob",
                entity_id=job_id,
                payload={
                    "action": "job_retried",
                    "retry_count": job.retry_count
                }
            )
            db.add(event)
            
            db.commit()
            db.refresh(job)
            
            logger.info(f"Retried job: {job_id} (attempt #{job.retry_count})")
            return job
            
        except Exception as e:
            db.rollback()
            logger.error(f"Error retrying job {job_id}: {e}")
            raise

    @staticmethod
    def cancel_job(db: Session, job_id: UUID, user_id: Optional[UUID] = None) -> Optional[PrintJob]:
        """Cancel a queued or processing job"""
        try:
            job = db.query(PrintJob).filter(PrintJob.id == job_id).first()
            if not job or job.status in [PrintJobStatus.COMPLETED, PrintJobStatus.FAILED, PrintJobStatus.CANCELLED]:
                return None
            
            job.status = PrintJobStatus.CANCELLED
            job.completed_at = datetime.utcnow()
            
            # Log event
            event = Event.create_event(
                event_type=EventTypes.SYSTEM_WARNING,
                org_id=job.org_id,
                user_id=user_id,
                entity_type="PrintJob",
                entity_id=job_id,
                payload={"action": "job_cancelled"}
            )
            db.add(event)
            
            db.commit()
            db.refresh(job)
            
            logger.info(f"Cancelled job: {job_id}")
            return job
            
        except Exception as e:
            db.rollback()
            logger.error(f"Error cancelling job {job_id}: {e}")
            raise

    @staticmethod
    def get_next_queued_job(db: Session, job_type: Optional[PrintJobType] = None) -> Optional[PrintJob]:
        """Get next queued job for processing"""
        query = db.query(PrintJob).filter(PrintJob.status == PrintJobStatus.QUEUED)
        
        if job_type:
            query = query.filter(PrintJob.job_type == job_type)
        
        return query.order_by(PrintJob.created_at.asc()).first()

    @staticmethod
    def get_job_stats(db: Session, org_id: UUID, days: int = 30) -> Dict[str, Any]:
        """Get print job statistics for organization"""
        try:
            # Date range for stats
            start_date = datetime.utcnow() - timedelta(days=days)
            
            # Total jobs
            total_jobs = db.query(func.count(PrintJob.id)).filter(
                PrintJob.org_id == org_id,
                PrintJob.created_at >= start_date
            ).scalar() or 0
            
            # Jobs by status
            status_stats = db.query(
                PrintJob.status,
                func.count(PrintJob.id).label('count')
            ).filter(
                PrintJob.org_id == org_id,
                PrintJob.created_at >= start_date
            ).group_by(PrintJob.status).all()
            
            # Jobs by type
            type_stats = db.query(
                PrintJob.job_type,
                func.count(PrintJob.id).label('count')
            ).filter(
                PrintJob.org_id == org_id,
                PrintJob.created_at >= start_date
            ).group_by(PrintJob.job_type).all()
            
            # Average processing time
            avg_time = db.query(
                func.avg(
                    func.extract('epoch', PrintJob.completed_at - PrintJob.started_at)
                )
            ).filter(
                PrintJob.org_id == org_id,
                PrintJob.status == PrintJobStatus.COMPLETED,
                PrintJob.started_at.isnot(None),
                PrintJob.completed_at.isnot(None),
                PrintJob.created_at >= start_date
            ).scalar()
            
            return {
                "total_jobs": total_jobs,
                "by_status": {status.value: count for status, count in status_stats},
                "by_type": {job_type.value: count for job_type, count in type_stats},
                "avg_processing_time": float(avg_time) if avg_time else None
            }
            
        except Exception as e:
            logger.error(f"Error getting job stats for org {org_id}: {e}")
            return {}

    @staticmethod
    def get_queue_info(db: Session, job_type: Optional[PrintJobType] = None) -> Dict[str, Any]:
        """Get queue information"""
        try:
            query = db.query(PrintJob)
            
            if job_type:
                query = query.filter(PrintJob.job_type == job_type)
            
            # Count jobs by status
            queued = query.filter(PrintJob.status == PrintJobStatus.QUEUED).count()
            processing = query.filter(PrintJob.status == PrintJobStatus.PROCESSING).count()
            
            # Estimate wait time based on average processing time
            # This is a simple estimation - in practice you'd want more sophisticated logic
            if queued > 0:
                avg_time = db.query(
                    func.avg(
                        func.extract('epoch', PrintJob.completed_at - PrintJob.started_at)
                    )
                ).filter(
                    PrintJob.status == PrintJobStatus.COMPLETED,
                    PrintJob.started_at.isnot(None),
                    PrintJob.completed_at.isnot(None),
                    PrintJob.created_at >= datetime.utcnow() - timedelta(days=7)
                ).scalar()
                
                estimated_wait = int(avg_time * queued) if avg_time else None
            else:
                estimated_wait = 0
            
            return {
                "queued_jobs": queued,
                "processing_jobs": processing,
                "estimated_wait_time": estimated_wait
            }
            
        except Exception as e:
            logger.error(f"Error getting queue info: {e}")
            return {"queued_jobs": 0, "processing_jobs": 0, "estimated_wait_time": None}