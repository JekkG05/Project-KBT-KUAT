from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user

from app.config import supabase
from app.services.kuat_engine import KuatTracker
from app.services.chart_generator import generate_dashboard_chart_data


home_bp = Blueprint("home", __name__)


@home_bp.route("/", methods=["GET", "POST"])
def index():

    if not current_user.is_authenticated:
        return render_template(
            "home.html",
            landing_only=True
        )


    # ambil engine state user dari Supabase
    engine_result = (
        supabase
        .table("engine_state")
        .select("*")
        .eq("user_id", current_user.id)
        .single()
        .execute()
    )


    engine_state = engine_result.data


    if not engine_state:

        tracker = KuatTracker(
            initial_dl=current_user.initial_dl,
            initial_sq=current_user.initial_sq,
            initial_bp=current_user.initial_bp,
        )


        supabase.table("engine_state").insert(
            {
                "user_id": current_user.id,
                "state_json": tracker.to_dict()
            }
        ).execute()


        state = tracker.to_dict()


    else:

        tracker = KuatTracker.from_dict(
            engine_state["state_json"]
        )

        state = engine_state["state_json"]



    # morning check
    if request.method == "POST":

        energi_slider = request.form.get(
            "energi_slider"
        )


        try:
            energi_slider = int(energi_slider)

        except:
            energi_slider = 3



        tracker.morning_check(
            energi_slider
        )


        supabase.table("engine_state") \
            .update(
                {
                    "state_json": tracker.to_dict()
                }
            ) \
            .eq(
                "user_id",
                current_user.id
            ) \
            .execute()


        flash(
            "Morning check-in tersimpan. Semangat latihan hari ini!",
            "success"
        )


        return redirect(
            url_for("home.index")
        )



    # total workout
    workout_result = (
        supabase
        .table("workout_log")
        .select("*")
        .eq(
            "user_id",
            current_user.id
        )
        .execute()
    )


    workouts = workout_result.data or []


    total_workout = len(workouts)



    total_volume = round(
        sum(
            float(x.get("volume", 0))
            for x in workouts
        ),
        2
    )



    chart_data = {

        "daily":
            generate_dashboard_chart_data(
                current_user.id,
                period="daily"
            ),


        "weekly":
            generate_dashboard_chart_data(
                current_user.id,
                period="weekly"
            ),


        "monthly":
            generate_dashboard_chart_data(
                current_user.id,
                period="monthly"
            )

    }



    return render_template(
        "home.html",
        landing_only=False,
        state=state,
        total_workout=total_workout,
        total_volume=total_volume,
        chart_data=chart_data,
    )
