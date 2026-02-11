"""
Tests for resume parser
"""
import pytest
from src.agents.resume_parser import ResumeParser


@pytest.fixture
def resume_parser():
    """Create resume parser instance"""
    return ResumeParser()


@pytest.fixture
def sample_resume():
    """Sample resume text"""
    return """
John Doe
john.doe@email.com | (555) 123-4567

EXPERIENCE
Senior Data Scientist | Tech Corp | 2020-Present
- Built machine learning models for customer segmentation
- Implemented real-time prediction pipelines using Python and AWS
- Led team of 3 data scientists

Data Analyst | Analytics Inc | 2018-2020
- Performed data analysis using SQL and Python
- Created dashboards in Tableau

EDUCATION
Master of Science in Computer Science
University of Technology | 2018

SKILLS
Python, SQL, Machine Learning, AWS, Docker, Pandas, Scikit-learn
    """


@pytest.fixture
def sample_job_requirements():
    """Sample job requirements"""
    return {
        "id": 1,
        "title": "Senior Data Scientist",
        "required_skills": ["python", "machine learning", "sql"],
        "preferred_skills": ["aws", "docker"],
        "min_years_experience": 3,
        "education_requirements": ["masters in computer science"],
        "certifications_required": []
    }


def test_resume_parser_initialization(resume_parser):
    """Test that resume parser initializes correctly"""
    assert resume_parser is not None
    assert resume_parser.client is not None


def test_extract_email(resume_parser, sample_resume):
    """Test email extraction"""
    email = resume_parser._extract_email(sample_resume)
    assert email == "john.doe@email.com"


def test_extract_phone(resume_parser, sample_resume):
    """Test phone extraction"""
    phone = resume_parser._extract_phone(sample_resume)
    assert phone is not None
    assert "555" in phone


def test_extract_skills(resume_parser, sample_resume):
    """Test skill extraction"""
    skills = resume_parser._extract_skills(sample_resume)
    assert "python" in skills
    assert "sql" in skills
    assert "aws" in skills


def test_skill_match(resume_parser):
    """Test skill matching logic"""
    candidate_skills = ["python", "sql", "java"]
    required_skills = ["python", "sql"]
    
    match_score = resume_parser._skill_match(candidate_skills, required_skills)
    assert match_score == 1.0  # 100% match


def test_partial_skill_match(resume_parser):
    """Test partial skill matching"""
    candidate_skills = ["python", "java"]
    required_skills = ["python", "sql", "javascript"]
    
    match_score = resume_parser._skill_match(candidate_skills, required_skills)
    assert 0.3 < match_score < 0.4  # 1/3 match


def test_experience_match_exceeds(resume_parser):
    """Test experience matching when candidate exceeds requirement"""
    match_score = resume_parser._experience_match(
        candidate_years=5,
        required_years=3
    )
    assert match_score == 1.0


def test_experience_match_below(resume_parser):
    """Test experience matching when candidate is below requirement"""
    match_score = resume_parser._experience_match(
        candidate_years=2,
        required_years=5
    )
    assert match_score < 1.0


def test_get_recommendation_strong_match(resume_parser):
    """Test recommendation for strong match"""
    recommendation = resume_parser._get_recommendation(0.80)
    assert recommendation == "STRONG_MATCH"


def test_get_recommendation_borderline(resume_parser):
    """Test recommendation for borderline candidate"""
    recommendation = resume_parser._get_recommendation(0.50)
    assert recommendation == "BORDERLINE"


def test_get_recommendation_not_qualified(resume_parser):
    """Test recommendation for unqualified candidate"""
    recommendation = resume_parser._get_recommendation(0.30)
    assert recommendation == "NOT_QUALIFIED"


def test_calculate_match_score(resume_parser, sample_job_requirements):
    """Test full scoring calculation"""
    profile = {
        "skills": {
            "technical": ["python", "sql", "machine learning", "aws"],
            "soft_skills": [],
            "tools": [],
            "languages": []
        },
        "total_years_experience": 4,
        "education": [{
            "degree": "Master of Science",
            "field": "Computer Science",
            "institution": "University",
            "graduation_year": 2018
        }],
        "certifications": []
    }
    
    result = resume_parser._calculate_match_score(profile, sample_job_requirements)
    
    assert "total_score" in result
    assert "breakdown" in result
    assert "recommendation" in result
    assert 0 <= result["total_score"] <= 1.0
    assert result["recommendation"] in ["STRONG_MATCH", "PROCEED_TO_SCREENING", "BORDERLINE", "NOT_QUALIFIED"]


@pytest.mark.asyncio
async def test_full_extraction_pipeline(resume_parser, sample_resume, sample_job_requirements):
    """Test complete extraction and scoring pipeline"""
    # Note: This would call Claude API in real usage
    # For testing, you may want to mock the API call
    
    # Mock version without API call
    profile = {
        "contact": {
            "email": "john.doe@email.com",
            "phone": "(555) 123-4567"
        },
        "skills": {
            "technical": ["python", "sql", "machine learning"],
            "soft_skills": [],
            "tools": [],
            "languages": []
        },
        "total_years_experience": 4,
        "education": [],
        "certifications": []
    }
    
    result = resume_parser._calculate_match_score(profile, sample_job_requirements)
    
    assert result["total_score"] > 0
    assert "breakdown" in result
