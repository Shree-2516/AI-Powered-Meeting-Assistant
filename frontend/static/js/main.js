const dropZone = document.getElementById('dropZone');
const audioInput = document.getElementById('audioInput');
const fileInfo = document.getElementById('fileInfo');
const fileName = document.getElementById('fileName');
const clearFile = document.getElementById('clearFile');
const uploadForm = document.getElementById('uploadForm');
const submitBtn = document.getElementById('submitBtn');
const btnText = document.getElementById('btnText');
const btnLoader = document.getElementById('btnLoader');
const loadingOverlay = document.getElementById('loadingOverlay');

if (audioInput) {
  audioInput.addEventListener('change', function () {
    if (this.files && this.files[0]) showFile(this.files[0]);
  });
}

if (dropZone) {
  dropZone.addEventListener('dragover', (e) => {
    e.preventDefault();
    dropZone.classList.add('dragover');
  });
  dropZone.addEventListener('dragleave', () => {
    dropZone.classList.remove('dragover');
  });
  dropZone.addEventListener('drop', (e) => {
    e.preventDefault();
    dropZone.classList.remove('dragover');
    const file = e.dataTransfer.files[0];
    if (file) {
      const dt = new DataTransfer();
      dt.items.add(file);
      audioInput.files = dt.files;
      showFile(file);
    }
  });
}

function showFile(file) {
  const sizeMB = (file.size / 1024 / 1024).toFixed(1);
  fileName.textContent = `${file.name}  (${sizeMB} MB)`;
  fileInfo.style.display = 'block';

  // Warn if large file
  if (file.size > 50 * 1024 * 1024) {
    const warn = document.getElementById('sizeWarning');
    if (warn) warn.style.display = 'block';
  }
}

if (clearFile) {
  clearFile.addEventListener('click', () => {
    audioInput.value = '';
    fileInfo.style.display = 'none';
    const warn = document.getElementById('sizeWarning');
    if (warn) warn.style.display = 'none';
  });
}

if (uploadForm) {
  uploadForm.addEventListener('submit', function () {
    if (!audioInput.files || audioInput.files.length === 0) return;

    const fileSizeMB = audioInput.files[0].size / 1024 / 1024;
    const estMinutes = Math.max(2, Math.ceil(fileSizeMB / 5));

    // Update loading subtitle with estimate
    const loadingSub = document.querySelector('.loading-sub');
    if (loadingSub) {
      loadingSub.textContent = `Estimated time: ${estMinutes}–${estMinutes + 3} minutes. Please keep this tab open.`;
    }

    submitBtn.disabled = true;
    btnText.style.display = 'none';
    btnLoader.style.display = 'inline';
    loadingOverlay.classList.add('active');

    // Step timings based on file size
    const step1Delay = Math.max(30000, fileSizeMB * 3000);
    const step2Delay = step1Delay + 20000;

    setTimeout(() => activateStep('step2'), step1Delay);
    setTimeout(() => activateStep('step3'), step2Delay);
  });
}

function activateStep(stepId) {
  document.querySelectorAll('.step').forEach(s => s.classList.remove('active'));
  const el = document.getElementById(stepId);
  if (el) el.classList.add('active');
}

// Activate step 1 immediately on load
document.addEventListener('DOMContentLoaded', () => {
  const s1 = document.getElementById('step1');
  if (s1) s1.classList.add('active');
});