from datetime import datetime



class WorkoutPlan:


    def __init__(self, data):

        self.id = data.get(
            "id"
        )


        self.user_id = data.get(
            "user_id"
        )


        self.folder_name = data.get(
            "folder_name"
        )


        self.train_focus = data.get(
            "train_focus"
        )


        self.notes = data.get(
            "notes"
        )


        self.created_at = data.get(
            "created_at",
            datetime.utcnow()
        )


        self.updated_at = data.get(
            "updated_at",
            datetime.utcnow()
        )


        # isi dari Supabase kalau join/select nested
        self.items = data.get(
            "items",
            []
        )


        self.logs = data.get(
            "logs",
            []
        )



    def __repr__(self):

        return (
            f"<WorkoutPlan "
            f"{self.folder_name}>"
        )
