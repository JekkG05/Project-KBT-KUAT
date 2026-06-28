from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager

from app.config import Config


db = SQLAlchemy()

login_manager = LoginManager()


@login_manager.user_loader
def load_user(user_id):

    from app.config import supabase

    result = (
        supabase
        .table("users")
        .select("*")
        .eq("id", user_id)
        .single()
        .execute()
    )


    if result.data:

        from app.models.user import User

        return User(result.data)


    return None



def create_app():

    app = Flask(__name__)


    app.config.from_object(Config)



    db.init_app(app)


    login_manager.init_app(app)

    login_manager.login_view = "auth.login"



    from app.controllers import (
        auth_bp,
        home_bp
    )


    app.register_blueprint(auth_bp)

    app.register_blueprint(home_bp)



    return app
