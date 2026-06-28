from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from app import db


class User(UserMixin, db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    name = db.Column(db.String(120), nullable=False)

    # Data diri
    usia = db.Column(db.Integer, nullable=False)
    bb = db.Column(db.Float, nullable=False)
    tinggi = db.Column(db.Float, nullable=True)

    # Kondisi badan
    bpm_base = db.Column(db.Integer, nullable=False)
    experience_level = db.Column(db.String(30), nullable=False, default="intermediate")
    injury_history = db.Column(db.Text, nullable=True)

    # Target & kekuatan awal
    initial_dl = db.Column(db.Float, nullable=False)
    initial_sq = db.Column(db.Float, nullable=False)
    initial_bp = db.Column(db.Float, nullable=False)

    engine_state = db.relationship(
        "EngineState", back_populates="user", uselist=False, cascade="all, delete-orphan"
    )
    workout_logs = db.relationship("WorkoutLog", back_populates="user", cascade="all, delete-orphan")
    workout_plans = db.relationship("WorkoutPlan", back_populates="user", cascade="all, delete-orphan")

    def set_password(self, password: str) -> None:
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        return check_password_hash(self.password_hash, password)
