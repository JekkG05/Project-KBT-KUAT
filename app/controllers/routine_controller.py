from flask import Blueprint, render_template
from flask_login import login_required, current_user

from app.config import supabase
from app.models.workout_plan import WorkoutPlan
from app.models.workout_log import WorkoutLog

routine_bp = Blueprint("routine", __name__, url_prefix="/routines")


@routine_bp.route("/", methods=["GET"])
@login_required
def index():
    plans_result = (
        supabase
        .table("workout_plans")
        .select("*")
        .eq("user_id", current_user.id)
        .order("created_at", desc=True)
        .execute()
    )
    plans = [WorkoutPlan(row) for row in (plans_result.data or [])]

    plan_ids = [p.id for p in plans]

    items_by_plan = {}
    if plan_ids:
        items_result = (
            supabase
            .table("workout_plan_items")
            .select("*")
            .in_("plan_id", plan_ids)
            .order("item_order")
            .execute()
        )
        for item in (items_result.data or []):
            items_by_plan.setdefault(item["plan_id"], []).append(item)

    for plan in plans:
        plan.items = items_by_plan.get(plan.id, [])

    logs_result = (
        supabase
        .table("workout_logs")
        .select("*")
        .eq("user_id", current_user.id)
        .order("created_at", desc=True)
        .limit(10)
        .execute()
    )
    recent_logs = [WorkoutLog(row) for row in (logs_result.data or [])]

    return render_template(
        "routines.html",
        plans=plans,
        recent_logs=recent_logs,
    )
