# IB Exam Generator

An AI-powered tool for generating official-style IB examination papers with mark schemes, grade boundaries, and assessment rubrics.

---

## Features

- **AI-Generated Exam Papers** — produces realistic IB-style questions for Math AA, Physics, Chemistry, Biology, History, English A, Business, and more
- **Official Mark Schemes** — displays subject-specific rubrics and marking criteria sourced from `data/mark_schemes.json`
- **Grade Boundaries** — shows official percentage bands (Grades 1–7) for each subject and level
- **Student / Teacher Views** — separate tabs for the question paper and the mark scheme
- **PDF Export** — print-ready layout via browser print dialog
- **HL & SL Support** — adapts topic lists, paper structure, and boundaries per level

---

## Project Structure

```
IB_Exam_Generator/
├── backend/
│   ├── main.py          # FastAPI app and /api/generate-exam endpoint
│   ├── generator.py     # Prompt construction and Gemini API call
│   ├── schemas.py       # Pydantic request/response models
│   ├── requirements.txt
│   └── .env             # GEMINI_API_KEY (not committed)
├── frontend/
│   ├── src/
│   │   ├── App.jsx      # Main React component
│   │   ├── index.css    # Global styles
│   │   └── data/
│   │       ├── exam_subject_structure.json   # Topics per subject/level/paper
│   │       └── mark_schemes.json             # Grade boundaries + rubrics
│   ├── index.html
│   ├── vite.config.js
│   └── package.json
├── data/                # Source copies of JSON data files
├── .gitignore
└── README.md
```

---

## Setup

### Prerequisites
- Python 3.10+
- Node.js 18+
- A [Google Gemini API key](https://aistudio.google.com/)

### Model Used
Qwen-Turbo

### Backend

```bash
cd backend
pip install -r requirements.txt
```
 

Create a `backend/.env` file:
```
QWEN_API_KEY=your_key_here
QWEN_BASE_URL=your_url_here
```

Start the server:
```bash
python -m uvicorn main:app --reload --port 8000
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Open [http://localhost:5173](http://localhost:5173)

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
- Diagram-based questions are intentionally excluded from generation
- Grade boundaries are approximate and based on recent IB May sessions
