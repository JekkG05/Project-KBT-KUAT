"""
kuat_engine.py

KuatTracker: state machine inti KUAT yang menyimpan progres fatigue,
ACWR, estimasi 1RM, dan menghitung Early Warning System (EWS) personal
berbasis pola RPE/RIR historis user. Seluruh perhitungan deterministik,
tidak ada random().
"""

import math

from app.services.gap_patch import (
    rir_to_rpe,
    proximity_to_failure,
    estimate_1rm_epley,
    cluster_multiplier,
    dual_fatigue_score,
    calculate_acwr,
    bayesian_recovery_update,
    fsm_state_from_fatigue,
)


class KuatTracker:
    """Engine analitik latihan kekuatan per-user."""

    def __init__(self, initial_dl=0.0, initial_sq=0.0, initial_bp=0.0):
        self.state = {
            "k_recovery": 0.08,
            "cns_fatigue": 0.0,
            "total_fatigue": 0.0,
            "acwr": 1.0,
            "fsm_state": "SEGAR",
            "estimated_1rm": {
                "deadlift": float(initial_dl),
                "squat": float(initial_sq),
                "bench_press": float(initial_bp),
            },
            "acute_load": 0.0,
            "chronic_load": 0.0,
            "last_warning": [],
        }

    # ------------------------------------------------------------------
    # Serialization
    # ------------------------------------------------------------------

    @classmethod
    def from_dict(cls, data):
        tracker = cls()
        if data:
            tracker.state.update(data)
            # ensure nested dict exists fully
            default_1rm = {"deadlift": 0.0, "squat": 0.0, "bench_press": 0.0}
            default_1rm.update(data.get("estimated_1rm", {}))
            tracker.state["estimated_1rm"] = default_1rm
        return tracker

    def to_dict(self):
        return dict(self.state)

    # ------------------------------------------------------------------
    # Morning check-in (energi slider only, TIDAK PAKAI BPM)
    # ------------------------------------------------------------------

    def morning_check(self, energi_slider):
        """
        energi_slider: 1 (sangat lelah) - 5 (sangat segar)
        Tidak memakai BPM dalam bentuk apapun.
        """
        new_k = bayesian_recovery_update(self.state.get("k_recovery", 0.08), energi_slider)
        self.state["k_recovery"] = new_k

        # Kurangi fatigue berdasarkan recovery rate (deterministik)
        recovery_factor = new_k
        self.state["cns_fatigue"] = round(
            max(0.0, self.state.get("cns_fatigue", 0.0) * (1 - recovery_factor)), 4
        )
        self.state["total_fatigue"] = round(
            max(0.0, self.state.get("total_fatigue", 0.0) * (1 - recovery_factor)), 4
        )

        self.state["fsm_state"] = fsm_state_from_fatigue(
            self.state["cns_fatigue"], self.state["total_fatigue"]
        )

        return self.to_dict()

    # ------------------------------------------------------------------
    # Log satu set latihan
    # ------------------------------------------------------------------

    def log_set(self, user_id, nama_gerakan, cluster, beban, reps, rir_user,
                bodyweight, recent_logs=None):
        # --- Validasi ---
        beban = float(beban)
        reps = int(reps)
        rir_user = int(rir_user)

        if beban <= 0:
            raise ValueError("Beban harus lebih besar dari 0.")
        if reps <= 0:
            raise ValueError("Reps harus lebih besar dari 0.")
        if rir_user < 0 or rir_user > 5:
            raise ValueError("RIR harus berada di antara 0 sampai 5.")

        # --- Konversi RIR -> RPE ---
        rpe = rir_to_rpe(rir_user)

        # --- Volume ---
        volume = round(beban * reps, 2)

        # --- Estimasi 1RM set ini ---
        estimated_1rm = estimate_1rm_epley(beban, reps)

        # --- Dual fatigue (peripheral + CNS) ---
        fatigue_result = dual_fatigue_score(beban, reps, rpe, cluster, bodyweight)

        # --- Update cumulative fatigue state (akumulasi deterministik) ---
        self.state["cns_fatigue"] = round(
            min(1.0, self.state.get("cns_fatigue", 0.0) + fatigue_result["cns_fatigue"]), 4
        )
        self.state["total_fatigue"] = round(
            min(1.0, self.state.get("total_fatigue", 0.0) + fatigue_result["total_fatigue"]), 4
        )

        # --- Update ACWR (acute = volume sesi terbaru, chronic = rata-rata historis) ---
        acute_load = self.state.get("acute_load", 0.0) + volume
        chronic_load = self.state.get("chronic_load", 0.0)
        if chronic_load <= 0:
            chronic_load = acute_load if acute_load > 0 else 1.0
        acwr = calculate_acwr(acute_load, chronic_load)

        self.state["acute_load"] = round(acute_load, 2)
        self.state["chronic_load"] = round((chronic_load * 0.9) + (acute_load * 0.1), 2)
        self.state["acwr"] = acwr

        # --- FSM update ---
        self.state["fsm_state"] = fsm_state_from_fatigue(
            self.state["cns_fatigue"], self.state["total_fatigue"]
        )

        # --- Update 1RM jika set ini cukup berat & dekat failure ---
        updated_1rm = dict(self.state["estimated_1rm"])
        nama_lower = (nama_gerakan or "").lower()
        if rpe >= 8.5 and reps <= 6:
            if "deadlift" in nama_lower:
                if estimated_1rm > updated_1rm.get("deadlift", 0):
                    updated_1rm["deadlift"] = estimated_1rm
            elif "squat" in nama_lower:
                if estimated_1rm > updated_1rm.get("squat", 0):
                    updated_1rm["squat"] = estimated_1rm
            elif "bench" in nama_lower or "press" in nama_lower:
                if estimated_1rm > updated_1rm.get("bench_press", 0):
                    updated_1rm["bench_press"] = estimated_1rm

        self.state["estimated_1rm"] = updated_1rm

        # --- Hitung warning (engine tetap menghitung untuk semua user;
        #     filtering free/premium dilakukan di controller) ---
        warnings = self.check_premium_warning(rpe, rir_user, recent_logs)
        self.state["last_warning"] = warnings

        return {
            "rpe_converted": rpe,
            "volume": volume,
            "estimated_1rm": estimated_1rm,
            "cns_fatigue": self.state["cns_fatigue"],
            "total_fatigue": self.state["total_fatigue"],
            "acwr": self.state["acwr"],
            "fsm_state": self.state["fsm_state"],
            "updated_1rm": updated_1rm,
            "warnings": warnings,
        }

    # ------------------------------------------------------------------
    # Early Warning System personal (hanya difilter di controller utk free)
    # ------------------------------------------------------------------

    def check_premium_warning(self, rpe_current, rir_current, recent_logs):
        """
        recent_logs: list of dict/object dengan atribut rpe_converted & rir_input,
        diambil dari 30 hari terakhir untuk gerakan yang sama
        (atau cluster yang sama jika data gerakan yang sama < 3).

        Return list of {"level": "WARNING"|"DANGER", "message": str}
        """
        if not recent_logs or len(recent_logs) < 3:
            return []

        rpe_values = []
        rir_values = []
        for log in recent_logs:
            rpe_val = getattr(log, "rpe_converted", None) if not isinstance(log, dict) else log.get("rpe_converted")
            rir_val = getattr(log, "rir_input", None) if not isinstance(log, dict) else log.get("rir_input")
            if rpe_val is not None:
                rpe_values.append(float(rpe_val))
            if rir_val is not None:
                rir_values.append(float(rir_val))

        if len(rpe_values) < 3 or len(rir_values) < 3:
            return []

        avg_rpe = sum(rpe_values) / len(rpe_values)
        avg_rir = sum(rir_values) / len(rir_values)

        std_rpe = _std_dev(rpe_values, avg_rpe)
        std_rir = _std_dev(rir_values, avg_rir)

        std_rpe = max(std_rpe, 0.25)
        std_rir = max(std_rir, 0.25)

        rpe_current = float(rpe_current)
        rir_current = float(rir_current)

        warnings = []

        is_danger = (
            rpe_current > avg_rpe + (2.0 * std_rpe)
            or rir_current < avg_rir - (2.0 * std_rir)
            or self.state.get("cns_fatigue", 0.0) > 0.70
        )

        is_warning_zscore = (
            rpe_current > avg_rpe + (1.5 * std_rpe)
            or rir_current < avg_rir - (1.5 * std_rir)
        )

        is_warning_pct = (
            (avg_rpe > 0 and rpe_current >= avg_rpe * 1.15)
            or (avg_rir > 0 and rir_current <= avg_rir * 0.70)
        )

        if is_danger:
            warnings.append({
                "level": "DANGER",
                "message": (
                    "🚨 FORCED REST! Intensitas set ini jauh melebihi pola "
                    "normalmu. Hentikan latihan berat dan lakukan recovery."
                ),
            })
        elif is_warning_zscore or is_warning_pct:
            warnings.append({
                "level": "WARNING",
                "message": (
                    "⚠️ RPE/RIR set ini menyimpang dari pola latihan normalmu. "
                    "Pertimbangkan turunkan beban, kurangi reps, atau tambah rest."
                ),
            })

        return warnings


def _std_dev(values, mean_value):
    """Standar deviasi populasi sederhana, tanpa dependency tambahan."""
    if len(values) < 2:
        return 0.0
    variance = sum((v - mean_value) ** 2 for v in values) / len(values)
    return math.sqrt(variance)
