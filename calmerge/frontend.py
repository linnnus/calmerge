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
    return render_template("dashboard.html")

@bp.route("/create_feed.html", methods=("GET", "POST"))
def create_feed():
    if request.method == "GET":
        return render_template("create_feed.html")
    else:
        assert request.method == "POST"
        name = request.form["name"]

        try:
            feed_id = domain.create_feed(name)
        except domain.DomainError as e:
            flash(str(e))
            return render_template("create_feed.html")

        return redirect(url_for("frontend.manage_feed", id=feed_id))

@bp.get("/manage/<feed_id>.html")
def manage_feed(feed_id: domain.FeedId):
    # TODO: Handle DomainError here!!
    feed_name = domain.get_feed_name(feed_id);
    return render_template("manage.html", feed_name=feed_name)
