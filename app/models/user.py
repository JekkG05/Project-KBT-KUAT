from datetime import datetime

from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

from app import db


class User(db.Model, UserMixin):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    name = db.Column(db.String(120), nullable=False)

    gender = db.Column(db.String(1), nullable=False)  # L atau P
    usia = db.Column(db.Integer, nullable=False)
    bb = db.Column(db.Float, nullable=False)
    tinggi = db.Column(db.Float, nullable=True)

    experience_level = db.Column(db.String(30), nullable=False)  # novice/intermediate/advanced
    injury_history = db.Column(db.Text, nullable=True)

    initial_dl = db.Column(db.Float, nullable=False)
    initial_sq = db.Column(db.Float, nullable=False)
    initial_bp = db.Column(db.Float, nullable=False)

    tier = db.Column(db.String(20), default="free", nullable=False)  # free/premium
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # --- Relationships ---
    engine_state = db.relationship(
        "EngineState", backref="user", uselist=False, cascade="all, delete-orphan"
    )
    workout_plans = db.relationship(
        "WorkoutPlan", backref="user", lazy=True, cascade="all, delete-orphan"
    )
    workout_logs = db.relationship(
        "WorkoutLog", backref="user", lazy=True, cascade="all, delete-orphan"
    )

    def set_password(self, raw_password):
        self.password_hash = generate_password_hash(raw_password)

    def check_password(self, raw_password):
        return check_password_hash(self.password_hash, raw_password)

    def is_premium(self):
        return self.tier == "premium"

    def __repr__(self):
        return f"<User {self.email} ({self.tier})>"
