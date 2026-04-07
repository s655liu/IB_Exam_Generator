from pydantic import BaseModel
from typing import Optional, Dict, Any, List

class GenerateRequest(BaseModel):
    subject: str
    level: str
    paper: str
    topic_or_type: List[str]
    include_answer_key: bool = True

class GenerateResponse(BaseModel):
    exam_text: str
    answer_key: Optional[str] = None
    grade_boundaries: Optional[str] = None
    metadata: Dict[str, Any]
