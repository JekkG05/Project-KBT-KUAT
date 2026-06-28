(() => {
    const ctx = window.KUAT_TRAIN_CONTEXT;
    if (!ctx) return;

    const $ = (id) => document.getElementById(id);
    let seconds = 0;
    let timerHandle = null;
    let restHandle = null;
    let currentSet = 1;
    let totalVolume = 0;

    function pad(n) { return String(n).padStart(2, "0"); }
    function formatHMS(s) {
        const h = Math.floor(s / 3600);
        const m = Math.floor((s % 3600) / 60);
        const sec = s % 60;
        return `${pad(h)}:${pad(m)}:${pad(sec)}`;
    }
    function startWorkoutTimer() {
        if (timerHandle) return;
        timerHandle = setInterval(() => {
            seconds += 1;
            $("workoutTimer").textContent = formatHMS(seconds);
        }, 1000);
    }
    function stopWorkoutTimer() {
        clearInterval(timerHandle);
        timerHandle = null;
    }
    function startRestTimer(duration = 120) {
        clearInterval(restHandle);
        let left = duration;
        $("restTimer").textContent = `${pad(Math.floor(left / 60))}:${pad(left % 60)}`;
        restHandle = setInterval(() => {
            left -= 1;
            $("restTimer").textContent = `${pad(Math.floor(left / 60))}:${pad(Math.max(0, left % 60))}`;
            if (left <= 0) clearInterval(restHandle);
        }, 1000);
    }
    function toast(message) {
        const node = document.createElement("div");
        node.className = "toast";
        node.textContent = message;
        $("toastRoot").appendChild(node);
        setTimeout(() => node.remove(), 5200);
    }
    function dangerModal(message) {
        stopWorkoutTimer();
        $("doneSet").disabled = true;
        $("doneSet").style.opacity = "0.55";
        $("dangerMessage").textContent = message;
        $("dangerModal").hidden = false;
    }
    function updateUI(result) {
        const cns = Number(result.cns_fatigue || 0);
        const total = Number(result.total_fatigue || 0);
        const acwr = Number(result.acwr || 0);
        $("cnsLabel").textContent = cns.toFixed(3);
        $("fatigueLabel").textContent = total.toFixed(3);
        $("acwrLabel").textContent = acwr.toFixed(3);
        $("fsmState").textContent = result.fsm_state || "Segar";
        $("cnsBar").style.width = `${Math.min(100, cns * 100).toFixed(1)}%`;
    }

    $("startTimer")?.addEventListener("click", startWorkoutTimer);
    $("startRest")?.addEventListener("click", () => startRestTimer(ctx.cluster === "A" ? 180 : ctx.cluster === "B" ? 120 : 60));
    $("rpeInput")?.addEventListener("input", (e) => { $("rpeValue").textContent = e.target.value; });

    $("doneSet")?.addEventListener("click", async () => {
        startWorkoutTimer();
        const reps = Number($("actualReps").value);
        const beban = Number($("actualLoad").value);
        const rpe = Number($("rpeInput").value);

        const response = await fetch(ctx.logUrl, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                plan_id: ctx.planId,
                nama: ctx.nama,
                cluster: ctx.cluster,
                reps,
                beban,
                rpe
            })
        });
        const result = await response.json();
        if (!response.ok) {
            toast(result.error || "Gagal menyimpan set.");
            return;
        }

        totalVolume += beban * reps;
        $("totalVolume").textContent = `${totalVolume.toFixed(1)} kg`;
        updateUI(result);

        const warnings = result.warnings || [];
        const danger = warnings.find((w) => w.level === "DANGER");
        const warning = warnings.find((w) => w.level === "WARNING");
        if (danger) {
            dangerModal(danger.message);
            return;
        }
        if (warning) toast(warning.message);

        currentSet = Math.min(ctx.targetSets, currentSet + 1);
        $("currentSet").textContent = `${currentSet} / ${ctx.targetSets}`;
        startRestTimer(ctx.cluster === "A" ? 180 : ctx.cluster === "B" ? 120 : 60);
        if (currentSet >= ctx.targetSets) {
            toast("Target set selesai. Evaluasi teknik dan fatigue sebelum menambah volume.");
        }
    });
})();
