from flask import Blueprint, render_template
from flask_login import login_required, current_user

from app.models.workout_plan import WorkoutPlan
from app.models.workout_log import WorkoutLog

routine_bp = Blueprint("routine", __name__, url_prefix="/routines")


@routine_bp.route("/", methods=["GET"])
@login_required
def index():
    plans = (
        WorkoutPlan.query.filter_by(user_id=current_user.id)
        .order_by(WorkoutPlan.created_at.desc())
        .all()
    )

    recent_logs = (
        WorkoutLog.query.filter_by(user_id=current_user.id)
        .order_by(WorkoutLog.created_at.desc())
        .limit(10)
        .all()
    )

    return render_template(
        "routines.html",
        plans=plans,
        recent_logs=recent_logs,
    )
