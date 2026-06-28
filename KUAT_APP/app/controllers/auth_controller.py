from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_user, logout_user
from app import db
from app.models.user import User
from app.models.engine_state import EngineState
from app.services.kuat_engine import KuatTracker


auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("home.home"))

    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        user = User.query.filter_by(email=email).first()
        if not user or not user.check_password(password):
            flash("Email atau password tidak tepat.", "danger")
            return render_template("auth/login.html")
        login_user(user)
        flash("Login berhasil. Selamat datang di KUAT.", "success")
        return redirect(url_for("home.home"))

    return render_template("auth/login.html")


@auth_bp.route("/signup", methods=["GET", "POST"])
def signup():
    if current_user.is_authenticated:
        return redirect(url_for("home.home"))

    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        password_confirm = request.form.get("password_confirm", "")
        first = request.form.get("first_name", "").strip()
        last = request.form.get("last_name", "").strip()

        if not email or not password or password != password_confirm:
            flash("Email wajib diisi dan konfirmasi password harus sama.", "danger")
            return render_template("auth/signup.html")
        if User.query.filter_by(email=email).first():
            flash("Email sudah terdaftar.", "danger")
            return render_template("auth/signup.html")

        try:
            user = User(
                email=email,
                name=f"{first} {last}".strip() or email.split("@")[0],
                usia=int(request.form.get("usia", 0)),
                bb=float(request.form.get("bb", 0)),
                tinggi=float(request.form.get("tinggi")) if request.form.get("tinggi") else None,
                bpm_base=int(request.form.get("bpm_base", 0)),
                experience_level=request.form.get("experience_level", "intermediate"),
                injury_history=request.form.get("injury_history", "").strip(),
                initial_dl=float(request.form.get("initial_dl", 0)),
                initial_sq=float(request.form.get("initial_sq", 0)),
                initial_bp=float(request.form.get("initial_bp", 0)),
            )
        except ValueError:
            flash("Data numerik belum valid. Periksa usia, BB, BPM, dan 1RM awal.", "danger")
            return render_template("auth/signup.html")

        required_numbers = [user.usia, user.bb, user.bpm_base, user.initial_dl, user.initial_sq, user.initial_bp]
        if any(float(x) <= 0 for x in required_numbers):
            flash("Usia, BB, BPM baseline, dan 1RM awal wajib lebih dari 0.", "danger")
            return render_template("auth/signup.html")

        user.set_password(password)
        db.session.add(user)
        db.session.flush()

        engine = KuatTracker.from_user(user)
        state = EngineState(user_id=user.id)
        state.update_from_dict(engine.to_dict())
        db.session.add(state)
        db.session.commit()

        flash("Akun KUAT berhasil dibuat. Silakan login.", "success")
        return redirect(url_for("auth.login"))

    return render_template("auth/signup.html")


@auth_bp.route("/logout")
def logout():
    logout_user()
    flash("Anda sudah logout.", "info")
    return redirect(url_for("auth.login"))
