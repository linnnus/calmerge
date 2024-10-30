"""
This module manages asynchronous background tasks like fetching calendars and
GC'ing the database.
"""

from calmerge.db import get_db
from . import domain
from celery import Celery, Task, shared_task
from datetime import datetime
from flask.app import Flask
from icalendar import Calendar
from mergecal import merge_calendars
import requests
import typing as t

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

    if content is not None:
        now = datetime.now()
        new_text = fetch_source(source.url)
        domain.update_content_by_id(content.id, last_updated=now, content=new_text)

    # Now that we have the source for the new source, we can finally compute the new merged calendar feed.
    combine_feed.delay(source.feed_id)

def fetch_source(url: str) -> str:
    # FIXME: Do these requests safely to prevent DOS, zip-bomb, etc.
    response = requests.get(url)

    response.raise_for_status()

    # FIXME: Maybe actually handle errors
    content_type = response.headers.get("Content-Type")
    assert content_type is not None and content_type.startswith("text/calendar")

    return response.text

@shared_task
def combine_all_feeds():
    for feed in domain.get_feeds():
        combine_feed.delay(feed.id)

@shared_task
def combine_feed(feed_id: domain.FeedId):
    feed = domain.get_feed_by_id(feed_id)

    contents = [domain.get_content_by_url(s.url) for s in feed.sources]
    # FIXME: A single improperly formatted ICS file shouldn't bring us down.
    calendars = [Calendar.from_ical(c.content) for c in contents if c.content is not None]
    merged_ics = merge_calendars(calendars).to_ical()

    db = get_db()
    db.execute("""
        UPDATE feed
           SET merged_ics = ?
         WHERE id = ?;
    """, [merged_ics, feed.id])
    db.commit()
