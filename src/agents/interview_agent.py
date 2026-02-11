"""
Video interview agent using LangGraph for adaptive questioning
"""
from typing import Dict, List, TypedDict, Annotated, Optional
from datetime import datetime
import json
from anthropic import Anthropic
from langgraph.graph import StateGraph, END
from loguru import logger

from config.settings import settings


class InterviewState(TypedDict):
    """State for interview workflow"""
    candidate_profile: Dict
    job_role: str
    job_requirements: Dict
    questions: List[Dict]
    current_question_index: int
    responses: List[Dict]
    evaluation_scores: Dict
    next_action: str
    final_score: Optional[float]
    final_evaluation: Optional[Dict]


class VideoInterviewAgent:
    """Conduct adaptive video interviews using LangGraph"""
    
    def __init__(self):
        """Initialize Claude client and build interview graph"""
        self.client = Anthropic(api_key=settings.anthropic_api_key)
        self.graph = self._build_interview_graph()
    
    def _build_interview_graph(self) -> StateGraph:
        """Build LangGraph workflow for interview process"""
        
        workflow = StateGraph(InterviewState)
        
        # Add nodes
        workflow.add_node("generate_questions", self.generate_questions)
        workflow.add_node("ask_question", self.ask_question)
        workflow.add_node("evaluate_response", self.evaluate_response)
        workflow.add_node("adaptive_followup", self.adaptive_followup)
        workflow.add_node("final_evaluation", self.final_evaluation)
        
        # Set entry point
        workflow.set_entry_point("generate_questions")
        
        # Add edges
        workflow.add_edge("generate_questions", "ask_question")
        
        workflow.add_conditional_edges(
            "ask_question",
            self.should_continue_interview,
            {
                "evaluate": "evaluate_response",
                "end": "final_evaluation"
            }
        )
        
        workflow.add_conditional_edges(
            "evaluate_response",
            self.needs_followup,
            {
                "followup": "adaptive_followup",
                "next": "ask_question"
            }
        )
        
        workflow.add_edge("adaptive_followup", "ask_question")
        workflow.add_edge("final_evaluation", END)
        
        return workflow.compile()
    
    def conduct_interview(
        self, 
        candidate_profile: Dict, 
        job_role: str,
        job_requirements: Dict
    ) -> Dict:
        """
        Main method to conduct full interview
        
        Args:
            candidate_profile: Extracted resume data
            job_role: Job title
            job_requirements: Complete job requirements
            
        Returns:
            Final interview evaluation
        """
        logger.info(f"Starting video interview for {job_role}")
        
        initial_state: InterviewState = {
            "candidate_profile": candidate_profile,
            "job_role": job_role,
            "job_requirements": job_requirements,
            "questions": [],
            "current_question_index": 0,
            "responses": [],
            "evaluation_scores": {},
            "next_action": "start",
            "final_score": None,
            "final_evaluation": None
        }
        
        # Run the graph
        final_state = self.graph.invoke(initial_state)
        
        logger.info(f"Interview complete. Final score: {final_state['final_score']}")
        return final_state["final_evaluation"]
    
    def generate_questions(self, state: InterviewState) -> InterviewState:
        """Generate role-specific interview questions using Claude"""
        logger.info("Generating interview questions")
        
        prompt = f"""Generate {settings.max_questions_per_interview} structured interview questions for a {state['job_role']} position.

Candidate background:
{json.dumps(state['candidate_profile'], indent=2)}

Job requirements:
{json.dumps(state['job_requirements'], indent=2)}

Create questions that:
1. Assess technical competency (40% weight)
2. Evaluate problem-solving approach (30% weight)  
3. Test cultural fit and soft skills (20% weight)
4. Verify experience claims (10% weight)

For each question, provide:
- question: The actual question text
- type: technical/behavioral/situational
- category: The skill being assessed
- evaluation_criteria: What to look for in a good answer
- ideal_answer_framework: Key points that should be covered

Return ONLY valid JSON array, no markdown or additional text."""

        try:
            response = self.client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=3000,
                temperature=0.7,
                messages=[{"role": "user", "content": prompt}]
            )
            
            content = response.content[0].text
            # Extract JSON from response
            import re
            json_match = re.search(r'\[.*\]', content, re.DOTALL)
            if json_match:
                questions = json.loads(json_match.group())
            else:
                questions = json.loads(content)
            
            state["questions"] = questions
            state["current_question_index"] = 0
            
            logger.info(f"Generated {len(questions)} questions")
            return state
            
        except Exception as e:
            logger.error(f"Error generating questions: {e}")
            # Fallback questions
            state["questions"] = self._get_fallback_questions(state["job_role"])
            return state
    
    def ask_question(self, state: InterviewState) -> InterviewState:
        """
        Present question to candidate (in production, this would trigger video UI)
        For this implementation, we'll simulate the response
        """
        idx = state["current_question_index"]
        
        if idx < len(state["questions"]):
            current_q = state["questions"][idx]
            logger.info(f"Asking question {idx + 1}: {current_q['question'][:50]}...")
            
            # In production, this would:
            # 1. Display question to candidate
            # 2. Record video response
            # 3. Transcribe audio to text
            # For now, we'll simulate with a placeholder
            
            simulated_response = {
                "question_index": idx,
                "question": current_q["question"],
                "text": "[Candidate response would be transcribed here]",
                "duration_seconds": 180,
                "timestamp": datetime.utcnow().isoformat()
            }
            
            state["responses"].append(simulated_response)
            state["current_question_index"] += 1
        
        return state
    
    def should_continue_interview(self, state: InterviewState) -> str:
        """Determine if more questions should be asked"""
        if state["current_question_index"] < len(state["questions"]):
            # Check if we just asked a question and need to evaluate
            if len(state["responses"]) > len(state["evaluation_scores"]):
                return "evaluate"
            return "evaluate"
        return "end"
    
    def evaluate_response(self, state: InterviewState) -> InterviewState:
        """Evaluate the most recent candidate response"""
        if not state["responses"]:
            return state
        
        current_response = state["responses"][-1]
        idx = current_response["question_index"]
        question = state["questions"][idx]
        
        logger.info(f"Evaluating response to question {idx + 1}")
        
        evaluation_prompt = f"""Evaluate this candidate's interview response:

Question: {question['question']}
Type: {question['type']}
Category: {question['category']}
Evaluation Criteria: {question['evaluation_criteria']}

Candidate Response: {current_response['text']}

Score (0-10) on:
1. Relevance to question
2. Depth of knowledge/experience
3. Communication clarity
4. Specific examples provided
5. Red flags (if any)

Return JSON with:
{{
  "relevance_score": float,
  "depth_score": float,
  "clarity_score": float,
  "examples_score": float,
  "overall_score": float,
  "strengths": ["list of strengths"],
  "weaknesses": ["list of weaknesses"],
  "red_flags": ["list of concerns or empty array"],
  "needs_followup": boolean,
  "followup_reason": "string if needs_followup is true"
}}"""

        try:
            response = self.client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=1500,
                temperature=0,
                messages=[{"role": "user", "content": evaluation_prompt}]
            )
            
            content = response.content[0].text
            import re
            json_match = re.search(r'\{.*\}', content, re.DOTALL)
            if json_match:
                evaluation = json.loads(json_match.group())
            else:
                evaluation = json.loads(content)
            
            state["evaluation_scores"][f"q{idx}"] = evaluation
            
            logger.info(f"Response score: {evaluation['overall_score']}/10")
            return state
            
        except Exception as e:
            logger.error(f"Error evaluating response: {e}")
            # Fallback evaluation
            state["evaluation_scores"][f"q{idx}"] = {
                "overall_score": 5.0,
                "needs_followup": False
            }
            return state
    
    def needs_followup(self, state: InterviewState) -> str:
        """Check if followup question is needed"""
        if not state["evaluation_scores"]:
            return "next"
        
        last_eval_key = f"q{len(state['responses']) - 1}"
        last_eval = state["evaluation_scores"].get(last_eval_key, {})
        
        # Follow up if answer was weak or had red flags
        if last_eval.get("needs_followup", False):
            return "followup"
        
        return "next"
    
    def adaptive_followup(self, state: InterviewState) -> InterviewState:
        """Generate adaptive followup question based on previous response"""
        logger.info("Generating followup question")
        
        last_response = state["responses"][-1]
        last_eval_key = f"q{len(state['responses']) - 1}"
        last_eval = state["evaluation_scores"].get(last_eval_key, {})
        
        followup_prompt = f"""Generate a targeted followup question based on this interaction:

Original Question: {last_response['question']}
Candidate Response: {last_response['text']}
Evaluation: {json.dumps(last_eval, indent=2)}

Create a followup question that:
- Probes deeper into areas that were unclear
- Asks for specific examples if none were provided
- Clarifies any concerning statements

Return JSON with same structure as original questions."""

        try:
            response = self.client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=800,
                temperature=0.7,
                messages=[{"role": "user", "content": followup_prompt}]
            )
            
            content = response.content[0].text
            import re
            json_match = re.search(r'\{.*\}', content, re.DOTALL)
            if json_match:
                followup_q = json.loads(json_match.group())
            else:
                followup_q = json.loads(content)
            
            # Insert followup question after current question
            state["questions"].insert(
                state["current_question_index"],
                followup_q
            )
            
            return state
            
        except Exception as e:
            logger.error(f"Error generating followup: {e}")
            return state
    
    def final_evaluation(self, state: InterviewState) -> InterviewState:
        """Generate comprehensive final evaluation"""
        logger.info("Generating final evaluation")
        
        final_prompt = f"""Provide a comprehensive evaluation of this interview:

Job Role: {state['job_role']}
Candidate Profile: {json.dumps(state['candidate_profile'], indent=2)}
Questions Asked: {len(state['questions'])}
Individual Scores: {json.dumps(state['evaluation_scores'], indent=2)}

Provide overall assessment:
{{
  "technical_competency_score": float (0-10),
  "problem_solving_score": float (0-10),
  "communication_score": float (0-10),
  "cultural_fit_score": float (0-10),
  "overall_score": float (0-10),
  "recommendation": "STRONG_HIRE / HIRE / MAYBE / NO_HIRE",
  "key_strengths": ["list"],
  "key_concerns": ["list"],
  "summary": "2-3 sentence summary",
  "next_steps": "recommended action"
}}"""

        try:
            response = self.client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=2000,
                temperature=0,
                messages=[{"role": "user", "content": final_prompt}]
            )
            
            content = response.content[0].text
            import re
            json_match = re.search(r'\{.*\}', content, re.DOTALL)
            if json_match:
                final_eval = json.loads(json_match.group())
            else:
                final_eval = json.loads(content)
            
            state["final_score"] = final_eval["overall_score"]
            state["final_evaluation"] = final_eval
            
            return state
            
        except Exception as e:
            logger.error(f"Error in final evaluation: {e}")
            # Calculate simple average as fallback
            scores = [eval_data.get("overall_score", 0) 
                     for eval_data in state["evaluation_scores"].values()]
            avg_score = sum(scores) / len(scores) if scores else 0
            
            state["final_score"] = avg_score
            state["final_evaluation"] = {
                "overall_score": avg_score,
                "recommendation": "MAYBE" if avg_score >= 5 else "NO_HIRE"
            }
            return state
    
    def _get_fallback_questions(self, job_role: str) -> List[Dict]:
        """Fallback questions if generation fails"""
        return [
            {
                "question": f"Tell me about your experience relevant to this {job_role} position.",
                "type": "behavioral",
                "category": "experience",
                "evaluation_criteria": "Relevance, depth, specific examples",
                "ideal_answer_framework": "Specific projects, measurable outcomes"
            },
            {
                "question": "Describe a challenging technical problem you solved recently.",
                "type": "technical",
                "category": "problem_solving",
                "evaluation_criteria": "Problem complexity, approach, outcome",
                "ideal_answer_framework": "Clear problem statement, systematic approach"
            },
            {
                "question": "How do you approach learning new technologies?",
                "type": "behavioral",
                "category": "adaptability",
                "evaluation_criteria": "Learning strategy, examples",
                "ideal_answer_framework": "Structured approach, specific examples"
            }
        ]
