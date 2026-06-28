import os
import csv

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from dotenv import load_dotenv

load_dotenv()

db = SQLAlchemy()
login_manager = LoginManager()
login_manager.login_view = "auth.login"
login_manager.login_message = "Silakan login untuk melanjutkan."
login_manager.login_message_category = "warning"


def create_app():
    app = Flask(__name__)

    from app.config import Config
    app.config.from_object(Config)

    if not os.environ.get("SUPABASE_DB_URL"):
        print(
            "[KUAT WARNING] SUPABASE_DB_URL belum diatur di environment / .env. "
            "Aplikasi akan mencoba menggunakan placeholder URL dan kemungkinan "
            "GAGAL terkoneksi ke database. Salin .env.example menjadi .env dan "
            "isi SUPABASE_DB_URL dengan connection string Supabase Anda."
        )

    db.init_app(app)
    login_manager.init_app(app)

    # --- Import models so SQLAlchemy is aware of them before create_all() ---
    from app.models.user import User
    from app.models.exercise_db import ExerciseDB
    from app.models.workout_plan import WorkoutPlan
    from app.models.workout_plan_item import WorkoutPlanItem
    from app.models.workout_log import WorkoutLog
    from app.models.engine_state import EngineState

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    # --- Register blueprints ---
    from app.controllers.auth_controller import auth_bp
    from app.controllers.home_controller import home_bp
    from app.controllers.exercise_controller import exercise_bp
    from app.controllers.routine_controller import routine_bp
    from app.controllers.train_controller import train_bp
    from app.controllers.account_controller import account_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(home_bp)
    app.register_blueprint(exercise_bp)
    app.register_blueprint(routine_bp)
    app.register_blueprint(train_bp)
    app.register_blueprint(account_bp)

    # --- Create tables & seed exercise database ---
    with app.app_context():
        try:
            db.create_all()
            seed_exercise_db()
        except Exception as exc:  # pragma: no cover
            print(f"[KUAT ERROR] Gagal menginisialisasi database: {exc}")
            print(
                "[KUAT ERROR] Pastikan SUPABASE_DB_URL valid dan project Supabase "
                "Anda aktif, lalu jalankan ulang `python run.py`."
            )

    return app


def seed_exercise_db():
    """Seed ExerciseDB table from app/services/clustering.csv.

    If the CSV file is missing, fall back to a minimal built-in seed list
    so the application still works.
    """
    from app.models.exercise_db import ExerciseDB

    if ExerciseDB.query.first() is not None:
        return  # already seeded, avoid duplicates

    csv_path = os.path.join(os.path.dirname(__file__), "services", "clustering.csv")

    rows_to_insert = []

    if os.path.exists(csv_path):
        try:
            with open(csv_path, newline="", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    rows_to_insert.append(
                        ExerciseDB(
                            kategori=row.get("Kategori", "").strip(),
                            nama_latihan=row.get("Nama Latihan", "").strip(),
                            target_otot=row.get("Target Otot", "").strip(),
                            peralatan=row.get("Peralatan", "").strip(),
                            tipe=row.get("Tipe", "").strip(),
                            deskripsi_singkat=row.get("Deskripsi Singkat", "").strip(),
                            cns_cluster=row.get("CNS Cluster", "B").strip() or "B",
                        )
                    )
        except Exception as exc:  # pragma: no cover
            print(f"[KUAT WARNING] Gagal membaca clustering.csv: {exc}")
            rows_to_insert = []

    if not rows_to_insert:
        fallback = [
            ("Compound", "Barbell Back Squat", "Quadriceps, Glutes", "Barbell", "Compound", "Squat dengan barbell di belakang bahu.", "A"),
            ("Compound", "Front Squat", "Quadriceps, Core", "Barbell", "Compound", "Squat dengan barbell di depan bahu.", "A"),
            ("Compound", "Deadlift", "Hamstring, Glutes, Punggung", "Barbell", "Compound", "Angkat barbell dari lantai dengan punggung lurus.", "A"),
            ("Compound", "Romanian Deadlift", "Hamstring, Glutes", "Barbell", "Compound", "Deadlift dengan lutut sedikit menekuk, fokus hamstring.", "B"),
            ("Compound", "Bench Press", "Dada, Triceps", "Barbell", "Compound", "Dorong barbell dari dada sambil berbaring.", "A"),
            ("Compound", "Overhead Press", "Bahu, Triceps", "Barbell", "Compound", "Dorong barbell ke atas dari bahu.", "A"),
            ("Compound", "Barbell Row", "Punggung, Bisep", "Barbell", "Compound", "Tarik barbell ke perut dalam posisi membungkuk.", "B"),
            ("Compound", "Pull Up", "Punggung, Bisep", "Pull Up Bar", "Compound", "Tarik tubuh ke atas hingga dagu melewati bar.", "B"),
            ("Compound", "Lat Pulldown", "Punggung", "Cable Machine", "Compound", "Tarik cable bar ke dada dari atas kepala.", "B"),
            ("Compound", "Leg Press", "Quadriceps, Glutes", "Machine", "Compound", "Dorong beban menggunakan kaki pada mesin leg press.", "B"),
            ("Compound", "Hip Thrust", "Glutes", "Barbell", "Compound", "Angkat pinggul dengan barbell di atas paha.", "B"),
            ("Compound", "Lunges", "Quadriceps, Glutes", "Dumbbell", "Compound", "Melangkah maju lalu menekuk lutut hingga 90 derajat.", "B"),
            ("Compound", "Cable Row", "Punggung", "Cable Machine", "Compound", "Tarik handle cable ke arah perut sambil duduk.", "B"),
            ("Compound", "Dumbbell Press", "Dada, Triceps", "Dumbbell", "Compound", "Dorong dumbbell dari dada sambil berbaring.", "B"),
            ("Isolasi", "Lateral Raise", "Bahu", "Dumbbell", "Isolasi", "Angkat dumbbell ke samping hingga sejajar bahu.", "C"),
            ("Isolasi", "Biceps Curl", "Bisep", "Dumbbell", "Isolasi", "Tekuk siku mengangkat dumbbell ke arah bahu.", "C"),
            ("Isolasi", "Triceps Pushdown", "Triceps", "Cable Machine", "Isolasi", "Dorong cable bar ke bawah meluruskan siku.", "C"),
            ("Isolasi", "Leg Curl", "Hamstring", "Machine", "Isolasi", "Tekuk lutut melawan beban pada mesin leg curl.", "C"),
            ("Isolasi", "Leg Extension", "Quadriceps", "Machine", "Isolasi", "Luruskan lutut melawan beban pada mesin leg extension.", "C"),
            ("Isolasi", "Calf Raise", "Betis", "Machine/Dumbbell", "Isolasi", "Angkat tumit menjinjit melawan beban.", "C"),
        ]
        rows_to_insert = [
            ExerciseDB(
                kategori=k, nama_latihan=n, target_otot=t, peralatan=p,
                tipe=ti, deskripsi_singkat=d, cns_cluster=c,
            )
            for (k, n, t, p, ti, d, c) in fallback
        ]

    db.session.bulk_save_objects(rows_to_insert)
    db.session.commit()
    print(f"[KUAT] Seeded {len(rows_to_insert)} exercises ke ExerciseDB.")
