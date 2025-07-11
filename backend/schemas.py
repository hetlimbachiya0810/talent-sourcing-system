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