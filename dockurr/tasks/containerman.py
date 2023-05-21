import logging

import docker
import docker.errors
import docker.models
from celery import shared_task

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
            logger.error('Failed to start container %s, exc: %r', id_, e)
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


def stop_container(id_):
    container = Container.query.filter_by(id=id_).first()
    logger.info('Stopping container id=%d', id_)

    if not container:
        raise ValueError(f'Container id={id_} not found')
    elif not container.internal_id \
            or not docker_container_exists(container.internal_id):
        # TODO
        pass

    if ContainerStatus(container.status) not in [
            ContainerStatus.RUNNING,
            ContainerStatus.PAUSED]:
        raise ValueError(f'Container {id_} is not stoppable')
    else:
        docker_container = client.containers.get(container.internal_id)
        docker_container.stop()

    container.status = ContainerStatus.EXITED
    db.session.add(ContainerActionLog(container.id, ContainerAction.STOP))
    db.session.commit()


@shared_task(ignore_result=True)
def container_reaper():
    """
    Remove a container from database, if they don't have internal ID and their
    status is ContainerStatus.ERROR
    """
    return


@shared_task(ignore_result=True)
def container_syncronizer():
    """
    Syncronize container status on database with the real Docker container status
    """
    return
