/* ==========================================================================
   ComicCraft — Interactive UI Script
   ========================================================================== */

document.addEventListener("DOMContentLoaded", () => {
  // 1. Quick Inspiration Presets
  const presetButtons = document.querySelectorAll(".preset-btn");
  const promptInput = document.getElementById("story_prompt");
  const characterInput = document.getElementById("character_name");
  const settingInput = document.getElementById("setting");
  const toneSelect = document.getElementById("story_tone");
  const styleSelect = document.getElementById("art_style");

  presetButtons.forEach((btn) => {
    btn.addEventListener("click", () => {
      if (promptInput) promptInput.value = btn.dataset.prompt || "";
      if (characterInput) characterInput.value = btn.dataset.character || "";
      if (settingInput) settingInput.value = btn.dataset.setting || "";
      if (toneSelect && btn.dataset.tone) toneSelect.value = btn.dataset.tone;
      if (styleSelect && btn.dataset.style) styleSelect.value = btn.dataset.style;

      // Subtle pulse effect on form
      const formCard = document.querySelector(".form-card");
      if (formCard) {
        formCard.style.transition = "transform 0.2s ease";
        formCard.style.transform = "scale(1.01)";
        setTimeout(() => {
          formCard.style.transform = "scale(1)";
        }, 200);
      }
    });
  });

  // 2. Form Submission & Generation Progress Modal
  const comicForm = document.getElementById("comicForm");
  const loadingModal = document.getElementById("loadingModal");
  const submitBtn = document.getElementById("submitBtn");

  if (comicForm && loadingModal) {
    comicForm.addEventListener("submit", (e) => {
      // Basic validation
      if (!comicForm.checkValidity()) {
        return;
      }

      // Show modal
      loadingModal.style.display = "flex";
      if (submitBtn) {
        submitBtn.disabled = true;
        submitBtn.innerHTML = `<span>⚡ GENERATING COMIC...</span>`;
      }

      // Step simulation for visual feedback
      const steps = [
        document.getElementById("step1"),
        document.getElementById("step2"),
        document.getElementById("step3"),
        document.getElementById("step4")
      ];

      let currentStep = 0;
      const interval = setInterval(() => {
        if (currentStep < steps.length - 1) {
          steps[currentStep].classList.remove("active");
          currentStep++;
          steps[currentStep].classList.add("active");
        } else {
          clearInterval(interval);
        }
      }, 2500);
    });
  }

  // 3. Smooth preview download tracking
  const downloadPdfBtn = document.getElementById("downloadPdfBtn");
  if (downloadPdfBtn) {
    downloadPdfBtn.addEventListener("click", () => {
      const href = downloadPdfBtn.getAttribute("href");
      console.log(`Downloading comic PDF: ${href}`);
    });
  }
});
