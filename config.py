import os

class Config:
    """Configuration class for the Flask application.

    This class contains settings for the Flask application, including security keys
    and database configuration.

    Attributes:
        SECRET_KEY (str): The secret key used for session management and cryptographic signing.
                          Defaults to 'a-hard-to-guess-string' if not set in environment variables.
        SQLALCHEMY_DATABASE_URI (str): The database URI used by SQLAlchemy for database connections.
                                       Defaults to a local SQLite database 'sqlite:///site.db' if not set.
        SQLALCHEMY_TRACK_MODIFICATIONS (bool): Configuration to disable SQLAlchemy's modification tracking
                                               system to save resources. Defaults to False.
    """
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'a-hard-to-guess-string'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'sqlite:///site.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
