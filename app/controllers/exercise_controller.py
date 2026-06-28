from flask import Blueprint, render_template, request, redirect, url_for, flash, abort
from flask_login import login_required, current_user

from app import db
from app.models.workout_plan import WorkoutPlan
from app.models.workout_plan_item import WorkoutPlanItem
from app.models.exercise_db import ExerciseDB

exercise_bp = Blueprint("exercise", __name__, url_prefix="/exercise")


def _get_owned_plan_or_404(plan_id):
    plan = WorkoutPlan.query.get_or_404(plan_id)
    if plan.user_id != current_user.id:
        abort(403)
    return plan


def _get_owned_item_or_404(item_id):
    item = WorkoutPlanItem.query.get_or_404(item_id)
    if item.plan.user_id != current_user.id:
        abort(403)
    return item


@exercise_bp.route("/", methods=["GET"])
@login_required
def index():
    plans = (
        WorkoutPlan.query.filter_by(user_id=current_user.id)
        .order_by(WorkoutPlan.created_at.desc())
        .all()
    )
    exercises = ExerciseDB.query.order_by(ExerciseDB.nama_latihan.asc()).all()

    active_plan_id = request.args.get("plan_id", type=int)
    active_plan = None
    if active_plan_id:
        active_plan = WorkoutPlan.query.filter_by(id=active_plan_id, user_id=current_user.id).first()
    if active_plan is None and plans:
        active_plan = plans[0]

    return render_template(
        "exercise.html",
        plans=plans,
        exercises=exercises,
        active_plan=active_plan,
    )


@exercise_bp.route("/create-plan", methods=["POST"])
@login_required
def create_plan():
    folder_name = (request.form.get("folder_name") or "").strip()
    train_focus = (request.form.get("train_focus") or "").strip()
    notes = (request.form.get("notes") or "").strip()

    if not folder_name:
        flash("Title routine tidak boleh kosong.", "danger")
        return redirect(url_for("exercise.index"))

    plan = WorkoutPlan(
        user_id=current_user.id,
        folder_name=folder_name,
        train_focus=train_focus or None,
        notes=notes or None,
    )
    db.session.add(plan)
    db.session.commit()

    flash(f"Routine '{folder_name}' berhasil dibuat.", "success")
    return redirect(url_for("exercise.index", plan_id=plan.id))


@exercise_bp.route("/add-item/<int:plan_id>", methods=["POST"])
@login_required
def add_item(plan_id):
    plan = _get_owned_plan_or_404(plan_id)

    exercise_id = request.form.get("exercise_id", type=int)
    target_sets = request.form.get("target_sets", type=int) or 3
    target_reps = request.form.get("target_reps", type=int) or 10
    target_weight = request.form.get("target_weight", type=float) or 0.0

    exercise = ExerciseDB.query.get(exercise_id) if exercise_id else None
    if exercise is None:
        flash("Pilih exercise yang valid dari daftar.", "danger")
        return redirect(url_for("exercise.index", plan_id=plan.id))

    item_order = len(plan.items)

    item = WorkoutPlanItem(
        plan_id=plan.id,
        exercise_id=exercise.id,
        nama_gerakan=exercise.nama_latihan,
        cluster=exercise.cns_cluster or "B",
        target_sets=target_sets,
        target_reps=target_reps,
        target_weight=target_weight,
        item_order=item_order,
    )
    db.session.add(item)
    db.session.commit()

    flash(f"{exercise.nama_latihan} ditambahkan ke routine.", "success")
    return redirect(url_for("exercise.index", plan_id=plan.id))


@exercise_bp.route("/edit-item/<int:item_id>", methods=["POST"])
@login_required
def edit_item(item_id):
    item = _get_owned_item_or_404(item_id)

    target_sets = request.form.get("target_sets", type=int)
    target_reps = request.form.get("target_reps", type=int)
    target_weight = request.form.get("target_weight", type=float)

    if target_sets is not None and target_sets > 0:
        item.target_sets = target_sets
    if target_reps is not None and target_reps > 0:
        item.target_reps = target_reps
    if target_weight is not None and target_weight >= 0:
        item.target_weight = target_weight

    db.session.commit()
    flash(f"{item.nama_gerakan} berhasil diperbarui.", "success")
    return redirect(url_for("exercise.index", plan_id=item.plan_id))


@exercise_bp.route("/delete-item/<int:item_id>", methods=["POST"])
@login_required
def delete_item(item_id):
    item = _get_owned_item_or_404(item_id)
    plan_id = item.plan_id
    nama = item.nama_gerakan

    db.session.delete(item)
    db.session.commit()

    flash(f"{nama} dihapus dari routine.", "success")
    return redirect(url_for("exercise.index", plan_id=plan_id))


@exercise_bp.route("/delete-plan/<int:plan_id>", methods=["POST"])
@login_required
def delete_plan(plan_id):
    plan = _get_owned_plan_or_404(plan_id)
    folder_name = plan.folder_name

    db.session.delete(plan)
    db.session.commit()

    flash(f"Routine '{folder_name}' dihapus.", "success")
    return redirect(url_for("exercise.index"))
