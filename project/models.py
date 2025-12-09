from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class User(db.Model):
    """Represents a user in the system.

    This model stores information about the user, identified by their TRMNL ID.
    A user can have multiple installations associated with them.

    Attributes:
        id (int): The unique identifier for the user (primary key).
        trmnl_id (str): The unique TRMNL user ID.
        installations (list): A list of `Installation` objects associated with this user.
    """
    id = db.Column(db.Integer, primary_key=True)
    trmnl_id = db.Column(db.String(80), unique=True, nullable=False)
    installations = db.relationship('Installation', backref='user', lazy=True)

class Installation(db.Model):
    """Represents a plugin installation.

    This model stores the installation details, including authentication tokens
    and plugin-specific settings for bus and train configurations.

    Attributes:
        id (int): The unique identifier for the installation (primary key).
        trmnl_installation_id (str): The unique installation ID provided by TRMNL.
        install_state (str): A unique state string used during the OAuth installation flow.
        user_id (int): The ID of the `User` who owns this installation.
        access_token (str): The OAuth access token for the installation.
        bus_stop (str): The bus stop code/identifier.
        bus_direction (str): The direction of the bus service.
        train_station (str): The train station code.
        train_destination (str): The train destination code.
        min_train_time (int): The minimum time (in minutes) for a train departure to be displayed. Defaults to 30.
        app_id (str): The TransportAPI Application ID.
        app_key (str): The TransportAPI Application Key.
    """
    id = db.Column(db.Integer, primary_key=True)
    trmnl_installation_id = db.Column(db.String(80), unique=True, nullable=True)
    install_state = db.Column(db.String(80), unique=True, nullable=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    access_token = db.Column(db.String(200), nullable=True)

    # Plugin-specific settings
    bus_stop = db.Column(db.String(100))
    bus_direction = db.Column(db.String(100))
    train_station = db.Column(db.String(100))
    train_destination = db.Column(db.String(100))
    min_train_time = db.Column(db.Integer, default=30)
    app_id = db.Column(db.String(100))
    app_key = db.Column(db.String(100))
