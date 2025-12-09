import unittest
from unittest.mock import patch, MagicMock
from project import create_app, db
from project.models import User, Installation
from config import Config
from datetime import datetime
import pytz

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

    @patch('project.main.fetch_train_data')
    @patch('project.main.fetch_bus_data')
    @patch('project.main.datetime')
    def test_min_train_time_zero(self, mock_datetime, mock_fetch_bus, mock_fetch_train):
        # Configure Time Mock
        uk_tz = pytz.timezone('Europe/London')
        # We need a fixed time: 11:45 UK time today
        # To make it "today", we should probably use real today but force 11:45
        # Or just pick a fixed date. The code uses `now.date()` to combine with train time.
        # If the train data has only HH:MM, the date matters for "today".

        # Let's fix "today" to a known date so "12:00" is definitely in the future relative to "11:45"
        fixed_now = datetime(2023, 10, 27, 11, 45, 0)
        localized_now = uk_tz.localize(fixed_now)

        # When datetime.now(uk_tz) is called, return our localized time
        mock_datetime.now.return_value = localized_now
        # Side effect: if called without args, maybe return naive? Code calls it with tz.

        # We also need to mock datetime.strptime because the code uses it for parsing times
        # But patching 'project.main.datetime' replaces the whole class.
        # We must ensure strptime works.
        # Ideally we only patch `now`. But `from datetime import datetime` means we patch the class.
        # If we patch the class, we lose `strptime` unless we provide it.
        # Strategy: Use `wraps` to pass through everything else?
        # Or just mock `now` specifically if possible?
        # Since `datetime` is imported in `project.main`, patching `project.main.datetime` mocks the class.
        # A common workaround for `datetime` mocking is tricky.
        # Let's try assigning the side_effect to delegate to real datetime for other methods?
        # Or better: use a library like `freezegun`? It's likely not installed.
        # Standard approach:
        # mock_datetime.now.return_value = localized_now
        # mock_datetime.strptime = datetime.strptime # Pass through
        # mock_datetime.combine = datetime.combine
        # mock_datetime.max = datetime.max

        mock_datetime.now.return_value = localized_now
        mock_datetime.strptime.side_effect = lambda *args, **kwargs: datetime.strptime(*args, **kwargs)
        mock_datetime.combine.side_effect = lambda *args, **kwargs: datetime.combine(*args, **kwargs)
        mock_datetime.max = datetime.max

        # Configure Data Mocks
        MOCK_TRAIN_DATA = {
            "departures": {
                "all": [
                    {"destination_name": "London Liverpool Street", "aimed_departure_time": "12:00", "status": "ON TIME", "operator_name": "Greater Anglia"},
                    {"destination_name": "Cambridge", "aimed_departure_time": "12:45", "status": "ON TIME", "operator_name": "Greater Anglia"},
                    {"destination_name": "Norwich", "aimed_departure_time": "12:15", "status": "LATE", "operator_name": "Greater Anglia"},
                    {"destination_name": "Stansted Airport", "aimed_departure_time": "12:05", "status": "ON TIME", "operator_name": "CrossCountry"}
                ]
            }
        }
        mock_fetch_train.return_value = MOCK_TRAIN_DATA
        mock_fetch_bus.return_value = {} # Not needed for this test

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

        times = [t['time'] for t in trains]

        # With 11:45 as now:
        # 12:00 is 15 mins away (should be included if min_train_time=0)
        # 12:15 is 30 mins away
        # 12:45 is 60 mins away

        self.assertIn('12:00', times, "12:00 train should be present if min_train_time is 0")
        self.assertIn('12:15', times)
        self.assertIn('12:45', times)
