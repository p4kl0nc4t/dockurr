from flask import Flask
from flask_sqlalchemy import SQLAlchemy

from .config import read_config
from .views import bp as views_bp

db = SQLAlchemy()
gconfig = read_config()


def create_app():
    app = Flask(__name__)
    app.config.update({
        'SQLALCHEMY_DATABASE_URI': gconfig['database']['uri']
    })

    app.config.from_prefixed_env()
    app.register_blueprint(views_bp)

    db.init_app(app)
    return app
