from datetime import datetime, timezone
from app import db


class WorkoutLog(db.Model):
    __tablename__ = "workout_logs"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    plan_id = db.Column(db.Integer, db.ForeignKey("workout_plans.id"), nullable=False, index=True)
    nama_gerakan = db.Column(db.String(160), nullable=False)
    cluster = db.Column(db.String(1), nullable=False)
    beban_aktual = db.Column(db.Float, nullable=False)
    reps_aktual = db.Column(db.Integer, nullable=False)
    rpe_input = db.Column(db.Float, nullable=False)
    rpe_corrected = db.Column(db.Float, nullable=False)
    fatigue_total = db.Column(db.Float, nullable=False)
    cns_fatigue = db.Column(db.Float, nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc), index=True)

    user = db.relationship("User", back_populates="workout_logs")
    plan = db.relationship("WorkoutPlan", back_populates="logs")
