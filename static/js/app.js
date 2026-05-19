// =====================
// ResumeIQ — app.js
// =====================

const dropZone = document.getElementById('dropZone');
const fileInput = document.getElementById('fileInput');
let selectedFile = null;

// Drag and drop
dropZone.addEventListener('dragover', e => {
  e.preventDefault();
  dropZone.classList.add('drag-over');
});

dropZone.addEventListener('dragleave', () => dropZone.classList.remove('drag-over'));

dropZone.addEventListener('drop', e => {
  e.preventDefault();
  dropZone.classList.remove('drag-over');
  const file = e.dataTransfer.files[0];
  if (file) handleFile(file);
});

fileInput.addEventListener('change', e => {
  if (e.target.files[0]) handleFile(e.target.files[0]);
});

function handleFile(file) {
  const allowed = ['application/pdf', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document', 'text/plain'];
  const ext = file.name.split('.').pop().toLowerCase();
  if (!['pdf', 'docx', 'txt'].includes(ext)) {
    alert('Please upload a PDF, DOCX, or TXT file.');
    return;
  }
  selectedFile = file;
  document.getElementById('fileName').textContent = file.name;
  document.getElementById('dropContent').style.display = 'none';
  document.getElementById('fileSelected').style.display = 'flex';
  dropZone.classList.add('has-file');
}

function removeFile(e) {
  e.stopPropagation();
  selectedFile = null;
  fileInput.value = '';
  document.getElementById('dropContent').style.display = 'block';
  document.getElementById('fileSelected').style.display = 'none';
  dropZone.classList.remove('has-file');
}

async function runAnalysis() {
  const jobRole = document.getElementById('jobRole').value.trim();

  if (!jobRole) {
    document.getElementById('jobRole').focus();
    document.getElementById('jobRole').style.borderColor = '#9a4a4a';
    setTimeout(() => document.getElementById('jobRole').style.borderColor = '', 1500);
    return;
  }

  if (!selectedFile) {
    dropZone.style.borderColor = '#9a4a4a';
    setTimeout(() => dropZone.style.borderColor = '', 1500);
    return;
  }

  const btn = document.getElementById('analyzeBtn');
  const btnText = btn.querySelector('.btn-text');
  const btnLoading = btn.querySelector('.btn-loading');

  btn.disabled = true;
  btnText.style.display = 'none';
  btnLoading.style.display = 'flex';

  const formData = new FormData();
  formData.append('resume', selectedFile);
  formData.append('job_role', jobRole);

  try {
    const response = await fetch('/analyze', {
      method: 'POST',
      body: formData
    });

    const data = await response.json();

    if (data.error) {
      alert('Error: ' + data.error);
      return;
    }

    renderResults(data);

  } catch (err) {
    alert('Could not connect to server. Make sure Flask is running on port 5000.');
  } finally {
    btn.disabled = false;
    btnText.style.display = 'inline';
    btnLoading.style.display = 'none';
  }
}

function renderResults(data) {
  // Show gauge
  const gaugeSection = document.getElementById('gaugeSection');
  gaugeSection.style.display = 'flex';

  // Animate gauge
  animateNumber(document.getElementById('gaugeScore'), 0, data.score, 1000);

  const gradeColors = { 'A+': '#5a9a5a', 'A': '#5a9a5a', 'B+': '#7a9a5a', 'B': '#9a9a4a', 'C+': '#c8a96e', 'C': '#9a7a3a', 'D': '#9a5a3a', 'F': '#9a4a4a' };
  const gradeEl = document.getElementById('gaugeGrade');
  gradeEl.textContent = data.grade;
  gradeEl.style.color = gradeColors[data.grade] || '#c8a96e';

  document.getElementById('gaugeSummary').textContent = data.summary;

  // Animate gauge arc
  setTimeout(() => {
    const fill = document.getElementById('gaugeFill');
    const circumference = 251.2;
    const offset = circumference - (data.score / 100) * circumference;
    fill.style.transition = 'stroke-dashoffset 1s cubic-bezier(0.4,0,0.2,1)';
    fill.style.strokeDashoffset = offset;
    // Color by score
    if (data.score >= 80) fill.style.stroke = '#5a9a5a';
    else if (data.score >= 60) fill.style.stroke = '#c8a96e';
    else fill.style.stroke = '#9a4a4a';
  }, 100);

  // Show results
  document.getElementById('emptyState').style.display = 'none';
  document.getElementById('resultsContent').style.display = 'flex';

  // Mini scores
  animateNumber(document.getElementById('atsScore'), 0, data.ats_score, 800);
  animateNumber(document.getElementById('roleMatch'), 0, data.role_match, 800);
  document.getElementById('atsFeedback').textContent = data.ats_feedback;
  document.getElementById('roleFeedback').textContent = data.role_feedback;

  // Section scores
  const SECTION_LABELS = {
    contact_info: 'Contact Info',
    professional_summary: 'Summary',
    work_experience: 'Work Experience',
    education: 'Education',
    skills: 'Skills',
    achievements: 'Achievements',
    formatting: 'Formatting'
  };

  const statusColors = {
    present: '#5a9a5a', strong: '#5a9a5a', excellent: '#5a9a5a', good: '#7a9a5a',
    average: '#9a7a3a', incomplete: '#9a7a3a', weak: '#9a5a3a',
    missing: '#9a4a4a', poor: '#9a4a4a'
  };

  const sectionsEl = document.getElementById('sectionScores');
  sectionsEl.innerHTML = '';

  if (data.sections) {
    Object.entries(data.sections).forEach(([key, val]) => {
      const color = val.score >= 70 ? '#5a9a5a' : val.score >= 50 ? '#c8a96e' : '#9a4a4a';
      const statusColor = statusColors[val.status] || '#888';
      const row = document.createElement('div');
      row.className = 'section-row';
      row.innerHTML = `
        <div class="section-name">${SECTION_LABELS[key] || key}</div>
        <div class="section-track">
          <div class="section-fill" data-width="${val.score}" style="width:0; background:${color}"></div>
        </div>
        <div class="section-score">${val.score}</div>
        <div class="section-status" style="background:${statusColor}22; color:${statusColor}; border:1px solid ${statusColor}44">${val.status}</div>
      `;
      sectionsEl.appendChild(row);
    });

    setTimeout(() => {
      document.querySelectorAll('.section-fill').forEach(el => {
        el.style.width = el.dataset.width + '%';
      });
    }, 100);
  }

  // Strengths
  const strengthsEl = document.getElementById('strengthsList');
  strengthsEl.innerHTML = (data.strengths || []).map(s => `
    <div class="strength-item">
      <div class="strength-dot"></div>
      <span>${s}</span>
    </div>
  `).join('');

  // Improvements
  const improvEl = document.getElementById('improvementsList');
  improvEl.innerHTML = (data.improvements || []).map(imp => `
    <div class="improvement-item ${imp.priority}">
      <div class="improvement-priority">${imp.priority} priority</div>
      <div class="improvement-issue">${imp.issue}</div>
      <div class="improvement-fix">→ ${imp.fix}</div>
    </div>
  `).join('');

  // Keywords
  const kwEl = document.getElementById('missingKeywords');
  kwEl.innerHTML = (data.missing_keywords || []).map(kw => `
    <span class="keyword-tag">${kw}</span>
  `).join('');

  if (window.innerWidth < 900) {
    document.getElementById('resultsContent').scrollIntoView({ behavior: 'smooth' });
  }
}

function animateNumber(el, from, to, duration) {
  const start = performance.now();
  const update = (time) => {
    const progress = Math.min((time - start) / duration, 1);
    const eased = 1 - Math.pow(1 - progress, 3);
    el.textContent = Math.round(from + (to - from) * eased);
    if (progress < 1) requestAnimationFrame(update);
  };
  requestAnimationFrame(update);
}
