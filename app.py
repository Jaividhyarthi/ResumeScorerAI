"""
app.py — ResumeIQ Backend
Run: python app.py
"""

from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import os
import re
import sqlite3
import json
from datetime import datetime
from groq import Groq

app = Flask(__name__)
CORS(app)
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024

# ---- Groq client ----
GROQ_API_KEY = 'YOUR_GROQ_API_KEY'
client = Groq(api_key=GROQ_API_KEY)

BASE_DIR = os.path.dirname(__file__)

# ---- Database ----
DB_PATH = os.path.join(BASE_DIR, 'resumes.db')

def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS analyses (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp   TEXT NOT NULL,
            filename    TEXT,
            job_role    TEXT,
            score       INTEGER,
            grade       TEXT,
            summary     TEXT
        )
    ''')
    conn.commit()
    conn.close()

def save_analysis(filename, job_role, score, grade, summary):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''
        INSERT INTO analyses (timestamp, filename, job_role, score, grade, summary)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (datetime.now().strftime('%Y-%m-%d %H:%M:%S'), filename, job_role, score, grade, summary))
    conn.commit()
    conn.close()

def get_history(limit=30):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute('SELECT * FROM analyses ORDER BY id DESC LIMIT ?', (limit,))
    rows = [dict(row) for row in c.fetchall()]
    conn.close()
    return rows

def get_stats():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('SELECT COUNT(*), AVG(score), MAX(score), MIN(score) FROM analyses')
    row = c.fetchone()
    c.execute('SELECT grade, COUNT(*) FROM analyses GROUP BY grade')
    grades = dict(c.fetchall())
    conn.close()
    return {
        'total': row[0] or 0,
        'avg_score': round(row[1] or 0, 1),
        'max_score': row[2] or 0,
        'min_score': row[3] or 0,
        'grades': grades
    }

init_db()

# ---- Text extraction ----
def extract_text_from_pdf(file_bytes):
    try:
        import fitz  # PyMuPDF
        doc = fitz.open(stream=file_bytes, filetype='pdf')
        text = ''
        for page in doc:
            text += page.get_text()
        doc.close()
        return text.strip()
    except Exception as e:
        return f'[PDF extraction failed: {str(e)}]'

def extract_text_from_docx(file_bytes):
    try:
        import io
        from docx import Document
        doc = Document(io.BytesIO(file_bytes))
        return '\n'.join([p.text for p in doc.paragraphs if p.text.strip()])
    except Exception as e:
        return f'[DOCX extraction failed: {str(e)}]'

# ---- AI Analysis ----
def analyze_resume(resume_text, job_role):
    prompt = f"""You are an expert HR consultant and resume evaluator with 15 years of experience. Analyze the following resume for the role of "{job_role}" and return a detailed JSON evaluation.

RESUME:
---
{resume_text[:8000]}
---

Return ONLY a valid JSON object with this exact structure (no markdown, no extra text):
{{
  "score": <integer 0-100>,
  "grade": "<A+|A|B+|B|C+|C|D|F>",
  "summary": "<2-3 sentence overall assessment>",
  "sections": {{
    "contact_info": {{ "score": <0-100>, "status": "<present|missing|incomplete>", "feedback": "<specific feedback>" }},
    "professional_summary": {{ "score": <0-100>, "status": "<present|missing|weak>", "feedback": "<specific feedback>" }},
    "work_experience": {{ "score": <0-100>, "status": "<strong|average|weak|missing>", "feedback": "<specific feedback>" }},
    "education": {{ "score": <0-100>, "status": "<present|missing|incomplete>", "feedback": "<specific feedback>" }},
    "skills": {{ "score": <0-100>, "status": "<strong|average|weak|missing>", "feedback": "<specific feedback>" }},
    "achievements": {{ "score": <0-100>, "status": "<present|missing|weak>", "feedback": "<specific feedback>" }},
    "formatting": {{ "score": <0-100>, "status": "<excellent|good|average|poor>", "feedback": "<specific feedback>" }}
  }},
  "strengths": ["<strength 1>", "<strength 2>", "<strength 3>"],
  "improvements": [
    {{ "priority": "high", "issue": "<issue>", "fix": "<specific actionable fix>" }},
    {{ "priority": "high", "issue": "<issue>", "fix": "<specific actionable fix>" }},
    {{ "priority": "medium", "issue": "<issue>", "fix": "<specific actionable fix>" }},
    {{ "priority": "medium", "issue": "<issue>", "fix": "<specific actionable fix>" }},
    {{ "priority": "low", "issue": "<issue>", "fix": "<specific actionable fix>" }}
  ],
  "missing_keywords": ["<keyword 1>", "<keyword 2>", "<keyword 3>", "<keyword 4>", "<keyword 5>"],
  "ats_score": <integer 0-100>,
  "ats_feedback": "<ATS compatibility assessment>",
  "role_match": <integer 0-100>,
  "role_feedback": "<how well this resume matches {job_role} requirements>"
}}"""

    response = client.chat.completions.create(
        model='llama-3.3-70b-versatile',
        messages=[{'role': 'user', 'content': prompt}],
        max_tokens=2000,
        temperature=0.3
    )

    raw = response.choices[0].message.content.strip()
    
    # Extract JSON from anywhere in the response
    match = re.search(r'\{[\s\S]*\}', raw)
    if not match:
        raise ValueError('No JSON found in response')
    
    clean = match.group(0)
    return json.loads(clean)

# ---- Routes ----
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/history')
def history_page():
    return render_template('history.html')

@app.route('/analyze', methods=['POST'])
def analyze():
    try:
        if 'resume' not in request.files:
            return jsonify({'error': 'No resume file uploaded'}), 400

        file = request.files['resume']
        job_role = request.form.get('job_role', 'Software Engineer').strip()

        if not job_role:
            job_role = 'Software Engineer'

        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400

        ext = file.filename.rsplit('.', 1)[-1].lower()
        if ext not in ['pdf', 'docx', 'txt']:
            return jsonify({'error': 'Please upload a PDF, DOCX, or TXT file'}), 400

        file_bytes = file.read()

        # Extract text
        if ext == 'pdf':
            resume_text = extract_text_from_pdf(file_bytes)
        elif ext == 'docx':
            resume_text = extract_text_from_docx(file_bytes)
        else:
            resume_text = file_bytes.decode('utf-8', errors='ignore')

        if len(resume_text.strip()) < 100:
            return jsonify({'error': 'Could not extract enough text from the resume. Try a different format.'}), 400

        # AI analysis
        result = analyze_resume(resume_text, job_role)

        # Save to DB
        save_analysis(
            file.filename,
            job_role,
            result.get('score', 0),
            result.get('grade', 'N/A'),
            result.get('summary', '')
        )

        return jsonify(result)

    except json.JSONDecodeError:
        return jsonify({'error': 'AI returned invalid response. Please try again.'}), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/history')
def api_history():
    return jsonify(get_history())

@app.route('/api/stats')
def api_stats():
    return jsonify(get_stats())

@app.route('/api/clear', methods=['DELETE'])
def clear_all():
    conn = sqlite3.connect(DB_PATH)
    conn.execute('DELETE FROM analyses')
    conn.commit()
    conn.close()
    return jsonify({'status': 'cleared'})

if __name__ == '__main__':
    print('ResumeIQ starting on http://localhost:5000')
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)), debug=False)



