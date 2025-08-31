from typing import List, Dict, Any
import logging

logger = logging.getLogger(__name__)

class JobDeduplicator:
    def deduplicate_jobs(self, jobs: List[Dict[str, Any]], existing_urls: set = None) -> List[Dict[str, Any]]:
        if existing_urls is None:
            existing_urls = set()
        
        seen_urls = existing_urls.copy()
        unique_jobs = []
        
        for job in jobs:
            apply_url = job.get('apply_url', '').strip()
            if not apply_url or apply_url in seen_urls:
                continue
            
            seen_urls.add(apply_url)
            unique_jobs.append(job)
        
        logger.info(f"Deduplicated {len(jobs)} -> {len(unique_jobs)} jobs")
        return unique_jobs
EOF