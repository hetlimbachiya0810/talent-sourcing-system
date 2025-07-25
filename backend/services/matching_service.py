from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from models.models import Candidate, Job
from utils.text_parser import TextParser
from utils.matching_engine import MatchingEngine
import logging
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)

class MatchingService:
    """
    Service class that orchestrates the CV-JD matching process.
    Handles the complete workflow from text extraction to result storage.
    """
    
    @staticmethod
    async def process_candidate_match(candidate_id: int, db: AsyncSession) -> Dict:
        """
        Process matching for a single candidate against their associated job.
        
        Args:
            candidate_id (int): ID of the candidate to process
            db (AsyncSession): Database session
            
        Returns:
            Dict: Match results with success status and details
        """
        try:
            # Fetch candidate and associated job
            candidate_result = await db.execute(
                select(Candidate).where(Candidate.id == candidate_id)
            )
            candidate = candidate_result.scalar_one_or_none()
            
            if not candidate:
                return {
                    'success': False,
                    'error': f'Candidate with ID {candidate_id} not found'
                }
            
            job_result = await db.execute(
                select(Job).where(Job.id == candidate.job_id)
            )
            job = job_result.scalar_one_or_none()
            
            if not job:
                return {
                    'success': False,
                    'error': f'Job with ID {candidate.job_id} not found'
                }
            
            # Extract text from CV
            cv_text = ""
            if candidate.cv_file_path:
                cv_text = TextParser.extract_text_from_cv(candidate.cv_file_path)
                if not cv_text:
                    logger.warning(f"No text extracted from CV for candidate {candidate_id}")
            
            # Extract text from JD
            jd_text = TextParser.extract_jd_text(job)
            
            # Perform matching
            match_result = MatchingEngine.match_candidate_to_job(
                candidate, job, cv_text, jd_text
            )
            
            # Update candidate record with results
            candidate.match_score = match_result['match_score']
            candidate.status = match_result['status']
            candidate.mismatch_summary = match_result['mismatch_summary']
            
            # Commit changes to database
            await db.commit()
            await db.refresh(candidate)
            
            logger.info(f"Successfully processed match for candidate {candidate_id}: "
                       f"Score={match_result['match_score']}, Status={match_result['status']}")
            
            return {
                'success': True,
                'candidate_id': candidate_id,
                'candidate_name': candidate.name,
                'job_title': job.title,
                'match_score': match_result['match_score'],
                'status': match_result['status'],
                'mismatch_summary': match_result['mismatch_summary'],
                'field_scores': match_result['field_scores']
            }
            
        except Exception as e:
            await db.rollback()
            logger.error(f"Error processing match for candidate {candidate_id}: {str(e)}")
            return {
                'success': False,
                'error': f'Error processing match: {str(e)}'
            }
    
    @staticmethod
    async def process_job_matches(job_id: int, db: AsyncSession) -> Dict:
        """
        Process matching for all candidates associated with a specific job.
        
        Args:
            job_id (int): ID of the job to process candidates for
            db (AsyncSession): Database session
            
        Returns:
            Dict: Results for all candidates processed
        """
        try:
            # Fetch job
            job_result = await db.execute(select(Job).where(Job.id == job_id))
            job = job_result.scalar_one_or_none()
            
            if not job:
                return {
                    'success': False,
                    'error': f'Job with ID {job_id} not found'
                }
            
            # Fetch all candidates for this job
            candidates_result = await db.execute(
                select(Candidate).where(Candidate.job_id == job_id)
            )
            candidates = candidates_result.scalars().all()
            
            if not candidates:
                return {
                    'success': True,
                    'message': f'No candidates found for job {job_id}',
                    'results': []
                }
            
            # Process each candidate
            results = []
            successful_matches = 0
            failed_matches = 0
            
            for candidate in candidates:
                result = await MatchingService.process_candidate_match(candidate.id, db)
                results.append(result)
                
                if result['success']:
                    successful_matches += 1
                else:
                    failed_matches += 1
            
            logger.info(f"Processed {len(candidates)} candidates for job {job_id}: "
                       f"{successful_matches} successful, {failed_matches} failed")
            
            return {
                'success': True,
                'job_id': job_id,
                'job_title': job.title,
                'total_candidates': len(candidates),
                'successful_matches': successful_matches,
                'failed_matches': failed_matches,
                'results': results
            }
            
        except Exception as e:
            logger.error(f"Error processing matches for job {job_id}: {str(e)}")
            return {
                'success': False,
                'error': f'Error processing job matches: {str(e)}'
            }
    
    @staticmethod
    async def get_match_results_for_job(job_id: int, db: AsyncSession) -> List[Dict]:
        """
        Retrieve match results for all candidates of a specific job.
        
        Args:
            job_id (int): ID of the job
            db (AsyncSession): Database session
            
        Returns:
            List[Dict]: List of candidate match results
        """
        try:
            # Fetch candidates with match results
            result = await db.execute(
                select(Candidate).where(Candidate.job_id == job_id)
            )
            candidates = result.scalars().all()
            
            match_results = []
            for candidate in candidates:
                match_results.append({
                    'candidate_id': candidate.id,
                    'candidate_name': candidate.name,
                    'vendor_id': candidate.vendor_id,
                    'match_score': candidate.match_score,
                    'status': candidate.status,
                    'mismatch_summary': candidate.mismatch_summary,
                    'hard_skills': candidate.hard_skills,
                    'soft_skills': candidate.soft_skills,
                    'experience': candidate.experience,
                    'certifications': candidate.certifications,
                    'time_zone_alignment': candidate.time_zone_alignment,
                    'contract_duration_willingness': candidate.contract_duration_willingness,
                    'submission_date': candidate.submission_date
                })
            
            return match_results
            
        except Exception as e:
            logger.error(f"Error retrieving match results for job {job_id}: {str(e)}")
            raise Exception(f"Error retrieving match results: {str(e)}")
    
    @staticmethod
    async def get_shortlisted_candidates(job_id: int, db: AsyncSession) -> List[Dict]:
        """
        Retrieve only shortlisted candidates for a specific job.
        
        Args:
            job_id (int): ID of the job
            db (AsyncSession): Database session
            
        Returns:
            List[Dict]: List of shortlisted candidate results
        """
        try:
            result = await db.execute(
                select(Candidate).where(
                    Candidate.job_id == job_id,
                    Candidate.status == "Shortlisted"
                )
            )
            candidates = result.scalars().all()
            
            shortlisted_results = []
            for candidate in candidates:
                shortlisted_results.append({
                    'candidate_id': candidate.id,
                    'candidate_name': candidate.name,
                    'vendor_id': candidate.vendor_id,
                    'match_score': candidate.match_score,
                    'status': candidate.status,
                    'hard_skills': candidate.hard_skills,
                    'soft_skills': candidate.soft_skills,
                    'experience': candidate.experience,
                    'certifications': candidate.certifications,
                    'time_zone_alignment': candidate.time_zone_alignment,
                    'contract_duration_willingness': candidate.contract_duration_willingness,
                    'submission_date': candidate.submission_date,
                    'cv_file_path': candidate.cv_file_path
                })
            
            return shortlisted_results
            
        except Exception as e:
            logger.error(f"Error retrieving shortlisted candidates for job {job_id}: {str(e)}")
            raise Exception(f"Error retrieving shortlisted candidates: {str(e)}")