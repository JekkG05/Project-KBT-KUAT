from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Tuple
import math
import numpy as np

ST = {"fresh": 0.30, "training": 0.55, "overreaching": 0.75}


def clamp(value: float, lower: float, upper: float) -> float:
    return max(lower, min(upper, float(value)))


def fsm_transition(f_total: float) -> str:
    if f_total < ST["fresh"]:
        return "Segar"
    if f_total < ST["training"]:
        return "Latihan"
    if f_total < ST["overreaching"]:
        return "Overreaching"
    return "Cedera"


@dataclass
class FatigueState:
    peripheral: float = 0.0
    central: float = 0.0

    @property
    def total(self) -> float:
        return 0.40 * self.peripheral + 0.60 * self.central

    def rest_intra_set(self, minutes: float) -> None:
        self.peripheral *= math.exp(-0.15 * max(0.0, minutes))
        self.peripheral = clamp(self.peripheral, 0.0, 1.0)

    def overnight(self, k_eff: float) -> None:
        self.central *= math.exp(-k_eff * 24.0)
        self.peripheral *= math.exp(-0.08 * 24.0)
        self.central = clamp(self.central, 0.0, 1.0)
        self.peripheral = clamp(self.peripheral, 0.0, 1.0)


def epley_1rm(beban: float, reps: int) -> float:
    beban = max(0.0, float(beban))
    reps = max(1, int(reps))
    return beban * (1.0 + reps / 30.0) if reps > 1 else beban


def pfail(rpe: float) -> float:
    return (clamp(rpe, 5.0, 10.0) / 10.0) ** 2


def stressor_peripheral(reps: int, rpe: float, cluster: str) -> float:
    mult = {"A": 0.8, "B": 1.0, "C": 1.4}.get((cluster or "B").upper(), 1.0)
    return (max(1, int(reps)) * pfail(rpe) * mult) / 50.0


def stressor_central(reps: int, rpe: float, cluster: str, bb: float = 70.0) -> float:
    mult = {"A": 1.8, "B": 1.0, "C": 0.25}.get((cluster or "B").upper(), 1.0)
    massa_faktor = 1.0 + (float(bb) - 70.0) / 200.0
    return (max(1, int(reps)) * (pfail(rpe) ** 2) * mult * massa_faktor) / 50.0


def bpm_modifier(bpm_now: float, bpm_base: float) -> float:
    delta = float(bpm_now) - float(bpm_base)
    if delta <= 5:
        return 1.00
    if delta <= 10:
        return 1.00 - 0.06 * (delta - 5)
    return max(0.40, 0.70 - 0.03 * (delta - 10))


def k_from_age(usia: int) -> float:
    usia = int(usia)
    if usia <= 25:
        return 0.050
    if usia <= 35:
        return 0.044
    if usia <= 45:
        return 0.035
    return 0.028


class BayesianRecoveryEstimator:
    def __init__(self, k_prior: float, usia: int, mu: float | None = None, sigma: float | None = None, n_obs: int = 0):
        self.k_prior = float(k_prior)
        self.mu = float(mu if mu is not None else k_prior)
        self.sigma = float(sigma if sigma is not None else k_prior * 0.25)
        self.sigma_obs_manual = k_prior * 0.35
        self.sigma_obs_hrv = k_prior * 0.15
        self.usia = int(usia)
        self.n_obs = int(n_obs)
        self.k_min = k_prior * 0.40
        self.k_max = k_prior * 1.80
        self.history: List[Dict] = []

    def proxy_from_user_input(self, energi: float, delta_bpm: float, f_malam: float) -> float:
        energi_norm = (clamp(energi, 1.0, 5.0) - 1.0) / 4.0
        bpm_penalty = max(0.0, float(delta_bpm)) / 20.0
        recovery_proxy = energi_norm * 0.5 - bpm_penalty * 0.3
        recovery_proxy = clamp(recovery_proxy, 0.05, 0.85)
        return clamp(f_malam * (1.0 - recovery_proxy), 0.0, max(0.0, f_malam))

    def update(self, f_total_malam: float, f_proxy_pagi: float, has_hrv: bool = False) -> float:
        f_total_malam = float(f_total_malam)
        f_proxy_pagi = float(f_proxy_pagi)
        if f_total_malam < 0.001 or f_proxy_pagi <= 0 or f_proxy_pagi >= f_total_malam:
            return self.mu
        k_obs = -math.log(f_proxy_pagi / f_total_malam) / 24.0
        k_obs = clamp(k_obs, self.k_min, self.k_max)
        sigma_obs = self.sigma_obs_hrv if has_hrv else self.sigma_obs_manual
        precision_prior = 1.0 / max(1e-9, self.sigma**2)
        precision_obs = 1.0 / max(1e-9, sigma_obs**2)
        precision_post = precision_prior + precision_obs
        self.mu = (precision_prior * self.mu + precision_obs * k_obs) / precision_post
        self.sigma = math.sqrt(1.0 / precision_post)
        self.mu = clamp(self.mu, self.k_min, self.k_max)
        self.n_obs += 1
        self.history.append({
            "k_implied": round(k_obs, 5),
            "k_posterior": round(self.mu, 5),
            "sigma": round(self.sigma, 5),
            "f_malam": round(f_total_malam, 4),
            "f_pagi": round(f_proxy_pagi, 4),
        })
        return self.mu

    @property
    def confidence(self) -> float:
        denom = max(1e-9, self.mu * 0.25)
        return clamp(1.0 - (self.sigma / denom), 0.0, 1.0)

    def to_dict(self) -> Dict:
        return {"mu": self.mu, "sigma": self.sigma, "n_obs": self.n_obs}


