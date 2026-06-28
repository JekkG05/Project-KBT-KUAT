from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import (
    login_user,
    logout_user,
    login_required,
    current_user
)

from werkzeug.security import generate_password_hash, check_password_hash

from app.config import supabase
from app.services.kuat_engine import KuatTracker
from app.models.user import User


auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/login", methods=["GET", "POST"])
def login():

    if current_user.is_authenticated:
        return redirect(url_for("home.index"))


    if request.method == "POST":

        email = (
            request.form.get("email") or ""
        ).strip().lower()

        password = (
            request.form.get("password") or ""
        )


        if not email or not password:

            flash(
                "Email dan password wajib diisi.",
                "danger"
            )

            return redirect(url_for("auth.login"))


        try:

            result = (
                supabase
                .table("users")
                .select("*")
                .eq("email", email)
                .single()
                .execute()
            )


            user_data = result.data


        except Exception:

            flash(
                "Email atau password salah.",
                "danger"
            )

            return redirect(url_for("auth.login"))



        if user_data and check_password_hash(
            user_data["password_hash"],
            password
        ):


            user = User(
                **user_data
            )


            login_user(user)


            flash(
                f"Selamat datang kembali, {user.name}!",
                "success"
            )


            return redirect(
                url_for("home.index")
            )


        flash(
            "Email atau password salah.",
            "danger"
        )


        return redirect(
            url_for("auth.login")
        )


    return render_template(
        "auth/login.html"
    )





@auth_bp.route("/signup", methods=["GET", "POST"])
def signup():


    if current_user.is_authenticated:

        return redirect(
            url_for("home.index")
        )



    if request.method == "POST":


        form = request.form


        name = (
            form.get("name") or ""
        ).strip()


        email = (
            form.get("email") or ""
        ).strip().lower()


        password = (
            form.get("password") or ""
        )


        confirm_password = (
            form.get("confirm_password") or ""
        )


        if password != confirm_password:

            flash(
                "Konfirmasi password tidak sama.",
                "danger"
            )

            return redirect(
                url_for("auth.signup")
            )



        gender = (
            form.get("gender") or ""
        ).upper()



        try:

            usia = int(form.get("usia"))
            bb = float(form.get("bb"))
            tinggi = float(form.get("tinggi"))

            initial_dl = float(form.get("initial_dl"))
            initial_sq = float(form.get("initial_sq"))
            initial_bp = float(form.get("initial_bp"))


        except:

            flash(
                "Data angka tidak valid.",
                "danger"
            )

            return redirect(
                url_for("auth.signup")
            )



        experience_level = (
            form.get("experience_level") or ""
        ).lower()


        injury_history = (
            form.get("injury_history") or ""
        )



        tier = (
            form.get("tier") or "free"
        )



        existing = (
            supabase
            .table("users")
            .select("id")
            .eq("email", email)
            .execute()
        )


        if existing.data:


            flash(
                "Email sudah terdaftar.",
                "danger"
            )

            return redirect(
                url_for("auth.signup")
            )



        password_hash = generate_password_hash(
            password
        )



        new_user = (

            supabase
            .table("users")
            .insert(
                {

                    "name": name,

                    "email": email,

                    "password_hash": password_hash,

                    "gender": gender,

                    "usia": usia,

                    "bb": bb,

                    "tinggi": tinggi,

                    "experience_level": experience_level,

                    "injury_history": injury_history,

                    "initial_dl": initial_dl,

                    "initial_sq": initial_sq,

                    "initial_bp": initial_bp,

                    "tier": tier

                }
            )
            .execute()

        )



        user_id = new_user.data[0]["id"]



        tracker = KuatTracker(

            initial_dl=initial_dl,

            initial_sq=initial_sq,

            initial_bp=initial_bp

        )



        supabase.table(
            "engine_states"
        ).insert(
            {

                "user_id": user_id,

                "state_json": tracker.to_dict()

            }

        ).execute()




        user = User(
            **new_user.data[0]
        )


        login_user(user)



        flash(
            f"Akun berhasil dibuat. Selamat datang, {name}!",
            "success"
        )


        return redirect(
            url_for("home.index")
        )



    return render_template(
        "auth/signup.html"
    )





@auth_bp.route("/logout")
@login_required
def logout():


    logout_user()


    flash(
        "Anda telah logout.",
        "success"
    )


    return redirect(
        url_for("auth.login")
    )
