import os
import json
import requests
import re
from typing import Dict, Any
from dotenv import load_dotenv
from schemas import GenerateRequest, GenerateResponse

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
        # 1. Normalize subject/paper keys
        subj_key = subject.replace(" ", "_").replace("-", "_")
        if "Math AA" in subject: subj_key = "Mathematics_AA"
        if "English Literature A" in subject: subj_key = "English_Literature_A"
        if "Mandarin B" in subject: subj_key = "Mandarin_B"
        if "French B" in subject: subj_key = "French_B"
        if "Spanish B" in subject: subj_key = "Spanish_B"
        
        paper_key = paper.replace(" ", "_").lower()
        if "1a" in paper_key: paper_key = "paper_1A"
        if "1b" in paper_key: paper_key = "paper_1B"
        
        # 1. Check for subject directly (Standard)
        subject_data = current_specs_data.get(subj_key)
        
        # 2. Check for subject inside groups (e.g., Sciences)
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
                    q_count = "5-10" # Fallback

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

def get_subject_specific_instructions(subject: str, level: str, paper: str, specs: Dict[str, Any]) -> str:
    instructions = ""
    calc_str = "CALCULATOR ALLOWED (GDC)" if specs.get("calculator") else "NO CALCULATORS ALLOWED"
    
    # Determine target language for Language B subjects
    target_lang = "English"
    if any(lang in subject for lang in ["French", "Spanish", "Mandarin", "Japanese", "Language"]):
        target_lang = subject.replace(" B", "").replace(" Ab Initio", "")
        if "Mandarin" in target_lang: target_lang = "Chinese (Simplified)"
    
    if "Math" in subject:
        instructions = f"- **{calc_str}**.\n- Show all working clearly.\n- Use LaTeX for all mathematical notation (e.g., $x^{{2}}$, $\\frac{{a}}{{b}}$).\n- Use SVG for coordinate graphs, geometric shapes, and statistical charts where appropriate.\n- **DIFFICULTY PROGRESSION**: \n  1. Ensure each multi-part question follows a 'low floor, high ceiling' approach—starting with accessible marks and concluding with more demanding proofs or problem-solving.\n  2. The paper should grow in complexity, moving from standard routine problems to non-routine or unfamiliar contexts (especially for Section B)."
    elif "History" in subject:
        if "Paper 1" in paper:
            instructions = "- Provide 4 source-based questions.\n- Include brief placeholders/descriptions for 4 sources (Source A, B, C, D).\n- Use Mermaid or SVG to provide timelines or source hierarchy diagrams."
        elif "Paper 2" in paper:
            instructions = (
                "- **STRICT TOPIC STRUCTURE**: For EACH of the focus areas (topics) provided, you MUST generate EXACTLY two questions.\n"
                "- **STRICT COMPARISON**: EVERY question MUST be comparative. Questions must require the student to compare and contrast at least two different leaders, states, or regions.\n"
                "- **MARKS**: Each question is worth exactly 15 marks.\n"
                "- **DEPTH**: Questions should focus on 20th-century world history themes (Authoritarian States, Cold War, etc.) as requested."
            )
        else:
            instructions = "- Provide essay prompts following IB command terms."
    elif any(lang in subject for lang in ["French", "Spanish", "Mandarin", "Japanese", "Language"]):
        target_lang = subject.replace(" B", "").replace(" Ab Initio", "")
        if "Mandarin" in target_lang: target_lang = "Chinese (Simplified)"
        
        lang_instr = f"- **STRICT LANGUAGE REQUIREMENT**: This is a {subject} exam. EVERYTHING (Instructions, Section Headers, Questions, and Transcripts/Texts) MUST be written in {target_lang}. Do NOT use English for any part of the exam content."
        
        if "Paper 1" in paper:
            instructions = f"{lang_instr}\n- Provide three specific writing prompts in {target_lang}.\n- Students must choose ONE and produce a piece of writing in {target_lang}.\n- Ensure each prompt specifies a clear text type (e.g., blog, email, report)."
        elif "Paper 2" in paper:
            # Language B Level-specific length requirements
            # We use 1200 characters for Mandarin B HL to match official complexity (e.g. Zhang Xiaofeng's style)
            if "Mandarin" in target_lang and level == "HL":
                len_instr = "1200 characters (MUST be extremely detailed and complex, matching the length of a professional literary essay)"
            else:
                len_instr = "450-600 words"

            instructions = (
                f"{lang_instr}\n"
                "- **RECEPTIVE FOCUS**: This paper tests Listening and Reading Comprehension only. NO WRITING TASKS.\n"
                f"- **SECTION A (LISTENING - 60 min)**: Provide THREE distinct listening transcripts in {target_lang}. **STRICT**: Each transcript MUST be a minimum of {len_instr}. Do NOT summarize.\n"
                "  - **AUDIO PLAYER**: Wrap the ENTIRE transcript within triple backtick code blocks with the language tag 'audio' (e.g., ```audio [transcript text] ```). **NEVER** use brackets like [PLAYABLE_AUDIO].\n"
                "  - **COMPLEXITY**: Passages must be academically demanding, including nuanced arguments and varying opinions.\n"
                "  - **QUESTIONS (25 marks)**: Include detailed questions in {target_lang} on tone, purpose, and inference.\n"
                f"- **SECTION B (READING - 60 min)**: Provide THREE authentic-style reading texts in {target_lang}.\n"
                f"  - **LENGTH**: Each HL text MUST be a minimum of {len_instr}. **CRITICAL**: Use high-level academic vocabulary and deep literary analysis.\n"
                "  - **QUESTIONS (40 marks)**: Focus on higher-order thinking in {target_lang}.\n"
                "- **STRICT**: Each section MUST sum to the following: Section A = 25 marks, Section B = 40 marks. Total = {specs.get('total_marks', 65)} marks.\n"
                "- **NO DICTIONARY**: Instruction (in {target_lang}): 'Do not use a dictionary.'\n"
                "- **PLAYBACK**: Instruction (in {target_lang}): 'You will hear each passage twice. You may take notes.'"
            )
        else:
            instructions = f"- Provide contextual situational prompts in {target_lang}."
    elif subject == "Geography":
        instructions = "- Use SVG for simple maps, demographic cycles, climate graphs, or landform diagrams."
    elif subject in ["ITGS", "Business"]:
        instructions = "- Use Mermaid for network diagrams, flowcharts, or organizational charts.\n- For Business, use SVG for supply/demand curves or break-even charts where appropriate."
    elif subject in ["Physics", "Chemistry", "Biology"]:
        instructions = f"- **{calc_str}**.\n- Reference relevant data from the IB {subject} Data Booklet."
        if "Paper 1A" in paper:
            instructions += "\n- **FORMAT**: Multiple Choice Questions only.\n- Provide 4 options (A, B, C, D) for each question.\n- Focus on core conceptual understanding and quick calculations."
        elif "Paper 1B" in paper:
            instructions += f"\n- **FORMAT**: Data analysis and experimental design questions.\n- **STRICT**: This is NOT multiple choice. Provide structured questions requiring written analysis.\n- **TABLES**: Present experimental data in standard Markdown tables (properly formatted with newlines).\n- **SKILLS FOCUS**: Focus heavily on the following selected skills: {', '.join(specs.get('selected_skills', [])) if 'selected_skills' in specs else 'general experimental design'}.\n- Include questions on: error analysis, graph interpretation, variable identification, and methodology evaluation.\n- Use SVG for experimental setups or data plots."
        
        instructions += f"\n- **DIFFICULTY GRADIENT (SCALING)**: \n  1. Within each multi-part question, parts (a), (b), (c), etc., must strictly increase in difficulty and cognitive demand (e.g., recall → application → complex evaluation).\n  2. The overall paper should be structured so that earlier questions are more accessible, while later questions increasingly require synthesis of multiple topics and higher-order thinking."
    return instructions

