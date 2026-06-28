import json
from app import db


class EngineState(db.Model):
    __tablename__ = "engine_states"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), unique=True, nullable=False, index=True)
    state_json = db.Column(db.Text, nullable=False, default="{}")

    user = db.relationship("User", back_populates="engine_state")

    def as_dict(self) -> dict:
        try:
            return json.loads(self.state_json or "{}")
        except json.JSONDecodeError:
            return {}

    def update_from_dict(self, payload: dict) -> None:
        self.state_json = json.dumps(payload, ensure_ascii=False)
