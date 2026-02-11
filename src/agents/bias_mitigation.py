"""
Bias mitigation and EEOC compliance module
"""
import re
from typing import Dict, List, Optional
from datetime import datetime
from loguru import logger

from config.settings import settings


class BiasMitigationLayer:
    """Ensure fair hiring practices and EEOC compliance"""
    
    # Protected attributes that should not influence decisions
    PROTECTED_ATTRIBUTES = [
        "gender", "age", "ethnicity", "race", "religion",
        "disability", "national_origin", "marital_status",
        "sexual_orientation", "gender_identity"
    ]
    
    # Patterns that might reveal protected information
    DEMOGRAPHIC_PATTERNS = {
        "age": [
            r'\b(19|20)\d{2}\b',  # Birth years
            r'\b\d{1,2}\s*years?\s*old\b',
            r'\bborn\s+in\b',
            r'\bgraduated\s+in\s+\d{4}\b'
        ],
        "gender": [
            r'\b(he|she|his|her|him)\b',
            r'\b(mr\.|mrs\.|ms\.|miss)\b',
            r'\b(male|female|man|woman)\b'
        ],
        "ethnicity": [
            r'\b(african|asian|hispanic|latino|latina|caucasian|white|black)\b'
        ],
        "religion": [
            r'\b(christian|muslim|jewish|hindu|buddhist|catholic|protestant)\b'
        ],
        "location_identifiers": [
            r'\b\d{5}\b',  # ZIP codes
            r'\b\d{1,5}\s+[\w\s]+\s+(street|st|avenue|ave|road|rd|drive|dr)\b'
        ]
    }
    
    def __init__(self):
        """Initialize bias mitigation system"""
        self.audit_enabled = settings.enable_bias_auditing
        self.adverse_impact_threshold = settings.adverse_impact_threshold
    
    def sanitize_resume(self, resume_text: str) -> str:
        """
        Remove personally identifiable and demographic information
        
        Args:
            resume_text: Raw resume text
            
        Returns:
            Sanitized resume text with PII removed
        """
        logger.info("Sanitizing resume to remove bias indicators")
        
        sanitized = resume_text
        
        # Remove names (keep first names if they appear with contact info)
        sanitized = self._remove_names(sanitized)
        
        # Remove addresses and ZIP codes
        sanitized = self._remove_addresses(sanitized)
        
        # Remove demographic indicators
        sanitized = self._remove_demographic_patterns(sanitized)
        
        # Remove age indicators
        sanitized = self._remove_age_indicators(sanitized)
        
        # Remove photos (if PDF parsing includes this)
        # Note: This would be handled at PDF parsing level
        
        logger.info("Resume sanitization complete")
        return sanitized
    
    def _remove_names(self, text: str) -> str:
        """Remove full names while preserving professional titles"""
        # This is simplified - in production, use NER models
        # Remove lines that look like name headers
        lines = text.split('\n')
        filtered_lines = []
        
        for i, line in enumerate(lines):
            # Skip first few lines that typically contain names
            if i < 3 and len(line.split()) <= 4 and not any(char.isdigit() for char in line):
                continue
            filtered_lines.append(line)
        
        return '\n'.join(filtered_lines)
    
    def _remove_addresses(self, text: str) -> str:
        """Remove physical addresses"""
        # Remove street addresses
        for pattern in self.DEMOGRAPHIC_PATTERNS["location_identifiers"]:
            text = re.sub(pattern, '[ADDRESS REMOVED]', text, flags=re.IGNORECASE)
        
        return text
    
    def _remove_demographic_patterns(self, text: str) -> str:
        """Remove demographic identifiers"""
        for category, patterns in self.DEMOGRAPHIC_PATTERNS.items():
            if category == "location_identifiers":
                continue  # Already handled
            
            for pattern in patterns:
                text = re.sub(pattern, '[REDACTED]', text, flags=re.IGNORECASE)
        
        return text
    
    def _remove_age_indicators(self, text: str) -> str:
        """Remove age-related information"""
        # Remove graduation years (keep just "Bachelor's Degree")
        text = re.sub(r'\b(19|20)\d{2}\s*[-–]\s*(19|20)?\d{2}\b', 
                     '[DATE RANGE]', text)
        
        # Remove single years that might indicate age
        # But preserve years in context of "5 years of experience"
        text = re.sub(r'(?<!\d)\b(19|20)\d{2}\b(?!\s*(years?|yrs?))', 
                     '[YEAR]', text)
        
        return text
    
    def audit_evaluation(
        self, 
        scores: List[Dict], 
        demographics: Optional[List[Dict]] = None
    ) -> Dict:
        """
        Perform statistical analysis for adverse impact
        
        Args:
            scores: List of candidate scores with decisions
            demographics: Optional demographic data (only for auditing)
            
        Returns:
            Audit results with compliance indicators
        """
        if not self.audit_enabled:
            return {"audit_enabled": False}
        
        logger.info("Performing bias audit")
        
        audit_results = {
            "audit_date": datetime.utcnow().isoformat(),
            "total_candidates": len(scores),
            "passed_screening": sum(1 for s in scores if s.get("passed", False)),
            "overall_pass_rate": 0.0,
            "adverse_impact_detected": False,
            "findings": []
        }
        
        if audit_results["total_candidates"] > 0:
            audit_results["overall_pass_rate"] = (
                audit_results["passed_screening"] / audit_results["total_candidates"]
            )
        
        # If demographic data is provided, check for adverse impact
        if demographics:
            group_analysis = self._analyze_demographic_groups(scores, demographics)
            audit_results["group_analysis"] = group_analysis
            audit_results["adverse_impact_detected"] = group_analysis["adverse_impact"]
            audit_results["findings"] = group_analysis["findings"]
        
        return audit_results
    
    def _analyze_demographic_groups(
        self, 
        scores: List[Dict], 
        demographics: List[Dict]
    ) -> Dict:
        """
        Analyze pass rates across demographic groups (4/5ths rule)
        
        Note: This should only be done in aggregate for compliance,
        not for individual hiring decisions
        """
        if len(scores) != len(demographics):
            logger.warning("Scores and demographics length mismatch")
            return {"adverse_impact": False, "findings": []}
        
        # Group by demographic category
        groups = {}
        for score, demo in zip(scores, demographics):
            # Aggregate by protected class (example: gender)
            category = demo.get("category", "unknown")
            
            if category not in groups:
                groups[category] = {"total": 0, "passed": 0}
            
            groups[category]["total"] += 1
            if score.get("passed", False):
                groups[category]["passed"] += 1
        
        # Calculate pass rates
        pass_rates = {}
        for group, stats in groups.items():
            if stats["total"] > 0:
                pass_rates[group] = stats["passed"] / stats["total"]
            else:
                pass_rates[group] = 0.0
        
        # Check 4/5ths rule (80% rule)
        if not pass_rates:
            return {"adverse_impact": False, "findings": []}
        
        highest_rate = max(pass_rates.values())
        adverse_impact = False
        findings = []
        
        for group, rate in pass_rates.items():
            ratio = rate / highest_rate if highest_rate > 0 else 1.0
            
            if ratio < self.adverse_impact_threshold:
                adverse_impact = True
                findings.append({
                    "group": group,
                    "pass_rate": round(rate, 3),
                    "impact_ratio": round(ratio, 3),
                    "concern": f"Pass rate below 4/5ths threshold ({self.adverse_impact_threshold})"
                })
        
        return {
            "adverse_impact": adverse_impact,
            "pass_rates": pass_rates,
            "findings": findings,
            "highest_pass_rate": highest_rate
        }
    
    def generate_compliance_report(
        self, 
        audit_results: Dict,
        job_id: int,
        period_start: datetime,
        period_end: datetime
    ) -> str:
        """
        Generate EEOC-compliant documentation
        
        Args:
            audit_results: Results from audit_evaluation
            job_id: Job posting ID
            period_start: Audit period start
            period_end: Audit period end
            
        Returns:
            Formatted compliance report
        """
        report = f"""
EQUAL EMPLOYMENT OPPORTUNITY COMPLIANCE REPORT
==============================================

Job ID: {job_id}
Report Period: {period_start.strftime('%Y-%m-%d')} to {period_end.strftime('%Y-%m-%d')}
Generated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}

SUMMARY STATISTICS
------------------
Total Applicants: {audit_results.get('total_candidates', 0)}
Passed Initial Screening: {audit_results.get('passed_screening', 0)}
Overall Pass Rate: {audit_results.get('overall_pass_rate', 0):.1%}

ADVERSE IMPACT ANALYSIS
-----------------------
Adverse Impact Detected: {'YES' if audit_results.get('adverse_impact_detected') else 'NO'}
Threshold Applied: {self.adverse_impact_threshold} (4/5ths rule)

"""
        
        if audit_results.get("findings"):
            report += "FINDINGS:\n"
            for finding in audit_results["findings"]:
                report += f"\nGroup: {finding['group']}\n"
                report += f"  Pass Rate: {finding['pass_rate']:.1%}\n"
                report += f"  Impact Ratio: {finding['impact_ratio']:.2f}\n"
                report += f"  Concern: {finding['concern']}\n"
        else:
            report += "No adverse impact detected.\n"
        
        report += """
CORRECTIVE ACTIONS
------------------
"""
        
        if audit_results.get('adverse_impact_detected'):
            report += """
- Review job requirements for unnecessary barriers
- Audit question generation for potential bias
- Expand recruitment channels to reach diverse candidates
- Consider additional training for hiring team
- Monitor ongoing metrics for improvement
"""
        else:
            report += "No corrective actions required at this time.\n"
        
        report += """
METHODOLOGY
-----------
This report uses the 4/5ths rule (adverse impact ratio) as specified
in the Uniform Guidelines on Employee Selection Procedures (1978).

All screening decisions are based on job-related criteria and business
necessity. No protected characteristics are used in automated scoring.

"""
        
        return report
    
    def validate_questions(self, questions: List[Dict]) -> Dict:
        """
        Validate interview questions for potential bias
        
        Args:
            questions: List of interview questions
            
        Returns:
            Validation results with flagged questions
        """
        flagged_questions = []
        
        # Prohibited question patterns
        prohibited_patterns = [
            (r'\b(married|spouse|children|kids|family|pregnant)\b', 
             "marital_status/family"),
            (r'\b(age|old|young|birthday|birth year)\b', 
             "age"),
            (r'\b(religion|church|mosque|temple|worship)\b', 
             "religion"),
            (r'\b(country|nationality|citizen|visa|accent)\b', 
             "national_origin"),
            (r'\b(disability|disabled|health|medical)\b', 
             "disability"),
        ]
        
        for i, q in enumerate(questions):
            question_text = q.get("question", "").lower()
            
            for pattern, category in prohibited_patterns:
                if re.search(pattern, question_text):
                    flagged_questions.append({
                        "question_index": i,
                        "question": q.get("question"),
                        "category": category,
                        "reason": f"May elicit information about {category}"
                    })
        
        return {
            "total_questions": len(questions),
            "flagged_count": len(flagged_questions),
            "flagged_questions": flagged_questions,
            "compliant": len(flagged_questions) == 0
        }
