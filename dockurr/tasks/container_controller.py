from celery import shared_task
from celery.utils.log import get_task_logger

from dockurr.docker_utils import client
from dockurr.models import Container, ContainerAction, ContainerActionLog, db
from dockurr.models import ContainerStatus

logger = get_task_logger(__name__)


@shared_task(ignore_result=True)
def start_container(id_):
    container = Container.query.filter_by(id=id_).first()
    if not container:
        raise ValueError(f'Container id={id_} not found')
    logger.info('Starting container id=%d', id_)

    # sync with docker, create container if not exists
    if container.status == ContainerStatus.NOT_FOUND:
        try:
            docker_container = client.containers.run(
                container.image,
                ports={f'{container.container_port}/tcp': container.public_port},
                detach=True)
        except Exception as e:
            logger.error('Failed to start container %s', id_, exc_info=True)
            # bye-bye, container will be reaped
            container.status = ContainerStatus.INTERNAL_ERROR
            db.session.commit()
            raise e
        container.internal_id = docker_container.id  # type: ignore
    elif not container.status.runnable:
        logger.error('Starting a non-runnable container %s', id_)
        raise ValueError(f'Container {id_} is not runnable')
    else:
        docker_container = client.containers.get(container.internal_id)
        docker_container.start()  # type: ignore

    db.session.add(ContainerActionLog(container.id, ContainerAction.START))
    db.session.commit()
    logger.info('Container id=%d started', id_)


@shared_task(ignore_result=True)
def stop_container(id_):
    container = Container.query.filter_by(id=id_).first()
    if not container:
        raise ValueError(f'Container id={id_} not found')
    logger.info('Stopping container id=%d', id_)

    if not container.status.stoppable:
        msg = f'Container {id_} is not stoppable'
        logger.critical(msg)
        raise ValueError(msg)

    docker_container = client.containers.get(container.internal_id)
    docker_container.stop()  # type: ignore
    db.session.add(ContainerActionLog(container.id, ContainerAction.STOP))
    db.session.commit()
    logger.info('Container id=%d stopped', id_)


@shared_task(ignore_result=True)
def delete_container(id_):
    container = Container.query.filter_by(id=id_).first()
    if not container:
        raise ValueError(f'Container id={id_} not found')
    logger.info('Deleting container id=%d', id_)

    if container.status != ContainerStatus.NOT_FOUND:
        docker_container = client.containers.get(container.internal_id)
        docker_container.remove(force=True)  # type: ignore

    db.session.delete(container)
    db.session.commit()
    logger.info('Container id=%d deleted', id_)
