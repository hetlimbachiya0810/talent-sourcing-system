import re
from fuzzywuzzy import fuzz, process
from typing import Dict, List, Tuple, Optional
import logging

logger = logging.getLogger(__name__)

class MatchingEngine:
    """
    CV-JD matching engine that compares candidate CVs with job descriptions
    and calculates match scores based on various criteria.
    """
    
    # Field weights for calculating overall match score
    FIELD_WEIGHTS = {
        'hard_skills': 0.40,
        'soft_skills': 0.20,
        'certifications': 0.20,
        'time_zone': 0.10,
        'contract_duration': 0.10
    }
    
    # Common skill keywords for better matching
    HARD_SKILLS_KEYWORDS = [
        'python', 'java', 'javascript', 'react', 'angular', 'vue', 'node.js', 'nodejs',
        'express', 'django', 'flask', 'fastapi', 'spring', 'hibernate',
        'sql', 'mysql', 'postgresql', 'mongodb', 'redis', 'elasticsearch',
        'aws', 'azure', 'gcp', 'docker', 'kubernetes', 'jenkins', 'git',
        'html', 'css', 'bootstrap', 'tailwind', 'sass', 'less',
        'machine learning', 'ai', 'data science', 'pandas', 'numpy', 'tensorflow',
        'pytorch', 'scikit-learn', 'opencv', 'nlp', 'deep learning',
        'microservices', 'rest api', 'graphql', 'websockets', 'grpc'
    ]
    
    SOFT_SKILLS_KEYWORDS = [
        'communication', 'leadership', 'teamwork', 'problem solving', 'analytical',
        'creative', 'adaptable', 'time management', 'project management',
        'collaboration', 'mentoring', 'presentation', 'negotiation',
        'critical thinking', 'decision making', 'conflict resolution'
    ]
    
    CERTIFICATION_KEYWORDS = [
        'aws certified', 'azure certified', 'google cloud', 'gcp certified',
        'pmp', 'scrum master', 'agile', 'cissp', 'ceh', 'comptia',
        'oracle certified', 'microsoft certified', 'cisco', 'ccna', 'ccnp',
        'itil', 'prince2', 'six sigma', 'lean'
    ]
    
    TIME_ZONE_KEYWORDS = [
        'ist', 'pst', 'est', 'cst', 'mst', 'utc', 'gmt', 'cet', 'jst',
        'india standard time', 'pacific standard time', 'eastern standard time',
        'central standard time', 'mountain standard time', 'coordinated universal time'
    ]
    
    CONTRACT_DURATION_KEYWORDS = [
        'permanent', 'contract', 'temporary', 'full-time', 'part-time',
        'freelance', 'consultant', '3 months', '6 months', '12 months',
        '1 year', '2 years', 'long term', 'short term'
    ]
    
    @staticmethod
    def extract_keywords_from_text(text: str, keyword_list: List[str]) -> List[str]:
        """
        Extract relevant keywords from text based on a predefined keyword list.
        
        Args:
            text (str): Text to search for keywords
            keyword_list (List[str]): List of keywords to search for
            
        Returns:
            List[str]: Found keywords
        """
        if not text:
            return []
        
        text_lower = text.lower()
        found_keywords = []
        
        for keyword in keyword_list:
            pattern = r'\b' + re.escape(keyword.lower()) + r'\b'

            if re.search(pattern, text_lower):
                found_keywords.append(keyword)
        
        return found_keywords
    
    @staticmethod
    def calculate_field_score(cv_keywords: List[str], jd_keywords: List[str], 
                            cv_text: str, jd_text: str) -> Tuple[float, List[str]]:
        """
        Calculate similarity score for a specific field and identify mismatches.
        
        Args:
            cv_keywords (List[str]): Keywords found in CV
            jd_keywords (List[str]): Keywords found in JD
            cv_text (str): Raw CV text for fuzzy matching
            jd_text (str): Raw JD text for fuzzy matching
            
        Returns:
            Tuple[float, List[str]]: Score (0-100) and list of missing keywords
        """
        if not jd_keywords:
            return 100.0, []  # No requirements, perfect match
        
        if not cv_keywords and not cv_text:
            return 0.0, jd_keywords  # No CV data, complete mismatch
        
        matched_keywords = []
        missing_keywords = []
        
        for jd_keyword in jd_keywords:
            # Check exact match first
            if jd_keyword.lower() in [cv_kw.lower() for cv_kw in cv_keywords]:
                matched_keywords.append(jd_keyword)
            else:
                # Try fuzzy matching against CV text
                fuzzy_score = fuzz.partial_ratio(jd_keyword.lower(), cv_text.lower())
                if fuzzy_score >= 80:  # 80% similarity threshold
                    matched_keywords.append(jd_keyword)
                else:
                    missing_keywords.append(jd_keyword)
        
        # Calculate score based on matched vs required keywords
        if jd_keywords:
            score = (len(matched_keywords) / len(jd_keywords)) * 100
        else:
            score = 100.0
        
        return score, missing_keywords
    
    @staticmethod
    def extract_experience_years(text: str) -> Optional[int]:
        """
        Extract years of experience from text using regex patterns.
        
        Args:
            text (str): Text to search for experience
            
        Returns:
            Optional[int]: Years of experience if found
        """
        if not text:
            return None
        
        # Common patterns for experience
        patterns = [
            r'(\d+)\+?\s*years?\s*of\s*experience',
            r'(\d+)\+?\s*years?\s*experience',
            r'experience\s*of\s*(\d+)\+?\s*years?',
            r'(\d+)\+?\s*yrs?\s*exp',
            r'exp\s*(\d+)\+?\s*years?',
        ]
        
        text_lower = text.lower()
        for pattern in patterns:
            matches = re.findall(pattern, text_lower)
            if matches:
                try:
                    return int(matches[0])
                except ValueError:
                    continue
        
        return None
    
    @staticmethod
    def match_candidate_to_job(candidate, job, cv_text: str, jd_text: str) -> Dict:
        """
        Calculate comprehensive match score between candidate and job.
        
        Args:
            candidate: Candidate model instance
            job: Job model instance
            cv_text (str): Extracted CV text
            jd_text (str): Extracted JD text
            
        Returns:
            Dict: Match results with score, status, and mismatch summary
        """
        scores = {}
        all_mismatches = {}
        
        # 1. Hard Skills Matching (40% weight)
        cv_hard_skills = MatchingEngine.extract_keywords_from_text(
            f"{candidate.hard_skills or ''} {cv_text}", 
            MatchingEngine.HARD_SKILLS_KEYWORDS
        )
        jd_hard_skills = MatchingEngine.extract_keywords_from_text(
            jd_text, MatchingEngine.HARD_SKILLS_KEYWORDS
        )
        
        scores['hard_skills'], all_mismatches['hard_skills'] = MatchingEngine.calculate_field_score(
            cv_hard_skills, jd_hard_skills, cv_text, jd_text
        )
        
        # 2. Soft Skills Matching (20% weight)
        cv_soft_skills = MatchingEngine.extract_keywords_from_text(
            f"{candidate.soft_skills or ''} {cv_text}", 
            MatchingEngine.SOFT_SKILLS_KEYWORDS
        )
        jd_soft_skills = MatchingEngine.extract_keywords_from_text(
            jd_text, MatchingEngine.SOFT_SKILLS_KEYWORDS
        )
        
        scores['soft_skills'], all_mismatches['soft_skills'] = MatchingEngine.calculate_field_score(
            cv_soft_skills, jd_soft_skills, cv_text, jd_text
        )
        
        # 3. Certifications Matching (20% weight)
        cv_certifications = MatchingEngine.extract_keywords_from_text(
            f"{candidate.certifications or ''} {cv_text}", 
            MatchingEngine.CERTIFICATION_KEYWORDS
        )
        jd_certifications = MatchingEngine.extract_keywords_from_text(
            jd_text, MatchingEngine.CERTIFICATION_KEYWORDS
        )
        
        scores['certifications'], all_mismatches['certifications'] = MatchingEngine.calculate_field_score(
            cv_certifications, jd_certifications, cv_text, jd_text
        )
        
        # 4. Time Zone Matching (10% weight)
        cv_timezone = MatchingEngine.extract_keywords_from_text(
            f"{candidate.time_zone_alignment or ''} {cv_text}", 
            MatchingEngine.TIME_ZONE_KEYWORDS
        )
        jd_timezone = MatchingEngine.extract_keywords_from_text(
            f"{job.time_zone or ''} {jd_text}", 
            MatchingEngine.TIME_ZONE_KEYWORDS
        )
        
        scores['time_zone'], all_mismatches['time_zone'] = MatchingEngine.calculate_field_score(
            cv_timezone, jd_timezone, cv_text, jd_text
        )
        
        # 5. Contract Duration Matching (10% weight)
        cv_contract = MatchingEngine.extract_keywords_from_text(
            f"{candidate.contract_duration_willingness or ''} {cv_text}", 
            MatchingEngine.CONTRACT_DURATION_KEYWORDS
        )
        jd_contract = MatchingEngine.extract_keywords_from_text(
            f"{job.contract_duration or ''} {jd_text}", 
            MatchingEngine.CONTRACT_DURATION_KEYWORDS
        )
        
        scores['contract_duration'], all_mismatches['contract_duration'] = MatchingEngine.calculate_field_score(
            cv_contract, jd_contract, cv_text, jd_text
        )
        
        # Calculate weighted overall score
        overall_score = 0.0
        for field, weight in MatchingEngine.FIELD_WEIGHTS.items():
            overall_score += scores[field] * weight
        
        # Determine status
        status = "Shortlisted" if overall_score >= 80.0 else "Rejected"
        
        # Generate mismatch summary for rejected candidates
        mismatch_summary = ""
        if overall_score < 80.0:
            mismatch_parts = []
            for field, missing_items in all_mismatches.items():
                if missing_items and scores[field] < 70:  # Only include significantly weak areas
                    field_name = field.replace('_', ' ').title()
                    mismatch_parts.append(f"{field_name}: Missing {', '.join(missing_items)}")
            
            if mismatch_parts:
                mismatch_summary = "; ".join(mismatch_parts)
            else:
                mismatch_summary = "Overall score below threshold despite partial matches"
        
        return {
            'match_score': round(overall_score, 2),
            'status': status,
            'mismatch_summary': mismatch_summary,
            'field_scores': scores,
            'mismatches': all_mismatches
        }