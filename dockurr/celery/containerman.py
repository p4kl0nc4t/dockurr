from dockurr.celery import app


@app.task
def add(x, y) -> int:
    return x + y
