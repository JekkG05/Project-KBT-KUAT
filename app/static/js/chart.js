// chart.js — renders Chart.js dashboards from KUAT_CHART_DATA (injected by home.html)
// KUAT_CHART_DATA shape: { daily: {...}, weekly: {...}, monthly: {...} }

document.addEventListener("DOMContentLoaded", () => {
    if (typeof KUAT_CHART_DATA === "undefined" || typeof Chart === "undefined") {
        return;
    }
    initChartDashboard(KUAT_CHART_DATA);
});

const KUAT_CHART_COLORS = {
    lime: "#b6ff17",
    limeDark: "#8fd600",
    danger: "#ff4d4d",
    warning: "#ffd166",
    muted: "#a9a9a9",
    grid: "rgba(255,255,255,0.08)",
};

const KUAT_PERIOD_LABELS = {
    daily: "(30 HARI TERAKHIR)",
    weekly: "(12 MINGGU TERAKHIR)",
    monthly: "(12 BULAN TERAKHIR)",
};

function emptyChartData() {
    return {
        labels: ["Belum ada data"],
        volume: [0],
        fatigue: [0],
        cns: [0],
        acwr: [1],
        estimated_1rm: [0],
    };
}

function baseOptions(yLabel) {
    return {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
            legend: {
                labels: { color: KUAT_CHART_COLORS.muted },
            },
        },
        scales: {
            x: {
                ticks: { color: KUAT_CHART_COLORS.muted },
                grid: { color: KUAT_CHART_COLORS.grid },
            },
            y: {
                title: { display: !!yLabel, text: yLabel, color: KUAT_CHART_COLORS.muted },
                ticks: { color: KUAT_CHART_COLORS.muted },
                grid: { color: KUAT_CHART_COLORS.grid },
            },
        },
    };
}

function initChartDashboard(allPeriodsData) {
    const volumeCanvas = document.getElementById("volumeChart");
    const fatigueCanvas = document.getElementById("fatigueChart");
    const oneRmCanvas = document.getElementById("oneRmAcwrChart");

    if (!volumeCanvas || !fatigueCanvas || !oneRmCanvas) return;

    let currentPeriod = "daily";

    const volumeChart = new Chart(volumeCanvas.getContext("2d"), {
        type: "bar",
        data: { labels: [], datasets: [{ label: "Volume (kg)", data: [], backgroundColor: KUAT_CHART_COLORS.lime, borderRadius: 6 }] },
        options: baseOptions("kg"),
    });

    const fatigueChart = new Chart(fatigueCanvas.getContext("2d"), {
        type: "line",
        data: {
            labels: [],
            datasets: [
                { label: "Total Fatigue", data: [], borderColor: KUAT_CHART_COLORS.warning, backgroundColor: "rgba(255,209,102,0.15)", tension: 0.3, fill: true },
                { label: "CNS Fatigue", data: [], borderColor: KUAT_CHART_COLORS.danger, backgroundColor: "rgba(255,77,77,0.1)", tension: 0.3, fill: true },
            ],
        },
        options: baseOptions("Skala 0-1"),
    });

    const oneRmChart = new Chart(oneRmCanvas.getContext("2d"), {
        type: "line",
        data: {
            labels: [],
            datasets: [
                { label: "Estimasi 1RM (kg)", data: [], borderColor: KUAT_CHART_COLORS.lime, backgroundColor: "rgba(182,255,23,0.1)", yAxisID: "y", tension: 0.3 },
                { label: "ACWR", data: [], borderColor: "#8fd6ff", backgroundColor: "rgba(143,214,255,0.1)", yAxisID: "y1", tension: 0.3 },
            ],
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: { legend: { labels: { color: KUAT_CHART_COLORS.muted } } },
            scales: {
                x: { ticks: { color: KUAT_CHART_COLORS.muted }, grid: { color: KUAT_CHART_COLORS.grid } },
                y: { position: "left", title: { display: true, text: "kg", color: KUAT_CHART_COLORS.muted }, ticks: { color: KUAT_CHART_COLORS.muted }, grid: { color: KUAT_CHART_COLORS.grid } },
                y1: { position: "right", title: { display: true, text: "ACWR", color: KUAT_CHART_COLORS.muted }, ticks: { color: KUAT_CHART_COLORS.muted }, grid: { display: false } },
            },
        },
    });

    function applyPeriod(period) {
        const data = (allPeriodsData && allPeriodsData[period] && allPeriodsData[period].labels && allPeriodsData[period].labels.length > 0)
            ? allPeriodsData[period]
            : emptyChartData();

        volumeChart.data.labels = data.labels;
        volumeChart.data.datasets[0].data = data.volume;
        volumeChart.update();

        fatigueChart.data.labels = data.labels;
        fatigueChart.data.datasets[0].data = data.fatigue;
        fatigueChart.data.datasets[1].data = data.cns;
        fatigueChart.update();

        oneRmChart.data.labels = data.labels;
        oneRmChart.data.datasets[0].data = data.estimated_1rm;
        oneRmChart.data.datasets[1].data = data.acwr;
        oneRmChart.update();

        const periodLabel = KUAT_PERIOD_LABELS[period] || "";
        const volLabelEl = document.getElementById("volumeChartPeriodLabel");
        const fatLabelEl = document.getElementById("fatigueChartPeriodLabel");
        const ormLabelEl = document.getElementById("oneRmChartPeriodLabel");
        if (volLabelEl) volLabelEl.textContent = periodLabel;
        if (fatLabelEl) fatLabelEl.textContent = periodLabel;
        if (ormLabelEl) ormLabelEl.textContent = periodLabel;
    }

    document.querySelectorAll(".period-btn").forEach((btn) => {
        btn.addEventListener("click", () => {
            if (btn.dataset.period === currentPeriod) return;
            currentPeriod = btn.dataset.period;

            document.querySelectorAll(".period-btn").forEach((b) => b.classList.remove("active"));
            btn.classList.add("active");

            applyPeriod(currentPeriod);
        });
    });

    applyPeriod(currentPeriod);
}
