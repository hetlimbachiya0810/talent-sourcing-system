# backend/services/cost_calculation_service.py
"""
Cost Calculation Service for Task 2
Handles all cost-related calculations and business logic.
"""

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import update
from models.models import Candidate
from typing import Dict, List, Optional, Tuple
import logging

logger = logging.getLogger(__name__)

class CostCalculationService:
    """Service class for handling cost calculations and updates."""
    
    @staticmethod
    def calculate_final_rate(rate: float, margin: float = 0.0, 
                           infrastructure_cost: float = 0.0, 
                           processing_cost: float = 0.0) -> float:
        """
        Calculate final client rate from cost components.
        
        Formula: final_rate = rate + margin + infrastructure_cost + processing_cost
        
        Args:
            rate: Base candidate rate
            margin: Company margin amount
            infrastructure_cost: Infrastructure costs
            processing_cost: Processing and administrative costs
            
        Returns:
            Final client rate
        """
        return (rate or 0.0) + (margin or 0.0) + (infrastructure_cost or 0.0) + (processing_cost or 0.0)
    
    @staticmethod
    def validate_cost_components(rate: Optional[float] = None, 
                               margin: Optional[float] = None,
                               infrastructure_cost: Optional[float] = None, 
                               processing_cost: Optional[float] = None) -> Dict:
        """
        Validate cost components and return validation results.
        
        Returns:
            Dict with validation results: {'valid': bool, 'errors': list, 'warnings': list}
        """
        result = {'valid': True, 'errors': [], 'warnings': []}
        
        cost_fields = {
            'rate': rate,
            'margin': margin,
            'infrastructure_cost': infrastructure_cost,
            'processing_cost': processing_cost
        }
        
        for field_name, value in cost_fields.items():
            if value is not None:
                if value < 0:
                    result['errors'].append(f"{field_name} cannot be negative: {value}")
                    result['valid'] = False
                elif value > 10000:  # Reasonable upper limit
                    result['warnings'].append(f"{field_name} is unusually high: {value}")
                elif field_name == 'rate' and value == 0:
                    result['warnings'].append("Rate is zero - candidate working for free?")
        
        return result
    
    @staticmethod
    async def update_candidate_costs(candidate_id: int, db: AsyncSession,
                                   rate: Optional[float] = None,
                                   margin: Optional[float] = None,
                                   infrastructure_cost: Optional[float] = None,
                                   processing_cost: Optional[float] = None) -> Dict:
        """
        Update cost fields for a specific candidate and recalculate final rate.
        
        Args:
            candidate_id: ID of the candidate to update
            db: Database session
            rate: New rate (optional)
            margin: New margin (optional)
            infrastructure_cost: New infrastructure cost (optional)
            processing_cost: New processing cost (optional)
            
        Returns:
            Dict with update results
        """
        try:
            # Fetch current candidate
            result = await db.execute(select(Candidate).where(Candidate.id == candidate_id))
            candidate = result.scalar_one_or_none()
            
            if not candidate:
                return {
                    'success': False,
                    'error': f'Candidate {candidate_id} not found'
                }
            
            # Prepare update data
            update_data = {}
            
            # Use new values or keep existing ones
            final_rate = rate if rate is not None else candidate.rate
            final_margin = margin if margin is not None else candidate.margin
            final_infrastructure = infrastructure_cost if infrastructure_cost is not None else candidate.infrastructure_cost
            final_processing = processing_cost if processing_cost is not None else candidate.processing_cost
            
            # Validate the cost data
            validation = CostCalculationService.validate_cost_components(
                rate=final_rate,
                margin=final_margin,
                infrastructure_cost=final_infrastructure,
                processing_cost=final_processing
            )
            
            if not validation['valid']:
                return {
                    'success': False,
                    'error': 'Validation failed',
                    'validation_errors': validation['errors']
                }
            
            # Update fields that were provided
            if rate is not None:
                update_data['rate'] = rate
            if margin is not None:
                update_data['margin'] = margin
            if infrastructure_cost is not None:
                update_data['infrastructure_cost'] = infrastructure_cost
            if processing_cost is not None:
                update_data['processing_cost'] = processing_cost
            
            # Calculate and update final rate
            calculated_final_rate = CostCalculationService.calculate_final_rate(
                final_rate, final_margin, final_infrastructure, final_processing
            )
            update_data['final_client_rate'] = calculated_final_rate
            
            # Execute update
            if update_data:
                await db.execute(
                    update(Candidate)
                    .where(Candidate.id == candidate_id)
                    .values(**update_data)
                )
                await db.commit()
            
            # Fetch updated candidate
            updated_result = await db.execute(select(Candidate).where(Candidate.id == candidate_id))
            updated_candidate = updated_result.scalar_one()
            
            return {
                'success': True,
                'candidate_id': candidate_id,
                'candidate_name': updated_candidate.name,
                'updated_fields': list(update_data.keys()),
                'cost_breakdown': {
                    'rate': updated_candidate.rate,
                    'margin': updated_candidate.margin,
                    'infrastructure_cost': updated_candidate.infrastructure_cost,
                    'processing_cost': updated_candidate.processing_cost,
                    'final_client_rate': updated_candidate.final_client_rate
                },
                'validation_warnings': validation.get('warnings', [])
            }
            
        except Exception as e:
            await db.rollback()
            logger.error(f"Error updating candidate costs {candidate_id}: {str(e)}")
            return {
                'success': False,
                'error': f'Database error: {str(e)}'
            }
    
    @staticmethod
    async def bulk_update_costs(candidate_ids: List[int], db: AsyncSession,
                              rate: Optional[float] = None,
                              margin: Optional[float] = None,
                              infrastructure_cost: Optional[float] = None,
                              processing_cost: Optional[float] = None) -> Dict:
        """
        Bulk update cost fields for multiple candidates.
        
        Args:
            candidate_ids: List of candidate IDs to update
            db: Database session
            rate: New rate to apply to all candidates
            margin: New margin to apply to all candidates
            infrastructure_cost: New infrastructure cost to apply to all candidates
            processing_cost: New processing cost to apply to all candidates
            
        Returns:
            Dict with bulk update results
        """
        try:
            # Validate input
            if not candidate_ids:
                return {'success': False, 'error': 'No candidate IDs provided'}
            
            # Validate cost components
            validation = CostCalculationService.validate_cost_components(
                rate=rate, margin=margin, 
                infrastructure_cost=infrastructure_cost, 
                processing_cost=processing_cost
            )
            
            if not validation['valid']:
                return {
                    'success': False,
                    'error': 'Validation failed',
                    'validation_errors': validation['errors']
                }
            
            # Prepare update data
            update_data = {}
            if rate is not None:
                update_data['rate'] = rate
            if margin is not None:
                update_data['margin'] = margin
            if infrastructure_cost is not None:
                update_data['infrastructure_cost'] = infrastructure_cost
            if processing_cost is not None:
                update_data['processing_cost'] = processing_cost
            
            if not update_data:
                return {'success': False, 'error': 'No cost data provided for update'}
            
            # First, get current data for candidates to calculate final rates
            candidates_result = await db.execute(
                select(Candidate).where(Candidate.id.in_(candidate_ids))
            )
            candidates = candidates_result.scalars().all()
            
            if len(candidates) != len(candidate_ids):
                found_ids = [c.id for c in candidates]
                missing_ids = [cid for cid in candidate_ids if cid not in found_ids]
                return {
                    'success': False,
                    'error': f'Some candidates not found: {missing_ids}'
                }
            
            # Calculate final rates for each candidate
            updated_count = 0
            results = []
            
            for candidate in candidates:
                # Use new values or existing ones
                final_rate = rate if rate is not None else candidate.rate
                final_margin = margin if margin is not None else candidate.margin
                final_infrastructure = infrastructure_cost if infrastructure_cost is not None else candidate.infrastructure_cost
                final_processing = processing_cost if processing_cost is not None else candidate.processing_cost
                
                calculated_final_rate = CostCalculationService.calculate_final_rate(
                    final_rate, final_margin, final_infrastructure, final_processing
                )
                
                # Update this specific candidate
                individual_update = update_data.copy()
                individual_update['final_client_rate'] = calculated_final_rate
                
                await db.execute(
                    update(Candidate)
                    .where(Candidate.id == candidate.id)
                    .values(**individual_update)
                )
                
                updated_count += 1
                results.append({
                    'candidate_id': candidate.id,
                    'candidate_name': candidate.name,
                    'final_client_rate': calculated_final_rate
                })
            
            await db.commit()
            
            return {
                'success': True,
                'updated_count': updated_count,
                'total_requested': len(candidate_ids),
                'updated_fields': list(update_data.keys()),
                'results': results,
                'validation_warnings': validation.get('warnings', [])
            }
            
        except Exception as e:
            await db.rollback()
            logger.error(f"Error in bulk cost update: {str(e)}")
            return {
                'success': False,
                'error': f'Database error: {str(e)}'
            }
    
    @staticmethod
    async def get_cost_summary_for_job(job_id: int, db: AsyncSession) -> Dict:
        """
        Get cost summary for all shortlisted candidates in a job.
        
        Args:
            job_id: Job ID to get cost summary for
            db: Database session
            
        Returns:
            Dict with cost summary data
        """
        try:
            # Get all shortlisted candidates for the job
            result = await db.execute(
                select(Candidate).where(
                    Candidate.job_id == job_id,
                    Candidate.status == "Shortlisted"
                )
            )
            candidates = result.scalars().all()
            
            if not candidates:
                return {
                    'success': True,
                    'job_id': job_id,
                    'total_shortlisted': 0,
                    'message': 'No shortlisted candidates found'
                }
            
            # Calculate summary statistics
            candidates_with_rates = [c for c in candidates if c.final_client_rate is not None]
            
            if not candidates_with_rates:
                return {
                    'success': True,
                    'job_id': job_id,
                    'total_shortlisted': len(candidates),
                    'candidates_with_cost_data': 0,
                    'message': 'No candidates have cost data configured'
                }
            
            # Cost calculations
            total_cost = sum(c.final_client_rate for c in candidates_with_rates)
            avg_cost = total_cost / len(candidates_with_rates)
            min_cost = min(c.final_client_rate for c in candidates_with_rates)
            max_cost = max(c.final_client_rate for c in candidates_with_rates)
            
            # Component breakdown
            total_base_rates = sum(c.rate or 0 for c in candidates_with_rates)
            total_margins = sum(c.margin or 0 for c in candidates_with_rates)
            total_infrastructure = sum(c.infrastructure_cost or 0 for c in candidates_with_rates)
            total_processing = sum(c.processing_cost or 0 for c in candidates_with_rates)
            
            return {
                'success': True,
                'job_id': job_id,
                'total_shortlisted': len(candidates),
                'candidates_with_cost_data': len(candidates_with_rates),
                'cost_summary': {
                    'total_cost': round(total_cost, 2),
                    'average_cost': round(avg_cost, 2),
                    'min_cost': round(min_cost, 2),
                    'max_cost': round(max_cost, 2)
                },
                'component_breakdown': {
                    'total_base_rates': round(total_base_rates, 2),
                    'total_margins': round(total_margins, 2),
                    'total_infrastructure': round(total_infrastructure, 2),
                    'total_processing': round(total_processing, 2)
                },
                'candidates': [
                    {
                        'id': c.id,
                        'name': c.name,
                        'rate': c.rate,
                        'margin': c.margin,
                        'infrastructure_cost': c.infrastructure_cost,
                        'processing_cost': c.processing_cost,
                        'final_client_rate': c.final_client_rate
                    }
                    for c in candidates_with_rates
                ]
            }
            
        except Exception as e:
            logger.error(f"Error getting cost summary for job {job_id}: {str(e)}")
            return {
                'success': False,
                'error': f'Error retrieving cost summary: {str(e)}'
            }
    
    @staticmethod
    async def recalculate_all_final_rates(db: AsyncSession) -> Dict:
        """
        Recalculate final rates for all candidates with cost data.
        Useful for fixing any calculation inconsistencies.
        
        Args:
            db: Database session
            
        Returns:
            Dict with recalculation results
        """
        try:
            # Get all candidates with rate data
            result = await db.execute(
                select(Candidate).where(Candidate.rate.isnot(None))
            )
            candidates = result.scalars().all()
            
            if not candidates:
                return {
                    'success': True,
                    'message': 'No candidates with rate data found',
                    'recalculated_count': 0
                }
            
            recalculated_count = 0
            
            for candidate in candidates:
                # Recalculate final rate
                calculated_rate = CostCalculationService.calculate_final_rate(
                    candidate.rate or 0.0,
                    candidate.margin or 0.0,
                    candidate.infrastructure_cost or 0.0,
                    candidate.processing_cost or 0.0
                )
                
                # Update if different
                if candidate.final_client_rate != calculated_rate:
                    await db.execute(
                        update(Candidate)
                        .where(Candidate.id == candidate.id)
                        .values(final_client_rate=calculated_rate)
                    )
                    recalculated_count += 1
            
            await db.commit()
            
            return {
                'success': True,
                'total_candidates_checked': len(candidates),
                'recalculated_count': recalculated_count,
                'message': f'Recalculated {recalculated_count} candidate final rates'
            }
            
        except Exception as e:
            await db.rollback()
            logger.error(f"Error recalculating final rates: {str(e)}")
            return {
                'success': False,
                'error': f'Error recalculating rates: {str(e)}'
            }