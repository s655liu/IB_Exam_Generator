import os
import json
import requests
import re
from typing import Dict, Any
from dotenv import load_dotenv
from schemas import GenerateRequest, GenerateResponse
from skills.registry import get_skill

# Load .env for local development
load_dotenv(os.path.join(os.path.dirname(__file__), '.env'))

QWEN_API_KEY = os.getenv("QWEN_API_KEY")
QWEN_BASE_URL = os.getenv("QWEN_BASE_URL", "https://dashscope-intl.aliyuncs.com/compatible-mode/v1")

# Path to exam specs
SPECS_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "exam_specs.json")


def load_specs():
    try:
        with open(SPECS_PATH, "r", encoding="utf-8", errors="replace") as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading exam_specs.json: {e}")
        return {}


def get_ib_specs(subject: str, level: str, paper: str) -> Dict[str, Any]:
    current_specs_data = load_specs()
    specs = {
        "duration": 120 if "HL" in level else 105 if any(l in subject for l in ["French", "Spanish", "Mandarin"]) else 60,
        "total_marks": 65 if "HL" in level else 40,
        "question_count": "5-10",
        "command_terms": ["Explain", "Describe", "Analyze", "Evaluate"],
        "structure_desc": "Standard IB question format"
    }
    try:
        # Normalize subject/paper keys
        subj_key = subject.replace(" ", "_").replace("-", "_")
        if "Math AA" in subject: subj_key = "Mathematics_AA"
        if "English Literature A" in subject: subj_key = "English_Literature_A"
        if "Mandarin B" in subject: subj_key = "Mandarin_B"
        if "French B" in subject: subj_key = "French_B"
        if "Spanish B" in subject: subj_key = "Spanish_B"

        paper_key = paper.replace(" ", "_").lower()
        if "1a" in paper_key: paper_key = "paper_1A"
        if "1b" in paper_key: paper_key = "paper_1B"

        # Check for subject directly (Standard)
        subject_data = current_specs_data.get(subj_key)

        # Check for subject inside groups (e.g., Sciences)
        if not subject_data:
            for group_name, group_data in current_specs_data.items():
                if isinstance(group_data, dict) and subject in group_data.get("subjects", []):
                    subject_data = group_data
                    break

        if subject_data and level in subject_data and paper_key in subject_data[level]:
            data = subject_data[level][paper_key]

            # Extract question count (handle integer or range)
            q_count = data.get("question_count")
            if not q_count:
                q_range = data.get("question_count_range")
                if isinstance(q_range, dict):
                    q_count = f"{q_range.get('min')}-{q_range.get('max')}"
                else:
                    q_count = "5-10"

            specs.update({
                "duration": data.get("duration_minutes", specs["duration"]),
                "total_marks": data.get("total_marks", specs["total_marks"]),
                "question_count": str(q_count),
                "command_terms": data.get("command_terms", specs["command_terms"]),
                "structure_type": data.get("structure", {}).get("type", "structured"),
                "structure_desc": data.get("question_structure", {}).get("description",
                                  data.get("structure", {}).get("description", specs["structure_desc"])),
                "calculator": data.get("calculator_allowed", data.get("calculator", False))
            })
    except Exception as e:
        print(f"Error parsing specs for {subject} {level} {paper}: {e}")
    return specs


