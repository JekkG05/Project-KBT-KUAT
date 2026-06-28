document.addEventListener("DOMContentLoaded", () => {
    const data = window.KUAT_CHART_DATA || { labels: [], one_rm: [], fatigue: [], acwr: [] };
    const baseOptions = {
        responsive: true,
        maintainAspectRatio: false,
        plugins: { legend: { labels: { color: "#f5f5f5" } } },
        scales: {
            x: { ticks: { color: "#cfcfcf" }, grid: { color: "rgba(255,255,255,.08)" } },
            y: { ticks: { color: "#cfcfcf" }, grid: { color: "rgba(255,255,255,.08)" } }
        }
    };

    const render = (id, label, values) => {
        const canvas = document.getElementById(id);
        if (!canvas) return;
        new Chart(canvas, {
            type: "line",
            data: {
                labels: data.labels,
                datasets: [{ label, data: values, tension: 0.35, borderWidth: 3, pointRadius: 3 }]
            },
            options: baseOptions
        });
    };

    render("oneRmChart", "Estimated 1RM", data.one_rm);
    render("fatigueChart", "Fatigue Total", data.fatigue);
    render("acwrChart", "ACWR", data.acwr);
});
