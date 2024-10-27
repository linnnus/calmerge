"""
This module manages asynchronous background tasks like fetching calendars and
GC'ing the database.
"""

from datetime import datetime
from flask.app import Flask
from celery import Celery, Task, shared_task
import requests
from . import domain

def init_app(flask_app: Flask) -> Celery:
    """Configure celery (task management) application on the given flask application."""

    class FlaskTask(Task):
        """Celery task invoked within application context."""

        def __call__(self, *args: object, **kwargs: object) -> object:
            with flask_app.app_context():
                return self.run(*args, **kwargs)

    celery_app = Celery(flask_app.name, task_cls=FlaskTask)

    # Celery configuration is set the same way as all other configuration.
    celery_app.config_from_object(flask_app.config["CELERY"])

    # As the celery application object isn't easily available (it exists only
    # as an attribute of `flask_app.extensions`), we can't easily call methods
    # on the application object. Instead we make this the default app and use
    # the global variants of those methods.
    celery_app.set_default()

    flask_app.extensions["celery"] = celery_app

    return celery_app

@shared_task()
def initial_fetch_source(source_id: domain.SourceId):
    """Task that performs the initial loading when a new source is added."""

    source = domain.get_source_by_id(source_id)
    content = domain.get_content_by_url(source.url)

    # If there is already a cached version, we are done.
    if content is None:
        return

    now = datetime.now()

    # FIXME: Do these requests safely to prevent DOS, zip-bomb, etc.
    response = requests.get(source.url)

    # FIXME: Maybe actually handle errors
    content_type = response.headers.get("Content-Type")
    assert content_type is not None and content_type.startswith("text/calendar")
    response.raise_for_status()

    domain.update_content_by_id(content.id, last_updated=now, content=response.text)
