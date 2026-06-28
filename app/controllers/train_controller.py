from datetime import datetime, timedelta

from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, abort
from flask_login import login_required, current_user

from app import db
from app.models.workout_plan import WorkoutPlan
from app.models.workout_plan_item import WorkoutPlanItem
from app.models.workout_log import WorkoutLog
from app.models.engine_state import EngineState
from app.services.kuat_engine import KuatTracker

train_bp = Blueprint("train", __name__, url_prefix="/train")


@train_bp.route("/", methods=["GET"])
@login_required
def train_landing():
    """Jika user klik TRAIN di navbar tanpa memilih routine dulu."""
    plan = (
        WorkoutPlan.query.filter_by(user_id=current_user.id)
        .order_by(WorkoutPlan.created_at.desc())
        .first()
    )
    if plan is None:
        flash("Buat routine terlebih dahulu sebelum mulai latihan.", "warning")
        return redirect(url_for("exercise.index"))
    return redirect(url_for("train.train_session", plan_id=plan.id))


@train_bp.route("/<int:plan_id>", methods=["GET"])
@login_required
def train_session(plan_id):
    plan = WorkoutPlan.query.get_or_404(plan_id)
    if plan.user_id != current_user.id:
        abort(403)

    items = (
        WorkoutPlanItem.query.filter_by(plan_id=plan.id)
        .order_by(WorkoutPlanItem.item_order.asc())
        .all()
    )

    engine_state = EngineState.query.filter_by(user_id=current_user.id).first()
    state = engine_state.state_json if engine_state else {}

    items_json = [
        {
            "id": item.id,
            "nama_gerakan": item.nama_gerakan,
            "cluster": item.cluster,
            "target_sets": item.target_sets,
            "target_reps": item.target_reps,
            "target_weight": item.target_weight,
        }
        for item in items
    ]

    return render_template(
        "train.html",
        plan=plan,
        items=items,
        items_json=items_json,
        state=state,
    )


@train_bp.route("/log_set", methods=["POST"])
@login_required
def log_set():
    data = request.get_json(silent=True) or {}

    plan_id = data.get("plan_id")
    plan_item_id = data.get("plan_item_id")
    nama = data.get("nama")
    cluster = data.get("cluster") or "B"
    beban = data.get("beban")
    reps = data.get("reps")
    rir = data.get("rir")

    if plan_id is None or nama is None or beban is None or reps is None or rir is None:
        return jsonify({"success": False, "error": "Data set tidak lengkap."}), 400

    plan = WorkoutPlan.query.get(plan_id)
    if plan is None or plan.user_id != current_user.id:
        return jsonify({"success": False, "error": "Routine tidak ditemukan atau bukan milik Anda."}), 403

    if plan_item_id:
        plan_item = WorkoutPlanItem.query.get(plan_item_id)
        if plan_item is None or plan_item.plan.user_id != current_user.id:
            return jsonify({"success": False, "error": "Item latihan tidak valid."}), 403

    # --- Ambil EngineState ---
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

    # --- Ambil recent logs 30 hari terakhir, prioritas gerakan sama ---
    since = datetime.utcnow() - timedelta(days=30)

    recent_same_exercise = (
        WorkoutLog.query.filter(
            WorkoutLog.user_id == current_user.id,
            WorkoutLog.nama_gerakan == nama,
            WorkoutLog.created_at >= since,
        )
        .order_by(WorkoutLog.created_at.desc())
        .all()
    )

    if len(recent_same_exercise) >= 3:
        recent_logs = recent_same_exercise
    else:
        recent_logs = (
            WorkoutLog.query.filter(
                WorkoutLog.user_id == current_user.id,
                WorkoutLog.cluster == cluster,
                WorkoutLog.created_at >= since,
            )
            .order_by(WorkoutLog.created_at.desc())
            .all()
        )

    try:
        result = tracker.log_set(
            user_id=current_user.id,
            nama_gerakan=nama,
            cluster=cluster,
            beban=beban,
            reps=reps,
            rir_user=rir,
            bodyweight=current_user.bb,
            recent_logs=recent_logs,
        )
    except ValueError as exc:
        return jsonify({"success": False, "error": str(exc)}), 400

    # --- Simpan WorkoutLog ---
    log_entry = WorkoutLog(
        user_id=current_user.id,
        plan_id=plan_id,
        plan_item_id=plan_item_id,
        nama_gerakan=nama,
        cluster=cluster,
        beban_aktual=float(beban),
        reps_aktual=int(reps),
        rir_input=int(rir),
        rpe_converted=result["rpe_converted"],
        volume=result["volume"],
        estimated_1rm=result["estimated_1rm"],
        fatigue_total=result["total_fatigue"],
        cns_fatigue=result["cns_fatigue"],
        acwr=result["acwr"],
        fsm_state=result["fsm_state"],
    )
    db.session.add(log_entry)

    # --- Update EngineState ---
    engine_state.state_json = tracker.to_dict()

    db.session.commit()

    # --- Filter warning untuk user free (LARANGAN: free tidak boleh terima warning) ---
    response_payload = {
        "success": True,
        "rpe_converted": result["rpe_converted"],
        "volume": result["volume"],
        "estimated_1rm": result["estimated_1rm"],
        "cns_fatigue": result["cns_fatigue"],
        "total_fatigue": result["total_fatigue"],
        "acwr": result["acwr"],
        "fsm_state": result["fsm_state"],
        "warnings": result["warnings"],
    }

    if current_user.tier == "free":
        response_payload["warnings"] = []

    return jsonify(response_payload)
