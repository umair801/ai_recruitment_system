# Quick Start Guide

## 5-Minute Setup

### 1. Install Dependencies

```bash
# Clone and enter directory
cd ai_recruitment_system

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install packages
pip install -r requirements.txt
python -m spacy download en_core_web_lg
```

### 2. Configure Environment

```bash
# Copy example environment file
cp .env.example .env

# Edit .env and add your Anthropic API key
ANTHROPIC_API_KEY=sk-ant-your-key-here
```

### 3. Run the System

```bash
# Start the API server
python src/api.py
```

The API will be available at `http://localhost:8000`

### 4. Test the System

```bash
# Run example usage
python examples/usage_examples.py
```

## First Application

### Option 1: Using Python SDK

```python
from src.recruitment_system import RecruitmentSystem

recruitment = RecruitmentSystem()

# Process a candidate
with open("candidate_resume.pdf", "rb") as f:
    result = recruitment.process_application(
        resume_file=f.read(),
        resume_filename="resume.pdf",
        candidate_email="candidate@example.com",
        job_requirements={
            "title": "Data Scientist",
            "required_skills": ["python", "machine learning"],
            "min_years_experience": 3
        }
    )

print(f"Status: {result['status']}")
print(f"Score: {result['resume_score']}")
```

### Option 2: Using REST API

```bash
curl -X POST "http://localhost:8000/api/v1/candidates/screen" \
  -F "resume=@resume.pdf" \
  -F "candidate_email=test@example.com" \
  -F "job_id=1" \
  -F 'job_requirements={
    "title": "Data Scientist",
    "required_skills": ["python", "sql"],
    "min_years_experience": 3
  }'
```

## What Happens Next?

1. **Resume is parsed** - Extracts skills, experience, education
2. **Bias mitigation** - Removes demographic information
3. **Scoring** - Matches against job requirements
4. **Decision**:
   - **Score < 45%**: Rejected
   - **Score 45-60%**: Human review
   - **Score 60-75%**: Video interview
   - **Score > 75%**: Fast-track to hiring manager

## Common Workflows

### Create a Job Posting

```python
job = {
    "title": "Senior Data Scientist",
    "department": "AI/ML",
    "required_skills": ["python", "tensorflow", "sql"],
    "preferred_skills": ["aws", "docker"],
    "min_years_experience": 5,
    "education_requirements": ["masters in cs or related"]
}
```

### Batch Process Applications

```python
applications = [
    {"resume_file": resume1, "candidate_email": "c1@example.com"},
    {"resume_file": resume2, "candidate_email": "c2@example.com"},
]

results = recruitment.batch_process_applications(
    applications=applications,
    job_requirements=job
)
```

### Schedule Interview

```python
recruitment.scheduler.send_interview_invite(
    candidate_email="candidate@example.com",
    interviewer_emails=["manager@company.com"],
    time_slot={
        "start": "2024-02-01T10:00:00Z",
        "end": "2024-02-01T10:30:00Z"
    },
    job_title="Data Scientist"
)
```

## Troubleshooting

**Issue**: Spacy model not found
```bash
python -m spacy download en_core_web_lg
```

**Issue**: Database connection error
- Check DATABASE_URL in .env
- Default is PostgreSQL, update if needed

**Issue**: API key error
- Verify ANTHROPIC_API_KEY in .env
- Check key has sufficient credits

## Next Steps

- Read full [README.md](README.md) for detailed documentation
- Check [examples/usage_examples.py](examples/usage_examples.py) for more examples
- See [deployment/DEPLOYMENT.md](deployment/DEPLOYMENT.md) for production deployment
- Review [API documentation](http://localhost:8000/docs) when server is running

## Support

- Documentation: See README.md
- Examples: See examples/ directory
- Issues: Create GitHub issue
