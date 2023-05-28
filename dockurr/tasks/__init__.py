import redis
from dockurr.config import gconfig
from celery.schedules import crontab

config = {
    # overriden by config.toml
    'include': ['dockurr.tasks.containerman',
                'dockurr.tasks.container_scheduler'],
    'beat_schedule': {
        'container-reaper': {
            'task': 'dockurr.tasks.containerman.container_reaper',
            'schedule': gconfig['celery']['intervals']['container_reaper'],
        },
        'update-beat-schedule': {
            'task': 'dockurr.tasks.container_scheduler.update_beat_schedule',
            'schedule': gconfig['celery']['intervals']['update_beat_schedule']
        }

    }
}

redbeat_rc = redis.Redis.from_url(gconfig['celery']['redbeat_redis_url'])
