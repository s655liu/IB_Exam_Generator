"""
sample_essay.py — Generates a Band 6–7 model essay for a given IB question.

Subject-aware: length targets, structural conventions, and academic style
expectations are tailored per subject/paper.
"""
import os
import requests
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), '.env'))

QWEN_API_KEY  = os.getenv("QWEN_API_KEY")
QWEN_BASE_URL = os.getenv("QWEN_BASE_URL", "https://dashscope-intl.aliyuncs.com/compatible-mode/v1")

# ---------------------------------------------------------------------------
# Subject-specific guidance + word-count targets
# ---------------------------------------------------------------------------

_GUIDANCE: dict[str, str] = {
    "History": (
        "- **Structure**: Introductory paragraph with a clear, debatable thesis → "
        "2–3 analytical body paragraphs each making ONE argument supported by specific "
        "historical evidence (dates, events, individuals, statistics) → Conclusion that "
        "reassesses the thesis without adding new evidence.\n"
        "- Apply historical thinking concepts: causation, consequence, continuity/change, "
        "significance, perspective, and evidence.\n"
        "- Do NOT merely describe events — critically evaluate their causes, effects, and "
        "historical significance.\n"
        "- Integrate counter-arguments and nuance to demonstrate higher-order thinking."
    ),
    "English Literature A": (
        "- **Structure**: Thesis-led introduction that addresses HOW the text creates meaning → "
        "body paragraphs each exploring a distinct literary technique with close textual analysis → "
        "Conclusion that synthesises the argument.\n"
        "- Quote directly from the text(s); analyse the language, not just the content.\n"
        "- Discuss literary techniques explicitly: imagery, symbolism, narrative voice, "
        "structure, tone, irony, characterisation, etc.\n"
        "- Maintain a formal, analytical register throughout — no personal opinion phrases."
    ),
    "French B": (
        "- Write ENTIRELY in French. Do not use any English.\n"
        "- Match the text type and register specified in the question (e.g. blog, letter, article).\n"
        "- Use a wide range of vocabulary and complex grammatical structures to demonstrate "
        "linguistic range (subjunctive, conditional, varied tenses).\n"
        "- Develop ideas clearly and coherently with linking expressions."
    ),
    "Spanish B": (
        "- Write ENTIRELY in Spanish. Do not use any English.\n"
        "- Match the text type and register specified in the question.\n"
        "- Demonstrate range: subjunctive, conditional, varied tenses, discourse markers.\n"
        "- Develop ideas clearly and coherently."
    ),
    "Mandarin B": (
        "- Write ENTIRELY in Mandarin Chinese. Do not use any English.\n"
        "- Match the text type and register specified in the question.\n"
        "- Demonstrate a wide range of vocabulary and complex sentence structures.\n"
        "- Use appropriate connectives and discourse markers."
    ),
    "Geography": (
        "- **Structure**: Introduction defining key terms and signposting the argument → "
        "body paragraphs each addressing a specific geographic theme, process, or case study → "
        "Balanced conclusion evaluating relative importance.\n"
        "- Reference specific case studies, locations, data, and geographic terminology.\n"
        "- Apply geographic concepts: sustainability, interdependence, scale, spatial patterns.\n"
        "- Acknowledge multiple perspectives and geographic scales (local → global)."
    ),
    "Business Management": (
        "- **Structure**: Introduction contextualising the business issue → body paragraphs "
        "applying specific business management theories/tools (SWOT, P&L, marketing mix, etc.) "
        "to the scenario → Balanced conclusion with justified recommendations.\n"
        "- Apply theory to context — do not define tools without applying them.\n"
        "- Use business terminology accurately and discuss quantitative and qualitative evidence.\n"
        "- Evaluate trade-offs and consider short-term vs long-term implications."
    ),
    "ITGS": (
        "- **Structure**: Introduction framing the IT system and its social/ethical context → "
        "body paragraphs examining impacts (social, ethical, economic, cultural) with specific "
        "examples → Conclusion evaluating overall significance.\n"
        "- Apply the ITGS triangle: IT system ↔ Social/ethical issue ↔ Stakeholders.\n"
        "- Reference real-world examples of IT systems and their consequences.\n"
        "- Evaluate multiple stakeholder perspectives."
    ),
}

