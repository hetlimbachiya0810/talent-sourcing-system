from sqlalchemy.orm import Session
from db.database import SessionLocal
from models.models import Job, Vendor, Candidate

def test_schema():
    db: Session = SessionLocal()
    vendor = Vendor(name="TechVendor Inc.", email="contact@techvendor.com", contact="+91-9876543210")
    db.add(vendor)
    db.commit()
    db.refresh(vendor)
    print(f"Created vendor: {vendor.name}, ID: {vendor.id}")

    job = Job(
        title="Python Developer",
        time_zone="IST",
        budget_range="$50–$70/hr",
        contract_duration="6 months",
        description="Develop backend APIs using FastAPI."
    )
    db.add(job)
    db.commit()
    db.refresh(job)
    print(f"Created job: {job.title}, ID: {job.id}, Created At: {job.created_at}")

    candidate = Candidate(
        job_id=job.id,
        vendor_id=vendor.id,
        name="John Doe",
        email="john.doe@example.com",
        phone="+91-1234567890",
        soft_skills="Communication, Teamwork",
        hard_skills="Python, SQL, FastAPI",
        experience=5,
        time_zone_alignment="Matches IST",
        contract_duration_willingness="6 months",
        certifications="AWS Certified",
        cv_file_path="uploads/cvs/john_doe.pdf"
    )
    db.add(candidate)
    db.commit()
    db.refresh(candidate)
    print(f"Created candidate: {candidate.name}, ID: {candidate.id}, Submission Date: {candidate.submission_date}")

if __name__ == "__main__":
    test_schema()