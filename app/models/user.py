from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash


class User(UserMixin):

    def __init__(self, data=None, **kwargs):

        if data is None:
            data = {}

        if kwargs:
            data.update(kwargs)


        self.id = data.get("id")

        self.email = data.get("email")

        # database kamu pakai kolom password
        self.password_hash = data.get(
            "password"
        ) or data.get(
            "password_hash"
        )


        self.name = data.get(
            "name"
        )


        self.gender = data.get(
            "gender"
        )


        self.usia = data.get(
            "usia"
        )


        self.bb = data.get(
            "bb"
        )


        self.tinggi = data.get(
            "tinggi"
        )


        self.experience_level = data.get(
            "experience_level"
        )


        self.injury_history = data.get(
            "injury_history"
        )


        self.initial_dl = data.get(
            "initial_dl",
            0
        )


        self.initial_sq = data.get(
            "initial_sq",
            0
        )


        self.initial_bp = data.get(
            "initial_bp",
            0
        )


        self.tier = data.get(
            "tier",
            "free"
        )


        self.created_at = data.get(
            "created_at"
        )



    def set_password(self, password):

        self.password_hash = generate_password_hash(
            password
        )



    def check_password(self, password):

        return check_password_hash(
            self.password_hash,
            password
        )



    def is_premium(self):

        return self.tier == "premium"



    def __repr__(self):

        return (
            f"<User {self.email} ({self.tier})>"
        )
