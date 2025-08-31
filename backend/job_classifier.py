from typing import Dict, Any
import re

class JobClassifier:
    def __init__(self):
        self.domain_keywords = {
            # DevOps & Cloud (High demand domains you mentioned)
            'DevOps': [
                'devops', 'dev ops', 'infrastructure', 'deployment', 'ci/cd', 'docker', 'kubernetes', 'k8s',
                'ansible', 'terraform', 'jenkins', 'pipeline', 'automation', 'sre', 'site reliability',
                'monitoring', 'observability', 'prometheus', 'grafana', 'helm', 'microservices infrastructure'
            ],
            'Cloud/AWS': [
                'aws', 'amazon web services', 'ec2', 's3', 'lambda', 'cloudformation', 'cloud architect',
                'cloud engineer', 'aws devops', 'aws developer', 'serverless', 'cloudwatch'
            ],
            'Azure': [
                'azure', 'microsoft azure', 'azure devops', 'azure architect', 'azure developer',
                'azure cloud', 'office 365', 'power platform', 'azure functions'
            ],
            'GCP': [
                'gcp', 'google cloud', 'google cloud platform', 'gke', 'cloud run', 'bigquery',
                'gcp engineer', 'gcp architect', 'firebase'
            ],
            
            # Programming Languages & Frameworks
            'Java': [
                'java', 'spring', 'spring boot', 'hibernate', 'maven', 'gradle', 'jvm', 'scala',
                'kotlin', 'microservices java', 'java developer', 'java engineer'
            ],
            'Python': [
                'python', 'django', 'flask', 'fastapi', 'pandas', 'numpy', 'python developer',
                'python engineer', 'python backend', 'pytest'
            ],
            'React': [
                'react', 'reactjs', 'react.js', 'next.js', 'nextjs', 'redux', 'react native',
                'react developer', 'react engineer', 'frontend react'
            ],
            'Full Stack': [
                'full stack', 'fullstack', 'full-stack', 'mern', 'mean', 'lamp', 'javascript developer',
                'web developer', 'frontend backend', 'end to end developer'
            ],
            
            # Mobile Development
            'Android': [
                'android', 'android developer', 'kotlin android', 'java android', 'android engineer',
                'mobile android', 'android app', 'flutter', 'react native'
            ],
            'iOS': [
                'ios', 'ios developer', 'swift', 'objective-c', 'iphone', 'ipad', 'ios engineer',
                'mobile ios', 'ios app development'
            ],
            
            # Backend & API
            'Backend': [
                'backend', 'back-end', 'api', 'server', 'database', 'sql', 'microservices',
                'rest', 'graphql', 'node.js', 'nodejs', 'go', 'rust', 'c#', '.net',
                'ruby', 'php', 'backend developer', 'server-side', 'backend engineer'
            ],
            
            # Frontend
            'Frontend': [
                'frontend', 'front-end', 'vue', 'vuejs', 'angular', 'angularjs', 'javascript', 'typescript',
                'html', 'css', 'scss', 'sass', 'ui', 'user interface', 'web developer', 'frontend developer',
                'svelte', 'ember', 'webpack', 'vite'
            ],
            
            # Data & Analytics (High demand)
            'Data/ML': [
                'data scientist', 'data science', 'machine learning', 'ml', 'ai', 'artificial intelligence',
                'data engineer', 'data analyst', 'python data', 'tensorflow', 'pytorch',
                'pandas', 'numpy', 'sql data', 'etl', 'data pipeline', 'analytics',
                'big data', 'spark', 'hadoop', 'kafka', 'airflow', 'snowflake'
            ],
            'PowerBI': [
                'power bi', 'powerbi', 'power platform', 'dax', 'power query', 'microsoft bi',
                'business intelligence', 'data visualization', 'reporting analyst'
            ],
            'Tableau': [
                'tableau', 'tableau developer', 'data visualization', 'dashboard', 'analytics',
                'business intelligence', 'tableau analyst'
            ],
            
            # Testing & Quality
            'QA': [
                'qa', 'quality assurance', 'test', 'testing', 'automation testing',
                'selenium', 'cypress', 'jest', 'qa engineer', 'test engineer',
                'quality engineer', 'sdet', 'test automation', 'manual testing'
            ],
            
            # Management & Leadership
            'PM': [
                'product manager', 'project manager', 'program manager', 'scrum master',
                'product owner', 'agile', 'pm', 'product management', 'project management',
                'technical program manager', 'engineering manager'
            ],
            
            # Enterprise & ERP
            'SAP': [
                'sap', 'sap consultant', 'sap developer', 'sap analyst', 'sap implementation',
                'sap fico', 'sap mm', 'sap sd', 'sap hana', 'sap s/4hana'
            ],
            
            # Security
            'Security': [
                'security', 'cybersecurity', 'information security', 'security engineer',
                'security analyst', 'penetration testing', 'security architect', 'devsecops'
            ]
        }
    
    def classify_job(self, job_data: Dict[str, Any]) -> str:
        """Classify a job based on title and description with enhanced domains"""
        
        # Get searchable text safely
        title = str(job_data.get('title', '')).lower()
        description = str(job_data.get('description', '')).lower()
        text_to_analyze = f"{title} {description}"
        
        # Score each domain
        domain_scores = {}
        for domain, keywords in self.domain_keywords.items():
            score = 0
            for keyword in keywords:
                # Count occurrences, give more weight to title matches
                title_matches = len(re.findall(re.escape(keyword.lower()), title))
                desc_matches = len(re.findall(re.escape(keyword.lower()), description))
                
                # Title matches are worth 5x more than description matches
                score += title_matches * 5 + desc_matches
            
            if score > 0:
                domain_scores[domain] = score
        
        # Return domain with highest score, or 'Other' if no matches
        if domain_scores:
            best_domain = max(domain_scores.items(), key=lambda x: x[1])
            return best_domain[0]
        
        return 'Other'
    
    def get_all_domains(self) -> list:
        """Get list of all available domains"""
        return list(self.domain_keywords.keys()) + ['Other']