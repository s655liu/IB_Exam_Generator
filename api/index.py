import os
import sys
import logging

# Ensure sibling modules (generator, schemas) are importable on Vercel
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), '.env'))

from generator import build_prompt, call_qwen_api, parse_response
from schemas import GenerateRequest, GenerateResponse

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="IB Exam Generator API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/api/health")
async def health_check():
    return {"status": "ok"}

@app.post("/api/generate-exam", response_model=GenerateResponse)
async def generate_exam(request: GenerateRequest):
    logger.info(f"Generating IB {request.subject} {request.level} {request.paper} - Topic: {request.topic_or_type}")
    try:
        prompt = build_prompt(request)
        content = await call_qwen_api(prompt)
        exam_text, answer_key, grade_boundaries = parse_response(content)
        metadata = {
            "subject": request.subject,
            "level": request.level,
            "paper": request.paper,
            "topics": request.topic_or_type,
        }
        return GenerateResponse(
            exam_text=exam_text,
            answer_key=answer_key,
            grade_boundaries=grade_boundaries,
            metadata=metadata
        )
    except Exception as e:
        logger.error(f"Error generating exam: {e}")
        raise HTTPException(status_code=500, detail=str(e))
