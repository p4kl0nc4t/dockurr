from celery import shared_task
from celery.utils.log import get_task_logger

from dockurr.models import Container, ContainerStatus, db

logger = get_task_logger(__name__)


@shared_task(ignore_result=True)
def reap_containers():
    containers = Container.query.filter_by(internal_id=None).all()
    removed_count = 0
    for container in containers:
        if container.status == ContainerStatus.DIRTY:
            logger.warning('Removing container id=%d', container.id)
            logger.warning('Container id=%d is in error state', container.id)
            removed_count += 1
            db.session.delete(container)
    db.session.commit()
    logger.info('Removed %d containers', removed_count)
