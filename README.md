# AI-Powered Recruitment System

An end-to-end automated recruitment system that screens resumes, conducts video interviews, and schedules candidates using AI and LangGraph orchestration.

## Features

- **Automated Resume Screening**: Parse and score resumes against job requirements
- **Bias Mitigation**: EEOC-compliant screening with demographic information removal
- **AI Video Interviews**: Adaptive questioning using LangGraph and Claude API
- **Smart Scheduling**: Automatic interview scheduling with calendar integration
- **REST API**: Complete API for ATS integration
- **Metrics Dashboard**: Track time-to-hire, quality-of-hire, and other KPIs

## Architecture

```
┌─────────────────┐
│   Resume Upload │
└────────┬────────┘
         │
         v
┌─────────────────┐      ┌──────────────────┐
│  Bias Removal   │──────>│ Resume Parsing   │
└─────────────────┘      └────────┬─────────┘
                                  │
                                  v
                         ┌─────────────────┐
                         │ Scoring Engine  │
                         └────────┬────────┘
                                  │
                    ┌─────────────┴─────────────┐
                    │                           │
                    v                           v
            ┌───────────────┐         ┌───────────────┐
            │   NOT QUALIFIED│         │   QUALIFIED   │
            └───────────────┘         └───────┬───────┘
                                              │
                                              v
                                     ┌────────────────┐
                                     │ Video Interview│
                                     │  (LangGraph)   │
                                     └────────┬───────┘
                                              │
                                   ┌──────────┴──────────┐
                                   │                     │
                                   v                     v
                          ┌────────────────┐   ┌────────────────┐
                          │  High Score    │   │   Low Score    │
                          └────────┬───────┘   └────────────────┘
                                   │
                                   v
                          ┌────────────────┐
                          │ Schedule with  │
                          │ Hiring Manager │
                          └────────────────┘
```

## Installation

### Prerequisites

- Python 3.9+
- PostgreSQL 13+ (or other SQL database)
- Google Calendar API credentials (optional)
- Anthropic API key

### Setup

1. **Clone the repository**
```bash
git clone <repository-url>
cd ai_recruitment_system
```

2. **Create virtual environment**
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
python -m spacy download en_core_web_lg
```

4. **Configure environment**
```bash
cp .env.example .env
# Edit .env with your credentials
```

5. **Setup database**
```bash
# Create PostgreSQL database
createdb recruitment_db

# Run migrations
python -m alembic upgrade head
```

6. **Run the application**
```bash
# Start API server
python src/api.py

# Or use uvicorn directly
uvicorn src.api:app --reload --host 0.0.0.0 --port 8000
```

## Configuration

### Environment Variables

Key configuration variables in `.env`:

```bash
# Required
ANTHROPIC_API_KEY=sk-ant-xxx
DATABASE_URL=postgresql://user:pass@localhost/recruitment_db

# Email notifications
SMTP_HOST=smtp.gmail.com
SMTP_USERNAME=your_email@company.com
SMTP_PASSWORD=your_app_password

# Scoring thresholds
MIN_RESUME_SCORE=0.45
STRONG_MATCH_THRESHOLD=0.75
MIN_INTERVIEW_SCORE=7.5
```

### Customizing Scoring Weights

Edit `src/agents/resume_parser.py`:

```python
scores = {
    "required_skills": ... * 0.35,     # 35% weight
    "experience_level": ... * 0.25,    # 25% weight
    "education": ... * 0.20,           # 20% weight
    "preferred_skills": ... * 0.15,    # 15% weight
    "certifications": ... * 0.05       # 5% weight
}
```

## API Usage

### Screen a candidate

```bash
curl -X POST "http://localhost:8000/api/v1/candidates/screen" \
  -F "resume=@candidate_resume.pdf" \
  -F "candidate_email=candidate@example.com" \
  -F "job_id=1" \
  -F 'job_requirements={
    "title": "Senior Data Scientist",
    "required_skills": ["python", "machine learning", "sql"],
    "min_years_experience": 5,
    "education_requirements": ["bachelors in computer science"]
  }'
```

### Schedule an interview

```bash
curl -X POST "http://localhost:8000/api/v1/interviews/schedule" \
  -H "Content-Type: application/json" \
  -d '{
    "candidate_email": "candidate@example.com",
    "interviewer_emails": ["manager@company.com"],
    "job_title": "Senior Data Scientist",
    "availability": {
      "slots": [
        {
          "start": "2024-02-01T09:00:00Z",
          "end": "2024-02-01T17:00:00Z"
        }
      ]
    }
  }'
