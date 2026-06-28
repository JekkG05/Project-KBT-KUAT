from datetime import datetime

from app import db


class WorkoutPlan(db.Model):
    __tablename__ = "workout_plans"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    folder_name = db.Column(db.String(150), nullable=False)
    train_focus = db.Column(db.String(100), nullable=True)
    notes = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    items = db.relationship(
        "WorkoutPlanItem",
        backref="plan",
        lazy=True,
        cascade="all, delete-orphan",
        order_by="WorkoutPlanItem.item_order",
    )
    logs = db.relationship("WorkoutLog", backref="plan", lazy=True)

    def __repr__(self):
        return f"<WorkoutPlan {self.folder_name}>"
