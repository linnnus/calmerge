"""
This module defines a blueprint which handles all frontend interactions. See
also `domain.py` which handles most of the business logic.
"""

from flask import Blueprint, request
from flask.templating import render_template
from flask.helpers import flash, redirect, url_for
from . import domain

bp = Blueprint("frontend", __name__)

@bp.get("/")
@bp.get("/dashboard.html")
def dashboard():
    feeds = domain.get_feeds()
    return render_template("dashboard.html", feeds=feeds)

@bp.route("/create_feed.html", methods=("GET", "POST"))
def create_feed():
    if request.method == "GET":
        return render_template("create_feed.html")
    else:
        assert request.method == "POST"
        name = request.form["name"]

        try:
            feed = domain.create_feed(name)
        except domain.DomainError as e:
            flash(str(e))
            return render_template("create_feed.html")

        return redirect(url_for("frontend.manage_feed", feed_id=feed.id))

@bp.get("/feeds/<int:feed_id>/manage.html")
def manage_feed(feed_id: domain.FeedId): # TODO: Handle DomainError here!
    feed = domain.get_feed_by_id(feed_id)
    return render_template("manage.html", feed=feed)

@bp.post("/feeds/<int:feed_id>/sources")
def add_source(feed_id: domain.FeedId):
    name = request.form["name"]
    url = request.form["url"]
    update_frequency = int(request.form["update_frequency"])

    try:
        domain.create_source(name, url, update_frequency, owning_feed_id=feed_id)
    except domain.DomainError as e:
        # This time we don't use PRG as failing requests are idempotent.
        flash(str(e))
        # FIXME: Kind of stupid to do a DB fetch just for an error message.
        return manage_feed(feed_id)

    # Post/Redirect/Get pattern: https://en.wikipedia.org/wiki/Post/Redirect/Get
    # FIXME: This adds an entry in the history, which we don't want. Fix with JS.
    return redirect(location=url_for("frontend.manage_feed", feed_id=feed_id),
                    code=303)
