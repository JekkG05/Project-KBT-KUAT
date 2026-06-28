from datetime import datetime

from app import db


class WorkoutPlanItem(db.Model):
    __tablename__ = "workout_plan_items"

    id = db.Column(db.Integer, primary_key=True)
    plan_id = db.Column(db.Integer, db.ForeignKey("workout_plans.id"), nullable=False)
    exercise_id = db.Column(db.Integer, db.ForeignKey("exercise_db.id"), nullable=True)

    nama_gerakan = db.Column(db.String(150), nullable=False)
    cluster = db.Column(db.String(1), nullable=False, default="B")  # A/B/C

    target_sets = db.Column(db.Integer, nullable=False, default=3)
    target_reps = db.Column(db.Integer, nullable=False, default=10)
    target_weight = db.Column(db.Float, nullable=False, default=0)

    item_order = db.Column(db.Integer, nullable=False, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    exercise = db.relationship("ExerciseDB", lazy=True)
    logs = db.relationship("WorkoutLog", backref="plan_item", lazy=True)

    def __repr__(self):
        return f"<WorkoutPlanItem {self.nama_gerakan}>"
