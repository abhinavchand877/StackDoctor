import os
from celery import Celery

def make_celery(app=None):
    """
    Initializes and configures a Celery instance for background scanning and asynchronous queue processing.
    """
    broker = os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/0")
    backend = os.getenv("CELERY_RESULT_BACKEND", "redis://localhost:6379/0")

    celery_instance = Celery(
        "stackdoctor_worker",
        broker=broker,
        backend=backend,
    )

    if app:
        celery_instance.conf.update(app.config)

        class ContextTask(celery_instance.Task):
            def __call__(self, *args, **kwargs):
                with app.app_context():
                    return self.run(*args, **kwargs)

        celery_instance.Task = ContextTask

    return celery_instance
