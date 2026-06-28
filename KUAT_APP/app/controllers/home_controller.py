from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required
from app import db
from app.models.workout_log import WorkoutLog
from app.models.engine_state import EngineState
from app.services.kuat_engine import KuatTracker
from app.services.chart_generator import build_chart_data


home_bp = Blueprint("home", __name__)


def _get_engine_state():
    state = current_user.engine_state
    if state is None:
        engine = KuatTracker.from_user(current_user)
        state = EngineState(user_id=current_user.id)
        state.update_from_dict(engine.to_dict())
        db.session.add(state)
        db.session.commit()
    return state


@home_bp.route("/", methods=["GET", "POST"])
@login_required
def home():
    state_model = _get_engine_state()
    state_dict = state_model.as_dict()
    engine = KuatTracker.from_user(current_user, state_dict)

    morning_result = None
    if request.method == "POST":
        try:
            energi = float(request.form.get("energi_slider", 3))
            bpm = float(request.form.get("bpm_pagi", current_user.bpm_base))
        except ValueError:
            flash("Input morning check-in tidak valid.", "danger")
            return redirect(url_for("home.home"))
        morning_result = engine.morning_check(energi, bpm)
        state_model.update_from_dict(engine.to_dict())
        db.session.commit()
        if morning_result["warnings"]:
            for warning in morning_result["warnings"]:
                flash(warning["message"], "warning")
        else:
            flash("Morning check-in tersimpan. k_recovery diperbarui.", "success")
        return redirect(url_for("home.home"))

    logs = (
        WorkoutLog.query.filter_by(user_id=current_user.id)
        .order_by(WorkoutLog.created_at.asc())
        .limit(120)
        .all()
    )
    chart_data = build_chart_data(logs, engine.to_dict())
    return render_template("home.html", state=engine.to_dict(), chart_data=chart_data, morning_result=morning_result)
