"""
gap_patch.py

Kumpulan fungsi matematis deterministik yang menjadi "tambalan" (patch)
logika sport-science KUAT. Tidak ada penggunaan random() di file ini.
Semua hasil murni fungsi dari input yang diberikan.
"""

# ---------------------------------------------------------------------------
# RIR -> RPE
# ---------------------------------------------------------------------------

def rir_to_rpe(rir_user):
    """Konversi RIR (0-5) menjadi RPE (5-10) secara deterministik."""
    rir_user = float(rir_user)
    rpe = max(5.0, min(10.0, 10 - rir_user))
    return rpe


# ---------------------------------------------------------------------------
# Proximity to failure
# ---------------------------------------------------------------------------

def proximity_to_failure(rpe):
    """Seberapa dekat set tersebut terhadap failure, skala 0-1."""
    pfail = (rpe / 10) ** 2
    return pfail


# ---------------------------------------------------------------------------
# Estimasi 1RM (Epley formula)
# ---------------------------------------------------------------------------

def estimate_1rm_epley(weight, reps):
    """Estimasi 1 Rep Max menggunakan formula Epley."""
    weight = float(weight)
    reps = float(reps)
    estimated_1rm = weight * (1 + reps / 30)
    return round(estimated_1rm, 2)


# ---------------------------------------------------------------------------
# Cluster multiplier (beban CNS berdasarkan jenis gerakan)
# ---------------------------------------------------------------------------

def cluster_multiplier(cluster):
    """
    A = compound berat / CNS tinggi
    B = compound sedang / CNS sedang
    C = isolasi / CNS rendah
    """
    mapping = {
        "A": 1.00,
        "B": 0.65,
        "C": 0.35,
    }
    return mapping.get(str(cluster).upper(), 0.65)


# ---------------------------------------------------------------------------
# Dual fatigue score (peripheral + central / CNS)
# ---------------------------------------------------------------------------

def dual_fatigue_score(weight, reps, rpe, cluster, bodyweight):
    """
    Menghitung fatigue perifer (otot) dan fatigue sentral (CNS) dari satu set.
    Mengembalikan dict: {"total_fatigue": float, "cns_fatigue": float}
    """
    weight = float(weight)
    reps = float(reps)
    bodyweight = float(bodyweight) if bodyweight else 1.0

    tonnage = weight * reps
    pfail = proximity_to_failure(rpe)
    cluster_factor = cluster_multiplier(cluster)

    peripheral = (tonnage / max(bodyweight, 1)) * pfail * 0.01
    central = cluster_factor * pfail * 0.12

    total = peripheral + central
    cns = central

    total_fatigue = min(1.0, max(0.0, total))
    cns_fatigue = min(1.0, max(0.0, cns))

    return {
        "total_fatigue": round(total_fatigue, 4),
        "cns_fatigue": round(cns_fatigue, 4),
    }


# ---------------------------------------------------------------------------
# ACWR (Acute:Chronic Workload Ratio)
# ---------------------------------------------------------------------------

def calculate_acwr(acute_load, chronic_load):
    """ACWR = acute_load / chronic_load. Default 1.0 jika chronic 0."""
    if chronic_load is None or chronic_load <= 0:
        return 1.0
    return round(acute_load / chronic_load, 3)


# ---------------------------------------------------------------------------
# Bayesian-style recovery update dari morning check (energi slider 1-5)
# ---------------------------------------------------------------------------

def bayesian_recovery_update(prior_k, energi_slider):
    """
    Update k_recovery (0.01 - 0.20) berdasarkan energi_slider (1-5).
    Deterministik: kombinasi prior dan sinyal energi hari ini.

    Energi 5 -> recovery sangat baik (k_recovery naik mendekati 0.20)
    Energi 1 -> recovery rendah (k_recovery turun mendekati 0.01)
    """
    energi_slider = max(1, min(5, int(energi_slider)))
    prior_k = float(prior_k) if prior_k is not None else 0.08

    # Sinyal energi dipetakan langsung ke target k_recovery
    energy_target_map = {
        1: 0.02,
        2: 0.05,
        3: 0.08,
        4: 0.13,
        5: 0.20,
    }
    target_k = energy_target_map[energi_slider]

    # Update bertahap (bayesian-style blending): 60% target baru, 40% prior
    new_k = (0.6 * target_k) + (0.4 * prior_k)
    new_k = min(0.20, max(0.01, new_k))

    return round(new_k, 4)


# ---------------------------------------------------------------------------
# FSM (Finite State Machine) berdasarkan fatigue
# ---------------------------------------------------------------------------

def fsm_state_from_fatigue(cns_fatigue, total_fatigue):
    """
    Tentukan state FSM:
        SEGAR        -> CNS < 0.30 dan total < 0.40
        LATIHAN      -> CNS < 0.55 dan total < 0.65
        WASPADA      -> CNS < 0.75
        OVERREACHING -> selain itu
    """
    if cns_fatigue < 0.30 and total_fatigue < 0.40:
        return "SEGAR"
    elif cns_fatigue < 0.55 and total_fatigue < 0.65:
        return "LATIHAN"
    elif cns_fatigue < 0.75:
        return "WASPADA"
    else:
        return "OVERREACHING"
