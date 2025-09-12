"""
Print Job API routes
"""

from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from sqlalchemy.orm import Session
from uuid import UUID
from typing import List, Optional

from server.src.database import get_db
from server.src.auth.dependencies import get_current_user
from server.src.entities.user import User
from server.src.routes.organizations.service import OrganizationService
from . import model
from .service import PrintJobService

router = APIRouter(prefix="/organizations/{org_id}/print-jobs", tags=["print-jobs"])

@router.post("/", response_model=model.PrintJobResponse)
def create_print_job(
    org_id: UUID,
    job_data: model.PrintJobCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new print job"""
    if not OrganizationService.check_user_access(db, current_user.id, org_id):
        raise HTTPException(status_code=403, detail="Access denied to this organization")
    
    try:
        job = PrintJobService.create_print_job(
            db=db,
            org_id=org_id,
            job_data=job_data,
            user_id=current_user.id
        )
        
        # TODO: Add background task to process job
        # background_tasks.add_task(process_print_job, job.id)
        
        return model.PrintJobResponse.model_validate(job)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/search", response_model=model.PrintJobListResponse)
def search_print_jobs(
    org_id: UUID,
    job_type: Optional[model.PrintJobType] = None,
    status: Optional[model.PrintJobStatus] = None,
    template_name: Optional[str] = None,
    created_by: Optional[UUID] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Search print jobs with filters"""
    if not OrganizationService.check_user_access(db, current_user.id, org_id):
        raise HTTPException(status_code=403, detail="Access denied to this organization")
    
    search_params = model.PrintJobSearch(
        job_type=job_type,
        status=status,
        template_name=template_name,
        created_by=created_by
    )
    
    jobs, total = PrintJobService.search_jobs(
        db=db,
        org_id=org_id,
        search_params=search_params,
        skip=skip,
        limit=limit
    )
    
    return model.PrintJobListResponse(
        jobs=[model.PrintJobResponse.model_validate(job) for job in jobs],
        total=total,
        limit=limit,
        offset=skip
    )

@router.get("/{job_id}", response_model=model.PrintJobResponse)
def get_print_job(
    org_id: UUID,
    job_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get print job by ID"""
    if not OrganizationService.check_user_access(db, current_user.id, org_id):
        raise HTTPException(status_code=403, detail="Access denied to this organization")
    
    job = PrintJobService.get_job_by_id(db=db, job_id=job_id)
    if not job or job.org_id != org_id:
        raise HTTPException(status_code=404, detail="Print job not found")
    
    return model.PrintJobResponse.model_validate(job)

@router.post("/{job_id}/retry", response_model=model.PrintJobResponse)
def retry_print_job(
    org_id: UUID,
    job_id: UUID,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Retry a failed print job"""
    if not OrganizationService.check_user_access(db, current_user.id, org_id):
        raise HTTPException(status_code=403, detail="Access denied to this organization")
    
    job = PrintJobService.get_job_by_id(db=db, job_id=job_id)
    if not job or job.org_id != org_id:
        raise HTTPException(status_code=404, detail="Print job not found")
    
    if job.status.value != "failed":
        raise HTTPException(status_code=400, detail="Only failed jobs can be retried")
    
    retried_job = PrintJobService.retry_failed_job(
        db=db,
        job_id=job_id,
        user_id=current_user.id
    )
    if not retried_job:
        raise HTTPException(status_code=400, detail="Unable to retry job")
    
    # TODO: Add background task to process retried job
    # background_tasks.add_task(process_print_job, job_id)
    
    return model.PrintJobResponse.model_validate(retried_job)

@router.post("/{job_id}/cancel", response_model=model.PrintJobResponse)
def cancel_print_job(
    org_id: UUID,
    job_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Cancel a queued or processing print job"""
    if not OrganizationService.check_user_access(db, current_user.id, org_id):
        raise HTTPException(status_code=403, detail="Access denied to this organization")
    
    job = PrintJobService.get_job_by_id(db=db, job_id=job_id)
    if not job or job.org_id != org_id:
        raise HTTPException(status_code=404, detail="Print job not found")
    
    if job.status.value in ["completed", "failed", "cancelled"]:
        raise HTTPException(status_code=400, detail="Cannot cancel completed, failed, or already cancelled jobs")
    
    cancelled_job = PrintJobService.cancel_job(
        db=db,
        job_id=job_id,
        user_id=current_user.id
    )
    if not cancelled_job:
        raise HTTPException(status_code=400, detail="Unable to cancel job")
    
    return model.PrintJobResponse.model_validate(cancelled_job)

@router.get("/stats/summary", response_model=model.PrintJobStatsResponse)
def get_job_stats(
    org_id: UUID,
    days: int = Query(30, ge=1, le=365, description="Number of days to include in stats"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get print job statistics for organization"""
    if not OrganizationService.check_user_access(db, current_user.id, org_id):
        raise HTTPException(status_code=403, detail="Access denied to this organization")
    
    stats = PrintJobService.get_job_stats(db=db, org_id=org_id, days=days)
    
    return model.PrintJobStatsResponse(
        total_jobs=stats.get("total_jobs", 0),
        by_status=stats.get("by_status", {}),
        by_type=stats.get("by_type", {}),
        avg_processing_time=stats.get("avg_processing_time")
    )

@router.get("/queue/info", response_model=model.JobQueueResponse)
def get_queue_info(
    org_id: UUID,
    job_type: Optional[model.PrintJobType] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get current queue information"""
    if not OrganizationService.check_user_access(db, current_user.id, org_id):
        raise HTTPException(status_code=403, detail="Access denied to this organization")
    
    from server.src.entities.print_job import PrintJobType
    
    queue_info = PrintJobService.get_queue_info(
        db=db,
        job_type=PrintJobType(job_type.value) if job_type else None
    )
    
    return model.JobQueueResponse(
        queued_jobs=queue_info.get("queued_jobs", 0),
        processing_jobs=queue_info.get("processing_jobs", 0),
        estimated_wait_time=queue_info.get("estimated_wait_time")
    )

# Worker endpoint for internal use
@router.get("/internal/next-job", response_model=Optional[model.PrintJobResponse])
def get_next_job_for_worker(
    job_type: Optional[model.PrintJobType] = None,
    db: Session = Depends(get_db)
):
    """Get next queued job for worker processing (internal endpoint)"""
    # TODO: Add worker authentication/authorization
    
    from server.src.entities.print_job import PrintJobType, PrintJobStatus
    
    job = PrintJobService.get_next_queued_job(
        db=db,
        job_type=PrintJobType(job_type.value) if job_type else None
    )
    
    if job:
        # Mark as processing
        PrintJobService.update_job_status(
            db=db,
            job_id=job.id,
            status=PrintJobStatus.PROCESSING
        )
        return model.PrintJobResponse.model_validate(job)
    
    return None

@router.put("/internal/{job_id}/status")
def update_job_status_internal(
    job_id: UUID,
    status: model.PrintJobStatus,
    error_message: Optional[str] = None,
    output_files: Optional[List[UUID]] = None,
    db: Session = Depends(get_db)
):
    """Update job status from worker (internal endpoint)"""
    # TODO: Add worker authentication/authorization
    
    from server.src.entities.print_job import PrintJobStatus
    
    job = PrintJobService.update_job_status(
        db=db,
        job_id=job_id,
        status=PrintJobStatus(status.value),
        error_message=error_message,
        output_files=output_files
    )
    
    if not job:
        raise HTTPException(status_code=404, detail="Print job not found")
    
    return {"message": "Job status updated successfully"}