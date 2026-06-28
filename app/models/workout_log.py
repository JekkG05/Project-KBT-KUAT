from datetime import datetime

from app.models._datetime_utils import parse_dt



class WorkoutLog:


    def __init__(self, data):

        self.id = data.get(
            "id"
        )


        self.user_id = data.get(
            "user_id"
        )


        self.plan_id = data.get(
            "plan_id"
        )


        self.plan_item_id = data.get(
            "plan_item_id"
        )


        self.nama_gerakan = data.get(
            "nama_gerakan"
        )


        self.cluster = data.get(
            "cluster",
            "B"
        )


        self.beban_aktual = data.get(
            "beban_aktual",
            0
        )


        self.reps_aktual = data.get(
            "reps_aktual",
            0
        )


        self.rir_input = data.get(
            "rir_input",
            0
        )


        self.rpe_converted = data.get(
            "rpe_converted",
            0
        )


        self.volume = data.get(
            "volume",
            0
        )


        self.estimated_1rm = data.get(
            "estimated_1rm",
            0
        )


        self.fatigue_total = data.get(
            "fatigue_total",
            0
        )


        self.cns_fatigue = data.get(
            "cns_fatigue",
            0
        )


        self.acwr = data.get(
            "acwr",
            1.0
        )


        self.fsm_state = data.get(
            "fsm_state",
            "SEGAR"
        )


        self.created_at = parse_dt(
            data.get("created_at")
        )



    def __repr__(self):

        return (
            f"<WorkoutLog "
            f"{self.nama_gerakan} "
            f"{self.beban_aktual}x"
            f"{self.reps_aktual}>"
        )
