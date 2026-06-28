from datetime import datetime


def parse_dt(value):
    """
    Supabase (lewat postgrest) selalu mengembalikan kolom timestamp
    sebagai string ISO 8601, bukan objek datetime Python. Kalau ini
    tidak di-parse, pemanggilan seperti `obj.created_at.strftime(...)`
    di template akan gagal dengan:

        'str object' has no attribute 'strftime'

    Helper ini dipakai di semua model (WorkoutLog, WorkoutPlan,
    EngineState, dst) supaya field tanggal selalu berupa objek
    datetime yang valid, baik datanya baru dibuat di Python
    (sudah datetime) maupun datang dari Supabase (masih string).
    """
    if value is None:
        return datetime.utcnow()

    if isinstance(value, datetime):
        return value

    if isinstance(value, str):
        normalized = value.replace("Z", "+00:00")
        try:
            return datetime.fromisoformat(normalized)
        except ValueError:
            try:
                return datetime.strptime(value[:19], "%Y-%m-%dT%H:%M:%S")
            except ValueError:
                return datetime.utcnow()

    return datetime.utcnow()
