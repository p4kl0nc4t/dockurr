from dockurr import create_app
from dockurr.models import db

app = create_app()


@app.cli.command()
def createdb():
    db.create_all()
