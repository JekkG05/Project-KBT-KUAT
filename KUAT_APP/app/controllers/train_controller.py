from flask import Blueprint, jsonify, render_template, request
from flask_login import current_user, login_required
from app import db
from app.models.engine_state import EngineState
from app.models.workout_log import WorkoutLog
from app.models.workout_plan import WorkoutPlan
from app.services.kuat_engine import KuatTracker


train_bp = Blueprint("train", __name__)


def _state_model():
    state = current_user.engine_state
    if state is None:
        engine = KuatTracker.from_user(current_user)
        state = EngineState(user_id=current_user.id)
        state.update_from_dict(engine.to_dict())
        db.session.add(state)
        db.session.commit()
    return state


@train_bp.route("/train/<int:plan_id>")
@login_required
def train(plan_id):
    plan = WorkoutPlan.query.filter_by(id=plan_id, user_id=current_user.id).first_or_404()
    state = _state_model().as_dict()
    return render_template("train.html", plan=plan, state=state)


@train_bp.route("/train/log_set", methods=["POST"])
@login_required
def log_set():
    payload = request.get_json(silent=True) or {}
    try:
        plan_id = int(payload.get("plan_id"))
        beban = float(payload.get("beban"))
        reps = int(payload.get("reps"))
        rpe = float(payload.get("rpe"))
    except (TypeError, ValueError):
        return jsonify({"error": "Payload tidak valid."}), 400

    plan = WorkoutPlan.query.filter_by(id=plan_id, user_id=current_user.id).first()
    if not plan:
        return jsonify({"error": "Plan tidak ditemukan."}), 404

    nama = payload.get("nama") or plan.nama_gerakan
    cluster = (payload.get("cluster") or plan.cluster or "B").upper()

    state_model = _state_model()
    engine = KuatTracker.from_user(current_user, state_model.as_dict())
    result = engine.log_set(nama, cluster, beban, reps, rpe)

    log = WorkoutLog(
        user_id=current_user.id,
        plan_id=plan.id,
        nama_gerakan=nama,
        cluster=cluster,
        beban_aktual=beban,
        reps_aktual=reps,
        rpe_input=rpe,
        rpe_corrected=result["rpe_corrected"],
        fatigue_total=result["total_fatigue"],
        cns_fatigue=result["cns_fatigue"],
    )
    db.session.add(log)
    state_model.update_from_dict(engine.to_dict())
    db.session.commit()

    return jsonify(result)
