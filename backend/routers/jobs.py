from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import List

from db.database import get_async_session
from models.models import Job
from schemas import JobCreate, JobResponse

router = APIRouter(prefix="/jobs", tags=["jobs"])

@router.post("/", response_model=JobResponse, status_code=status.HTTP_201_CREATED)
async def create_job(
    job: JobCreate,
    db: AsyncSession = Depends(get_async_session)
):
    """
    Create a new job description entry.
    
    - **title**: Job title (required)
    - **description**: Job description (optional)
    - **time_zone**: Required time zone (optional)
    - **budget_range**: Budget range for the job (optional)
    - **contract_duration**: Duration of the contract (optional)
    """
    try:
        # Create new job instance
        db_job = Job(
            title=job.title,
            description=job.description,
            time_zone=job.time_zone,
            budget_range=job.budget_range,
            contract_duration=job.contract_duration
        )
        
        # Add to database
        db.add(db_job)
        await db.commit()
        await db.refresh(db_job)
        
        return db_job
        
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating job: {str(e)}"
        )

@router.get("/", response_model=List[JobResponse])
async def get_all_jobs(
    db: AsyncSession = Depends(get_async_session)
):
    """
    Retrieve all job descriptions.
    """
    try:
        result = await db.execute(select(Job))
        jobs = result.scalars().all()
        return jobs
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving jobs: {str(e)}"
        )

@router.get("/{job_id}", response_model=JobResponse)
async def get_job(
    job_id: int,
    db: AsyncSession = Depends(get_async_session)
):
    """
    Retrieve a specific job by ID.
    """
    try:
        result = await db.execute(select(Job).where(Job.id == job_id))
        job = result.scalar_one_or_none()
        
        if not job:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Job with ID {job_id} not found"
            )
        
        return job
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving job: {str(e)}"
        )