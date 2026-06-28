from collections import defaultdict
from flask import Blueprint, render_template
from flask_login import current_user, login_required
from app.models.workout_plan import WorkoutPlan


routine_bp = Blueprint("routine", __name__)


@routine_bp.route("/routines")
@login_required
def routines():
    plans = WorkoutPlan.query.filter_by(user_id=current_user.id).order_by(WorkoutPlan.created_at.desc()).all()
    grouped = defaultdict(list)
    for plan in plans:
        grouped[plan.folder_name].append(plan)
    return render_template("routines.html", plans=plans, grouped=dict(grouped))
