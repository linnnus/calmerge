import sqlite3
import typing as t
import click
from flask import current_app, g
from flask.app import Flask

def get_db() -> sqlite3.Connection:
    """
    Returns a connection to the database.

    The connection is created, if one does not already exist.
    """
    if "db" not in g:
        db = sqlite3.connect(current_app.config["DATABASE"],
                             detect_types=sqlite3.PARSE_DECLTYPES)
        db.row_factory = sqlite3.Row

        # In debugging mode it is often useful to see which queries are executed.
        if current_app.debug or current_app.testing:
            db.set_trace_callback(print)

        # Make sure to validate the foreign key constraints and DELETE propagation we made in `schema.sql`.
        db.execute("PRAGMA foreign_keys=ON")

        # Cache for future calls to `get_db`.
        g.db = db

    return g.db

def close_db(_: t.Optional[BaseException]=None) -> None:
    """Closes connection to database, if one was opened."""
    db: t.Optional[sqlite3.Connection] = g.pop("db", default=None)
    if db is not None:
        db.close()

@click.command("init-db")
def init_db_command() -> None:
    """Cleans and (re)creates the database."""
    db = get_db()

    with current_app.open_resource("schema.sql") as f:
        script = f.read().decode("utf-8")

    db.executescript(script)
    db.commit()

    click.echo("Created database beeb boop")

def init_app(app: Flask) -> None:
    """Adds database management stuff to an application object."""
    app.teardown_appcontext(close_db)
    app.cli.add_command(init_db_command)
