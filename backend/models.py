from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
from enum import Enum

class JobDomain(str, Enum):
    DEVOPS = "DevOps"
    CLOUD_AWS = "Cloud/AWS"
    JAVA = "Java"
    BACKEND = "Backend"
    FRONTEND = "Frontend"
    DATA_ML = "Data/ML"
    QA = "QA"
    PM = "PM"
    OTHER = "Other"

class JobBase(BaseModel):
    title: str
    company: str
    description: str
    apply_url: str
    location: Optional[str] = None
    remote: bool = False
    salary_min: Optional[int] = None
    salary_max: Optional[int] = None
    domain: JobDomain = JobDomain.OTHER
    source: str
    source_job_id: Optional[str] = None

class JobCreate(JobBase):
    pass

class Job(JobBase):
    id: str
    created_at: datetime
    updated_at: datetime

class JobResponse(JobBase):
    id: str
    created_at: datetime

class JobsListResponse(BaseModel):
    jobs: List[JobResponse]
    total: int
    page: int
    pages: int