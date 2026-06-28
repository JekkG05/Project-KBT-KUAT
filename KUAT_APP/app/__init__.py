import csv
from pathlib import Path
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager

from .config import Config


db = SQLAlchemy()
login_manager = LoginManager()
login_manager.login_view = "auth.login"
login_manager.login_message = "Silakan login terlebih dahulu."
login_manager.login_message_category = "warning"


def create_app(config_class=Config):
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_object(config_class)

    db.init_app(app)
    login_manager.init_app(app)

    from .models.user import User
    from .models.exercise_db import ExerciseDB
    from .models.workout_plan import WorkoutPlan
    from .models.workout_log import WorkoutLog
    from .models.engine_state import EngineState

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    from .controllers.auth_controller import auth_bp
    from .controllers.home_controller import home_bp
    from .controllers.exercise_controller import exercise_bp
    from .controllers.routine_controller import routine_bp
    from .controllers.train_controller import train_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(home_bp)
    app.register_blueprint(exercise_bp)
    app.register_blueprint(routine_bp)
    app.register_blueprint(train_bp)

    with app.app_context():
        db.create_all()
        seed_exercises()

    return app


def seed_exercises():
    from .models.exercise_db import ExerciseDB

    if ExerciseDB.query.first():
        return

    csv_path = Path(__file__).resolve().parent / "services" / "clustering.csv"
    if not csv_path.exists():
        return

    with csv_path.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        rows = []
        for row in reader:
            rows.append(
                ExerciseDB(
                    nama_latihan=(row.get("Nama Latihan") or "").strip(),
                    target_otot=(row.get("Target Otot") or "").strip(),
                    peralatan=(row.get("Peralatan") or "").strip(),
                    tipe=(row.get("Tipe") or "").strip(),
                    cns_cluster=(row.get("CNS Cluster") or "B").strip().upper(),
                    kategori=(row.get("Kategori") or "").strip(),
                    deskripsi=(row.get("Deskripsi Singkat") or "").strip(),
                )
            )
        db.session.add_all(rows)
        db.session.commit()
