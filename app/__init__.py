from flask import Flask
from flask_login import LoginManager


login_manager = LoginManager()



@login_manager.user_loader
def load_user(user_id):

    from app.config import supabase

    result = (

        supabase
        .table("users")
        .select("*")
        .eq(
            "id",
            user_id
        )
        .execute()

    )


    if result.data:


        from app.models.user import User


        return User(
            result.data[0]
        )


    return None





def create_app():


    app = Flask(
        __name__
    )


    from app.config import Config


    app.config.from_object(
        Config
    )



    login_manager.init_app(
        app
    )


    login_manager.login_view = (
        "auth.login"
    )



    from app.controllers import (

        auth_bp,

        home_bp,

        account_bp,

        exercise_bp,

        routine_bp,

        train_bp

    )



    app.register_blueprint(
        auth_bp
    )


    app.register_blueprint(
        home_bp
    )


    app.register_blueprint(
        account_bp
    )


    app.register_blueprint(
        exercise_bp
    )


    app.register_blueprint(
        routine_bp
    )


    app.register_blueprint(
        train_bp
    )



    return app
