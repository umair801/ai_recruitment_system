"""
Example usage of AI Recruitment System
"""
from src.recruitment_system import RecruitmentSystem
from src.agents.bias_mitigation import BiasMitigationLayer
import json


def example_1_basic_screening():
    """Example 1: Basic resume screening"""
    print("\n=== Example 1: Basic Resume Screening ===\n")
    
    recruitment = RecruitmentSystem()
    
    # Sample resume text
    resume_text = """
    Sarah Johnson
    sarah.j@email.com | (555) 987-6543
    
    PROFESSIONAL EXPERIENCE
    Lead Data Scientist | DataCorp Inc | 2019-Present
    - Designed and deployed ML models for fraud detection
    - Built data pipelines processing 10M+ records daily
    - Mentored team of 5 junior data scientists
    
    Data Scientist | Analytics Solutions | 2017-2019
    - Developed predictive models using Python and R
    - Worked with stakeholders to define business requirements
    
    EDUCATION
    PhD in Statistics | Stanford University | 2017
    
    SKILLS
    Python, R, SQL, TensorFlow, PyTorch, AWS, Docker, Kubernetes
    Machine Learning, Deep Learning, Statistical Modeling
    
    CERTIFICATIONS
    AWS Certified Solutions Architect
    TensorFlow Developer Certificate
    """
    
    job_requirements = {
        "id": 1,
        "title": "Senior Data Scientist",
        "required_skills": ["python", "machine learning", "sql"],
        "preferred_skills": ["aws", "tensorflow", "docker"],
        "min_years_experience": 5,
        "education_requirements": ["phd in statistics or computer science"],
        "certifications_required": []
    }
    
    # Process application
    result = recruitment.process_application(
        resume_file=resume_text.encode(),
        resume_filename="resume.txt",
        candidate_email="sarah.j@email.com",
        job_requirements=job_requirements
    )
    
    print(f"Status: {result['status']}")
    print(f"Resume Score: {result.get('resume_score', 'N/A')}")
    print(f"Recommendation: {result.get('recommendation', 'N/A')}")
    print(f"Stage: {result.get('stage', 'N/A')}")


def example_2_bias_mitigation():
    """Example 2: Bias mitigation and sanitization"""
    print("\n=== Example 2: Bias Mitigation ===\n")
    
    bias_checker = BiasMitigationLayer()
    
    # Resume with demographic information
    raw_resume = """
    John Smith
    123 Main Street, New York, NY 10001
    john.smith@email.com
    Born in 1985
    
    I am a 38-year-old male software engineer...
    """
    
    # Sanitize resume
    sanitized = bias_checker.sanitize_resume(raw_resume)
    
    print("Original resume:")
    print(raw_resume[:200])
    print("\nSanitized resume:")
    print(sanitized[:200])
    
    # Validate interview questions
    questions = [
        {"question": "Tell me about your technical experience."},
        {"question": "Are you married?"},  # Prohibited
        {"question": "What is your age?"},  # Prohibited
        {"question": "Describe a challenging project."}
    ]
    
    validation = bias_checker.validate_questions(questions)
    
    print(f"\nQuestion Validation:")
    print(f"Total questions: {validation['total_questions']}")
    print(f"Flagged questions: {validation['flagged_count']}")
    print(f"Compliant: {validation['compliant']}")
    
    if validation['flagged_questions']:
        print("\nFlagged questions:")
        for flagged in validation['flagged_questions']:
            print(f"  - {flagged['question']}")
            print(f"    Reason: {flagged['reason']}")


def example_3_batch_processing():
    """Example 3: Batch process multiple applications"""
    print("\n=== Example 3: Batch Processing ===\n")
    
    recruitment = RecruitmentSystem()
    
    # Simulate multiple applications
    applications = [
        {
            "resume_file": "Resume 1 content...".encode(),
            "resume_filename": "candidate1.txt",
            "candidate_email": "candidate1@example.com"
        },
        {
            "resume_file": "Resume 2 content...".encode(),
            "resume_filename": "candidate2.txt",
            "candidate_email": "candidate2@example.com"
        },
        {
            "resume_file": "Resume 3 content...".encode(),
            "resume_filename": "candidate3.txt",
            "candidate_email": "candidate3@example.com"
        }
    ]
    
    job_requirements = {
        "id": 1,
        "title": "Data Engineer",
        "required_skills": ["python", "sql", "spark"],
        "min_years_experience": 3,
        "education_requirements": ["bachelors"]
    }
    
    # Process all applications
    results = recruitment.batch_process_applications(
        applications=applications,
        job_requirements=job_requirements
    )
    
    print(f"Total processed: {results['total_processed']}")
    print(f"Rejected: {results['rejected']}")
    print(f"Interviews scheduled: {results['interview_scheduled']}")
    print(f"Pending review: {results['pending_review']}")


def example_4_metrics():
    """Example 4: Get recruitment metrics"""
    print("\n=== Example 4: Recruitment Metrics ===\n")
    
    recruitment = RecruitmentSystem()
    
    # Get metrics
    metrics = recruitment.get_metrics(job_id=1)
    
    print("Performance Metrics:")
    print(f"  Time to hire: {metrics['time_to_hire_days']} days")
    print(f"  Time reduction: {metrics['time_reduction_percent']}%")
    print(f"  Quality of hire: {metrics['quality_of_hire_score']}/5.0")
    print(f"  Hours saved: {metrics['recruiter_hours_saved']} hours")
    print(f"  Candidate satisfaction: {metrics['candidate_satisfaction']}/5.0")
    print(f"  False negative rate: {metrics['false_negative_rate']:.1%}")


def example_5_api_integration():
    """Example 5: API integration example"""
    print("\n=== Example 5: API Integration ===\n")
    
    import requests
    
    # Note: This assumes API is running on localhost:8000
    base_url = "http://localhost:8000"
    
    print("API Integration example:")
    print("1. Create job posting via API")
    print("2. Submit candidate via API")
    print("3. Schedule interview via API")
    print("\nSee README.md for full API documentation")


if __name__ == "__main__":
    print("AI Recruitment System - Usage Examples")
    print("=" * 50)
    
    # Run examples
    example_1_basic_screening()
    example_2_bias_mitigation()
    example_3_batch_processing()
    example_4_metrics()
    example_5_api_integration()
    
    print("\n" + "=" * 50)
    print("Examples complete!")
