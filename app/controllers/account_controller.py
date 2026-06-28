from flask import Blueprint, render_template, redirect, url_for, flash
from flask_login import login_required, current_user

from app.config import supabase


account_bp = Blueprint(
    "account",
    __name__,
    url_prefix="/account"
)


@account_bp.route("/", methods=["GET"])
@login_required
def index():

    workout_result = (
        supabase
        .table("workout_logs")
        .select("*")
        .eq(
            "user_id",
            current_user.id
        )
        .execute()
    )


    workouts = workout_result.data or []


    total_workout = len(workouts)


    return render_template(
        "account.html",
        total_workout=total_workout
    )



@account_bp.route("/upgrade", methods=["POST"])
@login_required
def upgrade():

    if current_user.tier == "premium":

        flash(
            "Akun kamu sudah PREMIUM ACTIVE.",
            "success"
        )

        return redirect(
            url_for("account.index")
        )



    supabase.table("users") \
        .update(
            {
                "tier": "premium"
            }
        ) \
        .eq(
            "id",
            current_user.id
        ) \
        .execute()



    flash(
        "⭐ Selamat! Akun kamu sekarang PREMIUM ACTIVE. "
        "Early Warning System personal sudah aktif di halaman Train.",
        "success",
    )


    return redirect(
        url_for("account.index")
    )



@account_bp.route("/downgrade", methods=["POST"])
@login_required
def downgrade():

    if current_user.tier == "free":

        flash(
            "Akun kamu sudah FREE VERSION.",
            "success"
        )

        return redirect(
            url_for("account.index")
        )



    supabase.table("users") \
        .update(
            {
                "tier": "free"
            }
        ) \
        .eq(
            "id",
            current_user.id
        ) \
        .execute()



    flash(
        "Akun kamu kembali ke 🆓 FREE VERSION.",
        "success"
    )


    return redirect(
        url_for("account.index")
    )
