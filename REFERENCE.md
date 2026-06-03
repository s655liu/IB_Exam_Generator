# IB Exam Generator — AI Reference Document

> This file is written for AI assistants to quickly orient themselves in this codebase without needing to re-read every file. Keep it up to date when making significant changes.

---

## Project Overview

An AI-powered IB exam paper generator. Users select a subject, level, paper, and focus topics — the backend builds a structured prompt, calls the Qwen LLM API, and returns a parsed exam paper with optional mark scheme and grade boundaries.

**Stack:**
- **Backend:** Python, FastAPI, deployed as Vercel serverless functions
- **Frontend:** React (Vite), vanilla CSS, deployed as Vercel static site
- **LLM:** Qwen (`qwen-max`) via Alibaba Cloud DashScope API
- **Deployment:** Vercel (`vercel.json` handles routing for both)

---

## File Map

```
Exam_Generator/
├── api/
│   ├── index.py         # FastAPI app entry point (Vercel serverless)
│   ├── generator.py     # Core logic: prompt building, Qwen API call, response parsing
│   ├── schemas.py       # Pydantic request/response models
│   └── .env             # Local secrets (gitignored): QWEN_API_KEY, QWEN_BASE_URL
├── data/
│   └── exam_specs.json  # Per-subject paper specs (duration, marks, structure, command terms)
├── frontend/
│   └── src/
│       ├── App.jsx      # Entire frontend (single monolithic component file)
│       ├── index.css    # All styling (dark theme, glassmorphism)
│       └── data/
│           ├── exam_subject_structure.json  # Topics, levels, papers per subject (frontend)
│           └── mark_schemes.json            # Grade boundaries + official rubrics (frontend)
├── vercel.json          # Routing: /api/* → Python, everything else → React build
└── requirements.txt     # Python deps (at repo root for Vercel)
```

---

## Architecture: Skill-Based Pipeline

The backend is a **single-step, deterministic skill** — not an agent. The pipeline is:

```
User Input → build_prompt() → call_qwen_api() → parse_response() → JSON response
```

No branching, no tool use, no feedback loops. The LLM is called exactly once per request.

### Why not agent-based?
The current design is intentional: the output format is fully deterministic (3 sections) and user inputs drive everything. Agent-based patterns would only add value if self-correction, multi-step generation, or external tool use were needed.

---

## Backend Deep Dive (`api/`)

### `schemas.py` — Data Models

```python
class GenerateRequest:
    subject: str               # e.g. "Math AA", "History", "Physics"
    level: str                 # "HL" or "SL"
    paper: str                 # e.g. "Paper 1", "Paper 2", "Paper 1A", "Paper 1B"
    topic_or_type: List[str]   # Selected focus topics or task types
    include_answer_key: bool   # Default True
    prescribed_texts: Optional[List[str]]  # Only used for English Lit A Paper 2

class GenerateResponse:
    exam_text: str
    answer_key: Optional[str]
    grade_boundaries: Optional[str]
    metadata: Dict[str, Any]   # {subject, level, paper, topics}
```

### `generator.py` — Core Logic

**`get_ib_specs(subject, level, paper)`**
- Loads `exam_specs.json` and extracts: duration, total_marks, question_count, command_terms, structure_type, calculator allowed
- Normalizes subject keys (e.g. `"Math AA"` → `"Mathematics_AA"`, `"Paper 1A"` → `"paper_1A"`)
- Falls back to sensible defaults if specs not found
- Returns a `specs` dict

**`get_subject_specific_instructions(subject, level, paper, specs)`**
- Returns subject-tailored prompt additions as a string
- Key cases handled:
  - `Math AA` — LaTeX, SVG, difficulty progression, calculator
  - `History Paper 1` — 4 source-based questions, timeline diagram
  - `History Paper 2` — Comparative questions, exactly 2 per topic, 15 marks each
  - `Language B (French/Spanish/Mandarin)` — Entire exam in target language, audio transcripts in ` ```audio ``` ` blocks, reading texts
  - `Physics/Chemistry/Biology` — Data booklet reference, Paper 1A = MCQ, Paper 1B = data analysis with experimental skills
  - `Geography, ITGS, Business` — Mermaid/SVG diagrams

