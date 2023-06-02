from dockurr.config import gconfig

config = {
    # overriden by config.toml
    'include': ['dockurr.tasks.container_controller',
                'dockurr.tasks.container_reaper',
                'dockurr.tasks.container_scheduler'],

    'beat_sync_every': 1,
    'redbeat_lock_timeout': 30,
    'beat_max_loop_interval': 5,

    'beat_schedule': {
        'container-reaper': {
            'task': 'dockurr.tasks.container_reaper.reap_containers',
            'schedule': gconfig['celery']['intervals']['container_reaper'],
            'options': {
                'expires': 15,
            }
        },
        'update-beat-schedule': {
            'task': 'dockurr.tasks.container_scheduler.update_beat_schedule',
            'schedule': gconfig['celery']['intervals']['update_beat_schedule'],
            'options': {
                'expires': 15,
            }
        }

    }
}
