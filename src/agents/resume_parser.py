"""
Resume parsing and scoring agent using NLP and Claude API
"""
import re
import spacy
from typing import Dict, List, Optional, Tuple
from datetime import datetime
import json
from anthropic import Anthropic
from loguru import logger

from config.settings import settings


class ResumeParser:
    """Extract structured information from resumes and score against job requirements"""
    
    def __init__(self):
        """Initialize NLP models and API client"""
        try:
            self.nlp = spacy.load("en_core_web_lg")
        except OSError:
            logger.warning("Spacy model not found. Run: python -m spacy download en_core_web_lg")
            self.nlp = None
        
        self.client = Anthropic(api_key=settings.anthropic_api_key)
        
    def extract_structured_data(
        self, 
        resume_text: str, 
        job_requirements: Dict
    ) -> Dict:
        """
        Parse resume and score against job requirements
        
        Args:
            resume_text: Raw text from resume
            job_requirements: Job requirements dictionary
            
        Returns:
            Complete evaluation with profile and scores
        """
        logger.info("Starting resume parsing and evaluation")
        
        # Extract structured information using Claude
        candidate_profile = self._extract_with_claude(resume_text)
        
        # Calculate match score
        match_score = self._calculate_match_score(
            candidate_profile, 
            job_requirements
        )
        
        result = {
            "profile": candidate_profile,
            "match_score": match_score,
            "timestamp": datetime.utcnow().isoformat(),
            "job_id": job_requirements.get("id")
        }
        
        logger.info(f"Resume evaluation complete. Score: {match_score['total_score']}")
        return result
    
    def _extract_with_claude(self, resume_text: str) -> Dict:
        """Use Claude to extract structured data from resume"""
        
        extraction_prompt = f"""Extract the following information from this resume in JSON format:

{{
  "contact": {{
    "email": "string or null",
    "phone": "string or null"
  }},
  "education": [
    {{
      "degree": "string",
      "field": "string", 
      "institution": "string",
      "graduation_year": "integer or null"
    }}
  ],
  "experience": [
    {{
      "title": "string",
      "company": "string",
      "start_date": "YYYY-MM or YYYY",
      "end_date": "YYYY-MM or YYYY or 'Present'",
      "duration_months": integer,
      "responsibilities": ["string"],
      "achievements": ["string"]
    }}
  ],
  "skills": {{
    "technical": ["string"],
    "soft_skills": ["string"],
    "tools": ["string"],
    "languages": ["string"]
  }},
  "certifications": [
    {{
      "name": "string",
      "issuer": "string",
      "date": "YYYY-MM or null"
    }}
  ],
  "total_years_experience": float
}}

Resume text:
{resume_text}

Return ONLY the JSON, no additional text."""

        try:
            response = self.client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=4000,
                temperature=0,
                messages=[{"role": "user", "content": extraction_prompt}]
            )
            
            # Extract JSON from response
            content = response.content[0].text
            
            # Try to find JSON in response
            json_match = re.search(r'\{.*\}', content, re.DOTALL)
            if json_match:
                profile = json.loads(json_match.group())
            else:
                profile = json.loads(content)
            
            return profile
            
        except Exception as e:
            logger.error(f"Error extracting resume data with Claude: {e}")
            return self._fallback_extraction(resume_text)
    
    def _fallback_extraction(self, resume_text: str) -> Dict:
        """Fallback extraction using regex and spacy if Claude fails"""
        logger.info("Using fallback extraction method")
        
        profile = {
            "contact": {
                "email": self._extract_email(resume_text),
                "phone": self._extract_phone(resume_text)
            },
            "education": [],
            "experience": [],
            "skills": {
                "technical": self._extract_skills(resume_text),
                "soft_skills": [],
                "tools": [],
                "languages": []
            },
            "certifications": [],
            "total_years_experience": self._estimate_years_experience(resume_text)
        }
        
        return profile
    
    def _extract_email(self, text: str) -> Optional[str]:
        """Extract email address using regex"""
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        match = re.search(email_pattern, text)
        return match.group() if match else None
    
    def _extract_phone(self, text: str) -> Optional[str]:
        """Extract phone number using regex"""
        phone_pattern = r'(\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}'
        match = re.search(phone_pattern, text)
        return match.group() if match else None
    
    def _extract_skills(self, text: str) -> List[str]:
        """Extract technical skills using keyword matching"""
        # Common technical skills
        skill_keywords = [
            'python', 'java', 'javascript', 'sql', 'aws', 'docker', 'kubernetes',
            'react', 'angular', 'node.js', 'tensorflow', 'pytorch', 'scikit-learn',
            'pandas', 'numpy', 'git', 'linux', 'api', 'rest', 'graphql'
        ]
        
        text_lower = text.lower()
        found_skills = [skill for skill in skill_keywords if skill in text_lower]
        return found_skills
    
    def _estimate_years_experience(self, text: str) -> float:
        """Estimate years of experience from text"""
        # Look for patterns like "5 years", "3+ years"
        pattern = r'(\d+)[\+]?\s*years?\s*(of\s*)?(experience|exp)'
        matches = re.findall(pattern, text.lower())
        
        if matches:
            years = [int(match[0]) for match in matches]
            return max(years) if years else 0.0
        return 0.0
    
    def _calculate_match_score(
        self, 
        profile: Dict, 
        requirements: Dict
    ) -> Dict:
        """
        Calculate weighted match score against job requirements
        
        Scoring breakdown:
        - Required skills: 35%
        - Experience level: 25%
        - Education: 20%
        - Preferred skills: 15%
        - Certifications: 5%
        """
        scores = {}
        
        # Required skills match (35%)
        required_skills = requirements.get("required_skills", [])
        candidate_skills = self._flatten_skills(profile.get("skills", {}))
        scores["required_skills"] = self._skill_match(
            candidate_skills, 
            required_skills
        ) * 0.35
        
        # Experience level match (25%)
        min_years = requirements.get("min_years_experience", 0)
        candidate_years = profile.get("total_years_experience", 0)
        scores["experience_level"] = self._experience_match(
            candidate_years,
            min_years
        ) * 0.25
        
        # Education match (20%)
        education_req = requirements.get("education_requirements", [])
        candidate_edu = profile.get("education", [])
        scores["education"] = self._education_match(
            candidate_edu,
            education_req
        ) * 0.20
        
        # Preferred skills match (15%)
        preferred_skills = requirements.get("preferred_skills", [])
        scores["preferred_skills"] = self._skill_match(
            candidate_skills,
            preferred_skills
        ) * 0.15
        
        # Certifications match (5%)
        cert_req = requirements.get("certifications_required", [])
        candidate_certs = [c.get("name", "") for c in profile.get("certifications", [])]
        scores["certifications"] = self._cert_match(
            candidate_certs,
            cert_req
        ) * 0.05
        
        total_score = sum(scores.values())
        
        return {
            "total_score": round(total_score, 2),
            "breakdown": {k: round(v, 2) for k, v in scores.items()},
            "recommendation": self._get_recommendation(total_score),
            "recommendation_reason": self._get_recommendation_reason(scores, total_score)
        }
    
    def _flatten_skills(self, skills_dict: Dict) -> List[str]:
        """Flatten skills dictionary into single list"""
        all_skills = []
        for skill_list in skills_dict.values():
            if isinstance(skill_list, list):
                all_skills.extend([s.lower() for s in skill_list])
        return all_skills
    
    def _skill_match(self, candidate_skills: List[str], required_skills: List[str]) -> float:
        """Calculate skill match percentage"""
        if not required_skills:
            return 1.0
        
        candidate_skills_lower = [s.lower() for s in candidate_skills]
        required_skills_lower = [s.lower() for s in required_skills]
        
        matches = sum(1 for skill in required_skills_lower if skill in candidate_skills_lower)
        return matches / len(required_skills) if required_skills else 0.0
    
    def _experience_match(self, candidate_years: float, required_years: float) -> float:
        """Calculate experience level match"""
        if candidate_years >= required_years:
            return 1.0
        elif candidate_years >= required_years * 0.75:
            return 0.8
        elif candidate_years >= required_years * 0.5:
            return 0.5
        else:
            return 0.2
    
    def _education_match(self, candidate_edu: List[Dict], required_edu: List[str]) -> float:
        """Calculate education match"""
        if not required_edu:
            return 1.0
        
        if not candidate_edu:
            return 0.0
        
        # Education level hierarchy
        edu_levels = {
            "phd": 5,
            "doctorate": 5,
            "masters": 4,
            "bachelor": 3,
            "associate": 2,
            "high school": 1
        }
        
        # Get highest candidate education
        candidate_level = 0
        for edu in candidate_edu:
            degree = edu.get("degree", "").lower()
            for key, value in edu_levels.items():
                if key in degree:
                    candidate_level = max(candidate_level, value)
        
        # Get required education level
        required_level = 0
        for req in required_edu:
            req_lower = req.lower()
            for key, value in edu_levels.items():
                if key in req_lower:
                    required_level = max(required_level, value)
        
        if candidate_level >= required_level:
            return 1.0
        elif candidate_level == required_level - 1:
            return 0.7
        else:
            return 0.3
    
    def _cert_match(self, candidate_certs: List[str], required_certs: List[str]) -> float:
        """Calculate certification match"""
        if not required_certs:
            return 1.0
        
        candidate_certs_lower = [c.lower() for c in candidate_certs]
        required_certs_lower = [c.lower() for c in required_certs]
        
        matches = sum(
            1 for cert in required_certs_lower 
            if any(cert in c for c in candidate_certs_lower)
        )
        
        return matches / len(required_certs) if required_certs else 0.0
    
    def _get_recommendation(self, score: float) -> str:
        """Get hiring recommendation based on score"""
        if score >= settings.strong_match_threshold:
            return "STRONG_MATCH"
        elif score >= settings.proceed_to_interview_threshold:
            return "PROCEED_TO_SCREENING"
        elif score >= settings.min_resume_score:
            return "BORDERLINE"
        else:
            return "NOT_QUALIFIED"
    
    def _get_recommendation_reason(self, scores: Dict, total_score: float) -> str:
        """Generate explanation for recommendation"""
        reasons = []
        
        if scores.get("required_skills", 0) / 0.35 >= 0.8:
            reasons.append("Strong match on required skills")
        elif scores.get("required_skills", 0) / 0.35 < 0.5:
            reasons.append("Missing key required skills")
        
        if scores.get("experience_level", 0) / 0.25 >= 0.8:
            reasons.append("Meets experience requirements")
        elif scores.get("experience_level", 0) / 0.25 < 0.5:
            reasons.append("Insufficient experience")
        
        if total_score >= settings.strong_match_threshold:
            return "Excellent candidate profile. " + "; ".join(reasons)
        elif total_score >= settings.proceed_to_interview_threshold:
            return "Qualified candidate. " + "; ".join(reasons)
        elif total_score >= settings.min_resume_score:
            return "Marginal fit. " + "; ".join(reasons)
        else:
            return "Does not meet minimum requirements. " + "; ".join(reasons)
