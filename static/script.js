/* ═══════════════════════════════════════════════════════════════════
   EdgeVision — Frontend Logic
   ═══════════════════════════════════════════════════════════════════ */

(() => {
  "use strict";

  // ── DOM refs ───────────────────────────────────────────────────
  const $ = (sel) => document.querySelector(sel);
  const dropZone       = $("#drop-zone");
  const fileInput      = $("#file-input");
  const uploadSection  = $("#upload-section");
  const resultsSection = $("#results-section");
  const originalImg    = $("#original-img");
  const processedImg   = $("#processed-img");
  const algorithmSel   = $("#algorithm-select");
  const algoTrigger    = algorithmSel.querySelector(".custom-select-trigger");
  const algoLabel      = algorithmSel.querySelector(".custom-select-label");
  const algoOptions    = algorithmSel.querySelectorAll(".custom-select-option");
  const intensitySlider = $("#intensity-slider");
  const intensityValue  = $("#intensity-value");
  const downloadBtn    = $("#download-btn");
  const newImageBtn    = $("#new-image-btn");
  const themeToggle    = $("#theme-toggle");
  const loadingOverlay = $("#loading-overlay");

  // ── State ──────────────────────────────────────────────────────
  let imageBase64 = null;   // raw base64 (no prefix)
  let debounceTimer = null;
  const DEBOUNCE_MS = 300;

  // ── Theme ──────────────────────────────────────────────────────
  const savedTheme = localStorage.getItem("edgevision-theme") || "light";
  document.documentElement.setAttribute("data-theme", savedTheme);

  themeToggle.addEventListener("click", () => {
    const current = document.documentElement.getAttribute("data-theme");
    const next = current === "light" ? "dark" : "light";
    document.documentElement.setAttribute("data-theme", next);
    localStorage.setItem("edgevision-theme", next);
  });

  // ── Drag & drop ────────────────────────────────────────────────
  dropZone.addEventListener("click", () => fileInput.click());

  dropZone.addEventListener("dragover", (e) => {
    e.preventDefault();
    dropZone.classList.add("drag-over");
  });

  dropZone.addEventListener("dragleave", () => {
    dropZone.classList.remove("drag-over");
  });

  dropZone.addEventListener("drop", (e) => {
    e.preventDefault();
    dropZone.classList.remove("drag-over");
    const file = e.dataTransfer.files[0];
    if (file && file.type.startsWith("image/")) handleFile(file);
  });

  fileInput.addEventListener("change", () => {
    const file = fileInput.files[0];
    if (file) handleFile(file);
  });

  // ── Handle uploaded file ───────────────────────────────────────
  function handleFile(file) {
    if (file.size > 10 * 1024 * 1024) {
      alert("File is too large. Please upload an image under 10 MB.");
      return;
    }

    const reader = new FileReader();
    reader.onload = (e) => {
      const dataUrl = e.target.result;          // data:image/png;base64,XXXXX
      imageBase64 = dataUrl.split(",")[1];       // strip prefix
      originalImg.src = dataUrl;

      // Show results, hide upload
      uploadSection.classList.add("hidden");
      resultsSection.classList.remove("hidden");

      // Animate cards in
      resultsSection.style.animation = "none";
      void resultsSection.offsetHeight;          // reflow
      resultsSection.style.animation = "";

      processImage();
    };
    reader.readAsDataURL(file);
  }

  // ── Process image via API ──────────────────────────────────────
  async function processImage() {
    if (!imageBase64) return;

    showLoading(true);

    const body = {
      image:     imageBase64,
      algorithm: algorithmSel.dataset.value,
      intensity: parseInt(intensitySlider.value, 10),
    };

    try {
      const res = await fetch("/api/process", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
      });

      const data = await res.json();

      if (data.error) {
        console.error("Processing error:", data.error);
        alert("Error processing image: " + data.error);
      } else {
        processedImg.src = "data:image/png;base64," + data.image;
        processedImg.style.opacity = 0;
        requestAnimationFrame(() => {
          processedImg.style.opacity = 1;
        });
      }
    } catch (err) {
      console.error("Network error:", err);
      alert("Could not connect to the server. Is the backend running?");
    } finally {
      showLoading(false);
    }
  }

  // ── Debounced re-process ───────────────────────────────────────
  function scheduleProcess() {
    clearTimeout(debounceTimer);
    debounceTimer = setTimeout(processImage, DEBOUNCE_MS);
  }

  // ── Slider events ─────────────────────────────────────────────
  intensitySlider.addEventListener("input", () => {
    intensityValue.textContent = intensitySlider.value;
    scheduleProcess();
  });

  // ── Custom dropdown ────────────────────────────────────────────
  algoTrigger.addEventListener("click", (e) => {
    e.stopPropagation();
    algorithmSel.classList.toggle("open");
  });

  algoOptions.forEach((opt) => {
    opt.addEventListener("click", () => {
      algoOptions.forEach((o) => o.classList.remove("selected"));
      opt.classList.add("selected");
      algorithmSel.dataset.value = opt.dataset.value;
      algoLabel.textContent = opt.textContent;
      algorithmSel.classList.remove("open");
      processImage();
    });
  });

  // Close dropdown when clicking outside
  document.addEventListener("click", () => {
    algorithmSel.classList.remove("open");
  });

  algorithmSel.addEventListener("click", (e) => e.stopPropagation());

  // ── Download ───────────────────────────────────────────────────
  downloadBtn.addEventListener("click", () => {
    if (!processedImg.src) return;
    const a = document.createElement("a");
    a.href = processedImg.src;
    a.download = `edgevision-${algorithmSel.dataset.value}-${Date.now()}.png`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
  });

  // ── New image ──────────────────────────────────────────────────
  newImageBtn.addEventListener("click", () => {
    imageBase64 = null;
    originalImg.src = "";
    processedImg.src = "";
    fileInput.value = "";
    resultsSection.classList.add("hidden");
    uploadSection.classList.remove("hidden");

    // Animate upload card back in
    uploadSection.style.animation = "none";
    void uploadSection.offsetHeight;
    uploadSection.style.animation = "";
  });

  // ── Loading overlay ────────────────────────────────────────────
  function showLoading(on) {
    loadingOverlay.classList.toggle("hidden", !on);
  }
})();
