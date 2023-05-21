from celery import shared_task
from celery.schedules import crontab
from celery.utils.log import get_task_logger

from dockurr.models import Container, ContainerActionLog, ContainerAction, ContainerStatus
from dockurr.tasks.containerman import start_container, stop_container

logger = get_task_logger(__name__)


@shared_task(ignore_result=True)
def update_beat_schedule():
    containers = Container.query.filter_by(scheduled=True).all()
    
