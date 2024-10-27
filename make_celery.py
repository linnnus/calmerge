"""
Helper script which accesses the Celery application contained within the flask
application from our package.

See: https://flask.palletsprojects.com/en/stable/patterns/celery/#application-factory
"""

from calmerge import create_app

flask_app = create_app()
celery_app = flask_app.extensions["celery"]
