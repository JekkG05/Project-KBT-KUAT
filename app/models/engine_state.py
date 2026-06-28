from datetime import datetime


class EngineState:

    def __init__(self, data):

        self.id = data.get("id")

        self.user_id = data.get("user_id")

        self.state_json = data.get(
            "state_json",
            {}
        )

        self.updated_at = data.get(
            "updated_at",
            datetime.utcnow()
        )


    def __repr__(self):

        return f"<EngineState user_id={self.user_id}>"
