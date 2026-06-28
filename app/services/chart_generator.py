"""
chart_generator.py

Menyiapkan data chart untuk Chart.js di dashboard, dengan 3 granularitas
waktu yang bisa dipilih user di halaman Home:

    - "daily"   -> 30 hari terakhir, dikelompokkan per hari
    - "weekly"  -> 12 minggu terakhir, dikelompokkan per minggu (ISO week)
    - "monthly" -> 12 bulan terakhir, dikelompokkan per bulan
"""
from datetime import datetime, timedelta

from app.models.workout_log import WorkoutLog

EMPTY_CHART_DATA = {
    "labels": [],
    "volume": [],
    "fatigue": [],
    "cns": [],
    "acwr": [],
    "estimated_1rm": [],
}


def generate_dashboard_chart_data(user_id, period="daily"):
    """
    Entry point utama. `period` salah satu dari: "daily", "weekly", "monthly".
    Default ke "daily" jika nilai tidak dikenali.
    """
    period = (period or "daily").lower()

    if period in ("weekly", "week", "mingguan"):
        return _build_chart_data(
            user_id, days_back=12 * 7, group_fn=_week_key, label_fn=_week_label
        )
    elif period in ("monthly", "month", "bulanan"):
        return _build_chart_data(
            user_id, days_back=370, group_fn=_month_key, label_fn=_month_label
        )
    else:
        return _build_chart_data(
            user_id, days_back=30, group_fn=_day_key, label_fn=_day_label
        )


def _build_chart_data(user_id, days_back, group_fn, label_fn):
    since = datetime.utcnow() - timedelta(days=days_back)

    logs = (
        WorkoutLog.query.filter(
            WorkoutLog.user_id == user_id,
            WorkoutLog.created_at >= since,
        )
        .order_by(WorkoutLog.created_at.asc())
        .all()
    )

    if not logs:
        return dict(EMPTY_CHART_DATA)

    buckets = {}
    order = []

    for log in logs:
        key = group_fn(log.created_at)
        if key not in buckets:
            buckets[key] = {
                "volume": 0.0,
                "fatigue": 0.0,
                "cns": 0.0,
                "acwr": 1.0,
                "estimated_1rm": 0.0,
            }
            order.append(key)

        bucket = buckets[key]
        bucket["volume"] += log.volume or 0
        bucket["fatigue"] = log.fatigue_total or bucket["fatigue"]
        bucket["cns"] = log.cns_fatigue or bucket["cns"]
        bucket["acwr"] = log.acwr or bucket["acwr"]
        bucket["estimated_1rm"] = max(bucket["estimated_1rm"], log.estimated_1rm or 0)

    return {
        "labels": [label_fn(k) for k in order],
        "volume": [round(buckets[k]["volume"], 2) for k in order],
        "fatigue": [round(buckets[k]["fatigue"], 4) for k in order],
        "cns": [round(buckets[k]["cns"], 4) for k in order],
        "acwr": [round(buckets[k]["acwr"], 3) for k in order],
        "estimated_1rm": [round(buckets[k]["estimated_1rm"], 2) for k in order],
    }


# ---------------------------------------------------------------------------
# Grouping key + label helpers (deterministik, tanpa random)
# ---------------------------------------------------------------------------

def _day_key(dt):
    return dt.strftime("%Y-%m-%d")


def _day_label(key):
    dt = datetime.strptime(key, "%Y-%m-%d")
    return dt.strftime("%d %b")


def _week_key(dt):
    iso_year, iso_week, _ = dt.isocalendar()
    return f"{iso_year}-W{iso_week:02d}"


def _week_label(key):
    year_str, week_str = key.split("-W")
    monday = datetime.strptime(f"{year_str}-W{int(week_str)}-1", "%G-W%V-%u")
    sunday = monday + timedelta(days=6)
    return f"{monday.strftime('%d %b')}-{sunday.strftime('%d %b')}"


def _month_key(dt):
    return dt.strftime("%Y-%m")


def _month_label(key):
    dt = datetime.strptime(key, "%Y-%m")
    return dt.strftime("%b %Y")
