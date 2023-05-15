from flask import Flask
from .views import bp as views_bp


def create_app():
    app = Flask(__name__)
    app.register_blueprint(views_bp)
    return app
