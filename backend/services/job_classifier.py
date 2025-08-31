cat > backend/services/job_classifier.py << 'EOF'
from typing import Dict, Any

class JobClassifier:
    def __init__(self):
        self.domain_keywords = {
            'DevOps': ['devops', 'infrastructure', 'deployment', 'docker', 'kubernetes'],
            'Backend': ['backend', 'api', 'server', 'database', 'python', 'java'],
            'Frontend': ['frontend', 'react', 'vue', 'angular', 'javascript']
        }
    
    def classify_job(self, job_data: Dict[str, Any]) -> str:
        text = f"{job_data.get('title', '')} {job_data.get('description', '')}".lower()
        
        for domain, keywords in self.domain_keywords.items():
            if any(keyword in text for keyword in keywords):
                return domain
        
        return 'Other'
EOF