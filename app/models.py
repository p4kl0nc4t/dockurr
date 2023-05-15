import datetime

from flask_sqlalchemy import SQLAlchemy
from passlib.hash import pbkdf2_sha256

db = SQLAlchemy()


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(255))
    password = db.Column(db.String(87))  # pbkdf2_sha256

    def __init__(self, username: str, plain_password: str):
        self.username = username
        self.password = pbkdf2_sha256.hash(plain_password)

    @classmethod
    def authenticate(cls, username, password) -> bool:
        user: User = cls.query.filter_by(username=username).first()
        if not user:
            return False
        return pbkdf2_sha256.verify(user.password, password)


class BillingCharge(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, nullable=False,
                          default=datetime.datetime.now)
    amount = db.Column(db.Float, nullable=False)
    # for the sake of simplicity
    description = db.Column(db.String(255), nullable=False)

    def __init__(self, amount: float, item: str):
        self.amount = amount
        self.item = item


class Container(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    docker_id = db.Column(db.String(255), nullable=False)
    image_id = db.Column(db.String(255), nullable=True)
    status = db.Column(db.Integer, nullable=False, default=0)
