from datetime import datetime
from enum import Enum
from pydantic import BaseModel, ConfigDict, EmailStr, Field, computed_field, field_validator
import re
from typing import List, Optional, Dict
# from routers.candidates import 
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

    model_config = ConfigDict(from_attributes=True)


class JobUpdate(BaseModel):
    '''Schema for updating an existing job entry.'''
    title: Optional[str] = Field(None, min_length=1, max_length=255, description="Job title")
    description: Optional[str] = Field(None, description="Job description")
    time_zone: Optional[str] = Field(None, description="Time zone required for the job")
    budget_range: Optional[str] = Field(None, description="Budget range for the job")
    contract_duration: Optional[str] = Field(None, description="Contract duration for the job")

class VendorCreate(BaseModel):
    '''Schema for creating a new vendor entry.'''
    name: str = Field(..., min_length=1, max_length=255, description="Vendor's name")
    email: Optional[EmailStr] = Field(None, description="Vendor's email")
    contact: Optional[str] = Field(None, description="Vendor's contact number")
    
class VendorResponse(BaseModel):
    '''Schema for the response of a vendor entry.'''
    id: int
    name: str
    email: Optional[EmailStr] = None
    contact: Optional[str] = None

    model_config = ConfigDict(from_attributes=True) 


class CandidateCreate(BaseModel):
    '''Schema for creating a new candidate entry from form data.'''
    job_id: int
    vendor_id: int
    name: str = Field(..., min_length=1, max_length=255, description="Candidate's name")
    email: Optional[EmailStr] = Field(None, description="Candidate's email")
    phone: Optional[str] = Field(None, description="Candidate's phone number")
    soft_skills: Optional[str] = Field(None, description="Soft skills of the candidate")
    hard_skills: Optional[str] = Field(None, description="Hard skills of the candidate")
    experience: Optional[int] = Field(None, ge=0, description="Years of experience")
    time_zone_alignment: Optional[str] = Field(None, description="Time zone alignment with the job")
    contract_duration_willingness: Optional[str] = Field(None, description="Willingness for contract duration")
    certifications: Optional[str] = Field(None, description="Certifications held by the candidate")
    rate: Optional[float] = Field(None, ge=0, description="Candidate's hourly/daily rate")
    margin: Optional[float] = Field(None, ge=0, description="Company margin amount")
    infrastructure_cost: Optional[float] = Field(None, ge=0, description="Infrastructure cost")
    processing_cost: Optional[float] = Field(None, ge=0, description="Processing & administrative costs")
    notice_period: Optional[str] = Field(None, max_length=100, description="Notice period (e.g., '2 weeks', 'Immediate')")
    availability_status: Optional[str] = Field(None, description="Availability status (e.g., 'Available', 'Busy', 'Partially Available')")
    available_from: Optional[datetime] = Field(None, description="Date when candidate is available")
    comments: Optional[str] = Field(None, max_length=1000, description="Internal notes")
    priority_level: Optional[str] = Field(None, description="Priority level (e.g., 'High', 'Medium', 'Low')")
    
    # print("\n=== Parsed Data for Database ===")
    # print(f"Job ID (parsed): {candidate_data.job_id}")
    # print(f"Vendor ID (parsed): {candidate_data.vendor_id}")
    # print(f"Name (parsed): {candidate_data.name}")
    # print(f"Email (parsed): {candidate_data.email}")
    # print(f"Phone (parsed): {candidate_data.phone}")
    # print(f"Soft Skills (parsed): {candidate_data.soft_skills}")
    # print(f"Hard Skills (parsed): {candidate_data.hard_skills}")
    # print(f"Experience (parsed): {candidate_data.experience}")  # Already there, but full list
    # print(f"Time Zone Alignment (parsed): {candidate_data.time_zone_alignment}")
    # print(f"Contract Duration Willingness (parsed): {candidate_data.contract_duration_willingness}")
    # print(f"Certifications (parsed): {candidate_data.certifications}")
    # print(f"Rate (parsed): {candidate_data.rate}")
    # print(f"Margin (parsed): {candidate_data.margin}")
    # print(f"Infrastructure Cost (parsed): {candidate_data.infrastructure_cost}")
    # print(f"Processing Cost (parsed): {candidate_data.processing_cost}")
    # print(f"Notice Period (parsed): {candidate_data.notice_period}")
    # print(f"Availability Status (parsed): {candidate_data.availability_status}")
    # print(f"Available From (parsed): {candidate_data.available_from}")
    # print(f"Comments (parsed): {candidate_data.comments}")
    # print(f"Priority Level (parsed): {candidate_data.priority_level}")
    # print("=========================\n")
    @field_validator('experience', mode='before')
    @classmethod
    def parse_experience(cls, v):
        # Handle None/empty values
        if v is None or v == "":
            return None
            
        if isinstance(v, int):
            return v
            
        if isinstance(v, str):
            v = v.strip()
            if not v:  # Empty string after strip
                return None
                
            numbers = re.findall(r'\d+\.?\d*', v.lower())
            if numbers:
                return int(float(numbers[0]))
            
            if 'fresher' in v.lower() or 'entry' in v.lower():
                return 0
                
            return 0  # Default for unparseable strings
        
        return int(v) if v is not None else None
    
    @field_validator('phone', mode='before') 
    @classmethod
    def validate_phone(cls, v):
        if v:
            return re.sub(r'[\s\-\(\)]', '', str(v))
        return v
    
