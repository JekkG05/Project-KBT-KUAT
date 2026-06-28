from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user

from app import db
from app.models.engine_state import EngineState
from app.models.workout_log import WorkoutLog
from app.services.kuat_engine import KuatTracker
from app.services.chart_generator import generate_dashboard_chart_data

home_bp = Blueprint("home", __name__)


@home_bp.route("/", methods=["GET", "POST"])
def index():
    if not current_user.is_authenticated:
        return render_template("home.html", landing_only=True)

    engine_state = EngineState.query.filter_by(user_id=current_user.id).first()
    if engine_state is None:
        tracker = KuatTracker(
            initial_dl=current_user.initial_dl,
            initial_sq=current_user.initial_sq,
            initial_bp=current_user.initial_bp,
        )
        engine_state = EngineState(user_id=current_user.id, state_json=tracker.to_dict())
        db.session.add(engine_state)
        db.session.commit()
    else:
        tracker = KuatTracker.from_dict(engine_state.state_json)

    if request.method == "POST":
        energi_slider = request.form.get("energi_slider")
        try:
            energi_slider = int(energi_slider)
        except (TypeError, ValueError):
            energi_slider = 3

        tracker.morning_check(energi_slider)
        engine_state.state_json = tracker.to_dict()
        db.session.commit()
        flash("Morning check-in tersimpan. Semangat latihan hari ini!", "success")
        return redirect(url_for("home.index"))

    total_workout = WorkoutLog.query.filter_by(user_id=current_user.id).count()
    total_volume_row = db.session.query(db.func.coalesce(db.func.sum(WorkoutLog.volume), 0.0)).filter(
        WorkoutLog.user_id == current_user.id
    ).scalar()
    total_volume = round(total_volume_row or 0.0, 2)

    chart_data = {
        "daily": generate_dashboard_chart_data(current_user.id, period="daily"),
        "weekly": generate_dashboard_chart_data(current_user.id, period="weekly"),
        "monthly": generate_dashboard_chart_data(current_user.id, period="monthly"),
    }

    state = engine_state.state_json or {}

    return render_template(
        "home.html",
        landing_only=False,
        state=state,
        total_workout=total_workout,
        total_volume=total_volume,
        chart_data=chart_data,
    )
