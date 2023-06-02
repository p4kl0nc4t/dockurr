from celery import current_app, shared_task
from celery.schedules import crontab
from celery.utils.log import get_task_logger
from redbeat import RedBeatSchedulerEntry
from redbeat.schedulers import get_redis

from dockurr.models import Container

logger = get_task_logger(__name__)
rc = get_redis()


def _create_and_update_entry(prefix, key, task, args, schedule):
    new_entry = RedBeatSchedulerEntry(
        key, task, schedule, args=args, app=current_app)
    redis_key = f'{prefix}{key}'

    if rc.exists(redis_key):
        entry = RedBeatSchedulerEntry.from_key(redis_key, app=current_app)
        if entry.schedule == new_entry.schedule:
            logger.debug(f'Not updating {redis_key}')
            return
        logger.debug(f'Schedule change detected, updating {redis_key}')
        entry.update(new_entry)
    else:
        logger.debug(f'Creating {redis_key} because it does not exist')
        entry = new_entry

    logger.debug(f'Saving {key} to redis')
    entry.save()


@shared_task(ignore_result=True)
def update_beat_schedule():
    # TODO: grab these settings from config.toml
    redbeat_prefix = 'redbeat:'
    container_prefix = 'container:'
    pattern = f'{redbeat_prefix}{container_prefix}*'  # redbeat:container:*
    containers = Container.query.filter_by(scheduled=True).all()
    scheduled_container_ids = [container.id for container in containers]

    # remove keys from redis that are no longer scheduled
    with rc.pipeline() as pipe:
        for key in rc.scan_iter(pattern):
            container_id = int(key.rsplit(':', 2)[1])
            if container_id not in scheduled_container_ids:
                rc.delete(key)
                logger.debug(f'Deleted {key} (no longer scheduled)')
        pipe.execute()

    # add/update schedule entries
    for container in containers:
        container_key = f'{container_prefix}{container.id}'  # container:1
        start_entry_key = f'{container_key}:start'  # container:1:start
        stop_entry_key = f'{container_key}:stop'

        start_interval = crontab(hour=container.start_hour,
                                 minute=container.start_minute)
        stop_interval = crontab(hour=container.stop_hour,
                                minute=container.stop_minute)

        _create_and_update_entry(redbeat_prefix, start_entry_key,
                                 'dockurr.tasks.container_controller.start_container',
                                 (container.id,), start_interval)
        _create_and_update_entry(redbeat_prefix, stop_entry_key,
                                 'dockurr.tasks.container_controller.stop_container',
                                 (container.id,), stop_interval)

    logger.info('Updated beat schedule')
