import os
from datetime import datetime
from pathlib import Path
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
import cloudinary
import cloudinary.uploader
from db.database import get_async_session
from models.models import Candidate, Job, Vendor
from schemas import CandidateCreate, CandidateResponse, VendorResponse, MatchResultResponse
from services.matching_service import MatchingService

router = APIRouter(prefix="/candidates", tags=["candidates"])

# Cloudinary configuration
cloudinary_url = os.getenv("CLOUDINARY_URL")

if cloudinary_url:
    cloudinary.config(cloudinary_url=cloudinary_url)
else:
    cloudinary.config(
        cloud_name = os.getenv("CLOUDINARY_CLOUD_NAME"),
        api_key = os.getenv("CLOUDINARY_API_KEY"),
        api_secret = os.getenv("CLOUDINARY_API_SECRET"),
        secure = True
    )

# File validation constants
ALLOWED_EXTENSIONS = {".pdf", ".docx"}
ALLOWED_MIME_TYPES = {
    "application/pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
}
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB in bytes

def validate_file(file: UploadFile) -> None:
    """Validate uploaded file type and size."""
    if not file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No file selected"
        )
    
    file_ext = Path(file.filename).suffix.lower()
    if file_ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid file type. Only PDF and DOCX files are allowed. Got: {file_ext}"
        )
    
    if file.content_type not in ALLOWED_MIME_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid file type. Expected PDF or DOCX, got: {file.content_type}"
        )

