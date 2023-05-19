import logging

import docker
from celery import shared_task

from dockurr.models import db, Container, ContainerStatus

client = docker.from_env()
logger = logging.getLogger(__name__)


@shared_task
def start_container(id_):
    container = Container.query.filter_by(id=id_).first()
    logger.info('Starting container id=%d', id_)

    if not container:
        raise ValueError(f'Container id={id_} not found')
    elif not container.internal_id:
        try:
            docker_container = client.containers.run(
                container.image,
                ports={f'{container.container_port}/tcp': container.public_port},
                detach=True)
        except Exception as e:
            logger.error('Failed to start container %s, exc: %r', id_, e)
            raise e
        container.internal_id = docker_container.id
    else:
        docker_cont = client.containers.get(container.internal_id)
        docker_cont.start()

    container.status = ContainerStatus.RUNNING
    db.session.commit()
