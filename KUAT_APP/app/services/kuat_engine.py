from __future__ import annotations

from typing import Dict, List
from .gap_patch import (
    BayesianRecoveryEstimator,
    FatigueState,
    InjuryManager,
    RPEValidator,
    bpm_modifier,
    clamp,
    epley_1rm,
    fsm_transition,
    k_from_age,
    stressor_central,
    stressor_peripheral,
)


class KuatTracker:
    """Engine KUAT untuk request web.

    Semua update berasal dari input user: beban aktual, reps aktual, RPE user,
    energi pagi, dan BPM pagi. Tidak ada randomisasi dalam engine web ini.
    """

    def __init__(
        self,
        name: str,
        usia: int,
        bb: float,
        bpm_base: int,
        experience_level: str,
        initial_dl: float,
        initial_sq: float,
        initial_bp: float,
        state: Dict | None = None,
    ):
        state = state or {}
        self.name = name
        self.usia = int(usia)
        self.bb = float(bb)
        self.bpm_base = int(bpm_base)
        self.experience_level = experience_level or "intermediate"

        self.dl_1rm = float(state.get("dl_1rm", initial_dl))
        self.sq_1rm = float(state.get("sq_1rm", initial_sq))
        self.bp_1rm = float(state.get("bp_1rm", initial_bp))

        self.fatigue = FatigueState(
            peripheral=float(state.get("peripheral_fatigue", 0.0)),
            central=float(state.get("central_fatigue", 0.0)),
        )
        self.k_base = float(state.get("k_base", k_from_age(self.usia)))
        self.k_recovery = float(state.get("k_recovery", self.k_base))
        bayes_state = state.get("bayesian", {}) or {}
        self.bayes = BayesianRecoveryEstimator(
            k_prior=self.k_base,
            usia=self.usia,
            mu=bayes_state.get("mu", self.k_recovery),
            sigma=bayes_state.get("sigma"),
            n_obs=bayes_state.get("n_obs", 0),
        )
        rpe_state = state.get("rpe_validator", {}) or {}
        self.rpe_validator = RPEValidator(
            experience=self.experience_level,
            session_rpes=rpe_state.get("session_rpes", []),
            history_rpes=rpe_state.get("history_rpes", []),
        )
        injury_state = state.get("injury", {}) or {}
        self.injury_mgr = InjuryManager(
            workload_7day=injury_state.get("workload_7day", []),
            workload_28day=injury_state.get("workload_28day", []),
        )
        self.fsm_state = state.get("fsm_state", fsm_transition(self.fatigue.total))
        self.last_bpm = int(state.get("last_bpm", self.bpm_base))
        self.last_energy = float(state.get("last_energy", 3.0))
        self.set_counter = int(state.get("set_counter", 0))

    @classmethod
    def from_user(cls, user, state: Dict | None = None) -> "KuatTracker":
        return cls(
            name=user.name,
            usia=user.usia,
            bb=user.bb,
            bpm_base=user.bpm_base,
            experience_level=user.experience_level,
            initial_dl=user.initial_dl,
            initial_sq=user.initial_sq,
            initial_bp=user.initial_bp,
            state=state,
        )

    def _reference_1rm(self, nama_gerakan: str, cluster: str) -> float:
        name = (nama_gerakan or "").lower()
        if "squat" in name or "leg press" in name:
            return self.sq_1rm
        if "bench" in name or "press" in name or "dip" in name:
            return self.bp_1rm
        if "deadlift" in name or cluster == "A":
            return self.dl_1rm
        if cluster == "B":
            return self.bp_1rm
        return max(30.0, min(self.bp_1rm, self.dl_1rm) * 0.45)

    def _update_1rm(self, nama_gerakan: str, cluster: str, estimate: float, rpe_corrected: float) -> Dict[str, float]:
        if rpe_corrected < 7.0:
            return {"dl_1rm": round(self.dl_1rm, 2), "sq_1rm": round(self.sq_1rm, 2), "bp_1rm": round(self.bp_1rm, 2)}

        adjusted = estimate * 0.98
        name = (nama_gerakan or "").lower()
        if "squat" in name or "leg press" in name:
            self.sq_1rm = max(self.sq_1rm, adjusted)
        elif "bench" in name or "press" in name or "dip" in name:
            self.bp_1rm = max(self.bp_1rm, adjusted)
        elif "deadlift" in name or cluster == "A":
            self.dl_1rm = max(self.dl_1rm, adjusted)
        elif cluster == "B":
            self.bp_1rm = max(self.bp_1rm, adjusted)
        return {"dl_1rm": round(self.dl_1rm, 2), "sq_1rm": round(self.sq_1rm, 2), "bp_1rm": round(self.bp_1rm, 2)}

    def morning_check(self, energi_slider: float, bpm_pagi: float) -> Dict:
        energi_slider = clamp(energi_slider, 1.0, 5.0)
        bpm_pagi = max(35.0, float(bpm_pagi))
        f_malam = max(0.001, self.fatigue.total)
        delta_bpm = bpm_pagi - self.bpm_base
        f_proxy_pagi = self.bayes.proxy_from_user_input(energi_slider, delta_bpm, f_malam)
        self.k_recovery = self.bayes.update(f_malam, f_proxy_pagi, has_hrv=False)
        k_eff = self.k_recovery * bpm_modifier(bpm_pagi, self.bpm_base)
        self.fatigue.overnight(k_eff)
        self.fsm_state = fsm_transition(self.fatigue.total)
        self.last_bpm = int(round(bpm_pagi))
        self.last_energy = float(energi_slider)

        warnings = []
        if delta_bpm > 10:
            warnings.append({
                "level": "WARNING",
                "code": "BPM_HIGH",
                "message": "BPM pagi naik >10 dari baseline. Sesi berat sebaiknya diturunkan.",
            })
        return {
            "k_recovery": round(self.k_recovery, 5),
            "k_confidence": round(self.bayes.confidence, 3),
            "cns_fatigue": round(self.fatigue.central, 4),
            "total_fatigue": round(self.fatigue.total, 4),
            "fsm_state": self.fsm_state,
            "warnings": warnings,
        }

    def log_set(self, nama_gerakan: str, cluster: str, beban_aktual: float, reps_aktual: int, rpe_user: float) -> Dict:
        cluster = (cluster or "B").upper()
        beban_aktual = max(0.0, float(beban_aktual))
        reps_aktual = max(1, int(reps_aktual))
        rpe_user = clamp(rpe_user, 1.0, 10.0)

        one_rm_ref = self._reference_1rm(nama_gerakan, cluster)
        rpe_result = self.rpe_validator.validate(beban_aktual, reps_aktual, rpe_user, one_rm_ref)
        rpe_corrected = float(rpe_result["rpe_final"])

        sp = stressor_peripheral(reps_aktual, rpe_corrected, cluster)
        sc = stressor_central(reps_aktual, rpe_corrected, cluster, self.bb)
        if rpe_corrected >= 9.5:
            sp *= 1.30
            sc *= 1.50

        self.fatigue.peripheral = clamp(self.fatigue.peripheral + sp, 0.0, 1.0)
        self.fatigue.central = clamp(self.fatigue.central + sc, 0.0, 1.0)
        self.fatigue.rest_intra_set({"A": 3.0, "B": 2.0, "C": 1.0}.get(cluster, 2.0))

        volume = beban_aktual * reps_aktual
        self.injury_mgr.add_workload(volume)
        acwr = self.injury_mgr.acwr
        injury = self.injury_mgr.classify(self.fatigue.peripheral, self.fatigue.central, rpe_corrected, cluster)

        est_1rm = epley_1rm(beban_aktual, reps_aktual)
        updated = self._update_1rm(nama_gerakan, cluster, est_1rm, rpe_corrected)
        self.fsm_state = fsm_transition(self.fatigue.total)
        self.set_counter += 1

        warnings: List[Dict] = []
        if self.fatigue.central > 0.70 or self.fatigue.total >= 0.75:
            warnings.append({
                "level": "DANGER",
                "code": "CNS_DANGER",
                "message": "CNS fatigue melewati ambang aman. Forced rest direkomendasikan.",
            })
        if acwr > 1.5:
            warnings.append({
                "level": "WARNING",
                "code": "ACWR_SPIKE",
                "message": "ACWR > 1.5. Lonjakan beban akut meningkatkan risiko cedera.",
            })
        if rpe_result["flag_any"]:
            warnings.append({
                "level": "WARNING",
                "code": "RPE_VALIDATION",
                "message": rpe_result["layer1"].get("message", "RPE perlu diverifikasi."),
            })
        if injury.level in {"DANGER", "WARNING"} and not any(w["code"] == "CNS_DANGER" for w in warnings):
            warnings.append({"level": injury.level, "code": "INJURY_SPECTRUM", "message": injury.label})

        return {
            "cns_fatigue": round(self.fatigue.central, 4),
            "peripheral_fatigue": round(self.fatigue.peripheral, 4),
            "total_fatigue": round(self.fatigue.total, 4),
            "acwr": round(acwr, 3),
            "fsm_state": self.fsm_state,
            "updated_1rm": updated,
            "estimated_1rm": round(est_1rm, 2),
            "rpe_corrected": round(rpe_corrected, 2),
            "rpe_validation": rpe_result,
            "warnings": warnings,
        }

    def to_dict(self) -> Dict:
        return {
            "dl_1rm": self.dl_1rm,
            "sq_1rm": self.sq_1rm,
            "bp_1rm": self.bp_1rm,
            "peripheral_fatigue": self.fatigue.peripheral,
            "central_fatigue": self.fatigue.central,
            "total_fatigue": self.fatigue.total,
            "k_base": self.k_base,
            "k_recovery": self.k_recovery,
            "bayesian": self.bayes.to_dict(),
            "rpe_validator": self.rpe_validator.to_dict(),
            "injury": self.injury_mgr.to_dict(),
            "fsm_state": self.fsm_state,
            "last_bpm": self.last_bpm,
            "last_energy": self.last_energy,
            "set_counter": self.set_counter,
        }
