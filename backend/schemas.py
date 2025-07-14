from datetime import datetime
from pydantic import BaseModel, Field
from typing import Optional

class JobCreate(BaseModel):
    '''Schema for creating a new job entry.'''
    title: str = Field(..., min_length=1, max_length=255, description="Job title")
    description: Optional[str] = Field(None, description="Job description")
    time_zone: Optional[str] = Field(None, description="required TimeZone")
    budget_range: Optional[str] = Field(None, description="Budget range for the job")
    contract_duration: Optional[str] = Field(None, description="Contract duration")

class JobResponse(BaseModel):
    '''Schema for the response of a job entry.'''
    id: int
    title: str
    description: Optional[str] = None
    time_zone: Optional[str] = None
    budget_range: Optional[str] = None
    contract_duration: Optional[str] = None
    created_at: datetime

    class config:
        '''Configuration for the JobResponse schema.'''
        from_attributes = True
        orm_mode = True

class VendorCreate(BaseModel):
    '''Schema for creating a new vendor entry.'''
    name: str = Field(..., min_length=1, max_length=255, description="Vendor's name")
    email: Optional[str] = Field(None, description="Vendor's email")
    contact: Optional[str] = Field(None, description="Vendor's contact number")
    
class VendorResponse(BaseModel):
    '''Schema for the response of a vendor entry.'''
    id: int
    name: str
    email: Optional[str] = None
    contact: Optional[str] = None

    class config:
        '''Configuration for the VendorResponse schema.'''
        from_attributes = True
        orm_mode = True

class CandidateCreate(BaseModel):
    '''Schema for creating a new candidate entry.'''
    job_id: int
    vendor_id: int
    name: str = Field(..., min_length=1, max_length=255, description="Candidate's name")
    email: Optional[str] = Field(None, description="Candidate's email")
    phone: Optional[str] = Field(None, description="Candidate's phone number")
    soft_skills: Optional[str] = Field(None, description="Soft skills of the candidate")
    hard_skills: Optional[str] = Field(None, description="Hard skills of the candidate")
    experience: Optional[int] = Field(None, ge=0, description="Years of experience")
    time_zone_alignment: Optional[str] = Field(None, description="Time zone alignment with the job")
    contract_duration_willingness: Optional[str] = Field(None, description="Willingness for contract duration")
    certifications: Optional[str] = Field(None, description="Certifications held by the candidate")
    cv_file_path: Optional[str] = Field(None, description="File path to the candidate's CV")

class CandidateResponse(BaseModel):
    '''Schema for the response of a candidate entry.'''
    id: int
    job_id: int
    vendor_id: int
    name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    soft_skills: Optional[str] = None
    hard_skills: Optional[str] = None
    experience: Optional[int] = None
    time_zone_alignment: Optional[str] = None
    contract_duration_willingness: Optional[str] = None
    certifications: Optional[str] = None
    cv_file_path: Optional[str] = None
    submission_date: datetime
    created_at: datetime

    class config:
        '''Configuration for the CandidateResponse schema.'''
        from_attributes = True
        orm_mode = True

