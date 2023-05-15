from celery import Celery
from dockurr import gconfig


app = Celery('dockurr.celery',
             broker=gconfig['celery']['broker'],
             include=['dockurr.celery.containerman'])
