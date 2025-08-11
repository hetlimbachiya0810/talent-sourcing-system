from sqlalchemy import String, ForeignKey, DateTime, Float, Text, event
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from datetime import datetime, timezone

# This file defines the database models by defining every field that we will have for the talent sourcing system.

class Base(DeclarativeBase):
    pass

class Job(Base):
    __tablename__ = "jobs"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    title: Mapped[str] = mapped_column(nullable=False)
    description: Mapped[str] = mapped_column(nullable=False)
    time_zone: Mapped[str] = mapped_column(nullable=False)
    budget_range: Mapped[str] = mapped_column(nullable=False)
    contract_duration: Mapped[str] = mapped_column(nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc)
    )
    # is_accepted: Mapped[bool] = mapped_column(Boolean, default=True)

class Vendor(Base):
    __tablename__ = "vendors"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column(nullable=False)
    email: Mapped[str] = mapped_column(unique=True, nullable=True)
    contact: Mapped[str] = mapped_column(nullable=True)
class Candidate(Base):
    __tablename__ = "candidates"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    job_id: Mapped[int] = mapped_column(ForeignKey("jobs.id"))
    vendor_id: Mapped[int] = mapped_column(ForeignKey("vendors.id"))
    name: Mapped[str] = mapped_column(nullable=False)
    email: Mapped[str] = mapped_column(nullable=True)
    phone: Mapped[str] = mapped_column(nullable=True)
    soft_skills: Mapped[str] = mapped_column(nullable=True)
    hard_skills: Mapped[str] = mapped_column(nullable=True)
    experience: Mapped[int] = mapped_column(nullable=True)
    time_zone_alignment: Mapped[str] = mapped_column(nullable=True)
    contract_duration_willingness: Mapped[str] = mapped_column(nullable=True)
    certifications: Mapped[str] = mapped_column(nullable=True)
    cv_file_path: Mapped[str] = mapped_column(nullable=True)
    submission_date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc)
    )
    match_score: Mapped[float] = mapped_column(Float, nullable=True)
    status: Mapped[str] = mapped_column(String(50), nullable=True)
    mismatch_summary: Mapped[str] = mapped_column(nullable=True)

    # Financial Fields
    rate: Mapped[float] = mapped_column(Float, nullable=True, default= 0.0)
    margin: Mapped[float] = mapped_column(Float, nullable=True, default=0.0)
    infrastructure_cost: Mapped[float] = mapped_column(Float, nullable=True, default=0.0)
    processing_cost: Mapped[float] = mapped_column(Float, nullable=True, default=0.0)
    final_client_rate: Mapped[float] = mapped_column(Float, nullable=True, default=0.0)
    notice_period: Mapped[str] = mapped_column(String(100), nullable=True)
    availability_status: Mapped[str] = mapped_column(String(50), nullable=True)
    available_from: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    comments: Mapped[str] = mapped_column(Text, nullable=True)
    priority_level: Mapped[str] = mapped_column(String(20), nullable=True)
    shortlist_date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), 
        nullable=True
    )
    last_updated: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),   
    )

    def calculate_final_rate(self) -> float:
        """
        Calculate the final client rate based on the candidate's rate, margin, infrastructure cost, and processing cost.
        """
        rate = self.rate or 0.0
        margin = self.margin or 0.0
        infrastructure = self.infrastructure_cost or 0.0
        processing = self.processing_cost or 0.0
        return rate + margin + infrastructure + processing

    def update_final_rate(self) -> None:
        """
        Update the final client rate based on the current financial fields.
        """
        self.final_client_rate = self.calculate_final_rate()
        self.last_updated = datetime.now(timezone.utc)

@event.listens_for(Candidate.rate, 'set')
@event.listens_for(Candidate.margin, 'set')
@event.listens_for(Candidate.infrastructure_cost, 'set')
@event.listens_for(Candidate.processing_cost, 'set')
def update_candidate_final_rate(target, value, oldvalue, initiator):
    """
    Automatically recalculate final_client_rate when any cost component changes.
    Uses threading to avoid immediate recursion issues.
    """
    import threading
    def delayed_update():
        target.update_final_rate()
    threading.Timer(0, delayed_update).start()

# class ShortlistTracker(Base):
#     __tablename__ = "shortlist_tracker"
    
#     id: Mapped[int] = mapped_column(primary_key=True, index=True)
#     candidate_id: Mapped[int] = mapped_column(ForeignKey("candidates.id"), unique=True)
#     job_id: Mapped[int] = mapped_column(ForeignKey("jobs.id"))
    
#     # Business Fields
#     rate: Mapped[float] = mapped_column(Float, nullable=False)
#     margin_percentage: Mapped[float] = mapped_column(Float, nullable=False)
#     final_client_rate: Mapped[float] = mapped_column(Float, nullable=False)
    
#     # Availability Fields
#     notice_period: Mapped[str] = mapped_column(String(100), nullable=True)
#     availability_status: Mapped[str] = mapped_column(String(50), nullable=False)
#     available_from: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    
#     # Metadata
#     comments: Mapped[str] = mapped_column(Text, nullable=True)
#     priority_level: Mapped[str] = mapped_column(String(20), default="Medium")
#     created_at: Mapped[datetime] = mapped_column(
#         DateTime(timezone=True),
#         default=lambda: datetime.now(timezone.utc)
#     )
#     updated_at: Mapped[datetime] = mapped_column(
#         DateTime(timezone=True),
#         default=lambda: datetime.now(timezone.utc),
#         onupdate=lambda: datetime.now(timezone.utc)
#     )

# class User(Base):
#     __tablename__ = "users"

#     id: Mapped[int] = mapped_column(primary_key=True, index=True)
#     username: Mapped[str] = mapped_column(unique=True, nullable=False)
#     email: Mapped[str] = mapped_column(unique=True, nullable=False)
#     password: Mapped[str] = mapped_column(nullable=False)
    
#     created_at: Mapped[datetime] = mapped_column(
#         DateTime(timezone=True),
#         default=lambda: datetime.now(timezone.utc)
#     )