**`build_prompt(request)`**
- Orchestrates `get_ib_specs` + `get_subject_specific_instructions`
- Applies overrides for special cases (History P2 marks, receptive paper structure, essay-choice papers)
- Injects prescribed texts for English Lit A Paper 2
- Returns a large f-string prompt enforcing exact section headers:
  - `[SECTION_EXAM]`
  - `[SECTION_MARK_SCHEME]` (only if `include_answer_key=True`)
  - `[SECTION_GRADE_BOUNDARIES]`

**`call_qwen_api(prompt)`**
- Async, uses `requests.post` (sync inside async — works on Vercel, not ideal)
- Model: `qwen-max`
- System prompt: "You are an expert IB Senior Examiner..."
- `max_tokens: 6000`, `temperature: 0.7`
- Returns raw string content

> ⚠️ **Known limitation:** Single call with 6000 tokens can cause truncation, especially for language B exams with long transcripts.

**`parse_response(content)`**
- Splits by section headers using case-insensitive regex
- Returns `(exam_text, answer_key, grade_boundaries)` tuple
- Fallback aliases supported: `---ANSWER KEY---`, `MARK SCHEME`, `GRADE BOUNDARIES`

### `index.py` — FastAPI App

- Single endpoint: `POST /api/generate-exam`
- `sys.path.insert` ensures sibling modules importable on Vercel
- CORS: `allow_origins=["*"]` (open, OK for a student tool)
- Health check: `GET /api/health`

---

## Frontend Deep Dive (`frontend/src/`)

### `App.jsx` — Single File, All Logic

All UI, state, and rendering lives in one ~770-line file. No component files are split out.

**Key state:**
```js
selectedSubject, selectedLevel, selectedPaper   // Cascade-dependent dropdowns
selectedTopics                                   // Multi-select array
includeAnswerKey                                 // Toggle
prescribedTexts                                  // ['', ''] — only for English Lit A P2
isGenerating, result, error, activeTab          // UI state
```

**Data sources (JSON imports):**
- `exam_subject_structure.json` — drives all dropdown options (subjects, levels, papers, topics)
- `mark_schemes.json` — official grade boundaries + rubrics shown in the Mark Scheme tab

**Cascade logic:**
- Subject → clears Level, Paper, Topics
- Level → clears Paper, Topics
- Paper → populates `availableOptions` (topics or skills based on paper type)

**Special UI cases:**
- `History Paper 2` — enforces exactly 2 topic selections
- `English Lit A Paper 2` — shows prescribed works text inputs
- `Math/Science Paper 1B` — shows experimental skills from `post_2025_notes.key_skills_assessed`
- "Auto-Select All" button — only shown for Math/Science

**`canGenerate` condition:**
```js
selectedSubject && selectedLevel && selectedPaper &&
(isHistoryP2 ? selectedTopics.length === 2 : selectedTopics.length > 0)
```

**Keyboard shortcut:** `Enter` triggers generation if `canGenerate && !isGenerating`

**Custom markdown renderers (`MarkdownComponents`):**
| Code block language | Renders as |
|---|---|
| ` ```audio ``` ` | `<AudioPlayer>` (Web Speech API TTS) |
| ` ```mermaid ``` ` | `<Mermaid>` (mermaid.js render) |
| ` ```svg ``` ` | `<SVGRenderer>` (dangerouslySetInnerHTML) |

**Audio failsafe (post-processing):**
After the API response, the frontend applies regex to convert any `[PLAYABLE_AUDIO]...[/PLAYABLE_AUDIO]` tags that the LLM sometimes generates into proper ` ```audio ``` ` blocks.

**Tabs:**
- `paper` — shows `result.exam_text` rendered as Markdown
- `key` — shows official rubric (from local JSON) + AI mark scheme + grade boundaries (local JSON preferred over AI)

**PDF export:** `window.print()` with `no-print` / `print-only` CSS classes controlling what shows.

**`officialData` (useMemo):**
Derived from `mark_schemes.json` based on current selections. Contains `boundaries` and `rubric` objects that take priority over the AI-generated versions.

---

## Data Files

