"""
FastAPI REST API for AI Recruitment System
"""
from fastapi import FastAPI, UploadFile, File, HTTPException, Depends, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr
from typing import List, Optional, Dict
from datetime import datetime
import uvicorn
from loguru import logger

from src.recruitment_system import RecruitmentSystem
from config.settings import settings


# Initialize FastAPI app
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="AI-powered recruitment and candidate screening system"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins.split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize recruitment system
recruitment_system = RecruitmentSystem()


# Pydantic models for API
class JobRequirements(BaseModel):
    """Job requirements schema"""
    id: Optional[int] = None
    title: str
    department: Optional[str] = None
    required_skills: List[str]
    preferred_skills: List[str] = []
    min_years_experience: float
    education_requirements: List[str] = []
    certifications_required: List[str] = []
    hiring_managers: List[EmailStr] = []


class CandidateAvailability(BaseModel):
    """Candidate availability schema"""
    slots: List[Dict[str, str]]  # List of {"start": "ISO datetime", "end": "ISO datetime"}


class ApplicationResponse(BaseModel):
    """Application processing response"""
    candidate_email: str
    job_id: Optional[int]
    job_title: str
    status: str
    stage: Optional[str]
    resume_score: Optional[float]
    interview_score: Optional[float]
    recommendation: Optional[str]
    timestamp: str


class MetricsResponse(BaseModel):
    """Recruitment metrics response"""
    time_to_hire_days: float
    time_reduction_percent: float
    quality_of_hire_score: float
    recruiter_hours_saved: float
    candidate_satisfaction: float
    false_negative_rate: float


# API Endpoints

@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "service": settings.app_name,
        "version": settings.app_version,
        "status": "operational"
    }


@app.post("/api/v1/candidates/screen", response_model=ApplicationResponse)
async def screen_candidate(
    background_tasks: BackgroundTasks,
    resume: UploadFile = File(...),
    candidate_email: EmailStr = None,
    job_id: int = None,
    job_requirements: str = None  # JSON string of JobRequirements
):
    """
    Screen a candidate's resume
    
    Args:
        resume: Resume file (PDF, DOCX, or TXT)
        candidate_email: Candidate's email address
        job_id: Job posting ID
        job_requirements: JSON string of job requirements
        
    Returns:
        Screening results
    """
    try:
        # Validate file type
        if not resume.filename.lower().endswith(('.pdf', '.doc', '.docx', '.txt')):
            raise HTTPException(
                status_code=400,
                detail="Invalid file type. Accepted: PDF, DOC, DOCX, TXT"
            )
        
        # Read resume file
        resume_bytes = await resume.read()
        
        # Parse job requirements
        import json
        job_req_dict = json.loads(job_requirements) if job_requirements else {}
        job_req_dict["id"] = job_id
        
        # Process application
        result = recruitment_system.process_application(
            resume_file=resume_bytes,
            resume_filename=resume.filename,
            candidate_email=candidate_email,
            job_requirements=job_req_dict
        )
        
        # Store result in database (background task)
        # background_tasks.add_task(store_application_result, result)
        
        return ApplicationResponse(**result)
        
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid job requirements JSON")
    except Exception as e:
        logger.error(f"Error screening candidate: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/candidates/{candidate_email}/evaluation")
async def get_evaluation(candidate_email: str, job_id: Optional[int] = None):
    """
    Retrieve candidate evaluation results
    
    Args:
        candidate_email: Candidate's email
        job_id: Optional job ID filter
        
    Returns:
        Evaluation details
    """
    try:
        # In production, query from database
        # For now, return mock response
        return {
            "candidate_email": candidate_email,
            "job_id": job_id,
            "evaluations": [
                {
                    "type": "resume_screening",
                    "score": 0.75,
                    "status": "passed",
                    "timestamp": datetime.utcnow().isoformat()
                }
            ]
        }
    except Exception as e:
        logger.error(f"Error retrieving evaluation: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v1/interviews/schedule")
