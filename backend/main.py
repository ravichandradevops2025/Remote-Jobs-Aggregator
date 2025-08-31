from fastapi import FastAPI, HTTPException, Depends, Query
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Optional
import os
from datetime import datetime

from .models import Job, JobCreate, JobResponse, JobsListResponse
from .database import get_database, create_tables
from .scrapers.greenhouse import GreenHouseScraper
from .scrapers.lever import LeverScraper
from .scrapers.generic import GenericScraper
from .services.job_classifier import JobClassifier
from .services.deduplicator import JobDeduplicator

app = FastAPI(title="Remote Jobs API", version="1.0.0")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

security = HTTPBearer()
classifier = JobClassifier()
deduplicator = JobDeduplicator()

def verify_admin_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    if credentials.credentials != os.getenv("ADMIN_TOKEN"):
        raise HTTPException(status_code=401, detail="Invalid admin token")
    return credentials.credentials

@app.on_event("startup")
async def startup_event():
    await create_tables()

@app.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.utcnow().isoformat()}

@app.get("/jobs", response_model=JobsListResponse)
async def get_jobs(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    domain: Optional[str] = Query(None),
    remote: Optional[bool] = Query(None),
    search: Optional[str] = Query(None)
):
    db = await get_database()
    
    # Build query
    query = "SELECT * FROM jobs WHERE 1=1"
    params = []
    
    if domain:
        query += " AND domain = $" + str(len(params) + 1)
        params.append(domain)
    
    if remote is not None:
        query += " AND remote = $" + str(len(params) + 1)
        params.append(remote)
    
    if search:
        query += " AND (title ILIKE $" + str(len(params) + 1) + " OR company ILIKE $" + str(len(params) + 2) + ")"
        params.extend([f"%{search}%", f"%{search}%"])
    
    # Count total
    count_query = query.replace("SELECT *", "SELECT COUNT(*)")
    total_result = await db.fetch_one(count_query, params)
    total = total_result[0] if total_result else 0
    
    # Add pagination
    offset = (page - 1) * limit
    query += f" ORDER BY created_at DESC LIMIT ${len(params) + 1} OFFSET ${len(params) + 2}"
    params.extend([limit, offset])
    
    jobs = await db.fetch_all(query, params)
    
    return JobsListResponse(
        jobs=[JobResponse(**dict(job)) for job in jobs],
        total=total,
        page=page,
        pages=(total + limit - 1) // limit if total > 0 else 0
    )

@app.get("/jobs/{job_id}", response_model=JobResponse)
async def get_job(job_id: str):
    db = await get_database()
    job = await db.fetch_one("SELECT * FROM jobs WHERE id = $1", [job_id])
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return JobResponse(**dict(job))

@app.post("/admin/fetch")
async def trigger_manual_fetch(token: str = Depends(verify_admin_token)):
    """Manually trigger job fetching from all sources"""
    try:
        from scripts.run_scraper import main as run_scraper
        result = await run_scraper()
        return {"status": "success", "message": "Job fetch completed", "result": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Scraping failed: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)