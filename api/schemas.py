from pydantic import BaseModel
from typing import Optional, Dict, Any, List

class GenerateRequest(BaseModel):
    subject: str
    level: str
    paper: str
    topic_or_type: List[str]
    include_answer_key: bool = True
    prescribed_texts: Optional[List[str]] = None

class GenerateResponse(BaseModel):
    exam_text: str
    answer_key: Optional[str] = None
    grade_boundaries: Optional[str] = None
    metadata: Dict[str, Any]


class EvaluateRequest(BaseModel):
    subject: str
    level: str
    paper: str
    question: str                          # The specific prompt/question the student answered
    student_essay: str                     # The essay text
    mark_scheme: Optional[str] = ""       # AI-generated mark scheme (if available)
    prescribed_texts: Optional[List[str]] = []  # For English Lit A

class EvaluateResponse(BaseModel):
    evaluation: str                        # Full markdown evaluation from LLM
    metadata: Dict[str, Any]
