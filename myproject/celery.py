import os
from celery import Celery

# Set the default Django settings module
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'myproject.settings')

# Create the Celery app
app = Celery('myproject')

# Load task modules from all registered Django app configs.
app.config_from_object('django.conf:settings', namespace='CELERY')

# Configure Celery Beat schedule
app.conf.beat_schedule = {
    'check-disaster-predictions': {
        'task': 'users.tasks.check_disaster_predictions',
        'schedule': 900.0,  # 15 minutes in seconds
        'options': {
            'expires': 890.0,  # Slightly less than the schedule interval to avoid overlapping
            'retry': False,    # Don't auto-retry on failure
        }
    },
}

# Additional Celery configurations
app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    broker_connection_retry_on_startup=True,
    worker_prefetch_multiplier=1,  # Reduce prefetching for more stable worker behavior
    task_acks_late=True,  # Acknowledge tasks after they are executed, not before
    task_reject_on_worker_lost=True,  # Reject tasks if worker is disconnected
    task_remote_tracebacks=True,  # More detailed remote tracebacks
)

# Auto-discover tasks in all installed apps
app.autodiscover_tasks() 