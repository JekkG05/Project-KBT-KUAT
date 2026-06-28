from flask import Flask
from flask_login import LoginManager

from app.config import supabase
from app.models.user import User


login_manager = LoginManager()


login_manager.login_view = "auth.login"



@login_manager.user_loader
def load_user(user_id):

    result = (
        supabase
        .table("users")
        .select("*")
        .eq(
            "id",
            int(user_id)
        )
        .single()
        .execute()
    )


    if result.data:

        return User(result.data)


    return None





def create_app():

    app = Flask(
        __name__,
        template_folder="templates",
        static_folder="static"
    )


    app.config.from_object(
        "app.config.Config"
    )


    login_manager.init_app(app)



    from app.controllers import (

        home_bp,

        auth_bp,

        account_bp,

        exercise_bp,

        routine_bp,

        train_bp

    )



    app.register_blueprint(home_bp)

    app.register_blueprint(auth_bp)

    app.register_blueprint(account_bp)

    app.register_blueprint(exercise_bp)

    app.register_blueprint(routine_bp)

    app.register_blueprint(train_bp)



    return app
