from flask import Flask, register_blueprint
from .views import bp as views_bp


def create_app():
    app = Flask(__name__)
    return app