def build_prompt(request: GenerateRequest) -> str:
    # 1. Load base specs from JSON
    specs = get_ib_specs(request.subject, request.level, request.paper)
    specs["selected_skills"] = request.topic_or_type

    # 2. Resolve the skill for this subject
    skill = get_skill(request.subject)

    # 3. Get overrides (structure_rule, model_essay_req, specs_overrides)
    overrides = skill.get_prompt_overrides(request, specs)

    # 4. Apply any spec-level overrides (e.g. History P2 resets total_marks)
    specs.update(overrides.get("specs_overrides", {}))

    # 5. Get subject-specific LLM instructions
    subject_instr = skill.get_instructions(request.level, request.paper, specs)

    # 6. Unpack structure fields
    structure_rule = overrides.get(
        "structure_rule",
        f"\n- **STRICT QUESTION COUNT**: The exam MUST contain EXACTLY {specs['question_count']} questions/tasks."
    )
    model_essay_req = overrides.get("model_essay_req", "")
    output_lang = skill.output_language

    # 7. Determine whether to include a mark scheme section
    #    Skills can force it on (Math, Science, Language) regardless of the UI toggle.
    force_mark_scheme = overrides.get("force_mark_scheme", False)
    include_mark_scheme = request.include_answer_key or force_mark_scheme

    # 8. Build the mark scheme instruction for the FORMAT block
    mark_scheme_instr = overrides.get(
        "mark_scheme_instr",
        "[Provide a COMPLETE and DETAILED mark scheme for EVERY question here. "
        "For Math and Science: show FULL WORKED SOLUTIONS with every algebraic step, "
        "the FINAL NUMERICAL ANSWER with correct units, and mark allocation per step "
        "(e.g., M1 = method mark, A1 = accuracy mark, A0 = wrong answer). "
        "Do NOT write 'correct answer' or 'correct calculation' — write the ACTUAL answer.]"
    )

    prompt = f"""Generate an authentic International Baccalaureate (IB) {request.subject} {request.level} {request.paper} examination.

EXAM SPECIFICATIONS:
- Duration: {specs['duration']} minutes
- Total marks: {specs['total_marks']}
- Typical structure: {specs['structure_desc']}{structure_rule}
- Command terms to prioritize: {', '.join(specs['command_terms'])}
- Focus areas: {', '.join(request.topic_or_type)}

REQUIREMENTS:
1. Follow official IB Diploma Programme formatting and style.
2. Distribute marks according to IB patterns (1-2 for knowledge, 3-5 for application/analysis, 6-10 for evaluation).
3. Ensure total marks sum exactly to {specs['total_marks']}.
4. Use clear, concise language appropriate for Grade 11-12 students.
5. If multiple focus areas are provided, create a balanced exam covering all of them.
6. **STRICT QUESTION LIMIT**: Do NOT exceed {specs['question_count']} questions/options. If the spec says {specs['question_count']}, you MUST provide exactly that many. 
7. **TABLES**: Use standard Markdown tables for data.
   - **STRICT**: Each row MUST be on a new line.
   - **STRICT**: You MUST include the separator row (e.g., `|---|---|`).
   - **STRICT**: Do NOT use double pipes `||` inside tables.
8. **DIAGRAMS**: Use visual aids for **ALL** subjects inside ```mermaid ``` or ```svg ``` blocks.
   - **History/Business/ITGS**: Use Mermaid for timelines, network diagrams, or organizational charts. Use `theme: base` with high contrast.
   - **Math/Sci/Geography**: Use SVG for coordinate graphs, maps, circuits, or chemical structures.
   - **SVG QUALITY**: All graphs MUST include clear X/Y axes, tick marks, labels, and units. Use a professional style with `stroke="#1e293b"` (dark blue/black) to ensure visibility on white paper.
   - **Language/Social Sciences**: Use SVG for situational illustrations or Mermaid for logic flows.
   - **STRICT**: Only Mermaid.js and raw SVG are supported. Keep diagrams clear and professional.
9. **MATHEMATICAL NOTATION**: For every formula, symbol, or equation:
   - Inline math  → LATEX<<formula>>       e.g. LATEX<<x^{{2}} + y^{{2}} = r^{{2}}>>
   - Display math → LATEXBLOCK<<formula>>  e.g. LATEXBLOCK<<\\frac{{-b \\pm \\sqrt{{b^{{2}}-4ac}}}}{{2a}}>>
   - Use standard LaTeX commands inside the delimiters (fractions, integrals, roots, etc.).
   - **STRICT**: NEVER write bare LaTeX outside these wrappers (no raw \\sqrt, \\frac, $x^2$, etc.).
10. **STRICT LANGUAGE REQUIREMENT**: This is a {request.subject} exam. The ENTIRE exam (Instructions, Section Headers, Questions, Texts, and Mark Scheme) MUST be written in {output_lang}. Do NOT use English unless the subject name is English.
11. **MODEL ESSAY / ANSWERS**: All sample answers must be in {output_lang}.

{subject_instr}{model_essay_req}

FORMAT:
You MUST use these exact headers on their own lines to separate sections:
[SECTION_EXAM]
[Full exam paper content here]

{('[SECTION_MARK_SCHEME]' + chr(10) + mark_scheme_instr) if include_mark_scheme else ''}

[SECTION_GRADE_BOUNDARIES]
[Provide the Markdown table mapping raw marks to IB Grades here.]
"""
    # ── DEBUG: print the full prompt to the API terminal ──────────────────
    print("\n" + "=" * 80)
    print("PROMPT SENT TO LLM")
    print("=" * 80)
    print(prompt)
    print("=" * 80 + "\n")
    # ──────────────────────────────────────────────────────────────────────
    return prompt


async def call_qwen_api(prompt: str) -> str:
    headers = {
        "Authorization": f"Bearer {QWEN_API_KEY}",
        "X-DashScope-ApiKey": QWEN_API_KEY,
        "Content-Type": "application/json"
    }
    payload = {
        "model": "qwen-max",
        "messages": [
            {"role": "system", "content": "You are an expert IB Senior Examiner. You specialize in creating demanding, high-quality examination papers that strictly adhere to official IB length and complexity requirements. You never truncate content; you provide full, detailed reading texts and transcripts as requested."},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.7,
        "max_tokens": 6000
    }
    response = requests.post(f"{QWEN_BASE_URL}/chat/completions", headers=headers, json=payload)
    if response.status_code != 200:
        error_detail = response.json() if response.content else "No detail"
        raise Exception(f"Qwen API Error {response.status_code}: {error_detail}")
    return response.json()["choices"][0]["message"]["content"]


def parse_response(content: str):
    exam_text = content
    answer_key = ""
    grade_boundaries = ""

    # Case-insensitive split for sections using regex
    def split_section(text, tags):
        for tag in tags:
            pattern = re.compile(re.escape(tag), re.IGNORECASE)
            match = pattern.search(text)
            if match:
                return text[:match.start()], text[match.end():]
        return text, None

    # Split from bottom up
    # 1. Split Grade Boundaries
    remaining, grade_boundaries = split_section(content, ["[SECTION_GRADE_BOUNDARIES]", "---GRADE BOUNDARIES---", "GRADE BOUNDARIES"])

    if grade_boundaries is None: grade_boundaries = ""
    else: grade_boundaries = grade_boundaries.strip()

    # 2. Split Answer Key from the remaining top part
    exam_part, answer_part = split_section(remaining, ["[SECTION_MARK_SCHEME]", "---ANSWER KEY---", "ANSWER KEY", "MARK SCHEME"])

    if answer_part:
        exam_text = exam_part.replace("[SECTION_EXAM]", "").replace("---EXAM---", "").strip()
        answer_key = answer_part.strip()
    else:
        exam_text = exam_part.replace("[SECTION_EXAM]", "").replace("---EXAM---", "").strip()
        answer_key = ""

    return exam_text, answer_key, grade_boundaries
