from datetime import datetime, timezone
from app import db


class WorkoutPlan(db.Model):
    __tablename__ = "workout_plans"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    folder_name = db.Column(db.String(120), nullable=False, default="Default")
    created_at = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))

    # Detail rencana latihan. Field ini memperluas definisi folder agar endpoint /train bisa langsung berjalan.
    title = db.Column(db.String(160), nullable=False)
    exercise_id = db.Column(db.Integer, db.ForeignKey("exercise_db.id"), nullable=True)
    nama_gerakan = db.Column(db.String(160), nullable=False)
    target_otot = db.Column(db.String(120), nullable=True)
    cluster = db.Column(db.String(1), nullable=False)
    target_sets = db.Column(db.Integer, nullable=False, default=3)
    target_reps = db.Column(db.Integer, nullable=False, default=8)
    target_load = db.Column(db.Float, nullable=False, default=20.0)
    notes = db.Column(db.Text, nullable=True)

    user = db.relationship("User", back_populates="workout_plans")
    exercise = db.relationship("ExerciseDB")
    logs = db.relationship("WorkoutLog", back_populates="plan", cascade="all, delete-orphan")
