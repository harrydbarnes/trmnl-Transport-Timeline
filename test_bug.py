import unittest
from project import create_app, db
from project.models import User, Installation
from config import Config
from datetime import datetime, timedelta
import pytz
import json

class TestConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    WTF_CSRF_ENABLED = False
    SERVER_NAME = 'localhost:5000'

class TestBug(unittest.TestCase):
    def setUp(self):
        self.app = create_app(TestConfig)
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()
        self.client = self.app.test_client()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_min_train_time_zero(self):
        # Create an installation with min_train_time = 0
        user = User(trmnl_id='user123')
        db.session.add(user)

        installation = Installation(
            user=user,
            access_token='token123',
            trmnl_installation_id='inst123',
            min_train_time=0,  # Explicitly set to 0
            train_station='LST',
            bus_stop='12345'
        )
        db.session.add(installation)
        db.session.commit()

        # Verify it is saved as 0
        saved_inst = Installation.query.first()
        self.assertEqual(saved_inst.min_train_time, 0)

        # Call the API with the token
        headers = {'Authorization': 'Bearer token123'}
        response = self.client.get('/api/data', headers=headers)

        self.assertEqual(response.status_code, 200)
        data = response.json
        trains = data['trains']

        # MOCK_TRAIN_DATA has trains at 12:00, 12:45, 12:15.
        # "now" is mocked at 11:45.
        # 12:00 is 15 mins away.
        # 12:45 is 60 mins away.
        # 12:15 is 30 mins away.

        # If min_train_time is 0, we expect 12:00 to be present.
        # If min_train_time defaults to 30 (bug), 12:00 (15 mins) will be missing.

        times = [t['time'] for t in trains]

        self.assertIn('12:00', times, "12:00 train should be present if min_train_time is 0")
        self.assertIn('12:15', times)
        self.assertIn('12:45', times)