class CandidateResponse(BaseModel):
    '''Schema for the response of a candidate entry including matching results.'''
    id: int
    job_id: int
    vendor_id: int
    name: str
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    soft_skills: Optional[str] = None
    hard_skills: Optional[str] = None
    experience: Optional[int] = None
    time_zone_alignment: Optional[str] = None
    contract_duration_willingness: Optional[str] = None
    certifications: Optional[str] = None
    cv_file_path: Optional[str] = None
    submission_date: datetime
    match_score: Optional[float] = None
    status: Optional[str] = None  # "Shortlisted" or "Rejected"
    mismatch_summary: Optional[str] = None
    rate: Optional[float] = None
    margin: Optional[float] = None
    infrastructure_cost: Optional[float] = None
    processing_cost: Optional[float] = None
    final_client_rate: Optional[float] = None
    notice_period: Optional[str] = None
    availability_status: Optional[str] = None
    available_from: Optional[datetime] = None
    comments: Optional[str] = None
    priority_level: Optional[str] = None
    shortlist_date: Optional[datetime] = None
    last_updated: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)

    @computed_field
    @property
    def cost_breakdown(self) -> Optional[Dict[str, float]]:
        """Calculate and return a breakdown of costs."""
        if all(x is not None for x in [self.rate, self.margin, self.infrastructure_cost, self.processing_cost]):
            return {
                "base_rate": self.rate or 0.0,
                "margin": self.margin or 0.0,
                "infrastructure_cost": self.infrastructure_cost or 0.0,
                "processing_cost": self.processing_cost or 0.0,
                "total_cost": (self.rate or 0.0) + (self.margin or 0.0) +
                               (self.infrastructure_cost or 0.0) + (self.processing_cost or 0.0)
            }
        return None
    @computed_field
    @property
    def has_complete_cost_data(self) -> bool:
        """Check if all cost-related fields are populated."""
        return all(x is not None for x in [
            self.rate, self.margin, self.infrastructure_cost, 
            self.processing_cost
        ])

class CostCalculationRequest(BaseModel):
    """Schema for cost calculation requests."""
    rate: float = Field(..., ge=0, description="Base rate")
    margin: float = Field(..., ge=0, description="Margin amount")
    infrastructure_cost: float = Field(0.0, ge=0, description="Infrastructure costs")
    processing_cost: float = Field(0.0, ge=0, description="Processing costs")

class CostCalculationResponse(BaseModel):
    """Schema for cost calculation responses."""
    rate: float
    margin: float
    infrastructure_cost: float
    processing_cost: float
    final_client_rate: float
    breakdown: Dict[str, float]
    
    @computed_field
    @property
    def cost_summary(self) -> str:
        """Human-readable cost summary."""
        return f"Rate: ${self.rate} + Margin: ${self.margin} + Infrastructure: ${self.infrastructure_cost} + Processing: ${self.processing_cost} = ${self.final_client_rate}"

class BulkCostUpdate(BaseModel):
    """Schema for bulk cost updates."""
    candidate_ids: List[int]
    cost_data: CostCalculationRequest
    recalculate_final_rate: bool = Field(True, description="Whether to recalculate final rates")

