// main.js — utilities shared across all KUAT pages

document.addEventListener("DOMContentLoaded", () => {
    initNavbarToggle();
    initFlashAutoDismiss();
    initSignupStepper();
});

/* ---------------------------------------------------------
   Navbar mobile toggle
   --------------------------------------------------------- */
function initNavbarToggle() {
    const toggleBtn = document.getElementById("navbarToggle");
    const links = document.querySelector(".navbar-links");
    if (!toggleBtn || !links) return;

    toggleBtn.addEventListener("click", () => {
        links.classList.toggle("open");
    });
}

/* ---------------------------------------------------------
   Flash messages auto dismiss
   --------------------------------------------------------- */
function initFlashAutoDismiss() {
    const messages = document.querySelectorAll(".flash-message");
    messages.forEach((msg) => {
        setTimeout(() => {
            msg.style.transition = "opacity 0.3s ease";
            msg.style.opacity = "0";
            setTimeout(() => msg.remove(), 300);
        }, 5000);
    });
}

/* ---------------------------------------------------------
   Signup stepper (3 steps)
   --------------------------------------------------------- */
function initSignupStepper() {
    const form = document.getElementById("signupForm");
    if (!form) return;

    const steps = Array.from(form.querySelectorAll(".form-step"));
    const dots = Array.from(document.querySelectorAll(".step-dot"));
    let currentStep = 1;

    function showStep(stepNumber) {
        steps.forEach((stepEl) => {
            stepEl.classList.toggle("active", parseInt(stepEl.dataset.step, 10) === stepNumber);
        });
        dots.forEach((dot) => {
            dot.classList.toggle("active", parseInt(dot.dataset.stepDot, 10) <= stepNumber);
        });
        currentStep = stepNumber;
    }

    function validateStep(stepEl) {
        const inputs = stepEl.querySelectorAll("input[required], select[required]");
        for (const input of inputs) {
            if (!input.checkValidity()) {
                input.reportValidity();
                return false;
            }
        }
        return true;
    }

    form.querySelectorAll(".step-next").forEach((btn) => {
        btn.addEventListener("click", () => {
            const activeStepEl = form.querySelector(`.form-step[data-step="${currentStep}"]`);
            if (!validateStep(activeStepEl)) return;
            showStep(Math.min(currentStep + 1, steps.length));
        });
    });

    form.querySelectorAll(".step-prev").forEach((btn) => {
        btn.addEventListener("click", () => {
            showStep(Math.max(currentStep - 1, 1));
        });
    });

    showStep(1);
}

/* ---------------------------------------------------------
   Utility: format seconds as HH:MM:SS or MM:SS
   --------------------------------------------------------- */
function formatTimer(totalSeconds, withHours = true) {
    const hours = Math.floor(totalSeconds / 3600);
    const minutes = Math.floor((totalSeconds % 3600) / 60);
    const seconds = Math.floor(totalSeconds % 60);

    const pad = (n) => String(n).padStart(2, "0");

    if (withHours) {
        return `${pad(hours)}:${pad(minutes)}:${pad(seconds)}`;
    }
    return `${pad(minutes)}:${pad(seconds)}`;
}
