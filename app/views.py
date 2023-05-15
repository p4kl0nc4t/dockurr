from flask import Blueprint, render_template

bp = Blueprint('views', __name__)


@bp.route('/')
def home():
    return render_template('index.html')