def generate_public_id(original_filename: str, candidate_id: int) -> str:
    """Generate a unique public_id for Cloudinary upload."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"candidate_cvs/candidate_{candidate_id}_{timestamp}"

async def upload_file_to_cloudinary(file: UploadFile, public_id: str) -> str:
    """Upload file to Cloudinary and return the secure URL."""
    try:
        upload_result = cloudinary.uploader.upload(
            file.file,
            public_id=public_id,
            resource_type="raw",
            max_size=MAX_FILE_SIZE
        )
        return upload_result.get("secure_url")
    
    except cloudinary.exceptions.Error as e:
        if "file size" in str(e).lower():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"File is too large. Maximum size is {MAX_FILE_SIZE / (1024*1024):.0f}MB."
            )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error uploading file to Cloudinary: {str(e)}"
        )

@router.post("/", response_model=CandidateResponse, status_code=status.HTTP_201_CREATED)
async def create_candidate(
    cv_file: UploadFile = File(..., description="CV file (PDF or DOCX)"),
    job_id: int = Form(..., description="Job ID"),
    vendor_id: int = Form(..., description="Vendor ID"),
    name: str = Form(..., description="Candidate's name"),
    email: str = Form(None, description="Candidate's email"),
    phone: str = Form(None, description="Candidate's phone number"),
    soft_skills: str = Form(None, description="Soft skills"),
    hard_skills: str = Form(None, description="Hard skills"),
    experience: int = Form(None, description="Years of experience"),
    time_zone_alignment: str = Form(None, description="Time zone alignment"),
    contract_duration_willingness: str = Form(None, description="Contract duration willingness"),
    certifications: str = Form(None, description="Certifications"),
    db: AsyncSession = Depends(get_async_session)
):
    """Create a new candidate entry with CV upload and automatic matching."""
    try:
        print(f"Received experience: {experience}")
        validate_file(cv_file)
        
        # Validate job exists
        job_result = await db.execute(select(Job).where(Job.id == job_id))
        job = job_result.scalar_one_or_none()
        if not job:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Job with ID {job_id} not found"
            )
        
        # Validate vendor exists
        vendor_result = await db.execute(select(Vendor).where(Vendor.id == vendor_id))
        vendor = vendor_result.scalar_one_or_none()
        if not vendor:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Vendor with ID {vendor_id} not found"
            )

        candidate_data = CandidateCreate(
            job_id=job_id,
            vendor_id=vendor_id,
            name=name,
            email=email,
            phone=phone,
            soft_skills=soft_skills,
            hard_skills=hard_skills,
            experience=experience,
            time_zone_alignment=time_zone_alignment,
            contract_duration_willingness=contract_duration_willingness,
            certifications=certifications
        )

        print(f"Parsed experience: {candidate_data.experience}")

        candidate = Candidate(**candidate_data.model_dump())  # Use model_dump() for safe conversion
        
        db.add(candidate)
        await db.flush()
        
        # Upload CV file
        public_id = generate_public_id(cv_file.filename, candidate.id)
        file_url = await upload_file_to_cloudinary(cv_file, public_id)
        candidate.cv_file_path = file_url
        
        await db.commit()
        await db.refresh(candidate)
        
        # Automatically process matching for the new candidate
        try:
            match_result = await MatchingService.process_candidate_match(candidate.id, db)
            if not match_result['success']:
                # Log the error but don't fail the candidate creation
                print(f"Warning: Matching failed for candidate {candidate.id}: {match_result.get('error')}")
        except Exception as e:
            print(f"Warning: Error during automatic matching for candidate {candidate.id}: {str(e)}")
        
        return candidate
        
    except HTTPException:
        await db.rollback()
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating candidate: {str(e)}"
        )

@router.get("/", response_model=List[CandidateResponse])
async def get_all_candidates(db: AsyncSession = Depends(get_async_session)):
    """Retrieve all candidates with their details."""
    try:
        result = await db.execute(select(Candidate))
        candidates = result.scalars().all()
        return candidates
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving candidates: {str(e)}"
        )

@router.get("/{candidate_id}", response_model=CandidateResponse)
async def get_candidate(candidate_id: int, db: AsyncSession = Depends(get_async_session)):
    """Retrieve a specific candidate by ID."""
    try:
        result = await db.execute(select(Candidate).where(Candidate.id == candidate_id))
        candidate = result.scalar_one_or_none()
        
        if not candidate:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Candidate with ID {candidate_id} not found"
            )
        
        return candidate
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving candidate: {str(e)}"
        )

@router.get("/by-job/{job_id}", response_model=List[CandidateResponse])
async def get_candidates_by_job(job_id: int, db: AsyncSession = Depends(get_async_session)):
    """Retrieve all candidates for a specific job."""
    try:
        job_result = await db.execute(select(Job).where(Job.id == job_id))
        job = job_result.scalar_one_or_none()
        if not job:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Job with ID {job_id} not found"
            )
        
        # Get candidates for this job
        result = await db.execute(
            select(Candidate).where(Candidate.job_id == job_id)
        )
        candidates = result.scalars().all()
        return candidates
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving candidates for job {job_id}: {str(e)}"
        )

# NEW MATCHING ENDPOINTS FOR SPRINT 2

@router.post("/match/{candidate_id}")
async def match_candidate(candidate_id: int, db: AsyncSession = Depends(get_async_session)):
    """Process matching for a specific candidate against their job."""
    try:
        result = await MatchingService.process_candidate_match(candidate_id, db)
        
        if not result['success']:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result['error']
            )
        
        return {
            "message": "Candidate matching completed successfully",
            "result": result
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing candidate match: {str(e)}"
        )

@router.post("/match-job/{job_id}")
async def match_all_candidates_for_job(job_id: int, db: AsyncSession = Depends(get_async_session)):
    """Process matching for all candidates of a specific job."""
    try:
        result = await MatchingService.process_job_matches(job_id, db)
        
        if not result['success']:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result['error']
            )
        
        return {
            "message": "Job matching completed successfully",
            "result": result
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing job matches: {str(e)}"
        )

@router.get("/match-results/{job_id}")
async def get_match_results(job_id: int, db: AsyncSession = Depends(get_async_session)):
    """Retrieve match results for all candidates of a specific job."""
    try:
        # Verify job exists
        job_result = await db.execute(select(Job).where(Job.id == job_id))
        job = job_result.scalar_one_or_none()
        if not job:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Job with ID {job_id} not found"
            )
        
        results = await MatchingService.get_match_results_for_job(job_id, db)
        
        return {
            "job_id": job_id,
            "job_title": job.title,
            "total_candidates": len(results),
            "candidates": results
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving match results: {str(e)}"
        )

@router.get("/shortlisted/{job_id}")
async def get_shortlisted_candidates(job_id: int, db: AsyncSession = Depends(get_async_session)):
    """Retrieve only shortlisted candidates for a specific job."""
    try:
        # Verify job exists
        job_result = await db.execute(select(Job).where(Job.id == job_id))
        job = job_result.scalar_one_or_none()
        if not job:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Job with ID {job_id} not found"
            )
        
        shortlisted = await MatchingService.get_shortlisted_candidates(job_id, db)
        
        return {
            "job_id": job_id,
            "job_title": job.title,
            "shortlisted_count": len(shortlisted),
            "shortlisted_candidates": shortlisted
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving shortlisted candidates: {str(e)}"
        )

@router.get("/by-vendor/{vendor_id}", response_model=List[CandidateResponse])
async def get_candidates_by_vendor(vendor_id: int, db: AsyncSession = Depends(get_async_session)):
    """Retrieve all candidates submitted by a specific vendor."""
    try:
        # First check if vendor exists
        vendor_result = await db.execute(select(Vendor).where(Vendor.id == vendor_id))
        vendor = vendor_result.scalar_one_or_none()
        if not vendor:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Vendor with ID {vendor_id} not found"
            )
        
        # Get candidates from this vendor
        result = await db.execute(
            select(Candidate).where(Candidate.vendor_id == vendor_id)
        )
        candidates = result.scalars().all()
        return candidates
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving candidates for vendor {vendor_id}: {str(e)}"
        )