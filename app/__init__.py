from flask import Flask

def create_app():

    app = Flask(
        __name__,
        template_folder="templates",
        static_folder="static"
    )

    # config
    app.config.from_object("app.config.Config")


from app.controllers.main_controller import routes
app.register_blueprint(routes)


    return app
