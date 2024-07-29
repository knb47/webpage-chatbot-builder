from __future__ import absolute_import, unicode_literals
import os
from celery import Celery
import logging

# Set the default Django settings module for the 'celery' program.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')

app = Celery('backend')

# Using a string here means the worker doesn't have to serialize
# the configuration object to child processes.
# - namespace='CELERY' means all celery-related configuration keys
#   should have a `CELERY_` prefix.
app.config_from_object('django.conf:settings', namespace='CELERY')

# Additional configuration for error handling and retries
app.conf.update(
    broker_connection_retry_on_startup=True,
    broker_connection_max_retries=10,
    broker_connection_retry=True,
    broker_connection_retry_delay=5,
)

# Load task modules from all registered Django app configs.
app.autodiscover_tasks()

# Set up logging for Celery
logger = logging.getLogger(__name__)
handler = logging.StreamHandler()
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)
logger.setLevel(logging.DEBUG)


@app.task(bind=True)
def debug_task(self):
    print(f'Request: {self.request!r}')