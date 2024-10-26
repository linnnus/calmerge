"""
This module wraps all interactions with the Database in a
layer which ensures business logic is followed.

It is a bit of an experiment in separating business logic
from presentational logic. We may just merge it back into
`frontend.py` in the future.

This module _does_ interact with the DB as some domain logic
is contained withing the foreign key logic of the SQLite schema.
"""

import typing as t
from .db import get_db

FeedId = t.NewType('FeedId', int)
SourceId = t.NewType('SourceId', int)

class DomainError(Exception):
    """
    Represents errors on the level of business-logic,
    e.g. creating a feed with an empty name.
    """

def create_feed(name: str) -> FeedId:
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
            RETURNING id;
        """, [name])
        row = curs.fetchone()
        db.commit()
    except db.IntegrityError as e:
        raise DomainError("???") from e

    return row["id"]

def get_feed_name(feed_id: FeedId) -> str:
    """
    Returns the name of the feed with id `feed_id`, throwing `DomainError` when
    no such feed exists.
    """
    db = get_db()
    curs = db.execute("SELECT name FROM feed WHERE id = ?;", [feed_id])
    row = curs.fetchone()
    if row == None:
        raise DomainError(f"No feed with id {feed_id} exists")
    return row["name"]
