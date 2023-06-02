from typing import Optional
import docker
import docker.errors

client = docker.from_env()


def docker_container_exists(docker_container_id: str) -> bool:
    try:
        client.containers.get(docker_container_id)
    except docker.errors.NotFound:
        return False
    return True


def get_docker_container_status(docker_container_id: str) -> Optional[str]:
    if not docker_container_exists(docker_container_id):
        return
    container = client.containers.get(docker_container_id)
    return container.status  # type: ignore
