import os
from datetime import datetime
from pathlib import Path
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
import cloudinary
import cloudinary.uploader
from db.database import get_async_session
from models.models import Candidate, Job, Vendor
from schemas import CandidateCreate, CandidateResponse, VendorResponse, MatchResultResponse, CostCalculationRequest, CostCalculationResponse, BulkCostUpdate
from services.cost_calculation_service import CostCalculationService
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
    rate: Optional[float] = Form(None, ge=0, description="Candidate's hourly/daily rate"),
    margin: Optional[float] = Form(None, ge=0, description="Company margin amount"),
    infrastructure_cost: Optional[float] = Form(None, ge=0, description="Infrastructure cost"),
    processing_cost: Optional[float] = Form(None, ge=0, description="Processing & administrative costs"),
    notice_period: Optional[str] = Form(None, description="Notice period (e.g., '2 weeks', 'Immediate')"),
    availability_status: Optional[str] = Form(None, description="Availability status (e.g., 'Available', 'Busy')"),
    available_from: Optional[datetime] = Form(None, description="Date when candidate is available"),
    comments: Optional[str] = Form(None, description="Internal notes about the candidate"),
    priority_level: Optional[str] = Form(None, description="Priority level for candidate processing (e.g., 'High', 'Medium', 'Low')"),

    

    db: AsyncSession = Depends(get_async_session)
):
    """Create a new candidate entry with CV upload and automatic matching."""
    try:
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
            certifications=certifications,
            rate=rate,
            margin=margin,
            infrastructure_cost=infrastructure_cost,
            processing_cost=processing_cost,
            notice_period=notice_period,
            availability_status=availability_status,
            available_from=available_from,
            comments=comments,
            priority_level=priority_level
        )

        # print(f"Parsed experience: {candidate_data.experience}")

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

@router.put("/{candidate_id}/costs", response_model=dict)
async def update_candidate_costs(
    candidate_id: int,
    rate: Optional[float] = Form(None, ge=0, description="Base rate"),
    margin: Optional[float] = Form(None, ge=0, description="Margin amount"),
    infrastructure_cost: Optional[float] = Form(None, ge=0, description="Infrastructure costs"),
    processing_cost: Optional[float] = Form(None, ge=0, description="Processing costs"),
    db: AsyncSession = Depends(get_async_session)
):
    """
    Update cost-related fields for a specific candidate.
    
    - **rate**: Base hourly/daily rate
    - **margin**: Company margin amount (not percentage)
    - **infrastructure_cost**: Infrastructure costs
    - **processing_cost**: Processing and administrative costs
    
    The final_client_rate will be automatically calculated and updated.
    """
    try:
        result = await CostCalculationService.update_candidate_costs(
            candidate_id=candidate_id,
            db=db,
            rate=rate,
            margin=margin,
            infrastructure_cost=infrastructure_cost,
            processing_cost=processing_cost
        )
        
        if not result['success']:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result['error']
            )
        
        return {
            "message": "Candidate costs updated successfully",
            "data": result
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error updating candidate costs: {str(e)}"
        )

@router.post("/costs/bulk-update", response_model=dict)
async def bulk_update_candidate_costs(
    candidate_ids: List[int] = Form(..., description="List of candidate IDs"),
    rate: Optional[float] = Form(None, ge=0, description="Base rate for all candidates"),
    margin: Optional[float] = Form(None, ge=0, description="Margin for all candidates"),
    infrastructure_cost: Optional[float] = Form(None, ge=0, description="Infrastructure cost for all"),
    processing_cost: Optional[float] = Form(None, ge=0, description="Processing cost for all"),
    db: AsyncSession = Depends(get_async_session)
):
    """
    Bulk update cost fields for multiple candidates.
    
    All specified candidates will receive the same cost values.
    Final rates will be recalculated automatically.
    """
    try:
        if not candidate_ids:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No candidate IDs provided"
            )
        
        result = await CostCalculationService.bulk_update_costs(
            candidate_ids=candidate_ids,
            db=db,
            rate=rate,
            margin=margin,
            infrastructure_cost=infrastructure_cost,
            processing_cost=processing_cost
        )
        
        if not result['success']:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result['error']
            )
        
        return {
            "message": f"Successfully updated costs for {result['updated_count']} candidates",
            "data": result
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error in bulk cost update: {str(e)}"
        )

