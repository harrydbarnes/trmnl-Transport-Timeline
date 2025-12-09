from flask import Flask
from .main import main as main_blueprint
from .models import db
from flask_migrate import Migrate
from config import Config
from .oauth import init_oauth
from flask_wtf.csrf import CSRFProtect

csrf = CSRFProtect()

def create_app(config_class=Config):
    """Factory function to create the Flask application instance.

    This function initializes the Flask application, loads the configuration,
    initializes extensions (database, migrations, OAuth, CSRF protection),
    and registers the main blueprint.

    Args:
        config_class (class): The configuration class to use for setting up the app.
                              Defaults to `Config`.

    Returns:
        Flask: The initialized Flask application instance.
    """
    app = Flask(__name__)
    app.config.from_object(config_class)
    db.init_app(app)
    Migrate(app, db)
    init_oauth(app)
    csrf.init_app(app)
    app.register_blueprint(main_blueprint)
    return app
