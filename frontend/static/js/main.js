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
    if (this.files && this.files[0]) {
      showFile(this.files[0]);
    }
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
}

if (clearFile) {
  clearFile.addEventListener('click', () => {
    audioInput.value = '';
    fileInfo.style.display = 'none';
  });
}

if (uploadForm) {
  uploadForm.addEventListener('submit', function (e) {
    if (!audioInput.files || audioInput.files.length === 0) return;

    submitBtn.disabled = true;
    btnText.style.display = 'none';
    btnLoader.style.display = 'inline';
    loadingOverlay.classList.add('active');

    // Cycle through loading steps
    const steps = ['step1', 'step2', 'step3'];
    let currentStep = 0;

    const interval = setInterval(() => {
      if (currentStep > 0) {
        document.getElementById(steps[currentStep - 1])?.classList.remove('active');
      }
      if (currentStep < steps.length) {
        document.getElementById(steps[currentStep])?.classList.add('active');
        currentStep++;
      } else {
        clearInterval(interval);
      }
    }, 25000);
  });
}