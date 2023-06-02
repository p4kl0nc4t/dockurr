from celery import Celery, Task
from flask import Flask

from .config import gconfig
from .tasks import config as celery_config
from .views import bp as views_bp
from .models import db


def celery_init_app(app: Flask) -> Celery:
    class FlaskTask(Task):
        def __call__(self, *args: object, **kwargs: object) -> object:
            with app.app_context():
                return self.run(*args, **kwargs)

    celery_app = Celery(app.name, task_cls=FlaskTask)
    # set from internal celery config
    celery_app.conf.update(celery_config)
    # set from gconfig
    celery_app.config_from_object(gconfig['celery'])
    celery_app.set_default()
    app.extensions['celery'] = celery_app
    return celery_app


def create_app():
    app = Flask(__name__)
    app.config.update({
        'SQLALCHEMY_DATABASE_URI': gconfig['database']['uri'],
        'SECRET_KEY': gconfig['flask']['secret_key'],
        'DOCKURR_PRICES': gconfig['prices']
    })

    app.config.from_prefixed_env()
    app.register_blueprint(views_bp)

    db.init_app(app)
    celery_init_app(app)
    return app
