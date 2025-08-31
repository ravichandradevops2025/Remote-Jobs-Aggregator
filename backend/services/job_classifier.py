from typing import Dict, Any
import re
from ..models import JobDomain

class JobClassifier:
    def __init__(self):
        self.domain_keywords = {
            JobDomain.DEVOPS: [
                'devops', 'infrastructure', 'deployment', 'ci/cd', 'docker', 'kubernetes',
                'ansible', 'terraform', 'jenkins', 'pipeline', 'automation', 'sre',
                'site reliability', 'monitoring', 'observability'
            ],
            JobDomain.CLOUD_AWS: [
                'aws', 'azure', 'gcp', 'google cloud', 'cloud', 'serverless', 'lambda',
                'ec2', 's3', 'cloudformation', 'cloud architect', 'cloud engineer'
            ],
            JobDomain.JAVA: [
                'java', 'spring', 'hibernate', 'maven', 'gradle', 'jvm', 'scala',
                'kotlin', 'spring boot', 'microservices java'
            ],
            JobDomain.BACKEND: [
                'backend', 'api', 'server', 'database', 'sql', 'microservices',
                'rest', 'graphql', 'node.js', 'python', 'go', 'rust', 'c#', '.net',
                'ruby', 'php', 'backend developer', 'server-side'
            ],
            JobDomain.FRONTEND: [
                'frontend', 'react', 'vue', 'angular', 'javascript', 'typescript',
                'html', 'css', 'ui', 'user interface', 'web developer', 'frontend developer',
                'next.js', 'nuxt', 'svelte', 'ember'
            ],
            JobDomain.DATA_ML: [
                'data scientist', 'machine learning', 'ml', 'ai', 'artificial intelligence',
                'data engineer', 'data analyst', 'python data', 'tensorflow', 'pytorch',
                'pandas', 'numpy', 'sql data', 'etl', 'data pipeline', 'analytics',
                'big data', 'spark', 'hadoop'
            ],
            JobDomain.QA: [
                'qa', 'quality assurance', 'test', 'testing', 'automation testing',
                'selenium', 'cypress', 'jest', 'qa engineer', 'test engineer',
                'quality engineer', 'sdet', 'test automation'
            ],
            JobDomain.PM: [
                'product manager', 'project manager', 'program manager', 'scrum master',
                'product owner', 'agile', 'pm', 'product management', 'project management'
            ]
        }
    
    def classify_job(self, job_data: Dict[str, Any]) -> str:
        """Classify a job based on title and description"""
        text_to_analyze = ' '.join([
            job_data.get('title', ''),
            job_data.get('description', '')
        ]).lower()
        
        # Score each domain
        domain_scores = {}
        for domain, keywords in self.domain_keywords.items():
            score = 0
            for keyword in keywords:
                # Count occurrences, give more weight to title matches
                title_matches = len(re.findall(keyword.lower(), job_data.get('title', '').lower()))
                desc_matches = len(re.findall(keyword.lower(), job_data.get('description', '').lower()))
                
                score += title_matches * 3 + desc_matches
            
            if score > 0:
                domain_scores[domain] = score
        
        # Return domain with highest score, or 'Other' if no matches
        if domain_scores:
            best_domain = max(domain_scores.items(), key=lambda x: x[1])
            return best_domain[0].value
        
        return JobDomain.OTHER.value