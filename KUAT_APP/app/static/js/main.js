document.addEventListener("DOMContentLoaded", () => {
    const path = window.location.pathname;
    document.querySelectorAll(".nav-link").forEach((link) => {
        const href = link.getAttribute("href") || "";
        if (href !== "/" && path.startsWith(href)) link.classList.add("active");
        if (href === "/" && path === "/") link.classList.add("active");
    });

    document.querySelectorAll("[data-stepper]").forEach((stepper) => {
        let step = 0;
        const panels = [...stepper.querySelectorAll(".step-panel")];
        const dots = [...stepper.querySelectorAll(".step-dot")];
        const show = (idx) => {
            step = Math.max(0, Math.min(idx, panels.length - 1));
            panels.forEach((panel, i) => panel.classList.toggle("active", i === step));
            dots.forEach((dot, i) => dot.classList.toggle("active", i === step));
        };
        stepper.querySelectorAll(".next-step").forEach((btn) => btn.addEventListener("click", () => show(step + 1)));
        stepper.querySelectorAll(".prev-step").forEach((btn) => btn.addEventListener("click", () => show(step - 1)));
        dots.forEach((dot) => dot.addEventListener("click", () => show(Number(dot.dataset.stepTarget || 0))));
    });

    const energy = document.getElementById("energyRange");
    const output = document.getElementById("energyOutput");
    if (energy && output) {
        energy.addEventListener("input", () => { output.textContent = energy.value; });
    }

    document.querySelectorAll("[data-select-exercise]").forEach((btn) => {
        btn.addEventListener("click", () => {
            const id = btn.dataset.selectExercise;
            const select = document.getElementById("exerciseSelect");
            if (select) select.value = id;
            document.querySelectorAll("[data-exercise-card]").forEach((card) => card.classList.toggle("selected", card.dataset.id === id));
            window.scrollTo({ top: 0, behavior: "smooth" });
        });
    });
});
