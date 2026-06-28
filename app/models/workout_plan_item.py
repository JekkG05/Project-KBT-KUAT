from datetime import datetime


class WorkoutPlanItem:


    def __init__(self, data):

        self.id = data.get(
            "id"
        )


        self.plan_id = data.get(
            "plan_id"
        )


        self.exercise_id = data.get(
            "exercise_id"
        )


        self.nama_gerakan = data.get(
            "nama_gerakan"
        )


        self.cluster = data.get(
            "cluster",
            "B"
        )


        self.target_sets = data.get(
            "target_sets",
            3
        )


        self.target_reps = data.get(
            "target_reps",
            10
        )


        self.target_weight = data.get(
            "target_weight",
            0
        )


        self.item_order = data.get(
            "item_order",
            0
        )


        self.created_at = data.get(
            "created_at",
            datetime.utcnow()
        )


        # jika Supabase melakukan nested select
        self.exercise = data.get(
            "exercise",
            None
        )


        self.logs = data.get(
            "logs",
            []
        )



    def __repr__(self):

        return (
            f"<WorkoutPlanItem "
            f"{self.nama_gerakan}>"
        )
