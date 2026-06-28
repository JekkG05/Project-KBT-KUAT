from flask import Flask
from flask_login import LoginManager
from flask_sqlalchemy import SQLAlchemy


db = SQLAlchemy()

login_manager = LoginManager()



def create_app():

    app = Flask(
        __name__,
        template_folder="templates",
        static_folder="static"
    )


    app.config.from_object(
        "app.config.Config"
    )


    db.init_app(app)


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
