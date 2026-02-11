"""
Database models for recruitment system
"""
from datetime import datetime
from typing import Optional, List
from sqlalchemy import (
    Column, String, Integer, Float, DateTime, 
    Boolean, Text, ForeignKey, JSON, Enum
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
import enum


Base = declarative_base()


class CandidateStatus(str, enum.Enum):
    """Candidate application status"""
    NEW = "new"
    RESUME_SCREENED = "resume_screened"
    VIDEO_INTERVIEW_SCHEDULED = "video_interview_scheduled"
    VIDEO_INTERVIEW_COMPLETED = "video_interview_completed"
    HUMAN_INTERVIEW_SCHEDULED = "human_interview_scheduled"
    OFFER_EXTENDED = "offer_extended"
    HIRED = "hired"
    REJECTED = "rejected"
    WITHDRAWN = "withdrawn"


class Candidate(Base):
    """Candidate information and tracking"""
    __tablename__ = "candidates"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    first_name = Column(String(100))
    last_name = Column(String(100))
    phone = Column(String(20))
    
    # Application details
    job_id = Column(Integer, ForeignKey("jobs.id"), nullable=False)
    status = Column(Enum(CandidateStatus), default=CandidateStatus.NEW)
    applied_at = Column(DateTime, default=datetime.utcnow)
    
    # Resume data
    resume_path = Column(String(500))
    resume_text = Column(Text)
    sanitized_resume_text = Column(Text)
    
    # Structured data extracted from resume
    total_years_experience = Column(Float)
    education_level = Column(String(100))
    skills = Column(JSON)  # List of skills
    certifications = Column(JSON)  # List of certifications
    
    # Scoring
    resume_score = Column(Float)
    resume_score_breakdown = Column(JSON)
    video_interview_score = Column(Float)
    video_interview_breakdown = Column(JSON)
    overall_score = Column(Float)
    
    # Relationships
    job = relationship("Job", back_populates="candidates")
    video_interview = relationship("VideoInterview", back_populates="candidate", uselist=False)
    evaluations = relationship("CandidateEvaluation", back_populates="candidate")
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Job(Base):
    """Job posting information"""
    __tablename__ = "jobs"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), nullable=False)
    department = Column(String(100))
    location = Column(String(200))
    employment_type = Column(String(50))  # full-time, part-time, contract
    
    # Job requirements
    description = Column(Text)
    required_skills = Column(JSON)  # List of required skills
    preferred_skills = Column(JSON)  # List of preferred skills
    min_years_experience = Column(Float)
    max_years_experience = Column(Float)
    education_requirements = Column(JSON)
    certifications_required = Column(JSON)
    
    # Salary range
    min_salary = Column(Integer)
    max_salary = Column(Integer)
    
    # Status
    is_active = Column(Boolean, default=True)
    posted_date = Column(DateTime, default=datetime.utcnow)
    closing_date = Column(DateTime)
    
    # Relationships
    candidates = relationship("Candidate", back_populates="job")
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class VideoInterview(Base):
    """Video interview session details"""
    __tablename__ = "video_interviews"
    
    id = Column(Integer, primary_key=True, index=True)
    candidate_id = Column(Integer, ForeignKey("candidates.id"), unique=True, nullable=False)
    
    # Scheduling
    scheduled_at = Column(DateTime)
    completed_at = Column(DateTime)
    duration_minutes = Column(Integer)
    
    # Platform details
    platform = Column(String(50))  # zoom, teams, custom
    meeting_url = Column(String(500))
    meeting_id = Column(String(200))
    
    # Interview content
    questions_asked = Column(JSON)  # List of questions with metadata
    responses = Column(JSON)  # List of responses with transcripts
    
    # Evaluation
    technical_score = Column(Float)
    communication_score = Column(Float)
    problem_solving_score = Column(Float)
    cultural_fit_score = Column(Float)
    overall_score = Column(Float)
    detailed_evaluation = Column(JSON)
    
    # Recording
    recording_url = Column(String(500))
    transcript_path = Column(String(500))
    
    # Relationships
    candidate = relationship("Candidate", back_populates="video_interview")
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class CandidateEvaluation(Base):
    """Human evaluations and notes"""
    __tablename__ = "candidate_evaluations"
    
    id = Column(Integer, primary_key=True, index=True)
    candidate_id = Column(Integer, ForeignKey("candidates.id"), nullable=False)
    
    # Evaluator info
    evaluator_name = Column(String(200))
    evaluator_email = Column(String(255))
    evaluation_type = Column(String(50))  # resume, video, phone, in-person
    
    # Evaluation
    score = Column(Float)
    strengths = Column(Text)
    weaknesses = Column(Text)
    notes = Column(Text)
    recommendation = Column(String(50))  # hire, no_hire, maybe
    
    # Relationships
    candidate = relationship("Candidate", back_populates="evaluations")
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)


class BiasAuditLog(Base):
    """Log for bias detection and compliance"""
    __tablename__ = "bias_audit_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    job_id = Column(Integer, ForeignKey("jobs.id"))
    
    # Audit period
    audit_date = Column(DateTime, default=datetime.utcnow)
    period_start = Column(DateTime)
    period_end = Column(DateTime)
    
    # Statistics
    total_applicants = Column(Integer)
    total_screened = Column(Integer)
    total_interviewed = Column(Integer)
    total_hired = Column(Integer)
    
    # Demographic breakdowns (aggregated only, no individual tracking)
    demographic_stats = Column(JSON)
    
    # Adverse impact analysis
    adverse_impact_ratio = Column(Float)
    passes_four_fifths_rule = Column(Boolean)
    
    # Findings
    potential_bias_detected = Column(Boolean, default=False)
    findings = Column(JSON)
    corrective_actions = Column(Text)
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)


class SystemMetrics(Base):
    """Track system performance metrics"""
    __tablename__ = "system_metrics"
    
    id = Column(Integer, primary_key=True, index=True)
    metric_date = Column(DateTime, default=datetime.utcnow, index=True)
    
    # Performance metrics
    avg_time_to_hire_days = Column(Float)
    avg_time_to_screen_hours = Column(Float)
    avg_interview_score = Column(Float)
    
    # Volume metrics
    total_applications = Column(Integer)
    total_screenings_completed = Column(Integer)
    total_interviews_conducted = Column(Integer)
    total_hires = Column(Integer)
    
    # Quality metrics
    false_negative_rate = Column(Float)
    candidate_satisfaction_score = Column(Float)
    recruiter_hours_saved = Column(Float)
    
    # Cost metrics
    cost_per_hire = Column(Float)
    api_costs = Column(Float)
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