```

### Get metrics

```bash
curl "http://localhost:8000/api/v1/metrics?job_id=1"
```

## Python SDK Usage

```python
from src.recruitment_system import RecruitmentSystem

# Initialize system
recruitment = RecruitmentSystem()

# Process application
with open("resume.pdf", "rb") as f:
    resume_bytes = f.read()

result = recruitment.process_application(
    resume_file=resume_bytes,
    resume_filename="resume.pdf",
    candidate_email="candidate@example.com",
    job_requirements={
        "id": 1,
        "title": "Data Scientist",
        "required_skills": ["python", "sql", "machine learning"],
        "min_years_experience": 3,
        "education_requirements": ["bachelors"]
    }
)

print(f"Status: {result['status']}")
print(f"Resume Score: {result['resume_score']}")
print(f"Recommendation: {result['recommendation']}")
```

## Bias Mitigation

The system implements several measures for fair hiring:

1. **PII Removal**: Names, addresses, photos removed before scoring
2. **Demographic Sanitization**: Age, gender, ethnicity indicators redacted
3. **4/5ths Rule Auditing**: Statistical checks for adverse impact
4. **Question Validation**: Interview questions checked for prohibited topics
5. **Compliance Reporting**: EEOC-formatted audit reports

### Generate bias audit report

```python
from src.agents.bias_mitigation import BiasMitigationLayer

bias_checker = BiasMitigationLayer()

# Audit historical hiring data
audit = bias_checker.audit_evaluation(
    scores=candidate_scores,
    demographics=demographic_data  # Optional, for compliance only
)

# Generate report
report = bias_checker.generate_compliance_report(
    audit_results=audit,
    job_id=1,
    period_start=datetime(2024, 1, 1),
    period_end=datetime(2024, 1, 31)
)

print(report)
```

## Video Interview System

The video interview uses LangGraph for adaptive questioning:

```python
from src.agents.interview_agent import VideoInterviewAgent

interview_agent = VideoInterviewAgent()

# Conduct interview
result = interview_agent.conduct_interview(
    candidate_profile=parsed_resume,
    job_role="Data Scientist",
    job_requirements=job_requirements
)

print(f"Overall Score: {result['overall_score']}/10")
print(f"Recommendation: {result['recommendation']}")
print(f"Key Strengths: {result['key_strengths']}")
```

## Testing

```bash
# Run all tests
pytest tests/

# Run with coverage
pytest --cov=src tests/

# Run specific test file
pytest tests/test_resume_parser.py
```

## Deployment

### Docker Deployment

```bash
# Build image
docker build -t ai-recruitment-system .

# Run container
docker run -p 8000:8000 --env-file .env ai-recruitment-system
```

### AWS Deployment

See `deployment/aws_deploy.md` for detailed instructions.

### Environment-Specific Settings

- **Development**: DEBUG=True, detailed logging
- **Staging**: Test with sample data, bias auditing enabled
- **Production**: DEBUG=False, encrypted connections, rate limiting

## Performance Metrics

Expected performance improvements:

- **Time-to-hire**: 30-40% reduction
- **Recruiter time saved**: 45+ hours per month
- **Candidate satisfaction**: 4.0+ / 5.0
- **False negative rate**: < 10%
- **Cost per screening**: ~$0.50-1.00 (Claude API)

## Monitoring

The system logs all important events:

```python
# Check logs
tail -f logs/recruitment_system.log

# View metrics
curl http://localhost:8000/api/v1/metrics
```

## Troubleshooting

### Common Issues

1. **Spacy model not found**
```bash
python -m spacy download en_core_web_lg
```

2. **Database connection error**
- Check DATABASE_URL in .env
- Ensure PostgreSQL is running
- Verify credentials

3. **Claude API rate limits**
- Reduce concurrent processing
- Implement backoff strategy
- Contact Anthropic for higher limits

## Roadmap

- [ ] Multi-language support
- [ ] Advanced video analysis (facial expressions, tone)
- [ ] Integration with LinkedIn, Indeed
- [ ] Mobile app for candidates
- [ ] Real-time collaboration features
- [ ] Advanced ML models for quality-of-hire prediction

## License

MIT License - see LICENSE file

## Support

For issues or questions:
- GitHub Issues: https://github.com/umair801/ai_recruitment_system/issues
- Email: umair@datawebify.com
- Documentation: See README.md and project files

## Contributing

1. Fork the repository
2. Create feature branch
3. Make changes with tests
4. Submit pull request

## Acknowledgments

- Anthropic Claude API for AI capabilities
- LangGraph for workflow orchestration
- Spacy for NLP processing
