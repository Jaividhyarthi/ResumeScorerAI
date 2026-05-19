# ResumeIQ — AI Resume Scorer

A full-stack AI-powered resume analysis tool that scores resumes out of 100, identifies weaknesses, checks ATS compatibility, and provides a detailed improvement plan. Powered by Groq LLaMA 3.3 70B.

---

## Features

- Upload PDF, DOCX, or TXT resume
- Specify target job role for tailored analysis
- Overall score out of 100 with animated gauge
- Letter grade (A+ to F)
- ATS compatibility score
- Role match percentage
- 7-section breakdown with individual scores
- Top 3 strengths identified
- Prioritized improvement plan (High / Medium / Low)
- Missing keywords for the target role
- SQLite history dashboard
- Zero data stored permanently

---

## Project Structure

```
resume-scorer/
├── app.py                  — Flask backend + Groq API integration
├── requirements.txt        — Python dependencies
├── templates/
│   ├── index.html          — Main scorer UI
│   └── history.html        — Analysis history dashboard
├── static/
│   ├── css/styles.css      — All styling
│   └── js/app.js           — Frontend logic
└── README.md
```

---

## Setup & Run

### 1. Install dependencies
```bash
pip install -r requirements.txt
```

### 2. Add your Groq API key
Open `app.py` and replace on line 14:
```python
GROQ_API_KEY = 'your-groq-api-key-here'
```
Get a free key at: https://console.groq.com

### 3. Run the app
```bash
python app.py
```

Open `http://localhost:5000`

---

## API Reference

### POST /analyze
**Form data:**
- `resume` — PDF, DOCX, or TXT file
- `job_role` — Target job role string

**Response:**
```json
{
  "score": 74,
  "grade": "B+",
  "summary": "...",
  "sections": { ... },
  "strengths": [...],
  "improvements": [...],
  "missing_keywords": [...],
  "ats_score": 68,
  "ats_feedback": "...",
  "role_match": 71,
  "role_feedback": "..."
}
```

---

## Tech Stack

- **Backend:** Python, Flask, Groq API (LLaMA 3.3 70B)
- **PDF parsing:** PyMuPDF
- **DOCX parsing:** python-docx
- **Database:** SQLite
- **Frontend:** Vanilla HTML, CSS, JavaScript
- **Fonts:** Playfair Display + Epilogue

---

Built by Jaividhyarthi Vivekanand
