from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    url_for,
    flash
)

from flask_login import current_user

from app.config import supabase
from app.services.kuat_engine import KuatTracker
from app.services.chart_generator import generate_dashboard_chart_data



home_bp = Blueprint(
    "home",
    __name__
)



@home_bp.route("/", methods=["GET","POST"])
def index():


    if not current_user.is_authenticated:

        return render_template(
            "home.html",
            landing_only=True
        )



    engine_result = (
        supabase
        .table("engine_state")
        .select("*")
        .eq(
            "user_id",
            current_user.id
        )
        .execute()
    )



    engine_state = None


    if engine_result.data:

        engine_state = engine_result.data[0]



    if not engine_state:


        tracker = KuatTracker(

            initial_dl=current_user.initial_dl,

            initial_sq=current_user.initial_sq,

            initial_bp=current_user.initial_bp

        )


        supabase.table(
            "engine_state"
        ).insert(
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




    if request.method == "POST":


        energi = request.form.get(
            "energi_slider",
            3
        )


        try:

            energi = int(energi)

        except:

            energi = 3



        tracker.morning_check(
            energi
        )



        supabase.table(
            "engine_state"
        ).update(
            {

            "state_json":
                tracker.to_dict()

            }
        ).eq(
            "user_id",
            current_user.id
        ).execute()



        flash(
            "Morning check tersimpan!",
            "success"
        )


        return redirect(
            url_for(
                "home.index"
            )
        )




    workouts = (

        supabase
        .table("workout_log")
        .select("*")
        .eq(
            "user_id",
            current_user.id
        )
        .execute()
        .data
        or []

    )



    total_workout = len(workouts)



    total_volume = sum(

        float(
            x.get(
                "volume",
                0
            )
        )

        for x in workouts

    )



    chart_data = {

        "daily":
        generate_dashboard_chart_data(
            current_user.id,
            "daily"
        ),


        "weekly":
        generate_dashboard_chart_data(
            current_user.id,
            "weekly"
        ),


        "monthly":
        generate_dashboard_chart_data(
            current_user.id,
            "monthly"
        )

    }



    return render_template(

        "home.html",

        landing_only=False,

        state=state,

        total_workout=total_workout,

        total_volume=total_volume,

        chart_data=chart_data

    )
