from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from schemas import GenerateRequest, GenerateResponse
from generator import build_prompt, call_qwen_api, parse_response
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="IB Exam Generator API")

# Enable CORS for frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify your frontend origin
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/api/generate-exam", response_model=GenerateResponse)
async def generate_exam(request: GenerateRequest):
    try:
        logger.info(f"Generating IB {request.subject} {request.level} {request.paper} - Topic: {request.topic_or_type}")
        
        # 1. Build the prompt
        prompt = build_prompt(request)
        
        # 2. Call Qwen API
        content = await call_qwen_api(prompt)
        
        # 3. Parse the response
        exam_text, answer_key, grade_boundaries = parse_response(content)
        
        # 4. Prepare response metadata
        metadata = {
            "subject": request.subject,
            "level": request.level,
            "paper": request.paper,
            "topic_or_type": request.topic_or_type,
            "generated_at": datetime.now().isoformat(),
            "model": "qwen-turbo"
        }
        
        return GenerateResponse(
            exam_text=exam_text,
            answer_key=answer_key,
            grade_boundaries=grade_boundaries,
            metadata=metadata
        )
        
    except Exception as e:
        logger.error(f"Error generating exam: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Generation failed: {str(e)}")

@app.get("/api/health")
def health_check():
    return {"status": "ok"}
