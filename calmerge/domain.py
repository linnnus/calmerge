"""
This module wraps all interactions with the Database in a
layer which ensures business logic is followed.

It is a bit of an experiment in separating business logic
from presentational logic. We may just merge it back into
`frontend.py` in the future.

This module _does_ interact with the DB as some domain logic
is contained withing the foreign key logic of the SQLite schema.
"""

import sqlite3
import typing as t
from .db import get_db
from datetime import datetime
from dataclasses import dataclass

FeedId = t.NewType("FeedId", int)
"""Newtype representing `feed.id` column in database"""

SourceId = t.NewType("SourceId", int)
"""Newtype representing `source.id` column in database"""

@dataclass
class PartialFeed:
    """
    Represents a static snapshot of a feed object in the `feed` table in the database.

    Does not include list of sources, as that would require another database query.
    """

    id: FeedId
    name: str
    created: datetime

@dataclass
class Feed(PartialFeed):
    """Same as PartialFeed, except includes sources."""

    sources: list['Source']

@dataclass
class Source:
    """Represents a static snapshot of a source in the `source` table."""

    id: SourceId
    name: str
    url: str
    update_frequency: int
    feed_id: FeedId

def partial_feed_row_factory(cursor: sqlite3.Cursor, row: sqlite3.Row):
    assert cursor.description[0][0] == "id"
    assert cursor.description[1][0] == "name"
    assert cursor.description[2][0] == "created"
    return PartialFeed(id=row[0],
                       name=row[1],
                       created=row[2])

def source_row_factory(cursor: sqlite3.Cursor, row: sqlite3.Row):
    assert cursor.description[0][0] == "id"
    assert cursor.description[1][0] == "name"
    assert cursor.description[2][0] == "url"
    assert cursor.description[3][0] == "update_frequency"
    assert cursor.description[4][0] == "feed_id"
    return Source(id=row[0], name=row[1], url=row[2], update_frequency=row[3], feed_id=FeedId(row[4]))

class DomainError(Exception):
    """
    Represents errors on the level of business-logic,
    e.g. creating a feed with an empty name.
    """

def create_feed(name: str) -> PartialFeed:
    """
    Creates a new entry in the `feed` database, throwing `DomainError`
    on invalid input.
    """

    if name.strip() == "":
        raise DomainError("The 'name' field must be a non-empty string")

    db = get_db()
    try:
        curs = db.execute("""
            INSERT INTO feed(name, created)
            VALUES (?, datetime('now'))
            RETURNING id, name, created;
        """, [name])
        curs.row_factory = partial_feed_row_factory
        feed = curs.fetchone()
        db.commit()
    except db.IntegrityError as e:
        raise DomainError("Invalid operation") from e

    return feed

def get_feed_by_id(feed_id: FeedId) -> Feed:
    db = get_db()

    # Fetch feed
    curs = db.execute("SELECT id, name, created FROM feed WHERE id = ?;", [feed_id])
    curs.row_factory = partial_feed_row_factory
    feed: t.Optional[PartialFeed] = curs.fetchone()
    if feed is None:
        raise DomainError(f"No feed with id {feed_id} exists")

    # Fetch matching sources
    curs = db.execute("""
        SELECT id, name, url, update_frequency, feed_id FROM source WHERE feed_id = ?;
    """, [feed_id])
    curs.row_factory = source_row_factory
    sources = curs.fetchall()

    # Now we have all the information for a full feed representation
    return Feed(id=feed.id, name=feed.name, created=feed.created, sources=sources)

def create_source(name: str, url: str, update_frequency: int, owning_feed_id: FeedId) -> Source:
    """Adds a new source to the database."""

    MIN_UPDATE_FREQ = 60
    MAX_UPDATE_FREQ = 60 * 60 * 31
    if not MIN_UPDATE_FREQ <= update_frequency <= MAX_UPDATE_FREQ:
        raise DomainError(f"Update frequency of {update_frequency} is out of range. It should be between 60 (1 minute) and ")

    db = get_db()
    try:
        with db:
            db.execute("""
               INSERT INTO url_to_content (url, last_updated, content) VALUES (?, NULL, NULL);
            """, [url])

            curs = db.execute("""
                INSERT INTO source(name, url, update_frequency, feed_id)
                VALUES (?, ?, ?, ?)
                RETURNING id, name, url, update_frequency, feed_id;
            """, [name, url, update_frequency, owning_feed_id])
            curs.row_factory = source_row_factory
            source = curs.fetchone()
    except db.IntegrityError as e:
        if e.sqlite_errorcode == sqlite3.SQLITE_CONSTRAINT_UNIQUE and "url_to_content.url" in str(e):
            raise DomainError("URL already in use as source for this feed") from e
        else:
            # Some other integrity error which is an actual bug.
            raise

    return source

def get_feeds() -> list[PartialFeed]:
    db = get_db()
    curs = db.execute("""SELECT id, name, created FROM feed;""")
    curs.row_factory = partial_feed_row_factory
    return curs.fetchall()
