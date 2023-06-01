import datetime
import enum
import random
from typing import Union

from passlib.hash import pbkdf2_sha256
from flask_sqlalchemy import SQLAlchemy

from .config import gconfig

db = SQLAlchemy()


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(255))
    password = db.Column(db.String(87))  # pbkdf2_sha256
    containers = db.relationship('Container',
                                 lazy=True,
                                 backref='user',
                                 cascade='all,delete')

    def __init__(self, username: str, plain_password: str):
        self.username = username
        self.password = pbkdf2_sha256.hash(plain_password)

    @classmethod
    def authenticate(cls, username, password) -> Union[int, None]:
        user: User = cls.query.filter_by(username=username).first()
        if user and pbkdf2_sha256.verify(password, user.password):
            return user.id


class ContainerStatus(str, enum.Enum):
    ERROR = 'error'  # when a container is failed to run
    CREATING = 'creating'  # when a container is just created, no internal id set
    RUNNING = 'running'  # when a container has started
    EXITED = 'exited'
    PAUSED = 'paused'


class DockerContainerStatus(str, enum.Enum):
    CREATED = 'created'
    RUNNING = 'running'
    PAUSED = 'paused'
    RESTARTING = 'restarting'
    REMOVING = 'removing'
    EXITED = 'exited'
    DEAD = 'dead'


class Container(db.Model):
    """
    Merepresentasikan container di Docker.  Dari web interface, user HANYA
    bisa: 

    1. Membuat container dengan menspesifikasikan nama, image, dan container
       port (public port akan di-random)
    2. Mengedit nama (hanya nama) suatu container
    3. Menghapus container
    4. Menghentikan dan menjalankan container secara manual (via tombol)
       (dilakukan dengan memanggil task dari celery)
    5. Menghentikan dan menjalankan container secara otomatis (dilakukan dengan
       mengupdate start_hour, start_minute, stop_hour, stop_minute)
    """

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    name = db.Column(db.String(255), nullable=False)
    image = db.Column(db.String(255), nullable=False)
    internal_id = db.Column(db.String(64), nullable=True)

    container_port = db.Column(db.Integer, nullable=False)
    public_port = db.Column(db.Integer, nullable=False)

    scheduled = db.Column(db.Boolean, nullable=False, default=False)
    start_hour = db.Column(db.Integer, nullable=True)
    start_minute = db.Column(db.Integer, nullable=True)
    stop_hour = db.Column(db.Integer, nullable=True)
    stop_minute = db.Column(db.Integer, nullable=True)

    status = db.Column(db.String(255), nullable=False,
                       default=ContainerStatus.CREATING)
    action_logs = db.relationship(
        'ContainerActionLog',
        lazy=True,
        backref='container', cascade='all,delete')

    def __init__(self, user_id, name, image, container_port):
        self.user_id = user_id
        self.name = name
        self.image = image
        self.container_port = container_port
        self.assign_random_public_port()

    def set_schedule(self, start_hour, start_minute, stop_hour, stop_minute):
        self.scheduled = True
        self.start_hour = start_hour
        self.start_minute = start_minute
        self.stop_hour = stop_hour
        self.stop_minute = stop_minute

    def unset_schedule(self):
        self.scheduled = False

    def assign_random_public_port(self):
        allocated_ports = [c.public_port for c in self.query.all()]
        unused_ports = [
            p for p in range(1024, 65536)
            if p not in allocated_ports
        ]
        self.public_port = random.choice(unused_ports)

    def calculate_bills(self):
        action_logs = self.action_logs
        bills = []
        lone_start = None

        for log in action_logs:
            if lone_start is None and log.action == ContainerAction.START:
                lone_start = log
            elif lone_start is not None and log.action == ContainerAction.STOP:
                seconds = (log.timestamp -
                           lone_start.timestamp).total_seconds()
                minutes = seconds // 60
                bills.append({
                    'start': lone_start.timestamp,
                    'stop': log.timestamp,
                    'minutes': minutes,
                    'cost': minutes * gconfig['prices']['container_usage_per_minute'],
                })
                lone_start = None
        return bills

    @property
    def last_action(self):
        return self.action_logs[-1].action


class ContainerAction(str, enum.Enum):
    START = 'start'
    STOP = 'stop'


class ContainerActionLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    container_id = db.Column(db.Integer, db.ForeignKey('container.id'))
    timestamp = db.Column(db.DateTime, nullable=False,
                          default=datetime.datetime.now)
    action = db.Column(db.String(255), nullable=False)

    def __init__(self, container_id: str, action: ContainerAction):
        self.container_id = container_id
        self.action = action
