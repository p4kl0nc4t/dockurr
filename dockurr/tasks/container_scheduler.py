from redbeat import RedBeatSchedulerEntry
from celery import shared_task, current_app
from celery.schedules import crontab
from celery.utils.log import get_task_logger
from dockurr.models import Container, ContainerActionLog, ContainerAction, ContainerStatus
from dockurr.tasks.containerman import start_container, stop_container
# from dockurr.tasks import redbeat_rc

logger = get_task_logger(__name__)


@shared_task(ignore_result=True)
def update_beat_schedule():
    prefix = 'container:'
    pattern = f'{current_app.conf.redbeat_key_prefix}{prefix}'
    containers = Container.query.filter_by(scheduled=True).all()

    for key in redbeat_rc.scan_iter(pattern):
        redbeat_rc.delete(key)

    for container in containers:
        start_interval = crontab(
            hour=container.start_hour, minute=container.start_minute)
        stop_interval = crontab(hour=container.stop_hour,
                                minute=container.stop_minute)
        start_entry = RedBeatSchedulerEntry(f'{pattern}{container.id}:start',
                                            'dockurr.tasks.containerman.start_container',
                                            start_interval,
                                            args=[container.id],
                                            app=current_app)
        stop_entry = RedBeatSchedulerEntry(f'{pattern}{container.id}:stop',
                                           'dockurr.tasks.containerman.stop_container',
                                           stop_interval,
                                           args=[container.id],
                                           app=current_app)
        start_entry.save()
        stop_entry.save()
    logger.info('Updated beat schedule for container scheduler')
