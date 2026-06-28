from __future__ import annotations

from collections import defaultdict
from datetime import datetime
from typing import Iterable

from .gap_patch import epley_1rm


def build_chart_data(logs: Iterable, state: dict | None = None, limit: int = 30) -> dict:
    logs = list(logs)[-limit:]
    labels = []
    est_1rm = []
    fatigue = []
    acwr_values = []
    volumes = []

    for log in logs:
        created = log.created_at
        if isinstance(created, datetime):
            labels.append(created.strftime("%d/%m"))
        else:
            labels.append(str(created))
        est_1rm.append(round(epley_1rm(log.beban_aktual, log.reps_aktual), 2))
        fatigue.append(round(log.fatigue_total, 4))
        volumes.append(float(log.beban_aktual) * int(log.reps_aktual))

    for idx in range(len(volumes)):
        acute_slice = volumes[max(0, idx - 6): idx + 1]
        chronic_slice = volumes[max(0, idx - 27): idx + 1]
        acute = sum(acute_slice) / max(1, len(acute_slice))
        chronic = sum(chronic_slice) / max(1, len(chronic_slice))
        acwr_values.append(round(acute / chronic, 3) if chronic else 0)

    state = state or {}
    return {
        "labels": labels,
        "one_rm": est_1rm,
        "fatigue": fatigue,
        "acwr": acwr_values,
        "summary": {
            "dl_1rm": round(float(state.get("dl_1rm", 0.0)), 2),
            "sq_1rm": round(float(state.get("sq_1rm", 0.0)), 2),
            "bp_1rm": round(float(state.get("bp_1rm", 0.0)), 2),
            "total_fatigue": round(float(state.get("total_fatigue", 0.0)), 4),
            "k_recovery": round(float(state.get("k_recovery", 0.0)), 5),
        },
    }
