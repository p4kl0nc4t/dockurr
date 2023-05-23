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
        }
    }
}
