from datetime import datetime, timedelta
from typing import Dict, Any, List
import re
import logging

logger = logging.getLogger(__name__)

class JobDateFilter:
    def __init__(self, days_back: int = 15):
        self.cutoff_date = datetime.now() - timedelta(days=days_back)
        logger.info(f"Filtering jobs posted after: {self.cutoff_date.strftime('%Y-%m-%d')}")
    
    def is_job_recent(self, job_data: Dict[str, Any]) -> bool:
        """Check if job was posted within the last N days"""
        
        # Try to extract date from various fields
        date_fields = ['posted_date', 'created_at', 'published', 'date_posted', 'updated_at']
        
        for field in date_fields:
            if field in job_data:
                job_date = self._parse_date(job_data[field])
                if job_date:
                    return job_date >= self.cutoff_date
        
        # Try to extract from description or title
        description = str(job_data.get('description', ''))
        title = str(job_data.get('title', ''))
        text = f"{title} {description}"
        
        # Look for date patterns
        date_from_text = self._extract_date_from_text(text)
        if date_from_text:
            return date_from_text >= self.cutoff_date
        
        # If no date found, assume recent (better to include than exclude)
        logger.debug(f"No date found for job: {job_data.get('title', 'Unknown')}")
        return True
    
    def _parse_date(self, date_str) -> datetime:
        """Parse date from various formats"""
        if isinstance(date_str, datetime):
            return date_str
        
        if not isinstance(date_str, str):
            return None
            
        # Common date formats
        date_formats = [
            '%Y-%m-%d',
            '%Y-%m-%dT%H:%M:%S',
            '%Y-%m-%dT%H:%M:%SZ',
            '%Y-%m-%d %H:%M:%S',
            '%d/%m/%Y',
            '%m/%d/%Y',
            '%d-%m-%Y',
            '%Y/%m/%d'
        ]
        
        for fmt in date_formats:
            try:
                return datetime.strptime(date_str[:len(fmt)], fmt)
            except ValueError:
                continue
        
        return None
    
    def _extract_date_from_text(self, text: str) -> datetime:
        """Extract recent date indicators from text"""
        text_lower = text.lower()
        now = datetime.now()
        
        # Recent indicators
        if any(indicator in text_lower for indicator in 
               ['posted today', 'posted yesterday', 'just posted', 'new posting']):
            return now
        
        # Days ago pattern
        days_match = re.search(r'(\d+)\s*days?\s*ago', text_lower)
        if days_match:
            days_ago = int(days_match.group(1))
            return now - timedelta(days=days_ago)
        
        # Weeks ago pattern
        weeks_match = re.search(r'(\d+)\s*weeks?\s*ago', text_lower)
        if weeks_match:
            weeks_ago = int(weeks_match.group(1))
            return now - timedelta(weeks=weeks_ago)
        
        return None
    
    def filter_recent_jobs(self, jobs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Filter list of jobs to only recent ones"""
        recent_jobs = []
        total_jobs = len(jobs)
        
        for job in jobs:
            if self.is_job_recent(job):
                recent_jobs.append(job)
        
        filtered_count = total_jobs - len(recent_jobs)
        if filtered_count > 0:
            logger.info(f"Filtered out {filtered_count} old jobs, kept {len(recent_jobs)} recent jobs")
        
        return recent_jobs