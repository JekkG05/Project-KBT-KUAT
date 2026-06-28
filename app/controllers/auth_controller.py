from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_user, logout_user, login_required, current_user

from app import db
from app.models.user import User
from app.models.engine_state import EngineState
from app.services.kuat_engine import KuatTracker

auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("home.index"))

    if request.method == "POST":
        email = (request.form.get("email") or "").strip().lower()
        password = request.form.get("password") or ""

        if not email or not password:
            flash("Email dan password wajib diisi.", "danger")
            return redirect(url_for("auth.login"))

        user = User.query.filter_by(email=email).first()
        if user and user.check_password(password):
            login_user(user)
            flash(f"Selamat datang kembali, {user.name}!", "success")
            return redirect(url_for("home.index"))

        flash("Email atau password salah.", "danger")
        return redirect(url_for("auth.login"))

    return render_template("auth/login.html")


@auth_bp.route("/signup", methods=["GET", "POST"])
def signup():
    if current_user.is_authenticated:
        return redirect(url_for("home.index"))

    if request.method == "POST":
        form = request.form

        # --- Step 1: Akun ---
        name = (form.get("name") or "").strip()
        email = (form.get("email") or "").strip().lower()
        password = form.get("password") or ""
        confirm_password = form.get("confirm_password") or ""

        # --- Step 2: Data diri ---
        gender = (form.get("gender") or "").strip().upper()
        usia = form.get("usia")
        bb = form.get("bb")
        tinggi = form.get("tinggi")
        experience_level = (form.get("experience_level") or "").strip().lower()
        injury_history = (form.get("injury_history") or "").strip()

        # --- Step 3: Target + tier ---
        initial_dl = form.get("initial_dl")
        initial_sq = form.get("initial_sq")
        initial_bp = form.get("initial_bp")
        tier_choice = (form.get("tier") or "free").strip().lower()

        # --- Validasi dasar ---
        errors = []

        if not name or not email or not password or not confirm_password:
            errors.append("Semua field akun wajib diisi.")
        if password and len(password) < 6:
            errors.append("Password minimal 6 karakter.")
        if password != confirm_password:
            errors.append("Password dan konfirmasi password tidak sama.")
        if gender not in ("L", "P"):
            errors.append("Gender hanya boleh L atau P.")
        if experience_level not in ("novice", "intermediate", "advanced"):
            errors.append("Experience level tidak valid.")
        if tier_choice not in ("free", "premium"):
            errors.append("Tier hanya boleh free atau premium.")

        try:
            usia_val = int(usia)
            bb_val = float(bb)
            tinggi_val = float(tinggi) if tinggi else None
            initial_dl_val = float(initial_dl)
            initial_sq_val = float(initial_sq)
            initial_bp_val = float(initial_bp)
        except (TypeError, ValueError):
            errors.append("Pastikan usia, berat badan, tinggi, dan target angkatan berupa angka.")
            usia_val = bb_val = tinggi_val = initial_dl_val = initial_sq_val = initial_bp_val = None

        if email and User.query.filter_by(email=email).first():
            errors.append("Email sudah terdaftar. Silakan login.")

        if errors:
            for e in errors:
                flash(e, "danger")
            return redirect(url_for("auth.signup"))

        new_user = User(
            email=email,
            name=name,
            gender=gender,
            usia=usia_val,
            bb=bb_val,
            tinggi=tinggi_val,
            experience_level=experience_level,
            injury_history=injury_history or None,
            initial_dl=initial_dl_val,
            initial_sq=initial_sq_val,
            initial_bp=initial_bp_val,
            tier=tier_choice,
        )
        new_user.set_password(password)

        db.session.add(new_user)
        db.session.commit()

        # Buat EngineState awal dari KuatTracker
        tracker = KuatTracker(
            initial_dl=new_user.initial_dl,
            initial_sq=new_user.initial_sq,
            initial_bp=new_user.initial_bp,
        )
        engine_state = EngineState(user_id=new_user.id, state_json=tracker.to_dict())
        db.session.add(engine_state)
        db.session.commit()

        login_user(new_user)
        flash(f"Akun berhasil dibuat. Selamat datang, {new_user.name}!", "success")
        return redirect(url_for("home.index"))

    return render_template("auth/signup.html")


@auth_bp.route("/logout")
@login_required
def logout():
    logout_user()
    flash("Anda telah logout.", "success")
    return redirect(url_for("auth.login"))
