from flask import (Blueprint, abort, redirect, g,
                   render_template, request, session, url_for, flash)

from dockurr.models import User, Container, ContainerStatus, db
from dockurr.tasks import container_controller

bp = Blueprint('views', __name__)


@bp.before_request
def check_auth():
    on_auth_page = request.endpoint == 'views.auth'
    logged_in = session.get('uid') is not None
    if not on_auth_page and not logged_in:
        return redirect(url_for('views.auth'))
    elif on_auth_page and logged_in:
        return redirect(url_for('views.dashboard'))
    g.uid = session.get('uid')
    g.username = session.get('username')
    g.CS = ContainerStatus


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
        container_controller.start_container.delay(
            container.id)  # type: ignore
        flash(f'Container {name} created successfully, will start right away',
              'success')
        return redirect(url_for('views.dashboard'))
    return render_template('create_container.html')


@bp.route('/start-container/<int:id>')
def start_container(id):
    Container.query.filter_by(id=id, user_id=g.uid).first_or_404()
    flash(f'Container {id} will be started', 'info')
    container_controller.start_container.delay(id)  # type: ignore
    return redirect(url_for('views.dashboard'))


@bp.route('/stop-container/<int:id>')
def stop_container(id):
    Container.query.filter_by(id=id, user_id=g.uid).first_or_404()
    flash(f'Container {id} will be stopped', 'info')
    container_controller.stop_container.delay(id)  # type: ignore
    return redirect(url_for('views.dashboard'))


@bp.route('/delete-container/<int:id>')
def delete_container(id):
    Container.query.filter_by(id=id, user_id=g.uid).first_or_404()
    container_controller.delete_container.delay(id)  # type: ignore
    flash(f'Container {id} will be deleted', 'info')
    return redirect(url_for('views.dashboard'))


@bp.route('/schedule-container/<int:id>', methods=['GET', 'POST'])
def schedule_container(id):
    container = Container.query.filter_by(id=id,
                                          user_id=g.uid).first_or_404()
    if request.method == 'POST':
        scheduled = request.form.get('scheduled')
        start_hour = request.form.get('start_hour')
        start_minute = request.form.get('start_minute')
        stop_hour = request.form.get('stop_hour')
        stop_minute = request.form.get('stop_minute')

        if scheduled and start_hour and start_minute \
                and stop_hour and stop_minute:
            container.set_schedule(start_hour, start_minute,
                                   stop_hour, stop_minute)
            flash(f'Container {container.name} scheduled', 'success')
        else:
            container.unset_schedule()
            flash(f'Container {container.name} unscheduled', 'info')
        db.session.commit()
    return render_template('schedule_container.html', container=container)


@bp.route('/container-billing/<int:id>')
def container_billing(id):
    container = Container.query.filter_by(user_id=g.uid, id=id).first_or_404()
    return render_template('container_billing.html', container=container)


@bp.route('/user-billing')
def user_billing():
    user = User.query.filter_by(id=g.uid).first_or_404()
    return render_template('user_billing.html', user=user)
