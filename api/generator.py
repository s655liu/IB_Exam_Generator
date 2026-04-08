import os
import json
import requests
from typing import Dict, Any
from dotenv import load_dotenv
from schemas import GenerateRequest, GenerateResponse

# Load .env for local development
load_dotenv(os.path.join(os.path.dirname(__file__), '.env'))

QWEN_API_KEY = os.getenv("QWEN_API_KEY")
QWEN_BASE_URL = os.getenv("QWEN_BASE_URL", "https://dashscope-intl.aliyuncs.com/compatible-mode/v1")

# Load exam specs — same directory as this file
SPECS_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "exam_specs.json")
try:
    if not QWEN_API_KEY:
        print("WARNING: QWEN_API_KEY not found in environment variables!")
    with open(SPECS_PATH, "r", encoding="utf-8", errors="replace") as f:
        EXAM_SPECS = json.load(f)
except Exception as e:
    print(f"Error loading exam_specs.json: {e}")
    EXAM_SPECS = {}

def get_ib_specs(subject: str, level: str, paper: str) -> Dict[str, Any]:
    specs = {
        "duration": 60,
        "total_marks": 40,
        "question_count_range": "5-10",
        "command_terms": ["Explain", "Describe", "Analyze", "Evaluate"],
        "structure_desc": "Standard IB question format"
    }
    try:
        if subject in EXAM_SPECS and level in EXAM_SPECS[subject] and paper in EXAM_SPECS[subject][level]:
            data = EXAM_SPECS[subject][level][paper]
            specs.update({
                "duration": data.get("duration_minutes", 60),
                "total_marks": data.get("total_marks", 40),
                "question_count_range": str(data.get("typical_question_count", "5-10")),
                "command_terms": data.get("command_terms", specs["command_terms"]),
                "structure_desc": data.get("question_structure", {}).get("description", specs["structure_desc"]),
                "calculator": data.get("calculator", False)
            })
    except Exception as e:
        print(f"Error parsing specs for {subject} {level} {paper}: {e}")
    return specs

def get_subject_specific_instructions(subject: str, paper: str, specs: Dict[str, Any]) -> str:
    instructions = ""
    calc_str = "CALCULATOR ALLOWED (GDC)" if specs.get("calculator") else "NO CALCULATORS ALLOWED"
    if "Math" in subject:
        instructions = f"- **{calc_str}**.\n- Show all working clearly.\n- Use LaTeX for all mathematical notation (e.g., $x^{{2}}$, $\\frac{{a}}{{b}}$).\n- **DIFFICULTY PROGRESSION**: \n  1. Ensure each multi-part question follows a 'low floor, high ceiling' approach—starting with accessible marks and concluding with more demanding proofs or problem-solving.\n  2. The paper should grow in complexity, moving from standard routine problems to non-routine or unfamiliar contexts (especially for Section B)."
    elif "History" in subject:
        if "Paper 1" in paper:
            instructions = "- Provide 4 source-based questions.\n- Include brief placeholders/descriptions for 4 sources (Source A, B, C, D)."
        else:
            instructions = "- Provide essay prompts following IB command terms."
    elif "English" in subject:
        instructions = "- Provide a short unseen literary passage description followed by guiding questions."
    elif subject in ["Physics", "Chemistry", "Biology"]:
        instructions = f"- **{calc_str}**.\n- Reference relevant data from the IB {subject} Data Booklet.\n- **DIFFICULTY GRADIENT (SCALING)**: \n  1. Within each multi-part question, parts (a), (b), (c), etc., must strictly increase in difficulty and cognitive demand (e.g., recall → application → complex evaluation).\n  2. The overall paper should be structured so that earlier questions are more accessible, while later questions increasingly require synthesis of multiple topics and higher-order thinking."
    return instructions

def build_prompt(request: GenerateRequest) -> str:
    specs = get_ib_specs(request.subject, request.level, request.paper)
    subject_instr = get_subject_specific_instructions(request.subject, request.paper, specs)
    focus_areas = ", ".join(request.topic_or_type)
    prompt = f"""Generate an authentic International Baccalaureate (IB) {request.subject} {request.level} {request.paper} examination.

EXAM SPECIFICATIONS:
- Duration: {specs['duration']} minutes
- Total marks: {specs['total_marks']}
- Typical structure: {specs['structure_desc']}
- Command terms to prioritize: {', '.join(specs['command_terms'])}
- Focus areas: {focus_areas}

REQUIREMENTS:
1. Follow official IB Diploma Programme formatting and style.
2. Distribute marks according to IB patterns (1-2 for knowledge, 3-5 for application/analysis, 6-10 for evaluation).
3. Ensure total marks sum exactly to {specs['total_marks']}.
4. Use clear, concise language appropriate for Grade 11-12 students.
5. If multiple focus areas are provided, create a balanced exam covering all of them.
6. **STRICT CONSTRAINT**: Do not generate any questions that require the student to draw a diagram, graph, or sketch. All questions must be answerable using only text and mathematical notation.
{subject_instr}

FORMAT:
---EXAM---
[Full exam paper with mark allocations in square brackets at the end of each question, e.g., [4]]

{f'---ANSWER KEY---\\n[Provide a COMPLETE and DETAILED mark scheme for EVERY question.]' if request.include_answer_key else ''}

---GRADE BOUNDARIES---
[Provide a table or list mapping raw marks to IB Grades 1-7 based on the paper's total of {specs['total_marks']}. 
Suggested standard thresholds: 7 (80%+), 6 (70%+), 5 (60%+), 4 (50%+), 3 (40%+). 
Label this section clearly as "Official Grade Boundaries".]
"""
    return prompt

async def call_qwen_api(prompt: str) -> str:
    headers = {
        "Authorization": f"Bearer {QWEN_API_KEY}",
        "X-DashScope-ApiKey": QWEN_API_KEY,
        "Content-Type": "application/json"
    }
    payload = {
        "model": "qwen-turbo",
        "messages": [
            {"role": "system", "content": "You are an expert IB Senior Examiner responsible for creating official examination papers. Your output is always complete and never truncated."},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.5,
        "max_tokens": 4000
    }
    response = requests.post(f"{QWEN_BASE_URL}/chat/completions", headers=headers, json=payload)
    if response.status_code != 200:
        error_detail = response.json() if response.content else "No detail"
        raise Exception(f"Qwen API Error {response.status_code}: {error_detail}")
    return response.json()["choices"][0]["message"]["content"]

def parse_response(content: str):
    exam_text = content
    answer_key = None
    grade_boundaries = None

    boundary_seps = ["---GRADE BOUNDARIES---", "GRADE BOUNDARIES", "---OFFICIAL GRADE BOUNDARIES---"]
    for sep in boundary_seps:
        if sep in content:
            parts = content.split(sep, 1)
            content = parts[0]
            grade_boundaries = parts[1].strip()
            break

    key_seps = ["---ANSWER KEY---", "ANSWER KEY", "---MARK SCHEME---", "MARK SCHEME"]
    for sep in key_seps:
        if sep in content:
            parts = content.split(sep, 1)
            exam_text = parts[0].replace("---EXAM---", "").strip()
            answer_key = parts[1].strip()
            break
    else:
        exam_text = content.replace("---EXAM---", "").strip()

    return exam_text, answer_key, grade_boundaries
