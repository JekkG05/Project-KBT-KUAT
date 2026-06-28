from datetime import datetime, timedelta

from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, abort
from flask_login import login_required, current_user

from app.config import supabase
from app.services.kuat_engine import KuatTracker


train_bp = Blueprint(
    "train",
    __name__,
    url_prefix="/train"
)



@train_bp.route("/", methods=["GET"])
@login_required
def train_landing():


    result = (
        supabase
        .table("workout_plan")
        .select("*")
        .eq(
            "user_id",
            current_user.id
        )
        .order(
            "created_at",
            desc=True
        )
        .limit(1)
        .execute()
    )


    plans = result.data


    if not plans:

        flash(
            "Buat routine terlebih dahulu sebelum mulai latihan.",
            "warning"
        )

        return redirect(
            url_for("exercise.index")
        )


    return redirect(
        url_for(
            "train.train_session",
            plan_id=plans[0]["id"]
        )
    )





@train_bp.route("/<int:plan_id>", methods=["GET"])
@login_required
def train_session(plan_id):


    plan_result = (
        supabase
        .table("workout_plan")
        .select("*")
        .eq(
            "id",
            plan_id
        )
        .eq(
            "user_id",
            current_user.id
        )
        .single()
        .execute()
    )


    plan = plan_result.data


    if not plan:

        abort(404)



    items_result = (
        supabase
        .table("workout_plan_item")
        .select("*")
        .eq(
            "plan_id",
            plan_id
        )
        .order(
            "id"
        )
        .execute()
    )


    items = items_result.data or []



    state_result = (
        supabase
        .table("engine_state")
        .select("*")
        .eq(
            "user_id",
            current_user.id
        )
        .single()
        .execute()
    )


    state = {}


    if state_result.data:

        state = state_result.data["state_json"]



    items_json = [

        {

            "id": item["id"],

            "nama_gerakan": item["nama_gerakan"],

            "cluster": item["cluster"],

            "target_sets": item["target_sets"],

            "target_reps": item["target_reps"],

            "target_weight": item["target_weight"],

        }

        for item in items

    ]



    return render_template(
        "train.html",
        plan=plan,
        items=items,
        items_json=items_json,
        state=state
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



    if None in (
        plan_id,
        nama,
        beban,
        reps,
        rir
    ):

        return jsonify(
            {
                "success":False,
                "error":"Data set tidak lengkap."
            }
        ),400




    plan_check = (
        supabase
        .table("workout_plan")
        .select("*")
        .eq("id",plan_id)
        .eq("user_id",current_user.id)
        .execute()
    )


    if not plan_check.data:

        return jsonify(
            {
                "success":False,
                "error":"Routine tidak ditemukan."
            }
        ),403




    # ambil engine state

    state_result = (
        supabase
        .table("engine_state")
        .select("*")
        .eq(
            "user_id",
            current_user.id
        )
        .execute()
    )



    if not state_result.data:


        tracker = KuatTracker(

            initial_dl=current_user.initial_dl,

            initial_sq=current_user.initial_sq,

            initial_bp=current_user.initial_bp

        )


        supabase.table(
            "engine_state"
        ).insert(
            {

                "user_id":current_user.id,

                "state_json":tracker.to_dict()

            }

        ).execute()



    else:


        tracker = KuatTracker.from_dict(

            state_result.data[0]["state_json"]

        )




    since = (
        datetime.utcnow()
        -
        timedelta(days=30)
    )



    logs_result = (
        supabase
        .table("workout_log")
        .select("*")
        .eq(
            "user_id",
            current_user.id
        )
        .gte(
            "created_at",
            since.isoformat()
        )
        .order(
            "created_at",
            desc=True
        )
        .execute()
    )


    recent_logs = logs_result.data or []




    try:

        result = tracker.log_set(

            user_id=current_user.id,

            nama_gerakan=nama,

            cluster=cluster,

            beban=beban,

            reps=reps,

            rir_user=rir,

            bodyweight=current_user.bb,

            recent_logs=recent_logs

        )


    except ValueError as exc:


        return jsonify(
            {
                "success":False,
                "error":str(exc)
            }
        ),400





    supabase.table(
        "workout_log"
    ).insert(
        {

            "user_id":current_user.id,

            "plan_id":plan_id,

            "plan_item_id":plan_item_id,

            "nama_gerakan":nama,

            "cluster":cluster,

            "beban_aktual":float(beban),

            "reps_aktual":int(reps),

            "rir_input":int(rir),

            "rpe_converted":result["rpe_converted"],

            "volume":result["volume"],

            "estimated_1rm":result["estimated_1rm"],

            "fatigue_total":result["total_fatigue"],

            "cns_fatigue":result["cns_fatigue"],

            "acwr":result["acwr"],

            "fsm_state":result["fsm_state"]

        }

    ).execute()





    supabase.table(
        "engine_state"
    ).update(
        {
            "state_json":tracker.to_dict()
        }
    ).eq(
        "user_id",
        current_user.id
    ).execute()





    response_payload = {

        "success":True,

        "rpe_converted":result["rpe_converted"],

        "volume":result["volume"],

        "estimated_1rm":result["estimated_1rm"],

        "cns_fatigue":result["cns_fatigue"],

        "total_fatigue":result["total_fatigue"],

        "acwr":result["acwr"],

        "fsm_state":result["fsm_state"],

        "warnings":result["warnings"]

    }



    if current_user.tier == "free":

        response_payload["warnings"] = []



    return jsonify(response_payload)
