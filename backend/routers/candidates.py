import os
# import shutil
from datetime import datetime
from pathlib import Path
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
import cloudinary
import cloudinary.uploader
from cloudinary.utils import cloudinary_url
from db.database import get_async_session
from models.models import Candidate, Job, Vendor
from schemas import CandidateCreate, CandidateResponse, VendorResponse

router = APIRouter(prefix="/candidates", tags=["candidates"])

# # Create uploads directory if it doesn't exist
# UPLOAD_DIR = Path("backend/uploads")
# UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

cloudinary_url = os.getenv("CLOUDINARY_URL")

if cloudinary_url:
    cloudinary.config(cloudinary_url=cloudinary_url)
else:
    # Fallback to individual keys if the URL isn't set
    cloudinary.config(
        cloud_name = os.getenv("CLOUDINARY_CLOUD_NAME"),
        api_key = os.getenv("CLOUDINARY_API_KEY"),
        api_secret = os.getenv("CLOUDINARY_API_SECRET"),
        secure = True
    )

# Allowed file extensions and their MIME types
ALLOWED_EXTENSIONS = {".pdf", ".docx"}
ALLOWED_MIME_TYPES = {
    "application/pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
}

# Maximum file size (5MB)
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB in bytes

def validate_file(file: UploadFile) -> None:
    """Validate uploaded file type and size."""
    if not file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No file selected"
        )
    
    # Check file extension
    file_ext = Path(file.filename).suffix.lower()
    if file_ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid file type. Only PDF and DOCX files are allowed. Got: {file_ext}"
        )
    
    # Check MIME type
    if file.content_type not in ALLOWED_MIME_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid file type. Expected PDF or DOCX, got: {file.content_type}"
        )
    
    # # Check file size
    # if file.size and file.size > MAX_FILE_SIZE:
    #     raise HTTPException(
    #         status_code=status.HTTP_400_BAD_REQUEST,
    #         detail=f"File too large. Maximum size is 5MB, got: {file.size / (1024*1024):.2f}MB"
    #     )

# def generate_unique_filename(original_filename: str, candidate_id: int) -> str:
#     """Generate a unique filename for the uploaded CV."""
#     file_ext = Path(original_filename).suffix.lower()
#     timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
#     return f"candidate_{candidate_id}_{timestamp}{file_ext}"

def generate_public_id(original_filename: str, candidate_id: int) -> str:
    """Generate a unique public_id for the Cloudinary upload, including a folder path."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"candidate_cvs/candidate_{candidate_id}_{timestamp}"

# async def save_uploaded_file(file: UploadFile, filename: str) -> str:
#     """Save uploaded file to the uploads directory."""
#     try:
#         file_path = UPLOAD_DIR / filename
#         # print('Reached file till here')
#         upload_result = cloudinary.uploader.upload(file.file, 
#                                                    public_id="user_cv_loc",  
#                                                    resource_type="raw")
#         print(upload_result["secure_url"])

#         # Save the file
#         # with open(file_path, "wb") as buffer:
#         #     shutil.copyfileobj(file.file, buffer)
        
#         # Return relative path for database storage
#         return str(upload_result["secure_url"])
    
#     except Exception as e:
#         raise HTTPException(
#             status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
#             detail=f"Error saving file: {str(e)}"
#         )

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
         if "file size" in str(e).lower(): # Handle specific validation errors from Cloudinary
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
    """
    Create a new candidate entry with CV upload.
    
    - **cv_file**: CV file (PDF or DOCX format only, max 5MB)
    - **job_id**: ID of the job this candidate is applying for
    - **vendor_id**: ID of the vendor submitting this candidate
    - **name**: Candidate's full name (required)
    - **email**: Candidate's email address (optional)
    - **phone**: Candidate's phone number (optional)
    - **soft_skills**: Soft skills (optional)
    - **hard_skills**: Hard skills (optional)
    - **experience**: Years of experience (optional)
    - **time_zone_alignment**: Time zone alignment (optional)
    - **contract_duration_willingness**: Contract duration willingness (optional)
    - **certifications**: Certifications (optional)
    """
    try:
        # Validate file
        validate_file(cv_file)
        
        # Validate that job_id exists
        job_result = await db.execute(select(Job).where(Job.id == job_id))
        job = job_result.scalar_one_or_none()
        if not job:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Job with ID {job_id} not found"
            )
        
        # Validate that vendor_id exists
        vendor_result = await db.execute(select(Vendor).where(Vendor.id == vendor_id))
        vendor = vendor_result.scalar_one_or_none()
        if not vendor:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Vendor with ID {vendor_id} not found"
            )
        
        # Create candidate record first (without file path)
        candidate = Candidate(
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
        
        # Add candidate to database and flush to get the ID
        db.add(candidate)
        await db.flush()
        
        # # Generate unique filename using candidate ID
        # unique_filename = generate_unique_filename(cv_file.filename, candidate.id)
        
        # # Save the uploaded file
        # # file_path = await save_uploaded_file(cv_file, unique_filename)
        # file_path = await save_uploaded_file(cv_file, unique_filename)

        # Generate a unique public ID for Cloudinary using the candidate's new DB ID
        public_id = generate_public_id(cv_file.filename, candidate.id)

        #upload the file using the new function and unique ID
        file_url = await upload_file_to_cloudinary(cv_file, public_id)

        # Update candidate with file path
        candidate.cv_file_path = file_url
        
        # Commit the transaction
        await db.commit()
        await db.refresh(candidate)
        
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
async def get_all_candidates(
    db: AsyncSession = Depends(get_async_session)
):
    """
    Retrieve all candidates with their details.
    """
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
async def get_candidate(
    candidate_id: int,
    db: AsyncSession = Depends(get_async_session)
):
    """
    Retrieve a specific candidate by ID.
    """
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
async def get_candidates_by_job(
    job_id: int,
    db: AsyncSession = Depends(get_async_session)
):
    """
    Retrieve all candidates for a specific job.
    """
    try:
        # First check if job exists
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

@router.get("/by-vendor/{vendor_id}", response_model=List[CandidateResponse])
async def get_candidates_by_vendor(
    vendor_id: int,
    db: AsyncSession = Depends(get_async_session)
):
    """
    Retrieve all candidates submitted by a specific vendor.
    """
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