_DEFAULT_GUIDANCE = (
    "- Write a well-structured analytical essay with a clear introduction, developed body "
    "paragraphs with specific evidence, and a conclusion.\n"
    "- Use academic language appropriate to the IB Diploma level."
)

# Approximate target word counts by subject/paper
_WORD_TARGETS: dict[str, dict[str, int]] = {
    "History":               {"Paper 1": 600,  "Paper 2": 900,  "Paper 3": 1100, "default": 900},
    "English Literature A":  {"Paper 1": 700,  "Paper 2": 1000, "default": 850},
    "French B":              {"Paper 1": 350,  "default": 350},
    "Spanish B":             {"Paper 1": 350,  "default": 350},
    "Mandarin B":            {"Paper 1": 350,  "default": 350},
    "Geography":             {"default": 800},
    "Business Management":   {"default": 800},
    "ITGS":                  {"default": 700},
}


def _target_words(subject: str, paper: str) -> int:
    subj_map = _WORD_TARGETS.get(subject, {})
    # Try exact paper match, then "default"
    for key in (paper, "default"):
        if key in subj_map:
            return subj_map[key]
    return 800


# ---------------------------------------------------------------------------
# Prompt builder
# ---------------------------------------------------------------------------

def build_sample_essay_prompt(request) -> str:
    guidance   = _GUIDANCE.get(request.subject, _DEFAULT_GUIDANCE)
    word_count = _target_words(request.subject, request.paper)

    mark_scheme_section = ""
    if request.mark_scheme and request.mark_scheme.strip():
        mark_scheme_section = (
            f"\n\n## MARK SCHEME (use for reference — do NOT copy verbatim)\n"
            f"{request.mark_scheme.strip()}"
        )

    texts_section = ""
    if request.prescribed_texts:
        texts = [t for t in request.prescribed_texts if t.strip()]
        if texts:
            texts_section = f"\n\nPrescribed texts: {', '.join(texts)}"

    return f"""You are writing a model answer for an IB {request.subject} {request.level} {request.paper} examination.

Your task is to write a **Band 6–7 quality** sample essay in direct response to the following question.

---

## EXAM QUESTION
{request.question.strip()}
{mark_scheme_section}{texts_section}

---

## ESSAY WRITING GUIDELINES for {request.subject}

{guidance}

## OUTPUT REQUIREMENTS

1. Write a **COMPLETE essay** — full introduction, developed body paragraphs, and conclusion.
2. Target **{word_count} words** (±10%).
3. Aim for the quality of a top IB student (Band 6–7).
4. **Do NOT** include section labels like "Introduction:", "Body 1:", "Conclusion:" — write as a flowing, continuous prose essay.
5. **Do NOT** include marker commentary, annotations, or meta-discussion about the essay.
6. **Do NOT** start with "As an AI" or similar disclaimers — begin immediately with the essay itself.
7. Use academic register throughout.

Begin the essay now:
"""


# ---------------------------------------------------------------------------
# API call
# ---------------------------------------------------------------------------

async def call_qwen_sample_essay(prompt: str) -> str:
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
                    "You are an exemplary IB Diploma student with top marks across all subjects. "
                    "You write sophisticated, well-structured essays that achieve Band 6–7 under "
                    "IB criteria. You write directly and confidently without caveats."
                ),
            },
            {"role": "user", "content": prompt},
        ],
        "temperature": 0.75,
        "max_tokens": 3000,
    }
    response = requests.post(
        f"{QWEN_BASE_URL}/chat/completions", headers=headers, json=payload
    )
    if response.status_code != 200:
        detail = response.json() if response.content else "No detail"
        raise Exception(f"Qwen API Error {response.status_code}: {detail}")
    return response.json()["choices"][0]["message"]["content"]