### `data/exam_specs.json` (backend)
Used by `get_ib_specs()`. Structure:
```json
{
  "Mathematics_AA": {
    "HL": {
      "paper_1A": {
        "duration_minutes": 60,
        "total_marks": 40,
        "calculator_allowed": false,
        "question_count": 30,
        "structure": { "type": "mcq", "description": "..." },
        "command_terms": [...]
      }
    }
  }
}
```

### `frontend/src/data/exam_subject_structure.json` (frontend)
Drives all dropdowns. Structure:
```json
{
  "Math AA": {
    "levels": ["HL", "SL"],
    "papers_by_level": { "HL": ["Paper 1A", "Paper 1B", "Paper 2", "Paper 3"] },
    "topics": {
      "core_topics": [...],
      "hl_topics": [...]
    },
    "post_2025_notes": {
      "key_skills_assessed": [...]
    }
  }
}
```

### `frontend/src/data/mark_schemes.json` (frontend)
```json
{
  "grade_boundaries": {
    "explanation": "...",
    "Mathematics_AA": {
      "HL": { "grade_7": { "min": 70, "max": 100, "description": "..." }, ... }
    }
  },
  "rubrics": {
    "English_Literature_A": {
      "paper_2": {
        "title": "...",
        "criteria": [
          { "criterion": "A", "what_is_assessed": "...", "descriptors": { "5": "..." } }
        ]
      }
    }
  }
}
```

---

## Subjects Supported

| Subject | Notes |
|---|---|
| Math AA | HL/SL, Papers 1A/1B/2/3(HL), LaTeX + SVG |
| Physics / Chemistry / Biology | HL/SL, Papers 1A/1B/2/3, post-2025 experimental skills on 1B |
| History | HL/SL, P1 (source-based), P2 (2-topic comparative), P3 (HL only) |
| English Literature A | HL/SL, Paper 1 (unseen), Paper 2 (essay with prescribed texts) |
| French B / Spanish B / Mandarin B | HL/SL, P1 (writing), P2 (receptive: listening + reading transcripts in target language) |
| Business Management | HL/SL |
| Geography | HL/SL |
| ITGS | HL/SL |

---

## Environment & Deployment

**Local dev:**
```bash
# Backend (port 8000)
cd api && uvicorn index:app --reload --port 8000

# Frontend (port 5173, proxies /api to :8000)
cd frontend && npm run dev
```

**Required env vars (`api/.env`):**
```
QWEN_API_KEY=...
QWEN_BASE_URL=https://dashscope-intl.aliyuncs.com/compatible-mode/v1
```

**Vercel:** Auto-detected via `vercel.json`. Sets env vars in Vercel dashboard. No build config needed beyond what's in `vercel.json`.

---

## Known Issues & Improvement Areas

| Issue | Location | Notes |
|---|---|---|
| Response truncation | `generator.py` → `call_qwen_api` | 6000 token cap. Language B exams most affected. Consider splitting into separate calls per section. |
| Sync `requests` inside `async` | `call_qwen_api()` | Works but blocks the event loop. Should use `httpx` with `await` for correctness. |
| No exam history | Frontend state | Each new generation replaces the current result. No persistence. |
| Subject key normalization | `get_ib_specs()` | Fragile `str.replace` chain. A lookup dict would be cleaner. |
| Large monolithic `App.jsx` | Frontend | 768 lines. Could benefit from splitting into `<ConfigPanel>`, `<ExamViewer>`, `<MarkSchemeViewer>` components. |
| CORS wildcard | `index.py` | `allow_origins=["*"]` — fine for now, restrict if API key security becomes a concern. |

---

## Key Conventions

- **Section headers in LLM output** are the parsing contract: `[SECTION_EXAM]`, `[SECTION_MARK_SCHEME]`, `[SECTION_GRADE_BOUNDARIES]`. Do not change these without updating `parse_response()` and `build_prompt()` together.
- **Subject key normalization** must stay in sync between backend (`generator.py`) and frontend (`App.jsx`). Both independently map `"Math AA"` → `"Mathematics_AA"` etc.
- **Local JSON data takes priority** over AI-generated content for grade boundaries and rubrics — this is intentional for accuracy.
- **Audio blocks** use the ` ```audio ``` ` code fence convention (custom, not standard Markdown). The frontend has a regex failsafe for LLM deviations.