def build_prompt(request: GenerateRequest) -> str:
    specs = get_ib_specs(request.subject, request.level, request.paper)
    # Pass selected topics/skills into the instructions generator
    specs['selected_skills'] = request.topic_or_type
    
    subject_instr = get_subject_specific_instructions(request.subject, request.level, request.paper, specs)
    
    # Determine output language for requirements
    output_lang = "English"
    if any(lang in request.subject for lang in ["French", "Spanish", "Mandarin", "Japanese", "Language"]):
        output_lang = request.subject.replace(" B", "").replace(" Ab Initio", "")
        if "Mandarin" in output_lang: output_lang = "Chinese (Simplified)"
        
    focus_areas = ", ".join(request.topic_or_type)
    
    # Specific logic for choice-based papers
    structure_rule = ""
    model_essay_req = ""
    
    # Override for History Paper 2
    if request.subject == "History" and "Paper 2" in request.paper:
        specs['total_marks'] = 30
        specs['question_count'] = len(request.topic_or_type) * 2
        specs['structure_desc'] = "Answer two questions. Each question must be selected from a different topic."
        structure_rule = f"\n- **STRICT QUESTION COUNT**: You MUST provide EXACTLY {specs['question_count']} questions (2 questions per topic). The user will choose 2 questions, each from a different topic."
        model_essay_req = "\n- **MODEL ESSAY**: Inside the [SECTION_MARK_SCHEME], you MUST provide ONE FULL, HIGH-LEVEL sample essay response (approx 800-1000 words in analysis) for at least one of the generated prompts."
    
    elif specs.get("structure_type") == "receptive":
        structure_rule = (
            f"\n- **STRICT RECEPTIVE FORMAT**: This is a {specs['duration']}-minute comprehension paper. Do NOT include any writing tasks.\n"
            "- **TRANSCRIPTS**: You MUST provide the full text transcripts for the Section A Listening passages. Wrap EACH transcript in triple backtick code blocks with the language tag 'audio'.\n"
            "- **AUTHENTIC TEXTS**: You MUST provide the full reading texts for Section B.\n"
            "- **NO DICTIONARY**: Instruction: 'Do not use a dictionary.'\n"
            "- **PLAYBACK**: Instruction: 'You will hear each passage twice.'"
        )
        model_essay_req = "\n- **MODEL ANSWERS**: Inside the [SECTION_MARK_SCHEME], provide a complete answer key for every question. No essay is required for receptive papers."
    
    elif specs.get("structure_type") in ["essay_choice", "essay_based", "short_and_extended_response"]:
        structure_rule = f"\n- **STRICT QUESTION COUNT**: You MUST provide EXACTLY {specs['question_count']} essay prompts/options. The user will choose 1 of these {specs['question_count']} prompts."
        model_essay_req = "\n- **MODEL ESSAY & GRADING**: Inside the [SECTION_MARK_SCHEME], you MUST provide ONE FULL, HIGH-LEVEL sample essay response for at least one of the generated prompts. IMMEDIATELY FOLLOWING the essay, provide a detailed **EXAMINER COMMENTARY AND GRADE**. Break down the marks for each IB Criterion (e.g., Criterion A, B, C, D) and provide a 2-3 sentence justification for the marks in each category."
        if request.prescribed_texts and len(request.prescribed_texts) >= 2:
            texts_str = " and ".join([t for t in request.prescribed_texts if t.strip()])
            if texts_str:
                structure_rule += f"\n- **CUSTOM CONTEXT**: The student has specifically studied: {texts_str}. Tailor the essay prompts to be highly relevant to exploring themes, techniques, or contexts found in these works."
    else:
        structure_rule = f"\n- **STRICT QUESTION COUNT**: The exam MUST contain EXACTLY {specs['question_count']} questions/tasks."

    # Use more distinctive separators
    prompt = f"""Generate an authentic International Baccalaureate (IB) {request.subject} {request.level} {request.paper} examination.

EXAM SPECIFICATIONS:
- Duration: {specs['duration']} minutes
- Total marks: {specs['total_marks']}
- Typical structure: {specs['structure_desc']}{structure_rule}
- Command terms to prioritize: {', '.join(specs['command_terms'])}
- Focus areas: {focus_areas}

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
10. **STRICT LANGUAGE REQUIREMENT**: This is a {request.subject} exam. The ENTIRE exam (Instructions, Section Headers, Questions, Texts, and Mark Scheme) MUST be written in {output_lang}. Do NOT use English unless the subject name is English.
11. **MODEL ESSAY / ANSWERS**: All sample answers must be in {output_lang}.

{subject_instr}{model_essay_req}

FORMAT:
You MUST use these exact headers on their own lines to separate sections:
[SECTION_EXAM]
[Full exam paper paper content here]

{f'[SECTION_MARK_SCHEME]\\n[Provide a COMPLETE and DETAILED mark scheme for EVERY question here.]' if request.include_answer_key else ''}

[SECTION_GRADE_BOUNDARIES]
[Provide the Markdown table mapping raw marks to IB Grades here.]
"""
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
            # Escape for regex and build case-insensitive pattern
            pattern = re.compile(re.escape(tag), re.IGNORECASE)
            match = pattern.search(text)
            if match:
                return text[:match.start()], text[match.end():]
        return text, None

    # Order of reversal: Split from bottom up
    # 1. Split Grade Boundaries
    remaining, grade_boundaries = split_section(content, ["[SECTION_GRADE_BOUNDARIES]", "---GRADE BOUNDARIES---", "GRADE BOUNDARIES"])
    
    # 2. Split Answer Key from the remaining top part
    if grade_boundaries is None: grade_boundaries = ""
    else: grade_boundaries = grade_boundaries.strip()

    exam_part, answer_part = split_section(remaining, ["[SECTION_MARK_SCHEME]", "---ANSWER KEY---", "ANSWER KEY", "MARK SCHEME"])
    
    if answer_part:
        exam_text = exam_part.replace("[SECTION_EXAM]", "").replace("---EXAM---", "").strip()
        answer_key = answer_part.strip()
    else:
        # Fallback: if no answer key tag but found boundaries, exam_text is everything before boundaries
        exam_text = exam_part.replace("[SECTION_EXAM]", "").replace("---EXAM---", "").strip()
        answer_key = ""

    return exam_text, answer_key, grade_boundaries
