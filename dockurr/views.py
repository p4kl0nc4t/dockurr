from flask import (Blueprint, abort, redirect, g,
                   render_template, request, session, url_for, flash)

from dockurr.models import User, Container, db
from dockurr.tasks import containerman

bp = Blueprint('views', __name__)


@bp.before_request
def check_auth():
    if request.endpoint != 'views.auth' and not session.get('uid'):
        return redirect(url_for('views.auth'))
    g.uid = session.get('uid')
    g.username = session.get('username')


@bp.route('/')
def home():
    return redirect(url_for('views.dashboard'))


@bp.route('/logout')
def logout():
    session.pop('uid')
    session.pop('username')
    flash('Bye-bye', 'info')
    return redirect(url_for('views.auth'))


@bp.route('/auth', methods=['GET', 'POST'])
def auth():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        if not username or not password:
            abort(400)

        if not User.query.filter_by(username=username).first():
            user = User(username, password)
            db.session.add(user)
            db.session.commit()
            flash('New user created', 'info')
        else:
            uid = User.authenticate(username, password)
            if uid is not None:
                session['uid'] = uid
                session['username'] = username
                return redirect(url_for('views.home'))
            flash('Invalid username or password', 'danger')
    return render_template('auth.html')


@bp.route('/dashboard')
def dashboard():
    containers = Container.query.filter_by(user_id=g.uid).all()
    return render_template('dashboard.html', containers=containers)


@bp.route('/create-container', methods=['GET', 'POST'])
def create_container():
    if request.method == 'POST':
        name = request.form.get('name')
        image = request.form.get('image')
        container_port = request.form.get('container_port')
        if not (name and image and container_port):
            abort(400)
        container = Container(g.uid, name, image, container_port)
        db.session.add(container)
        db.session.commit()
        containerman.start_container.delay(container.id)
        flash(f'Container {name} created successfully, will start right away',
              'success')
        return redirect(url_for('views.dashboard'))
    return render_template('create_container.html')


@bp.route('/start-container/<int:id>')
def start_container(id):
    containerman.start_container(id)
    return redirect(url_for('views.dashboard'))


@bp.route('/stop-container/<int:id>')
def stop_container(id):
    containerman.stop_container(id)
    return redirect(url_for('views.dashboard'))

@bp.route('/delete-container/<int:id>')
def delete_container(id):
    containerman.delete_container(id)
    flash(f'Container {id} deleted', 'info')
    return redirect(url_for('views.dashboard'))


@bp.route('/schedule-container/<int:id>')
def schedule_container(id):
    container = Container.query.filter_by(id=id).first_or_404()
    return render_template('schedule_container.html', container=container)

