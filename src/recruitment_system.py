"""
Main recruitment system orchestrating all agents
"""
from typing import Dict, Optional
from datetime import datetime
from loguru import logger
import PyPDF2
import io

from src.agents.resume_parser import ResumeParser
from src.agents.interview_agent import VideoInterviewAgent
from src.agents.bias_mitigation import BiasMitigationLayer
from src.agents.scheduler import InterviewScheduler
from config.settings import settings


class RecruitmentSystem:
    """End-to-end AI-powered recruitment system"""
    
    def __init__(self):
        """Initialize all sub-agents"""
        logger.info("Initializing AI Recruitment System")
        
        self.resume_parser = ResumeParser()
        self.interview_agent = VideoInterviewAgent()
        self.bias_checker = BiasMitigationLayer()
        self.scheduler = InterviewScheduler()
        
        logger.info("All agents initialized successfully")
    
    def process_application(
        self,
        resume_file: bytes,
        resume_filename: str,
        candidate_email: str,
        job_requirements: Dict,
        candidate_availability: Optional[Dict] = None
    ) -> Dict:
        """
        Process complete candidate application workflow
        
        Args:
            resume_file: Resume file bytes
            resume_filename: Name of resume file
            candidate_email: Candidate's email
            job_requirements: Complete job requirements
            candidate_availability: Optional availability windows
            
        Returns:
            Complete processing results
        """
        logger.info(f"Processing application for {candidate_email}")
        
        result = {
            "candidate_email": candidate_email,
            "job_id": job_requirements.get("id"),
            "job_title": job_requirements.get("title"),
            "timestamp": datetime.utcnow().isoformat(),
            "status": "processing"
        }
        
        try:
            # Stage 1: Extract text from resume
            resume_text = self._extract_text_from_pdf(resume_file, resume_filename)
            
            # Stage 2: Sanitize resume to remove bias
            sanitized_resume = self.bias_checker.sanitize_resume(resume_text)
            
            # Stage 3: Parse and score resume
            logger.info("Stage 1: Resume screening")
            evaluation = self.resume_parser.extract_structured_data(
                sanitized_resume,
                job_requirements
            )
            
            result["resume_evaluation"] = evaluation
            result["resume_score"] = evaluation["match_score"]["total_score"]
            result["recommendation"] = evaluation["match_score"]["recommendation"]
            
            # Decision point 1: Check if candidate passes resume screening
            if evaluation["match_score"]["recommendation"] == "NOT_QUALIFIED":
                logger.info(f"Candidate does not meet minimum requirements")
                result["status"] = "rejected"
                result["rejection_reason"] = "Does not meet minimum job requirements"
                result["stage"] = "resume_screening"
                
                # Send rejection email
                self._send_notification(
                    candidate_email,
                    "application_rejected",
                    job_requirements.get("title")
                )
                
                return result
            
            # Stage 4: Video interview (if borderline or better)
            if evaluation["match_score"]["total_score"] >= settings.proceed_to_interview_threshold:
                logger.info("Stage 2: Video interview")
                
                interview_result = self.interview_agent.conduct_interview(
                    candidate_profile=evaluation["profile"],
                    job_role=job_requirements.get("title"),
                    job_requirements=job_requirements
                )
                
                result["interview_evaluation"] = interview_result
                result["interview_score"] = interview_result.get("overall_score", 0)
                
                # Decision point 2: Check interview performance
                if interview_result.get("overall_score", 0) >= settings.min_interview_score:
                    logger.info("Stage 3: Scheduling human interview")
                    
                    # Schedule interview with hiring manager
                    if candidate_availability:
                        available_slots = self.scheduler.find_optimal_slots(
                            candidate_availability=candidate_availability.get("slots", []),
                            interviewer_ids=job_requirements.get("hiring_managers", []),
                            duration_minutes=settings.video_interview_duration_minutes
                        )
                        
                        if available_slots:
                            # Schedule first available slot
                            meeting = self.scheduler.send_interview_invite(
                                candidate_email=candidate_email,
                                interviewer_emails=job_requirements.get("hiring_managers", []),
                                time_slot=available_slots[0],
                                job_title=job_requirements.get("title")
                            )
                            
                            result["scheduled_interview"] = meeting
                            result["status"] = "human_interview_scheduled"
                            result["stage"] = "awaiting_human_interview"
                            
                            # Send confirmation email
                            self._send_notification(
                                candidate_email,
                                "interview_scheduled",
                                job_requirements.get("title"),
                                meeting_details=meeting
                            )
                        else:
                            result["status"] = "pending_scheduling"
                            result["stage"] = "awaiting_availability"
                    else:
                        result["status"] = "pending_scheduling"
                        result["stage"] = "awaiting_availability"
                        
                        # Send email requesting availability
                        self._send_notification(
                            candidate_email,
                            "request_availability",
                            job_requirements.get("title")
                        )
                else:
                    logger.info("Candidate did not pass video interview threshold")
                    result["status"] = "rejected"
                    result["rejection_reason"] = "Did not meet interview performance threshold"
                    result["stage"] = "video_interview"
                    
                    self._send_notification(
                        candidate_email,
                        "application_rejected",
                        job_requirements.get("title")
                    )
            else:
                # Borderline candidate - needs human review
                logger.info("Borderline candidate - flagging for human review")
                result["status"] = "pending_human_review"
                result["stage"] = "resume_screening"
                result["review_reason"] = "Borderline resume score - human review recommended"
            
            logger.info(f"Application processing complete. Status: {result['status']}")
            return result
            
        except Exception as e:
            logger.error(f"Error processing application: {e}")
            result["status"] = "error"
            result["error_message"] = str(e)
            return result
    
    def _extract_text_from_pdf(self, file_bytes: bytes, filename: str) -> str:
        """
        Extract text from PDF resume
        
        Args:
            file_bytes: PDF file bytes
            filename: Original filename
            
        Returns:
            Extracted text
        """
        try:
            if filename.lower().endswith('.pdf'):
                pdf_reader = PyPDF2.PdfReader(io.BytesIO(file_bytes))
                text = ""
                for page in pdf_reader.pages:
                    text += page.extract_text()
                return text
            elif filename.lower().endswith(('.doc', '.docx')):
                # For .docx files, use python-docx
                from docx import Document
                doc = Document(io.BytesIO(file_bytes))
                text = "\n".join([para.text for para in doc.paragraphs])
                return text
            else:
                # Assume plain text
                return file_bytes.decode('utf-8')
        except Exception as e:
            logger.error(f"Error extracting text from {filename}: {e}")
            raise
    
    def _send_notification(
        self,
        recipient: str,
        notification_type: str,
        job_title: str,
        **kwargs
    ):
        """
        Send email notification to candidate
        
        Args:
            recipient: Email address
            notification_type: Type of notification
            job_title: Job title
            **kwargs: Additional context
        """
        # Mock implementation - in production, use SMTP or email service
        logger.info(f"Sending {notification_type} email to {recipient}")
        
        templates = {
            "application_rejected": f"""
Subject: Application Update - {job_title}

Dear Candidate,

Thank you for your interest in the {job_title} position. After careful review of your application, we have decided to move forward with other candidates whose qualifications more closely match our current needs.

We appreciate the time you took to apply and wish you the best in your job search.

Best regards,
Recruitment Team
            """,
            "interview_scheduled": f"""
Subject: Interview Scheduled - {job_title}

Dear Candidate,

Congratulations! We would like to invite you for an interview for the {job_title} position.

Meeting Details:
Time: {kwargs.get('meeting_details', {}).get('scheduled_time')}
Video Link: {kwargs.get('meeting_details', {}).get('meeting_url')}

Please join a few minutes early and ensure your camera and microphone are working.

Best regards,
Recruitment Team
            """,
            "request_availability": f"""
Subject: Next Steps - {job_title}

Dear Candidate,

Thank you for completing the initial screening. We would like to schedule an interview with our hiring team.

Please provide your availability for the next two weeks using this link: [calendar link]

Best regards,
Recruitment Team
            """
        }
        
        message = templates.get(notification_type, "")
        logger.debug(f"Email content: {message}")
        
        # In production, send via SMTP:
        # import smtplib
        # from email.mime.text import MIMEText
        # ... send email
    
    def batch_process_applications(
        self,
        applications: list,
        job_requirements: Dict
    ) -> Dict:
        """
        Process multiple applications in batch
        
        Args:
            applications: List of application dictionaries
            job_requirements: Job requirements
            
        Returns:
            Batch processing results
        """
        logger.info(f"Batch processing {len(applications)} applications")
        
        results = {
            "total_processed": 0,
            "rejected": 0,
            "interview_scheduled": 0,
            "pending_review": 0,
            "errors": 0,
            "details": []
        }
        
        for app in applications:
            try:
                result = self.process_application(
                    resume_file=app["resume_file"],
                    resume_filename=app["resume_filename"],
                    candidate_email=app["candidate_email"],
                    job_requirements=job_requirements,
                    candidate_availability=app.get("availability")
                )
                
                results["details"].append(result)
                results["total_processed"] += 1
                
                if result["status"] == "rejected":
                    results["rejected"] += 1
                elif result["status"] == "human_interview_scheduled":
                    results["interview_scheduled"] += 1
                elif result["status"] == "pending_human_review":
                    results["pending_review"] += 1
                    
            except Exception as e:
                logger.error(f"Error processing application: {e}")
                results["errors"] += 1
        
        logger.info(f"Batch processing complete: {results}")
        return results
    
    def get_metrics(self, job_id: Optional[int] = None) -> Dict:
        """
        Calculate recruitment metrics
        
        Args:
            job_id: Optional job ID to filter metrics
            
        Returns:
            Metrics dictionary
        """
        # In production, query database for actual metrics
        # This is a mock implementation
        
        return {
            "time_to_hire_days": 12.5,
            "time_reduction_percent": 35.0,
            "quality_of_hire_score": 4.2,  # out of 5
            "recruiter_hours_saved": 45.0,
            "candidate_satisfaction": 4.1,  # out of 5
            "false_negative_rate": 0.08,  # 8%
            "total_applications": 150,
            "passed_screening": 45,
            "interviews_conducted": 22,
            "offers_extended": 5,
            "hires": 3
        }
