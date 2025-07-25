import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.ext.asyncio import AsyncSession
from db.database import async_session
from models.models import Job, Vendor, Candidate
from services.matching_service import MatchingService

async def create_test_data():
    """Create sample test data for testing the matching engine."""
    async with async_session() as db:
        try:
            # Create a test job
            job = Job(
                title="Senior Python Developer",
                description="We are looking for a Senior Python Developer with experience in FastAPI, AWS, and machine learning. Must have strong communication skills and be available in IST timezone for 6 months contract.",
                time_zone="IST",
                budget_range="$50-70/hour",
                contract_duration="6 months"
            )
            db.add(job)
            await db.flush()
            
            # Create a test vendor
            vendor = Vendor(
                name="TechTalent Solutions",
                email="contact@techtalent.com",
                contact="+91-9876543210"
            )
            db.add(vendor)
            await db.flush()
            
            # Create test candidates with different skill levels
            candidates = [
                Candidate(
                    job_id=job.id,
                    vendor_id=vendor.id,
                    name="Alice Johnson",
                    email="alice@example.com",
                    hard_skills="Python, FastAPI, AWS, Machine Learning, Docker",
                    soft_skills="Communication, Leadership, Team work",
                    experience=5,
                    time_zone_alignment="IST",
                    contract_duration_willingness="6 months",
                    certifications="AWS Certified Developer, Python Institute"
                ),
                Candidate(
                    job_id=job.id,
                    vendor_id=vendor.id,
                    name="Bob Smith",
                    email="bob@example.com",
                    hard_skills="Python, Django, PostgreSQL",
                    soft_skills="Problem solving, Analytical thinking",
                    experience=3,
                    time_zone_alignment="EST",
                    contract_duration_willingness="3 months",
                    certifications="None"
                ),
                Candidate(
                    job_id=job.id,
                    vendor_id=vendor.id,
                    name="Carol Davis",
                    email="carol@example.com",
                    hard_skills="Java, Spring Boot, MySQL",
                    soft_skills="Communication, Teamwork",
                    experience=7,
                    time_zone_alignment="PST",
                    contract_duration_willingness="12 months",
                    certifications="Oracle Certified"
                )
            ]
            
            for candidate in candidates:
                db.add(candidate)
            
            await db.commit()
            
            print(f"Created test job: {job.title} (ID: {job.id})")
            print(f"Created test vendor: {vendor.name} (ID: {vendor.id})")
            print(f"Created {len(candidates)} test candidates")
            
            return job.id
            
        except Exception as e:
            await db.rollback()
            print(f"Error creating test data: {str(e)}")
            return None

async def test_matching_engine(job_id: int):
    """Test the matching engine with the created test data."""
    async with async_session() as db:
        try:
            print(f"\n=== Testing Matching Engine for Job ID: {job_id} ===")
            
            # Process matches for all candidates in the job
            result = await MatchingService.process_job_matches(job_id, db)
            
            if result['success']:
                print(f"\nMatching Results Summary:")
                print(f"Job: {result['job_title']}")
                print(f"Total candidates: {result['total_candidates']}")
                print(f"Successful matches: {result['successful_matches']}")
                print(f"Failed matches: {result['failed_matches']}")
                
                print(f"\nDetailed Results:")
                for candidate_result in result['results']:
                    if candidate_result['success']:
                        print(f"\n📋 {candidate_result['candidate_name']}:")
                        print(f"   Match Score: {candidate_result['match_score']}%")
                        print(f"   Status: {candidate_result['status']}")
                        if candidate_result['mismatch_summary']:
                            print(f"   Mismatches: {candidate_result['mismatch_summary']}")
                        
                        # Show field-level scores
                        if 'field_scores' in candidate_result:
                            print(f"   Field Scores:")
                            for field, score in candidate_result['field_scores'].items():
                                print(f"     {field.replace('_', ' ').title()}: {score:.1f}%")
                    else:
                        print(f"\n❌ {candidate_result.get('candidate_name', 'Unknown')}: {candidate_result['error']}")
            else:
                print(f"Matching failed: {result['error']}")
            
            # Test getting match results
            print(f"\n=== Testing Match Results Retrieval ===")
            match_results = await MatchingService.get_match_results_for_job(job_id, db)
            print(f"Retrieved {len(match_results)} match results")
            
            # Test getting shortlisted candidates
            shortlisted = await MatchingService.get_shortlisted_candidates(job_id, db)
            print(f"Found {len(shortlisted)} shortlisted candidates")
            
            for candidate in shortlisted:
                print(f"  ✅ {candidate['candidate_name']} - Score: {candidate['match_score']}%")
            
        except Exception as e:
            print(f"Error testing matching engine: {str(e)}")

async def main():
    """Main test function."""
    print("🚀 Starting Matching Engine Test")
    
    # Create test data
    job_id = await create_test_data()
    if not job_id:
        print("Failed to create test data. Exiting.")
        return
    
    # Test the matching engine
    await test_matching_engine(job_id)
    
    print("\n✅ Matching Engine Test Completed!")

if __name__ == "__main__":
    asyncio.run(main())