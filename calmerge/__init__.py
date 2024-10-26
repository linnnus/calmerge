import os
from flask import Flask

def create_app() -> Flask:
    """Create a configure the Flask app."""

    app = Flask(__name__)

    app.config.from_mapping(SECRET_KEY="dev",
                            DATABASE=os.path.join(app.instance_path, "calmerge.sqlite"))

    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    from . import db
    db.init_app(app)

    from . import frontend
    app.register_blueprint(frontend.bp)

    return app
