# IB Exam Generator

An AI-powered tool for generating official-style IB examination papers with mark schemes, grade boundaries, and assessment rubrics — built with FastAPI + React (Vite), deployable on Vercel.

---

## Features

- **AI-Generated Exam Papers** — produces realistic IB-style questions for Math AA, Physics, Chemistry, Biology, History, English A, Business, and more
- **Official Mark Schemes** — displays subject-specific rubrics and marking criteria
- **Grade Boundaries** — shows official percentage bands (Grades 1–7) per subject and level
- **Student / Teacher Views** — separate tabs for question paper and mark scheme
- **PDF Export** — print-ready layout via browser print dialog
- **HL & SL Support** — adapts topic lists, paper structure, and boundaries per level

---

## Project Structure

```
IB_Exam_Generator/
├── api/                          # Backend — Vercel Python serverless functions
│   ├── index.py                  # FastAPI app (Vercel entry point)
│   ├── generator.py              # Prompt building & Qwen API call
│   ├── schemas.py                # Pydantic models
│   ├── exam_specs.json           # Exam structure data (used by backend)
│   └── .env                      # Local dev secrets (not committed)
├── frontend/                     # React (Vite) frontend
│   ├── src/
│   │   ├── App.jsx
│   │   ├── index.css
│   │   └── data/
│   │       ├── exam_subject_structure.json   # Topics per subject/level/paper
│   │       └── mark_schemes.json             # Grade boundaries + rubrics
│   ├── package.json
│   └── vite.config.js            # Dev proxy: /api → localhost:8000
├── requirements.txt              # Python deps (at root for Vercel)
├── vercel.json                   # Vercel deployment config
├── .gitignore
└── README.md
```

---

## Model Used

**Qwen-Turbo** via Alibaba Cloud DashScope API (international endpoint).

---

## Local Development

### Prerequisites
- Python 3.10+
- Node.js 18+
- A [Qwen API key](https://dashscope.aliyuncs.com/)

### Backend (runs on port 8000)

```bash
cd api
pip install -r ../requirements.txt
uvicorn index:app --reload --port 8000
```

Create `api/.env`:
```
QWEN_API_KEY=your_key_here
QWEN_BASE_URL=https://dashscope-intl.aliyuncs.com/compatible-mode/v1
```

### Frontend (runs on port 5173)

```bash
cd frontend
npm install
npm run dev
```

Open [http://localhost:5173](http://localhost:5173) — the Vite dev proxy automatically forwards `/api` requests to port 8000.

---

## Deploying to Vercel

### 1. Push to GitHub
Make sure your repo is on GitHub.

### 2. Import project on Vercel
Go to [vercel.com](https://vercel.com) → **Add New Project** → import your repo.

### 3. Set environment variables
In Vercel project settings → **Environment Variables**, add:
```
QWEN_API_KEY=your_key_here
QWEN_BASE_URL=https://dashscope-intl.aliyuncs.com/compatible-mode/v1
```

### 4. Deploy
Vercel will automatically detect `vercel.json` and:
- Build the React frontend from `frontend/`
- Deploy the FastAPI backend as a Python serverless function at `/api`

No additional configuration needed.

---

## Usage

1. Select a **Subject**, **Level** (HL/SL), and **Paper**
2. Choose one or more **Focus Topics**
3. Toggle **Answer Key** on or off
4. Click **Generate Examination**
5. Switch between **Question Paper** and **Mark Scheme & Boundaries** tabs
6. Click **Download PDF** to export a print-ready copy

---

## Notes

- Generating a new exam **replaces** the current one (no history is saved)
- Diagram-based questions are excluded from generation by design
- Grade boundaries are approximate, based on recent IB May sessions
- The `api/.env` file is gitignored — never commit your API key
