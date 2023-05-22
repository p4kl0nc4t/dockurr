import logging

import docker
import docker.errors
import docker.models

from celery import shared_task
from celery.utils.log import get_task_logger

from dockurr.models import (
    db,
    Container, ContainerStatus,
    ContainerActionLog, ContainerAction)

client = docker.from_env()
logger = logging.getLogger(__name__)


def docker_container_exists(docker_container_id: str) -> bool:
    try:
        client.containers.get(docker_container_id)
    except docker.errors.NotFound:
        return False
    return True


@shared_task(ignore_result=True)
def start_container(id_):
    container = Container.query.filter_by(id=id_).first()
    logger.info('Starting container id=%d', id_)

    if not container:
        raise ValueError(f'Container id={id_} not found')

    # sync with docker, create container if not exists
    if not container.internal_id or \
            not docker_container_exists(container.internal_id):
        try:
            docker_container = client.containers.run(
                container.image,
                ports={f'{container.container_port}/tcp': container.public_port},
                detach=True)
        except Exception as e:
            logger.error('Failed to start container %s', id_, exc_info=True)
            # bye-bye, container will be reaped
            container.status = ContainerStatus.ERROR
            db.session.commit()
            raise e
        container.internal_id = docker_container.id
    else:
        docker_container = client.containers.get(container.internal_id)
        docker_container.start()

    container.status = ContainerStatus.RUNNING
    db.session.add(ContainerActionLog(container.id, ContainerAction.START))
    db.session.commit()
    logger.info('Container id=%d started', id_)


@shared_task(ignore_result=True)
def stop_container(id_):
    container = Container.query.filter_by(id=id_).first()
    logger.info('Stopping container id=%d', id_)

    if not container:
        raise ValueError(f'Container id={id_} not found')
    elif not container.internal_id \
            or not docker_container_exists(container.internal_id):
        msg = f'Container {id_} status is not in sync'
        logger.critical(msg)
        raise ValueError(msg)

    if ContainerStatus(container.status) not in [
            ContainerStatus.RUNNING,
            ContainerStatus.PAUSED]:
        logger.warning('Stopping a non-running container %s', id_)
        raise ValueError(f'Container {id_} is not stoppable')
    else:
        docker_container = client.containers.get(container.internal_id)
        docker_container.stop()

    container.status = ContainerStatus.EXITED
    db.session.add(ContainerActionLog(container.id, ContainerAction.STOP))
    db.session.commit()
    logger.info('Container id=%d stopped', id_)


@shared_task(ignore_result=True)
def delete_container(id_):
    container = Container.query.filter_by(id=id_).first()
    logger.info('Deleting container id=%d', id_)

    if not container:
        raise ValueError(f'Container id={id_} not found')

    if container.internal_id and docker_container_exists(container.internal_id):
        docker_container = client.containers.get(container.internal_id)
        docker_container.remove(force=True)

    db.session.delete(container)
    db.session.commit()
    logger.info('Container id=%d deleted', id_)


@shared_task(ignore_result=True)
def container_reaper():
    """
    Remove a container from database, if they don't have internal ID and their
    status is ContainerStatus.ERROR
    """
    containers = Container.query.filter_by(status=ContainerStatus.ERROR).all()
    for container in containers:
        logger.warning('Removing container id=%d', container.id)
        if not container.internal_id:
            db.session.delete(container)
    db.session.commit()
    logger.info('Removed %d containers', len(containers))


@shared_task(ignore_result=True)
def container_syncronizer():
    """
    Syncronize container status on database with the real Docker container status
    """
    containers = Container.query.filter(
        Container.internal_id is not None).all()
    for container in containers:
        pass
