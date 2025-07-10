from sqlalchemy import String, Integer, ForeignKey, DateTime
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from datetime import datetime, timezone

# This file defines the database models by defining every field that we will have for the talent sourcing system.

class Base(DeclarativeBase):
    pass

class Job(Base):
    __tablename__ = "jobs"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    title: Mapped[str] = mapped_column(nullable=False)
    description: Mapped[str] = mapped_column(nullable=True)
    time_zone: Mapped[str] = mapped_column(nullable=True)
    budget_range: Mapped[str] = mapped_column(nullable=True)
    contract_duration: Mapped[str] = mapped_column(nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc)
    )

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
