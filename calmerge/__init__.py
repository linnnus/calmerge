import os
from flask import Flask

def create_app() -> Flask:
    """Create a configure the Flask app."""

    app = Flask(__name__)

    app.config.from_mapping(SECRET_KEY="dev",
                            DATABASE=os.path.join(app.instance_path, "calmerge.sqlite"),
                            CELERY={
                                "broker_connection_retry_on_startup": True,
                                # For development, we run redis at port 5002.
                                "broker_url": "redis://localhost:5002",
                                "result_backend": "redis://localhost:5002",
                                # Don't store task results by default. This means that unless we explicitly
                                # opt in, we don't have to worry about memory leaks when handling `AsyncResult`s.
                                "task_ignore_result": True,
                            })

    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    from . import db
    db.init_app(app)

    from . import frontend
    app.register_blueprint(frontend.bp)

    from . import tasks
    tasks.init_app(app)

    return app
