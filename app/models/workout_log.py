from datetime import datetime

from app import db


class WorkoutLog(db.Model):
    __tablename__ = "workout_logs"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    plan_id = db.Column(db.Integer, db.ForeignKey("workout_plans.id"), nullable=True)
    plan_item_id = db.Column(db.Integer, db.ForeignKey("workout_plan_items.id"), nullable=True)

    nama_gerakan = db.Column(db.String(150), nullable=False)
    cluster = db.Column(db.String(1), nullable=False, default="B")

    beban_aktual = db.Column(db.Float, nullable=False)
    reps_aktual = db.Column(db.Integer, nullable=False)
    rir_input = db.Column(db.Integer, nullable=False)
    rpe_converted = db.Column(db.Float, nullable=False)

    volume = db.Column(db.Float, nullable=False, default=0)
    estimated_1rm = db.Column(db.Float, nullable=False, default=0)
    fatigue_total = db.Column(db.Float, nullable=False, default=0)
    cns_fatigue = db.Column(db.Float, nullable=False, default=0)
    acwr = db.Column(db.Float, nullable=False, default=1.0)
    fsm_state = db.Column(db.String(20), nullable=False, default="SEGAR")

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<WorkoutLog {self.nama_gerakan} {self.beban_aktual}x{self.reps_aktual}>"