class RPEValidator:
    EXPERIENCE_BIAS = {"novice": 1.35, "intermediate": 1.10, "advanced": 1.00}

    def __init__(self, experience: str = "intermediate", session_rpes: List[float] | None = None, history_rpes: List[float] | None = None):
        self.exp = experience or "intermediate"
        self.bias_factor = self.EXPERIENCE_BIAS.get(self.exp, 1.10)
        self.session_rpes = list(session_rpes or [])
        self.history_rpes = list(history_rpes or [])
        self.LAYER1_TOLERANCE = 1.5
        self.LAYER2_VARIANCE = 0.25

    def epley_reps_max(self, beban: float, one_rm: float) -> float:
        beban = float(beban)
        one_rm = float(one_rm)
        if beban <= 0 or one_rm <= beban:
            return 1.0
        return 30.0 * (one_rm / beban - 1.0)

    def layer1_velocity_check(self, beban: float, reps_actual: int, rpe_user: float, one_rm: float) -> Dict:
        reps_max = self.epley_reps_max(beban, one_rm)
        rir_pred = max(0.0, reps_max - int(reps_actual))
        rpe_pred = clamp(10.0 - rir_pred, 5.0, 10.0)
        delta = abs(float(rpe_user) - rpe_pred)
        flagged = delta > self.LAYER1_TOLERANCE
        return {
            "layer": 1,
            "rpe_user": round(float(rpe_user), 1),
            "rpe_pred": round(rpe_pred, 1),
            "rir_pred": round(rir_pred, 1),
            "delta": round(delta, 2),
            "flagged": flagged,
            "message": f"RPE input berbeda dari prediksi sistem ±{round(delta, 1)}." if flagged else "OK",
        }

    def layer2_session_pattern(self) -> Dict:
        if len(self.session_rpes) < 4:
            return {"layer": 2, "flagged": False, "message": "Data sesi belum cukup"}
        variance = float(np.var(self.session_rpes))
        flagged = variance < self.LAYER2_VARIANCE
        return {
            "layer": 2,
            "variance": round(variance, 3),
            "flagged": flagged,
            "message": "RPE terlalu datar; pastikan input jujur." if flagged else "OK",
        }

    def correct_rpe(self, rpe_user: float, flag_l1: bool) -> Tuple[float, str]:
        if not flag_l1 or self.exp == "advanced":
            return clamp(rpe_user, 1.0, 10.0), "Tidak dikoreksi"
        corrected = clamp(float(rpe_user) * self.bias_factor, 1.0, 10.0)
        return corrected, f"Koreksi {self.exp}: ×{self.bias_factor}"

    def validate(self, beban: float, reps: int, rpe_user: float, one_rm: float) -> Dict:
        rpe_user = clamp(rpe_user, 1.0, 10.0)
        self.session_rpes.append(rpe_user)
        self.history_rpes.append(rpe_user)
        layer1 = self.layer1_velocity_check(beban, reps, rpe_user, one_rm)
        layer2 = self.layer2_session_pattern()
        corrected, note = self.correct_rpe(rpe_user, layer1["flagged"])
        return {
            "rpe_input": rpe_user,
            "rpe_final": round(corrected, 2),
            "correction": note,
            "flag_any": bool(layer1["flagged"] or layer2["flagged"]),
            "layer1": layer1,
            "layer2": layer2,
        }

    def to_dict(self) -> Dict:
        return {
            "session_rpes": self.session_rpes[-20:],
            "history_rpes": self.history_rpes[-100:],
        }


@dataclass
class InjurySpectrumResult:
    level: str
    label: str
    protocol: str
    load_modifier: float
    restricted_clusters: List[str] = field(default_factory=list)


class InjuryManager:
    ACWR_DANGER = 1.5

    def __init__(self, workload_7day: List[float] | None = None, workload_28day: List[float] | None = None):
        self.workload_7day = list(workload_7day or [])[-7:]
        self.workload_28day = list(workload_28day or [])[-28:]

    def add_workload(self, volume: float) -> None:
        volume = max(0.0, float(volume))
        self.workload_7day.append(volume)
        self.workload_28day.append(volume)
        self.workload_7day = self.workload_7day[-7:]
        self.workload_28day = self.workload_28day[-28:]

    @property
    def acwr(self) -> float:
        acute = float(np.mean(self.workload_7day)) if self.workload_7day else 0.0
        chronic = float(np.mean(self.workload_28day)) if self.workload_28day else 0.0
        if chronic <= 0:
            return 0.0
        return acute / chronic

    def classify(self, f_peripheral: float, f_central: float, rpe: float, cluster: str) -> InjurySpectrumResult:
        cluster = (cluster or "B").upper()
        if f_central > 0.70 or self.acwr > self.ACWR_DANGER:
            return InjurySpectrumResult(
                level="DANGER",
                label="Kritis: risiko overuse/CNS tinggi",
                protocol="Forced rest. Hentikan set berat dan lakukan deload 48-72 jam.",
                load_modifier=0.30,
                restricted_clusters=["A", "B"],
            )
        if f_peripheral > 0.55 and rpe >= 9.0:
            return InjurySpectrumResult(
                level="WARNING",
                label="Sedang: risiko strain lokal meningkat",
                protocol="Turunkan beban 10-20% dan tambah rest antar set.",
                load_modifier=0.80,
                restricted_clusters=[cluster],
            )
        return InjurySpectrumResult(
            level="INFO",
            label="Normal: kelelahan dalam batas adaptif",
            protocol="Lanjutkan dengan teknik stabil dan RPE jujur.",
            load_modifier=1.00,
            restricted_clusters=[],
        )

    def to_dict(self) -> Dict:
        return {"workload_7day": self.workload_7day[-7:], "workload_28day": self.workload_28day[-28:]}
