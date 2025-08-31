from typing import List, Dict, Any
import logging

logger = logging.getLogger(__name__)

class JobDeduplicator:
    def __init__(self):
        pass
    
    def deduplicate_jobs(self, jobs: List[Dict[str, Any]], existing_urls: set = None) -> List[Dict[str, Any]]:
        """Remove duplicate jobs based on apply_url and similar titles"""
        if existing_urls is None:
            existing_urls = set()
        
        seen_urls = existing_urls.copy()
        unique_jobs = []
        duplicates_removed = 0
        
        for job in jobs:
            apply_url = job.get('apply_url', '').strip()
            
            if not apply_url:
                logger.warning("Job missing apply_url, skipping")
                continue
            
            # Check for exact URL match
            if apply_url in seen_urls:
                duplicates_removed += 1
                continue
            
            # Check for similar jobs (same company + similar title)
            is_duplicate = self._is_similar_job(job, unique_jobs)
            if is_duplicate:
                duplicates_removed += 1
                continue
            
            seen_urls.add(apply_url)
            unique_jobs.append(job)
        
        if duplicates_removed > 0:
            logger.info(f"Removed {duplicates_removed} duplicate jobs")
        
        return unique_jobs
    
    def _is_similar_job(self, job: Dict[str, Any], existing_jobs: List[Dict[str, Any]]) -> bool:
        """Check if job is similar to existing jobs (same company + similar title)"""
        job_title = job.get('title', '').lower().strip()
        job_company = job.get('company', '').lower().strip()
        
        if not job_title or not job_company:
            return False
        
        for existing_job in existing_jobs:
            existing_title = existing_job.get('title', '').lower().strip()
            existing_company = existing_job.get('company', '').lower().strip()
            
            # Same company and very similar title
            if (job_company == existing_company and 
                self._similarity_score(job_title, existing_title) > 0.8):
                return True
        
        return False
    
    def _similarity_score(self, str1: str, str2: str) -> float:
        """Calculate similarity score between two strings"""
        if not str1 or not str2:
            return 0.0
        
        # Simple Jaccard similarity using words
        words1 = set(str1.split())
        words2 = set(str2.split())
        
        if not words1 or not words2:
            return 0.0
        
        intersection = words1.intersection(words2)
        union = words1.union(words2)
        
        return len(intersection) / len(union)