from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    trmnl_id = db.Column(db.String(80), unique=True, nullable=False)
    installations = db.relationship('Installation', backref='user', lazy=True)

class Installation(db.Model):
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
