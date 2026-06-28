from flask import Blueprint, render_template, redirect, url_for, flash
from flask_login import login_required, current_user

from app import db
from app.models.workout_log import WorkoutLog

account_bp = Blueprint("account", __name__, url_prefix="/account")


@account_bp.route("/", methods=["GET"])
@login_required
def index():
    total_workout = WorkoutLog.query.filter_by(user_id=current_user.id).count()
    return render_template("account.html", total_workout=total_workout)


@account_bp.route("/upgrade", methods=["POST"])
@login_required
def upgrade():
    if current_user.tier == "premium":
        flash("Akun kamu sudah PREMIUM ACTIVE.", "success")
        return redirect(url_for("account.index"))

    current_user.tier = "premium"
    db.session.commit()
    flash(
        "⭐ Selamat! Akun kamu sekarang PREMIUM ACTIVE. "
        "Early Warning System personal sudah aktif di halaman Train.",
        "success",
    )
    return redirect(url_for("account.index"))


@account_bp.route("/downgrade", methods=["POST"])
@login_required
def downgrade():
    if current_user.tier == "free":
        flash("Akun kamu sudah FREE VERSION.", "success")
        return redirect(url_for("account.index"))

    current_user.tier = "free"
    db.session.commit()
    flash("Akun kamu kembali ke 🆓 FREE VERSION.", "success")
    return redirect(url_for("account.index"))
