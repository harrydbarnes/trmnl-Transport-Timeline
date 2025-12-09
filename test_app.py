import unittest
import json
from project import create_app, db
from project.models import User, Installation
from config import Config
from unittest.mock import patch
import uuid

class TestConfig(Config):
    """Configuration for testing.

    Overrides the default configuration with settings suitable for testing,
    such as using an in-memory database and disabling CSRF protection.
    """
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    WTF_CSRF_ENABLED = False
    SERVER_NAME = 'localhost:5000'

class TestApp(unittest.TestCase):
    """Test case for the Flask application.

    This class contains integration tests for the installation flow, callbacks,
    and webhooks.
    """

    def setUp(self):
        """Sets up the test environment.

        Creates the app with the test configuration, pushes the application context,
        and creates the database tables.
        """
        self.app = create_app(TestConfig)
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()
        self.client = self.app.test_client()

    def tearDown(self):
        """Tears down the test environment.

        Removes the database session, drops all tables, and pops the application context.
        """
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_install_redirect(self):
        """Tests the installation redirect.

        Verifies that accessing the '/install' route redirects to the TRMNL
        authorization page and creates a placeholder installation record with a state.
        """
        response = self.client.get('/install')
        self.assertEqual(response.status_code, 302)
        self.assertIn('usetrmnl.com/api/oauth/authorize', response.location)
        
        # Check that a placeholder installation with a state has been created
        self.assertEqual(Installation.query.count(), 1)
        self.assertIsNotNone(Installation.query.first().install_state)

    @patch('project.main.oauth.trmnl.authorize_access_token')
    @patch('project.main.oauth.trmnl.get')
    def test_callback_and_webhook(self, mock_get, mock_authorize):
        """Tests the full installation flow including callback and webhook.

        Simulates the user authorizing the app, the callback handling, and the
        final installation success webhook. Verifies that the installation record
        is correctly updated with the user ID, access token, and TRMNL installation ID.

        Args:
            mock_get (Mock): Mock for the requests.get method (to fetch user profile).
            mock_authorize (Mock): Mock for the authorize_access_token method.
        """
        # 1. User starts installation
        with self.client as c:
            response = c.get('/install')
            state = Installation.query.first().install_state

        # 2. User is redirected back from TRMNL
        mock_authorize.return_value = {'access_token': 'test_token'}
        mock_get.return_value.json.return_value = {'id': 'trmnl_user_123'}
        mock_get.return_value.raise_for_status.return_value = None

        response = self.client.get(f'/callback?state={state}')
        self.assertEqual(response.status_code, 200)

        # 3. TRMNL sends installation success webhook
        trmnl_installation_id = str(uuid.uuid4())
        webhook_payload = {
            'id': trmnl_installation_id,
            'state': state,
            'account_id': 'trmnl_user_123'
        }
        response = self.client.post('/webhook/installation_success', json=webhook_payload)
        self.assertEqual(response.status_code, 200)

        # Verify the installation is finalized
        installation = Installation.query.filter_by(trmnl_installation_id=trmnl_installation_id).first()
        self.assertIsNotNone(installation)
        self.assertIsNone(installation.install_state)
        self.assertEqual(installation.user.trmnl_id, 'trmnl_user_123')
        self.assertEqual(installation.access_token, 'test_token')

if __name__ == '__main__':
    unittest.main()