async def schedule_interview(
    candidate_email: EmailStr,
    interviewer_emails: List[EmailStr],
    job_title: str,
    availability: CandidateAvailability
):
    """
    Schedule an interview
    
    Args:
        candidate_email: Candidate's email
        interviewer_emails: List of interviewer emails
        job_title: Job title
        availability: Candidate availability windows
        
    Returns:
        Scheduled meeting details
    """
    try:
        # Find optimal time slots
        slots = recruitment_system.scheduler.find_optimal_slots(
            candidate_availability=availability.slots,
            interviewer_ids=interviewer_emails,
            duration_minutes=settings.video_interview_duration_minutes
        )
        
        if not slots:
            raise HTTPException(
                status_code=404,
                detail="No available time slots found"
            )
        
        # Schedule interview using first available slot
        meeting = recruitment_system.scheduler.send_interview_invite(
            candidate_email=candidate_email,
            interviewer_emails=interviewer_emails,
            time_slot=slots[0],
            job_title=job_title
        )
        
        return {
            "status": "scheduled",
            "meeting": meeting,
            "alternative_slots": slots[1:3] if len(slots) > 1 else []
        }
        
    except Exception as e:
        logger.error(f"Error scheduling interview: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v1/batch/process")
async def batch_process(
    job_id: int,
    job_requirements: JobRequirements
):
    """
    Process multiple applications in batch
    
    Args:
        job_id: Job posting ID
        job_requirements: Job requirements
        
    Returns:
        Batch processing summary
    """
    try:
        # In production, retrieve applications from database
        applications = []  # Query from DB
        
        results = recruitment_system.batch_process_applications(
            applications=applications,
            job_requirements=job_requirements.dict()
        )
        
        return results
        
    except Exception as e:
        logger.error(f"Error in batch processing: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/metrics", response_model=MetricsResponse)
async def get_metrics(job_id: Optional[int] = None):
    """
    Get recruitment metrics
    
    Args:
        job_id: Optional job ID to filter metrics
        
    Returns:
        Recruitment KPIs
    """
    try:
        metrics = recruitment_system.get_metrics(job_id=job_id)
        return MetricsResponse(**metrics)
        
    except Exception as e:
        logger.error(f"Error retrieving metrics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/bias-audit")
async def get_bias_audit(
    job_id: Optional[int] = None,
    period_start: Optional[str] = None,
    period_end: Optional[str] = None
):
    """
    Get bias audit report
    
    Args:
        job_id: Optional job ID
        period_start: ISO datetime string
        period_end: ISO datetime string
        
    Returns:
        Bias audit results
    """
    try:
        # In production, query from database
        # Mock response
        return {
            "audit_date": datetime.utcnow().isoformat(),
            "job_id": job_id,
            "total_candidates": 100,
            "adverse_impact_detected": False,
            "passes_four_fifths_rule": True,
            "findings": []
        }
        
    except Exception as e:
        logger.error(f"Error generating bias audit: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v1/jobs", response_model=Dict)
async def create_job(job: JobRequirements):
    """
    Create a new job posting
    
    Args:
        job: Job requirements
        
    Returns:
        Created job with ID
    """
    try:
        # In production, store in database
        job_dict = job.dict()
        job_dict["id"] = 1  # Mock ID
        job_dict["created_at"] = datetime.utcnow().isoformat()
        
        return job_dict
        
    except Exception as e:
        logger.error(f"Error creating job: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/jobs/{job_id}")
async def get_job(job_id: int):
    """
    Get job details
    
    Args:
        job_id: Job ID
        
    Returns:
        Job details
    """
    try:
        # In production, query from database
        return {
            "id": job_id,
            "title": "Senior Data Scientist",
            "status": "active"
        }
        
    except Exception as e:
        logger.error(f"Error retrieving job: {e}")
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    uvicorn.run(
        "api:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.debug
    )
