# IB Exam Generator — Gemini AI Context File

> **This is the primary AI context file for this project** (equivalent to `CLAUDE.md` for Anthropic's Claude). Gemini / Antigravity reads this automatically at the start of each conversation to orient itself without needing to re-read every source file. Keep it up to date when making significant changes.

---

## Project Overview

An AI-powered IB exam paper generator and essay evaluator. Users select a subject, level, paper, and focus topics — the backend builds a structured prompt, calls the Qwen LLM API, and returns a parsed exam paper with mark scheme and grade boundaries. Essay-based subjects also support AI-graded essay evaluation against IB criteria, and sample model essay generation.

**Stack:**
- **Backend:** Python, FastAPI, deployed as Vercel serverless functions
- **Frontend:** React (Vite), vanilla CSS, deployed as Vercel static site
- **LLM:** Qwen (`qwen-max`) via Alibaba Cloud DashScope API
- **Math rendering:** KaTeX via `remark-math` + `rehype-katex`
- **Diagram rendering:** Mermaid.js (flowcharts, timelines) + raw SVG injection
- **Dev workflow:** `npm run dev` at repo root runs both API + frontend via `concurrently`

---

## File Map

```
Exam_Generator/
├── api/
│   ├── index.py             # FastAPI app — all endpoints
│   ├── generator.py         # Exam prompt builder, Qwen API call, response parser
│   ├── evaluator.py         # Essay evaluation prompt builder + Qwen API call
│   ├── sample_essay.py      # Sample model essay prompt builder + Qwen API call
│   ├── schemas.py           # Pydantic models (all request/response types)
│   ├── skills/              # Subject-specific prompt logic (registry pattern)
│   │   ├── base.py          # BaseExamSkill interface
│   │   ├── registry.py      # get_skill(subject) → skill instance
│   │   ├── group1_language_literature/
│   │   │   └── english_lit_a.py
│   │   ├── group2_language_acquisition/
│   │   │   ├── language_b.py    # LanguageBSkill base (French/Spanish/Mandarin inherit)
│   │   │   ├── french_b.py
│   │   │   ├── spanish_b.py
│   │   │   └── mandarin_b.py
│   │   ├── group3_individuals_societies/
│   │   │   ├── history.py
│   │   │   ├── geography.py
│   │   │   ├── business.py
│   │   │   └── itgs.py
│   │   ├── group4_sciences/
│   │   │   ├── science_base.py  # ScienceSkill base (Physics/Chemistry/Biology inherit)
│   │   │   ├── physics.py
│   │   │   ├── chemistry.py
│   │   │   └── biology.py
│   │   └── group5_mathematics/
│   │       └── math_aa.py
│   └── .env                 # Local secrets (gitignored): QWEN_API_KEY, QWEN_BASE_URL
├── data/
│   └── exam_specs.json      # Per-subject paper specs (duration, marks, structure, command terms)
├── frontend/
│   └── src/
│       ├── App.jsx          # Main frontend component (~800 lines)
│       ├── index.css        # All styling (dark theme, glassmorphism, square corners globally)
│       ├── components/
│       │   ├── MarkdownRenderer.jsx    # Unified markdown renderer with LaTeX preprocessing
│       │   ├── EssayEvaluator.jsx      # Essay upload/paste + AI evaluation UI
│       │   └── SampleEssayGenerator.jsx  # Sample model essay UI (in progress)
│       └── data/
│           ├── exam_subject_structure.json  # Topics, levels, papers per subject (frontend)
│           └── mark_schemes.json            # Grade boundaries + official rubrics (frontend)
├── GEMINI.md                # ← THIS FILE (AI context, replaces REFERENCE.md)
├── package.json             # Root: `npm run dev` runs API + frontend via concurrently
├── vercel.json              # Routing: /api/* → Python, everything else → React build
└── requirements.txt         # Python deps (at repo root for Vercel)
```

---

## Local Dev

```bash
# One command — starts API (port 8000) + frontend (port 5173)
npm run dev
```

Vite proxies `/api/*` → `:8000`. KaTeX CSS bundled via npm.

**Required env vars (`api/.env`):**
```
QWEN_API_KEY=...
QWEN_BASE_URL=https://dashscope-intl.aliyuncs.com/compatible-mode/v1
```

---

## API Endpoints (`api/index.py`)

| Method | Path | Module | Purpose |
|---|---|---|---|
| GET | `/api/health` | — | Health check |
| POST | `/api/generate-exam` | `generator.py` | Generate full exam paper |
| POST | `/api/evaluate-essay` | `evaluator.py` | Grade a student essay with IB criteria |
| POST | `/api/generate-sample-essay` | `sample_essay.py` | Generate a Band 6–7 model essay |

---

## Architecture

### Exam Generation Pipeline

```
User Input → build_prompt() → call_qwen_api() → parse_response() → JSON
```

Single LLM call per request, no agent loops.

### Essay Evaluation Pipeline

```
Essay + Question → build_evaluation_prompt() → call_qwen_evaluation() → JSON
```

### Sample Essay Pipeline

```
Question → build_sample_essay_prompt() → call_qwen_sample_essay() → JSON
```

---

## Backend Deep Dive (`api/`)

### `schemas.py` — Data Models

```python
class GenerateRequest:
    subject, level, paper: str
    topic_or_type: List[str]
    include_answer_key: bool = True
    prescribed_texts: Optional[List[str]]

class GenerateResponse:
    exam_text, answer_key, grade_boundaries: str
    metadata: Dict[str, Any]  # {subject, level, paper, topics}

class EvaluateRequest:
    subject, level, paper: str
    question: str              # Exam prompt the student answered
    student_essay: str
    mark_scheme: Optional[str]
    prescribed_texts: Optional[List[str]]

class EvaluateResponse:
    evaluation: str            # Full markdown feedback
    metadata: Dict[str, Any]

class SampleEssayRequest:
    subject, level, paper: str
    question: str              # Essay prompt to respond to
    mark_scheme: Optional[str]
    prescribed_texts: Optional[List[str]]

class SampleEssayResponse:
    essay: str                 # Full model essay
    metadata: Dict[str, Any]
```

### `generator.py` — Exam Prompt Builder

**`get_ib_specs(subject, level, paper)`** — loads `data/exam_specs.json`, normalizes keys, returns specs dict.

**`build_prompt(request)`** flow:
1. `get_ib_specs()` → base specs
2. `get_skill(subject)` → skill instance
3. `skill.get_prompt_overrides()` → `structure_rule`, `model_essay_req`, `force_mark_scheme`, `mark_scheme_instr`, `specs_overrides`
4. `skill.get_instructions()` → subject-specific prompt additions
5. Assembles f-string with 11 REQUIREMENTS (LaTeX notation, diagrams, language, etc.)
6. FORMAT section: always `[SECTION_EXAM]` + `[SECTION_GRADE_BOUNDARIES]`; `[SECTION_MARK_SCHEME]` added if `include_answer_key OR force_mark_scheme`
7. **Debug print** to stdout — remove before production

**LLM Math Notation Contract (IMPORTANT):**
- Inline: `LATEX<<formula>>` → `$formula$` (after preprocessing)
- Display: `LATEXBLOCK<<formula>>` → `$$\nformula\n$$` (after preprocessing)
- `<<>>` chosen because they never appear in LaTeX syntax
- Frontend `preprocessMarkdown()` also handles 3 fallback patterns for when LLM ignores instruction

**`parse_response(content)`** — splits on `[SECTION_EXAM]`, `[SECTION_MARK_SCHEME]`, `[SECTION_GRADE_BOUNDARIES]` with fallback aliases.

### `evaluator.py` — Essay Grader

**`_CRITERIA` dict** — per-subject IB marking criteria:
- History: A (Knowledge, 6) + B (Critical thinking, 6) + C (Organisation, 3) = 15
- English Lit A: A–D, 5 each = 20
- Language B (all): A (Language, 12) + B (Message, 12) = 24
- Geography, Business, ITGS: subject-specific

**Output format:** Overall Band + criterion scores + Strengths + Areas for Improvement + Top Recommendation.

### `sample_essay.py` — Model Essay Generator

**`_GUIDANCE` dict** — per-subject structural and stylistic guidance for the LLM.
**`_WORD_TARGETS` dict** — approximate word counts by subject/paper (e.g. History P2 = 900 words).
**Output:** Continuous prose essay, no section labels, no AI disclaimers. `temperature: 0.75`, `max_tokens: 3000`.

### `skills/` — Registry Pattern

**`BaseExamSkill`** interface (`base.py`):
```python
subject_key: str          # e.g. "Mathematics_AA"
output_language: str      # "English" (Language B skills override this)

get_instructions(level, paper, specs) -> str
get_prompt_overrides(request, specs) -> dict
# dict keys: structure_rule, model_essay_req, force_mark_scheme,
#            mark_scheme_instr, specs_overrides
```

**`registry.py`** — `get_skill(subject_str)` maps display name to skill class. Falls back to `BaseExamSkill`.

**Key skill behaviours:**
- `MathAASkill` — LATEX<<>> notation, SVG, difficulty progression, calculator note
- `ScienceSkill` — Paper 1A = MCQ format, Paper 1B = data analysis + experimental skills, LATEX notation
- `LanguageBSkill` — sets `output_language` to target language (French/Spanish/Mandarin)
- `HistorySkill` — P1 = 4 source-based questions, P2 = exactly 2 topics × 15 marks

**`force_mark_scheme`** — when `True` in overrides, always generates mark scheme regardless of UI toggle. Intended for Math/Science (not yet fully implemented in those skills).

---

## Frontend Deep Dive (`frontend/src/`)

### `App.jsx` — Main Component

**Key state:**
```js
selectedSubject, selectedLevel, selectedPaper  // Cascade dropdowns
selectedTopics                                  // Multi-select
includeAnswerKey                                // Toggle
prescribedTexts                                 // English Lit A P2 only
isGenerating, result, error, activeTab         // UI state
```

**`isEssayCapable(subject, paper)`** — returns `true` for essay subjects (History, English Lit A, French/Spanish/Mandarin B, Geography, Business, ITGS) and `false` for Paper 1A (MCQ).

**Tabs after generation:**
| Tab key | Condition | Component |
|---|---|---|
| `paper` | always | `MarkdownRenderer` with exam text |
| `key` | answer_key present | Official rubric + AI mark scheme + grade boundaries |
| `evaluate` | essay-capable | `EssayEvaluator` |
| `sample` | essay-capable | `SampleEssayGenerator` (planned) |

**Custom code fence renderers (`MarkdownComponents`):**
- `` ```audio `` → `<AudioPlayer>` (Web Speech API TTS)
- `` ```mermaid `` → `<Mermaid>` (mermaid.js)
- `` ```svg `` → `<SVGRenderer>` (dangerouslySetInnerHTML)

**`officialData` (useMemo):** From `mark_schemes.json`. Local JSON **always takes priority** over AI output for boundaries and rubrics.

### `components/MarkdownRenderer.jsx`

All markdown rendering goes through this single component.

**`preprocessMarkdown(text)`** — 5-step LaTeX conversion:
1. `LATEXBLOCK<<...>>` → `$$\n...\n$$`
2. `LATEX<<...>>` → `$...$`
3. `\[...\]` → `$$...$$` (standard LaTeX fallback)
4. `\(...\)` → `$...$` (standard LaTeX fallback)
5. `( \formula )` → `$...$` (LLM space-padded parens fallback)

**Usage:**
```jsx
<MarkdownRenderer content={someString} components={MarkdownComponents} />
```

### `components/EssayEvaluator.jsx`

**Props:** `subject`, `level`, `paper`, `examText`, `markScheme`, `prescribedTexts`

**Features:** question input, essay textarea + `.txt`/`.md` file upload, live word counter, `POST /api/evaluate-essay`, results rendered via `MarkdownRenderer`.

### `components/SampleEssayGenerator.jsx` *(in progress)*

**Planned props:** same as EssayEvaluator minus `examText`.

**Features:** question input, "Generate Sample Essay" button, rendered essay output, copy-to-clipboard.

---

## UI Conventions

- **Square corners everywhere**: `border-radius: 0` set globally in `index.css`. Only exception: toggle switch slider (functional pill shape).
- **Dark theme**: Deep navy/slate palette, glassmorphism cards.
- **Tab colours**: Blue (paper), Green (mark scheme), Purple (evaluate), Indigo (sample essay).
- **No rounding in inline styles**: Any `borderRadius` in JSX must be `'0'`.

---

## Data File Schemas

### `data/exam_specs.json` (backend)
```json
{
  "Mathematics_AA": {
    "HL": {
      "paper_1A": {
        "duration_minutes": 60, "total_marks": 40,
        "calculator_allowed": false, "question_count": 30,
        "structure": { "type": "mcq", "description": "..." },
        "command_terms": [...]
      }
    }
  }
}
```

### `frontend/src/data/exam_subject_structure.json`
```json
{
  "Math AA": {
    "levels": ["HL", "SL"],
    "papers_by_level": { "HL": ["Paper 1A", "Paper 1B", "Paper 2", "Paper 3"] },
    "topics": { "core_topics": [...], "hl_topics": [...] },
    "post_2025_notes": { "key_skills_assessed": [...] }
  }
}
```

### `frontend/src/data/mark_schemes.json`
```json
{
  "grade_boundaries": {
    "explanation": "...",
    "Mathematics_AA": { "HL": { "grade_7": { "min": 70, "max": 100, "description": "..." } } }
  },
  "rubrics": {
    "English_Literature_A": {
      "paper_2": {
        "title": "...",
        "criteria": [{ "criterion": "A", "what_is_assessed": "...", "descriptors": {} }]
      }
    }
  }
}
```

---

## Subjects Supported

| Subject | IB Group | Essay capable? | Notes |
|---|---|---|---|
| Math AA | 5 | No | LaTeX + SVG, Papers 1A/1B/2/3(HL) |
| Physics / Chemistry / Biology | 4 | No | Papers 1A/1B/2/3, experimental skills on 1B |
| History | 3 | **Yes** | P1 (source), P2 (2-topic comparative), P3 (HL) |
| English Literature A | 1 | **Yes** | P1 (unseen), P2 (essay + prescribed texts) |
| French / Spanish / Mandarin B | 2 | **Yes** | P1 (writing in target lang), P2 (receptive) |
| Business Management | 3 | **Yes** | |
| Geography | 3 | **Yes** | |
| ITGS | 3 | **Yes** | |

---

## Key Conventions

- **Section header contract**: `[SECTION_EXAM]`, `[SECTION_MARK_SCHEME]`, `[SECTION_GRADE_BOUNDARIES]` — do not rename without updating both `build_prompt()` and `parse_response()`.
- **Math**: LLM instructed to use `LATEX<<>>` / `LATEXBLOCK<<>>`. Frontend has 5-step fallback preprocessor.
- **Local JSON > AI**: Grade boundaries and rubrics from `mark_schemes.json` override AI output.
- **Audio code fence**: `` ```audio `` is a custom non-standard fence. Frontend regex failsafe converts `[PLAYABLE_AUDIO]...[/PLAYABLE_AUDIO]` tags.
- **Subject key normalisation**: Both backend (`get_ib_specs`) and frontend (`officialData` useMemo) independently map `"Math AA"` → `"Mathematics_AA"`, etc. Keep in sync.

---

## Known Issues & Pending Work

| Issue | File | Notes |
|---|---|---|
| Debug prompt print in production | `generator.py` | Remove `print(prompt)` block before deploying |
| `force_mark_scheme` not wired | `math_aa.py`, `science_base.py` | `get_prompt_overrides` should return `force_mark_scheme: True` + detailed `mark_scheme_instr` |
| `SampleEssayGenerator.jsx` not wired | `App.jsx`, `index.py` | Backend ready (`sample_essay.py`), frontend component and tab not yet created |
| Sync `requests` inside async | `call_qwen_*` functions | Works on Vercel but blocks event loop; should migrate to `httpx` |
| Response truncation | `generator.py` | 6000-token cap; Language B exams most affected |
| No exam history / persistence | Frontend | Each generation replaces the current result |
| CORS wildcard | `index.py` | `allow_origins=["*"]` fine for now; tighten if needed |