class CostValidationResult(BaseModel):
    """Schema for cost validation results."""
    valid: bool
    errors: List[str] = []
    warnings: List[str] = []
    calculated_final_rate: Optional[float] = None
class ShortlistWithCosts(BaseModel):
    """Enhanced shortlist tracker with detailed cost information."""
    job_id: int
    job_title: str
    total_shortlisted: int
    candidates: List[CandidateResponse]
    
    @computed_field
    @property
    def cost_summary(self) -> Dict[str, float]:
        """Calculate cost summary for all shortlisted candidates."""
        candidates_with_costs = [c for c in self.candidates if c.final_client_rate is not None]
        
        if not candidates_with_costs:
            return {"total_candidates": len(self.candidates), "candidates_with_costs": 0}
        
        total_cost = sum(c.final_client_rate for c in candidates_with_costs)
        avg_cost = total_cost / len(candidates_with_costs) if candidates_with_costs else 0.0
        min_cost = min(c.final_client_rate for c in candidates_with_costs)
        max_cost = max(c.final_client_rate for c in candidates_with_costs)
        
        return {
            "total_candidates": len(self.candidates),
            "candidates_with_costs": len(candidates_with_costs),
            "total_cost": round(total_cost, 2),
            "average_cost": round(avg_cost, 2),
            "min_cost": round(min_cost, 2),
            "max_cost": round(max_cost, 2)
        }

    @computed_field
    @property
    def cost_breakdown_by_component(self) -> Dict[str, float]:
        """Break down costs by component across all candidates."""
        candidates_with_costs = [c for c in self.candidates if c.has_complete_cost_data]
        
        if not candidates_with_costs:
            return {}
        
        return {
            "total_base_rate": sum(c.rate or 0 for c in candidates_with_costs),
            "total_margin": sum(c.margin or 0 for c in candidates_with_costs),
            "total_infrastructure": sum(c.infrastructure_cost or 0 for c in candidates_with_costs),
            "total_processing": sum(c.processing_cost or 0 for c in candidates_with_costs),
        }

def validate_cost_data(rate: float = None, margin: float = None, 
                      infrastructure_cost: float = None, processing_cost: float = None) -> CostValidationResult:
    """Validate cost calculation data."""
    errors = []
    warnings = []
    
    # Validation rules
    for field_name, value in [("rate", rate), ("margin", margin), 
                             ("infrastructure_cost", infrastructure_cost), 
                             ("processing_cost", processing_cost)]:
        if value is not None:
            if value < 0:
                errors.append(f"{field_name} cannot be negative: {value}")
            elif value > 10000:  # Reasonable upper limit
                warnings.append(f"{field_name} is unusually high: {value}")
    
    # Calculate final rate if all components are provided
    calculated_final_rate = None
    if all(x is not None for x in [rate, margin, infrastructure_cost, processing_cost]):
        calculated_final_rate = rate + margin + infrastructure_cost + processing_cost
    
    return CostValidationResult(
        valid=len(errors) == 0,
        errors=errors,
        warnings=warnings,
        calculated_final_rate=calculated_final_rate
    )

def calculate_final_rate(rate: float, margin: float = 0.0, 
                        infrastructure_cost: float = 0.0, processing_cost: float = 0.0) -> float:
    """
    Calculate final client rate from cost components.
    
    Args:
        rate: Base candidate rate
        margin: Company margin
        infrastructure_cost: Infrastructure costs
        processing_cost: Processing costs
        
    Returns:
        Final client rate
    """
    return rate + margin + infrastructure_cost + processing_cost

class MatchResultResponse(BaseModel):
    '''Schema for match result responses.'''
    candidate_id: int
    candidate_name: str
    vendor_id: int
    match_score: Optional[float] = None
    status: Optional[str] = None
    mismatch_summary: Optional[str] = None
    hard_skills: Optional[str] = None
    soft_skills: Optional[str] = None
    experience: Optional[int] = None
    certifications: Optional[str] = None
    time_zone_alignment: Optional[str] = None
    contract_duration_willingness: Optional[str] = None
    submission_date: datetime

class MatchProcessResult(BaseModel):
    '''Schema for match processing results.'''
    success: bool
    candidate_id: Optional[int] = None
    candidate_name: Optional[str] = None
    job_title: Optional[str] = None
    match_score: Optional[float] = None
    status: Optional[str] = None
    mismatch_summary: Optional[str] = None
    field_scores: Optional[Dict[str, float]] = None
    error: Optional[str] = None