@router.post("/costs/calculate", response_model=CostCalculationResponse)
async def calculate_cost(cost_request: CostCalculationRequest):
    """
    Calculate final client rate from cost components without updating database.
    
    Useful for previewing calculations before saving.
    """
    try:
        # Validate input
        validation = CostCalculationService.validate_cost_components(
            rate=cost_request.rate,
            margin=cost_request.margin,
            infrastructure_cost=cost_request.infrastructure_cost,
            processing_cost=cost_request.processing_cost
        )
        
        if not validation['valid']:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Validation failed: {validation['errors']}"
            )
        
        # Calculate final rate
        final_rate = CostCalculationService.calculate_final_rate(
            rate=cost_request.rate,
            margin=cost_request.margin,
            infrastructure_cost=cost_request.infrastructure_cost,
            processing_cost=cost_request.processing_cost
        )
        
        # Prepare breakdown
        breakdown = {
            "base_rate": cost_request.rate,
            "margin": cost_request.margin,
            "infrastructure": cost_request.infrastructure_cost,
            "processing": cost_request.processing_cost,
            "total": final_rate
        }
        
        return CostCalculationResponse(
            rate=cost_request.rate,
            margin=cost_request.margin,
            infrastructure_cost=cost_request.infrastructure_cost,
            processing_cost=cost_request.processing_cost,
            final_client_rate=final_rate,
            breakdown=breakdown
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error calculating costs: {str(e)}"
        )

@router.get("/costs/summary/{job_id}", response_model=dict)
async def get_job_cost_summary(
    job_id: int,
    db: AsyncSession = Depends(get_async_session)
):
    """
    Get cost summary for all shortlisted candidates in a specific job.
    
    Returns total costs, averages, and breakdown by cost components.
    """
    try:
        result = await CostCalculationService.get_cost_summary_for_job(
            job_id=job_id,
            db=db
        )
        
        if not result['success']:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result['error']
            )
        
        return {
            "message": "Cost summary retrieved successfully",
            "data": result
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving cost summary: {str(e)}"
        )

@router.post("/costs/recalculate-all", response_model=dict)
async def recalculate_all_final_rates(db: AsyncSession = Depends(get_async_session)):
    """
    Recalculate final rates for all candidates with cost data.
    
    Useful for fixing any calculation inconsistencies or after formula changes.
    Admin endpoint - use with caution.
    """
    try:
        result = await CostCalculationService.recalculate_all_final_rates(db=db)
        
        if not result['success']:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result['error']
            )
        
        return {
            "message": "Final rates recalculated successfully",
            "data": result
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error recalculating final rates: {str(e)}"
        )

@router.get("/{candidate_id}/costs", response_model=dict)
async def get_candidate_cost_details(
    candidate_id: int,
    db: AsyncSession = Depends(get_async_session)
):
    """
    Get detailed cost breakdown for a specific candidate.
    """
    try:
        # Get candidate with cost data
        result = await db.execute(select(Candidate).where(Candidate.id == candidate_id))
        candidate = result.scalar_one_or_none()
        
        if not candidate:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Candidate with ID {candidate_id} not found"
            )
        
        # Calculate current final rate (in case it's not updated)
        calculated_final_rate = CostCalculationService.calculate_final_rate(
            candidate.rate or 0.0,
            candidate.margin or 0.0,
            candidate.infrastructure_cost or 0.0,
            candidate.processing_cost or 0.0
        )
        
        cost_data = {
            "candidate_id": candidate.id,
            "candidate_name": candidate.name,
            "cost_components": {
                "rate": candidate.rate,
                "margin": candidate.margin,
                "infrastructure_cost": candidate.infrastructure_cost,
                "processing_cost": candidate.processing_cost
            },
            "final_client_rate": candidate.final_client_rate,
            "calculated_final_rate": calculated_final_rate,
            "calculation_matches": abs((candidate.final_client_rate or 0) - calculated_final_rate) < 0.01,
            "has_complete_cost_data": all(x is not None for x in [
                candidate.rate, candidate.margin, 
                candidate.infrastructure_cost, candidate.processing_cost
            ])
        }
        
        return {
            "message": "Candidate cost details retrieved successfully",
            "data": cost_data
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving candidate cost details: {str(e)}"
        )