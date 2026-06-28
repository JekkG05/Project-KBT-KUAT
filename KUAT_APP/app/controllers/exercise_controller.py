from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required
from app import db
from app.models.exercise_db import ExerciseDB
from app.models.workout_plan import WorkoutPlan


exercise_bp = Blueprint("exercise", __name__)


@exercise_bp.route("/exercise", methods=["GET", "POST"])
@login_required
def exercise():
    exercises = ExerciseDB.query.order_by(ExerciseDB.kategori.asc(), ExerciseDB.nama_latihan.asc()).all()

    if request.method == "POST":
        try:
            exercise_id = int(request.form.get("exercise_id", 0))
            target_sets = int(request.form.get("target_sets", 3))
            target_reps = int(request.form.get("target_reps", 8))
            target_load = float(request.form.get("target_load", 20))
        except ValueError:
            flash("Input rencana latihan tidak valid.", "danger")
            return render_template("exercise.html", exercises=exercises)

        selected = ExerciseDB.query.get(exercise_id)
        if not selected:
            flash("Pilih gerakan terlebih dahulu.", "danger")
            return render_template("exercise.html", exercises=exercises)

        folder = request.form.get("folder_name", "").strip() or "Default"
        title = request.form.get("title", "").strip() or selected.nama_latihan
        plan = WorkoutPlan(
            user_id=current_user.id,
            folder_name=folder,
            title=title,
            exercise_id=selected.id,
            nama_gerakan=selected.nama_latihan,
            target_otot=selected.target_otot,
            cluster=selected.cns_cluster,
            target_sets=max(1, target_sets),
            target_reps=max(1, target_reps),
            target_load=max(0.0, target_load),
            notes=request.form.get("notes", "").strip(),
        )
        db.session.add(plan)
        db.session.commit()
        flash("Rencana latihan tersimpan.", "success")
        return redirect(url_for("routine.routines"))

    recent = WorkoutPlan.query.filter_by(user_id=current_user.id).order_by(WorkoutPlan.created_at.desc()).limit(7).all()
    return render_template("exercise.html", exercises=exercises, recent=recent)