class JobMatchResults(BaseModel):
    '''Schema for job-level match results.'''
    job_id: int
    job_title: str
    total_candidates: int
    candidates: List[MatchResultResponse]

class ShortlistedResults(BaseModel):
    '''Schema for shortlisted candidates results.'''
    job_id: int
    job_title: str
    shortlisted_count: int
    shortlisted_candidates: List[MatchResultResponse]

class AvailabilityStatus(str, Enum):
    '''Enum for availability status.'''
    AVAILABLE = "Available"
    BUSY = "Busy"
    PARTIALLY_AVAILABLE = "Partially Available"

class PriorityLevel(str, Enum):
    '''Enum for priority levels.'''
    LOW = "Low"
    MEDIUM = "Medium"
    HIGH = "High"

class CandidateUpdate(BaseModel):
    '''Schema for updating candidate with tracker information.'''

    name: Optional[str] = Field(None, min_length=1, max_length=255, description="Candidate's name")
    email: Optional[EmailStr] = Field(None, description="Candidate's email")
    phone: Optional[str] = Field(None, description="Candidate's phone number")

    rate: Optional[float] = Field(None, ge=0, description="Candidate's hourly/daily rate")
    margin: Optional[float] = Field(None, ge=0, description="Company margin amount")
    infrastructure_cost: Optional[float] = Field(None, ge=0, description="Infrastructure costs (servers, software, etc.)")
    processing_cost: Optional[float] = Field(None, ge=0, description="Processing and administrative costs")
    notice_period: Optional[str] = Field(None, max_length=100, description="Notice period")
    availability_status: Optional[AvailabilityStatus] = Field(None, description="Availability status")
    available_from: Optional[datetime] = Field(None, description="Date when candidate is available")
    comments: Optional[str] = Field(None,max_length=1000, description="Internal notes")
    priority_level: Optional[PriorityLevel] = Field(None, description="Priority level")

    @computed_field
    @property
    def calculated_final_rate(self) -> Optional[float]:
        '''Calculate final client rate based on rate and margin percentage.'''
        if all(x is not None for x in [self.rate, self.margin, self.infrastructure_cost, self.processing_cost]):
            return self.rate + self.margin + self.infrastructure_cost + self.processing_cost
        return None

class CandidateTracker(BaseModel):
    '''Schema for Candidate in shortlist tracker view.'''
    id: int
    name: str
    email: Optional[EmailStr] = None

    rate: Optional[float] = None
    margin: Optional[float] = None
    final_client_rate: Optional[float] = None

    notice_period: Optional[str] = None
    availability_status: Optional[AvailabilityStatus] = None
    available_from: Optional[datetime] = None

    priority_level: Optional[PriorityLevel] = None
    comments: Optional[str] = Field(None, max_length=1000)

    submission_date: datetime
    shortlist_date: Optional[datetime] = None

    @computed_field
    @property
    def calculated_client_rate(self) -> Optional[float]:
        '''Calculate final client rate based on rate and margin percentage.'''
        if self.final_client_rate:
            return self.final_client_rate
        if self.rate and self.margin:
            return self.rate + self.margin 
        return None
    
class ShortlistSummary(BaseModel):
    """Summary statistics for shortlisted candidates."""
    total_candidates: int
    average_match_score: Optional[float] = None
    average_rate: Optional[float] = None
    rate_range: Optional[Dict[str, float]] = None
    total_estimated_cost: Optional[float] = None
    availability_breakdown: Dict[str, int] = Field(default_factory=dict)
    priority_breakdown: Dict[str, int] = Field(default_factory=dict)

class JobShortlistTracker(BaseModel):
    """Complete shortlist tracker for a job."""
    job_id: int
    job_title: str
    created_at: datetime
    last_updated: datetime
    
    # Candidates data
    candidates: List[CandidateTracker]
    summary: ShortlistSummary
    
    # Metadata
    total_shortlisted: int
    
    @computed_field
    @property
    def has_rates_configured(self) -> bool:
        """Check if any candidates have rate information."""
        return any(c.rate is not None for c in self.candidates)
    
    @computed_field  
    @property
    def ready_for_export(self) -> bool:
        """Check if tracker is ready for Excel export."""
        return len(self.candidates) > 0 and self.has_rates_configured