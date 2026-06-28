// train.js — logic for the active training session page (train.html)
//
// Revisi:
//  - Tracking set dilakukan satu-per-satu (SET 1/3, SET 2/3, dst) per gerakan,
//    setiap set mengukur RIR -> RPE sendiri-sendiri.
//  - Saat semua target_sets pada satu gerakan selesai, otomatis pindah ke
//    gerakan berikutnya (set kembali ke 1).
//  - Tombol "DONE LATIHAN" menutup sesi: menghitung ringkasan (total set,
//    total volume, rata-rata RPE, durasi, fatigue & FSM akhir) dari seluruh
//    set yang sudah dicatat selama sesi ini, lalu kembali ke Home.

document.addEventListener("DOMContentLoaded", () => {
    if (typeof KUAT_ITEMS === "undefined") return;

    const state = {
        items: KUAT_ITEMS || [],
        currentIndex: 0,
        currentSet: 1,
        workoutSeconds: 0,
        workoutInterval: null,
        workoutRunning: false,
        restSeconds: 0,
        restInterval: null,
        lastCns: 0,
        lastFsm: "SEGAR",
        session: {
            totalSets: 0,
            totalVolume: 0,
            rpeSum: 0,
        },
    };

    const els = {
        workoutTimer: document.getElementById("workoutTimer"),
        restTimer: document.getElementById("restTimer"),
        startWorkoutBtn: document.getElementById("startWorkoutBtn"),
        startWorkoutIconPlay: document.getElementById("startWorkoutIconPlay"),
        startWorkoutIconPause: document.getElementById("startWorkoutIconPause"),
        startWorkoutLabel: document.getElementById("startWorkoutLabel"),
        startRestBtn: document.getElementById("startRestBtn"),
        setProgressText: document.getElementById("setProgressText"),
        exerciseProgressText: document.getElementById("exerciseProgressText"),
        currentExerciseName: document.getElementById("currentExerciseName"),
        currentTargetSets: document.getElementById("currentTargetSets"),
        currentTargetReps: document.getElementById("currentTargetReps"),
        currentTargetWeight: document.getElementById("currentTargetWeight"),
        bebanInput: document.getElementById("bebanInput"),
        repsInput: document.getElementById("repsInput"),
        rirSlider: document.getElementById("rirSlider"),
        rirValue: document.getElementById("rirValue"),
        rpePreview: document.getElementById("rpePreview"),
        doneSetBtn: document.getElementById("doneSetBtn"),
        doneSetLabel: document.getElementById("doneSetLabel"),
        nextExerciseBtn: document.getElementById("nextExerciseBtn"),
        finishWorkoutBtn: document.getElementById("finishWorkoutBtn"),
        cnsFatigueBar: document.getElementById("cnsFatigueBar"),
        cnsFatigueValue: document.getElementById("cnsFatigueValue"),
        fsmStateLabel: document.getElementById("fsmStateLabel"),
        toastContainer: document.getElementById("toastContainer"),
        dangerModal: document.getElementById("dangerModal"),
        dangerModalMessage: document.getElementById("dangerModalMessage"),
        closeDangerModal: document.getElementById("closeDangerModal"),
        summaryModal: document.getElementById("summaryModal"),
        summaryTotalSets: document.getElementById("summaryTotalSets"),
        summaryTotalVolume: document.getElementById("summaryTotalVolume"),
        summaryAvgRpe: document.getElementById("summaryAvgRpe"),
        summaryDuration: document.getElementById("summaryDuration"),
        summaryCns: document.getElementById("summaryCns"),
        summaryFsm: document.getElementById("summaryFsm"),
        summaryBackToHomeBtn: document.getElementById("summaryBackToHomeBtn"),
        exerciseCards: document.querySelectorAll(".train-exercise-card"),
    };

    initRirSlider();
    initWorkoutTimer();
    initRestTimer();
    initDoneSet();
    initNextExercise();
    initFinishWorkout();
    initDangerModalClose();
    highlightActiveCard();
    highlightActiveSetRow();

    /* -----------------------------------------------------
       RIR slider -> live RPE conversion (RPE = 10 - RIR)
       ----------------------------------------------------- */
    function initRirSlider() {
        if (!els.rirSlider) return;
        updateRpePreview();
        els.rirSlider.addEventListener("input", updateRpePreview);
    }

    function updateRpePreview() {
        const rir = parseInt(els.rirSlider.value, 10);
        els.rirValue.textContent = rir;
        const rpe = Math.max(5, Math.min(10, 10 - rir));
        els.rpePreview.textContent = rpe;
    }

    /* -----------------------------------------------------
       Workout timer (juga dipakai untuk durasi di ringkasan)
       ----------------------------------------------------- */
    function initWorkoutTimer() {
        if (!els.startWorkoutBtn) return;
        els.startWorkoutBtn.addEventListener("click", () => {
            if (state.workoutRunning) {
                stopWorkoutTimer();
                setWorkoutButtonState(false);
            } else {
                startWorkoutTimer();
                setWorkoutButtonState(true);
            }
        });
    }

    function setWorkoutButtonState(isRunning) {
        if (els.startWorkoutIconPlay) els.startWorkoutIconPlay.classList.toggle("icon-hidden", isRunning);
        if (els.startWorkoutIconPause) els.startWorkoutIconPause.classList.toggle("icon-hidden", !isRunning);
        if (els.startWorkoutLabel) els.startWorkoutLabel.textContent = isRunning ? "PAUSE" : "START";
    }

    function startWorkoutTimer() {
        if (state.workoutRunning) return;
        state.workoutRunning = true;
        state.workoutInterval = setInterval(() => {
            state.workoutSeconds += 1;
            els.workoutTimer.textContent = formatTimer(state.workoutSeconds, true);
        }, 1000);
    }

    function stopWorkoutTimer() {
        state.workoutRunning = false;
        clearInterval(state.workoutInterval);
    }

    /* -----------------------------------------------------
       Rest timer (countdown 90 detik tetap)
       ----------------------------------------------------- */
    function initRestTimer() {
        if (!els.startRestBtn) return;
        els.startRestBtn.addEventListener("click", () => {
            clearInterval(state.restInterval);
            state.restSeconds = 90;
            els.restTimer.textContent = formatTimer(state.restSeconds, false);

            state.restInterval = setInterval(() => {
                state.restSeconds -= 1;
                if (state.restSeconds <= 0) {
                    clearInterval(state.restInterval);
                    els.restTimer.textContent = "00:00";
                    showToast({ level: "WARNING", message: "⏱️ Rest selesai, lanjutkan set berikutnya." });
                    return;
                }
                els.restTimer.textContent = formatTimer(state.restSeconds, false);
            }, 1000);
        });
    }

    /* -----------------------------------------------------
       Done Set -> AJAX POST /train/log_set
       Setiap set diukur RIR/RPE-nya sendiri, lalu otomatis
       maju ke set berikutnya (atau gerakan berikutnya bila
       target_sets gerakan ini sudah tercapai).
       ----------------------------------------------------- */
    function initDoneSet() {
        if (!els.doneSetBtn) return;
        els.doneSetBtn.addEventListener("click", async () => {
            const currentItem = state.items[state.currentIndex];
            if (!currentItem) return;

            const payload = {
                plan_id: KUAT_PLAN_ID,
                plan_item_id: currentItem.id,
                nama: currentItem.nama_gerakan,
                cluster: currentItem.cluster,
                beban: parseFloat(els.bebanInput.value),
                reps: parseInt(els.repsInput.value, 10),
                rir: parseInt(els.rirSlider.value, 10),
            };

            if (!payload.beban || payload.beban <= 0) {
                showToast({ level: "WARNING", message: "Beban harus lebih besar dari 0." });
                return;
            }
            if (!payload.reps || payload.reps <= 0) {
                showToast({ level: "WARNING", message: "Reps harus lebih besar dari 0." });
                return;
            }

            els.doneSetBtn.disabled = true;
            if (els.doneSetLabel) els.doneSetLabel.textContent = "MENYIMPAN...";

            try {
                const response = await fetch("/train/log_set", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify(payload),
                });

                const data = await response.json();

                if (!data.success) {
                    showToast({ level: "WARNING", message: data.error || "Gagal menyimpan set." });
                    return;
                }

                // Akumulasi statistik sesi (dipakai oleh tombol DONE LATIHAN)
                state.session.totalSets += 1;
                state.session.totalVolume += data.volume || 0;
                state.session.rpeSum += data.rpe_converted || 0;
                state.lastCns = data.cns_fatigue || 0;
                state.lastFsm = data.fsm_state || "SEGAR";

                updateCnsBar(data.cns_fatigue);
                updateFSM(data.fsm_state);
                handleWarnings(data.warnings);

                advanceAfterSet(currentItem);
            } catch (err) {
                showToast({ level: "WARNING", message: "Koneksi gagal. Coba lagi." });
            } finally {
                els.doneSetBtn.disabled = false;
                if (els.doneSetLabel) els.doneSetLabel.textContent = "DONE SET";
            }
        });
    }

    /* -----------------------------------------------------
       Maju ke set berikutnya, atau ke gerakan berikutnya
       bila set gerakan saat ini sudah lengkap.
       ----------------------------------------------------- */
    function advanceAfterSet(currentItem) {
        if (state.currentSet < currentItem.target_sets) {
            state.currentSet += 1;
            updateSetProgressUI();
            highlightActiveSetRow();
            showToast({
                level: "WARNING",
                message: `Set ${state.currentSet - 1} tersimpan. Lanjut ke SET ${state.currentSet} dari ${currentItem.target_sets}.`,
            });
            return;
        }

        // Semua set gerakan ini selesai
        markExerciseCompleted(state.currentIndex);

        if (state.currentIndex < state.items.length - 1) {
            state.currentIndex += 1;
            state.currentSet = 1;
            loadCurrentExercise();
            highlightActiveCard();
            highlightActiveSetRow();
            showToast({
                level: "WARNING",
                message: `Gerakan selesai! Lanjut ke "${state.items[state.currentIndex].nama_gerakan}".`,
            });
        } else {
            showToast({
                level: "WARNING",
                message: "🎉 Semua gerakan & set sudah selesai. Klik DONE LATIHAN untuk menutup sesi.",
            });
        }
    }

    function updateSetProgressUI() {
        const item = state.items[state.currentIndex];
        if (!item || !els.setProgressText) return;
        els.setProgressText.textContent = `SET ${state.currentSet} / ${item.target_sets}`;
    }

    function markExerciseCompleted(index) {
        els.exerciseCards.forEach((card) => {
            if (parseInt(card.dataset.index, 10) === index) {
                card.classList.add("completed-exercise");
            }
        });
    }

    function highlightActiveSetRow() {
        els.exerciseCards.forEach((card) => {
            const idx = parseInt(card.dataset.index, 10);
            const rows = card.querySelectorAll(".set-table tbody tr");
            rows.forEach((row) => {
                const setNum = parseInt(row.dataset.set, 10);
                const isActive = idx === state.currentIndex && setNum === state.currentSet;
                row.classList.toggle("active-set-row", isActive);
            });
        });
    }

    function updateCnsBar(cnsFatigue) {
        if (!els.cnsFatigueBar) return;
        const pct = Math.round((cnsFatigue || 0) * 100);
        els.cnsFatigueBar.style.width = `${pct}%`;
        els.cnsFatigueValue.textContent = `${pct}%`;
    }

    function updateFSM(fsmState) {
        if (!els.fsmStateLabel) return;
        els.fsmStateLabel.textContent = fsmState;
        els.fsmStateLabel.className = "fsm-pill fsm-" + (fsmState || "segar").toLowerCase();
    }

    function handleWarnings(warnings) {
        // Untuk user free, backend selalu mengirim warnings = [].
        // Frontend hanya membaca warnings, tidak menampilkan apapun jika kosong.
        if (!warnings || warnings.length === 0) return;

        warnings.forEach((w) => {
            if (w.level === "DANGER") {
                showDangerModal(w.message);
                disableDoneButton();
                stopWorkoutTimer();
            } else if (w.level === "WARNING") {
                showToast(w);
            }
        });
    }

    function disableDoneButton() {
        if (els.doneSetBtn) {
            els.doneSetBtn.disabled = true;
            if (els.doneSetLabel) els.doneSetLabel.textContent = "FORCED REST";
        }
    }

    /* -----------------------------------------------------
       Toast (WARNING level / info)
       ----------------------------------------------------- */
    function showToast(warning) {
        if (!els.toastContainer) return;
        const toast = document.createElement("div");
        toast.className = "toast";
        toast.textContent = warning.message;
        els.toastContainer.appendChild(toast);

        setTimeout(() => {
            toast.style.transition = "opacity 0.3s ease";
            toast.style.opacity = "0";
            setTimeout(() => toast.remove(), 300);
        }, 4500);
    }

    /* -----------------------------------------------------
       Danger modal (DANGER level / forced rest)
       ----------------------------------------------------- */
    function showDangerModal(message) {
        if (!els.dangerModal) return;
        els.dangerModalMessage.textContent = message;
        els.dangerModal.classList.add("open");
    }

    function initDangerModalClose() {
        if (!els.closeDangerModal) return;
        els.closeDangerModal.addEventListener("click", () => {
            els.dangerModal.classList.remove("open");
        });
    }

    /* -----------------------------------------------------
       Skip manual ke gerakan berikutnya (override)
       ----------------------------------------------------- */
    function initNextExercise() {
        if (!els.nextExerciseBtn) return;
        els.nextExerciseBtn.addEventListener("click", () => {
            if (state.items.length === 0) return;
            state.currentIndex = (state.currentIndex + 1) % state.items.length;
            state.currentSet = 1;
            loadCurrentExercise();
            highlightActiveCard();
            highlightActiveSetRow();
        });
    }

    function loadCurrentExercise() {
        const item = state.items[state.currentIndex];
        if (!item) return;
        els.currentExerciseName.textContent = item.nama_gerakan;
        els.currentTargetSets.textContent = item.target_sets;
        els.currentTargetReps.textContent = item.target_reps;
        els.currentTargetWeight.textContent = item.target_weight;
        els.bebanInput.value = item.target_weight;
        els.repsInput.value = item.target_reps;
        if (els.exerciseProgressText) {
            els.exerciseProgressText.textContent = `Gerakan ${state.currentIndex + 1} / ${state.items.length}`;
        }
        updateSetProgressUI();
    }

    function highlightActiveCard() {
        els.exerciseCards.forEach((card) => {
            const idx = parseInt(card.dataset.index, 10);
            card.classList.toggle("active-exercise", idx === state.currentIndex);
        });
    }

    /* -----------------------------------------------------
       DONE LATIHAN -> tutup sesi, hitung & tampilkan ringkasan
       ----------------------------------------------------- */
    function initFinishWorkout() {
        if (!els.finishWorkoutBtn) return;
        els.finishWorkoutBtn.addEventListener("click", () => {
            if (state.session.totalSets === 0) {
                const confirmEmpty = confirm(
                    "Kamu belum mencatat satu set pun. Tetap akhiri latihan dan kembali ke Home?"
                );
                if (!confirmEmpty) return;
                goHome();
                return;
            }

            stopWorkoutTimer();
            showWorkoutSummary();
        });

        if (els.summaryBackToHomeBtn) {
            els.summaryBackToHomeBtn.addEventListener("click", goHome);
        }
    }

    function showWorkoutSummary() {
        if (!els.summaryModal) return;

        const avgRpe = state.session.totalSets > 0
            ? (state.session.rpeSum / state.session.totalSets)
            : 0;

        els.summaryTotalSets.textContent = state.session.totalSets;
        els.summaryTotalVolume.textContent = Math.round(state.session.totalVolume * 100) / 100;
        els.summaryAvgRpe.textContent = avgRpe.toFixed(1);
        els.summaryDuration.textContent = formatTimer(state.workoutSeconds, true);
        els.summaryCns.textContent = `${Math.round((state.lastCns || 0) * 100)}%`;
        els.summaryFsm.textContent = state.lastFsm || "SEGAR";
        els.summaryFsm.className = "summary-stat-value fsm-" + (state.lastFsm || "segar").toLowerCase();

        els.summaryModal.classList.add("open");
    }

    function goHome() {
        window.location.href = (typeof KUAT_HOME_URL !== "undefined") ? KUAT_HOME_URL : "/";
    }
});
