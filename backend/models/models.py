from sqlalchemy import Column, Integer, String, ForeignKey, DateTime
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime,timezone

Base = declarative_base()

class Job(Base):
    __tablename__ = 'jobs'
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    description = Column(String)
    time_zone = Column(String)
    budget_range = Column(String)
    contract_duration = Column(String)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))  

class Vendor(Base):
    __tablename__ = 'vendors'
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    email = Column(String, unique=True)
    contact = Column(String)

class Candidate(Base):
    __tablename__ = 'candidates'
    id = Column(Integer, primary_key=True, index=True)
    job_id = Column(Integer, ForeignKey('jobs.id'))
    vendor_id = Column(Integer, ForeignKey('vendors.id'))
    name = Column(String, nullable=False)
    email = Column(String)
    phone = Column(String)
    soft_skills = Column(String)
    hard_skills = Column(String)
    experience = Column(Integer)
    time_zone_alignment = Column(String)
    contract_duration_willingness = Column(String)
    certifications = Column(String)
    cv_file_path = Column(String)
    submission_date = Column(DateTime, default=lambda: datetime.now(timezone.utc))





