"""
evaluator.py — Essay evaluation logic for IB subjects.

Builds a subject-aware evaluation prompt and calls the Qwen API.
The LLM acts as an IB senior examiner and grades the essay using
official criteria for the subject/paper combination.
"""
import os
import requests
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), '.env'))

QWEN_API_KEY = os.getenv("QWEN_API_KEY")
QWEN_BASE_URL = os.getenv("QWEN_BASE_URL", "https://dashscope-intl.aliyuncs.com/compatible-mode/v1")

# ---------------------------------------------------------------------------
# Subject-specific IB marking criteria
# ---------------------------------------------------------------------------

# Each entry: list of (criterion_name, max_marks, description)
_CRITERIA: dict[str, list[tuple[str, int, str]]] = {
    "History": [
        ("A — Knowledge and understanding",    6, "Accuracy, detail, and relevance of historical knowledge"),
        ("B — Critical thinking",              6, "Analysis, synthesis, evaluation, and use of historical concepts"),
        ("C — Clarity and organization",       3, "Structured argument with coherent introduction, body, and conclusion"),
    ],
    "English Literature A": [
        ("A — Knowledge and understanding",    5, "Understanding of the works studied and the question"),
        ("B — Analysis and evaluation",        5, "Examination of how language, structure, and technique create meaning"),
        ("C — Coherence and organization",     5, "Logical structure; effective use of evidence and examples"),
        ("D — Language",                       5, "Clarity, precision, and appropriate register"),
    ],
    "French B": [
        ("A — Language",    12, "Range, accuracy, and effectiveness of language; grammar, vocabulary, register"),
        ("B — Message",     12, "Relevance, development, and clarity of ideas; coherent argument"),
    ],
    "Spanish B": [
        ("A — Language",    12, "Range, accuracy, and effectiveness of language; grammar, vocabulary, register"),
        ("B — Message",     12, "Relevance, development, and clarity of ideas; coherent argument"),
    ],
    "Mandarin B": [
        ("A — Language",    12, "Range, accuracy, and effectiveness of language; grammar, vocabulary, register"),
        ("B — Message",     12, "Relevance, development, and clarity of ideas; coherent argument"),
    ],
    "Geography": [
        ("Knowledge and understanding",   3, "Accurate use of geographic terminology and concepts"),
        ("Application and analysis",      3, "Application of concepts; analysis of geographic patterns/processes"),
        ("Synthesis and evaluation",      3, "Synthesis of evidence; evaluation of geographic outcomes"),
        ("Skills",                        3, "Use of maps, data, diagrams, and geographic methods"),
    ],
    "Business Management": [
        ("Knowledge and understanding",   2, "Relevant business management concepts, theories, and tools"),
        ("Application",                   4, "Appropriate application to the given context or business"),
        ("Analysis and synthesis",        4, "In-depth analysis linking concepts to outcomes; integration"),
        ("Evaluation",                    4, "Balanced judgement; strengths, limitations, and recommendations"),
    ],
    "ITGS": [
        ("A — Knowledge and understanding",  4, "Understanding of IT systems and ITGS concepts"),
        ("B — Application",                  4, "Application to specific social and ethical contexts"),
        ("C — Evaluation",                   4, "Judgement of impacts, solutions, and trade-offs"),
    ],
}

_DEFAULT_CRITERIA = [
    ("Knowledge and understanding", 5, "Accurate and relevant content"),
    ("Analysis and argument",       5, "Quality of reasoning and argumentation"),
    ("Organization and clarity",    5, "Structure, coherence, and academic language"),
]


def _get_criteria(subject: str) -> list[tuple[str, int, str]]:
    return _CRITERIA.get(subject, _DEFAULT_CRITERIA)


def _fmt_criteria_list(criteria: list[tuple[str, int, str]]) -> str:
    lines = []
    for name, marks, desc in criteria:
        lines.append(f"  - **Criterion {name}** (/{marks}): {desc}")
    return "\n".join(lines)


def _total_marks(criteria: list[tuple[str, int, str]]) -> int:
    return sum(m for _, m, _ in criteria)


# ---------------------------------------------------------------------------
# Prompt builder
# ---------------------------------------------------------------------------

def build_evaluation_prompt(request) -> str:
    """
    Build a prompt that turns the LLM into an IB senior examiner for the
    given subject/paper and asks it to grade the student essay.
    """
    criteria = _get_criteria(request.subject)
    total = _total_marks(criteria)
    criteria_block = _fmt_criteria_list(criteria)

    mark_scheme_section = (
        f"\n\n## OFFICIAL MARK SCHEME\n{request.mark_scheme.strip()}"
        if request.mark_scheme and request.mark_scheme.strip()
        else ""
    )

    prescribed_section = ""
    if request.prescribed_texts:
        texts = [t for t in request.prescribed_texts if t.strip()]
        if texts:
            prescribed_section = (
                f"\n\nPrescribed texts studied: {', '.join(texts)}"
            )

    return f"""You are a senior IB examiner specializing in {request.subject}.
Evaluate the following student essay submitted in response to the {request.subject} {request.level} {request.paper} examination.

---

## EXAM QUESTION
{request.question.strip()}
{mark_scheme_section}{prescribed_section}

---

## STUDENT ESSAY
{request.student_essay.strip()}

---

## YOUR TASK

Provide a thorough, honest, and constructive IB-style evaluation using the official criteria below.

**IB Marking Criteria for {request.subject} {request.paper}** (Total: {total} marks)
{criteria_block}

### OUTPUT FORMAT (use this EXACT structure):

## Overall Assessment
**Estimated Band**: [1–7]  |  **Total Marks**: [X / {total}]

## Criterion-by-Criterion Breakdown

For EACH criterion, provide:
- **Score**: X / Y
- **Justification**: 2–4 sentences explaining the score with specific reference to the student's essay.
- **Examiner Comment**: One concrete suggestion for improvement.

## Summary

### ✅ Strengths
- [3–5 specific strengths, referencing actual content/phrasing from the essay]

### ⚠️ Areas for Improvement
- [3–5 specific, actionable improvements]

### 💡 Examiner's Top Recommendation
[The single most important thing the student should do to raise their grade]

---

Be honest: do NOT inflate marks. Use the full range of the marking scale. Reference specific sentences or arguments from the student's essay in your feedback.
"""


# ---------------------------------------------------------------------------
# API call (reuses the same Qwen API used by generator.py)
# ---------------------------------------------------------------------------

async def call_qwen_evaluation(prompt: str) -> str:
    headers = {
        "Authorization": f"Bearer {QWEN_API_KEY}",
        "X-DashScope-ApiKey": QWEN_API_KEY,
        "Content-Type": "application/json",
    }
    payload = {
        "model": "qwen-max",
        "messages": [
            {
                "role": "system",
                "content": (
                    "You are a senior IB Diploma examiner with 15+ years of experience. "
                    "You provide rigorous, fair, and constructive essay evaluations following "
                    "official IB marking criteria. You do not inflate grades."
                ),
            },
            {"role": "user", "content": prompt},
        ],
        "temperature": 0.4,
        "max_tokens": 3000,
    }
    response = requests.post(
        f"{QWEN_BASE_URL}/chat/completions", headers=headers, json=payload
    )
    if response.status_code != 200:
        detail = response.json() if response.content else "No detail"
        raise Exception(f"Qwen API Error {response.status_code}: {detail}")
    return response.json()["choices"][0]["message"]["content"]
