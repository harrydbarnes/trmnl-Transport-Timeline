import unittest
import json
from project import create_app, db
from project.models import User, Installation
from config import Config
from unittest.mock import patch
import uuid

class TestConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    WTF_CSRF_ENABLED = False
    SERVER_NAME = 'localhost:5000'

class TestApp(unittest.TestCase):
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

    def test_install_redirect(self):
        response = self.client.get('/install')
        self.assertEqual(response.status_code, 302)
        self.assertIn('usetrmnl.com/api/oauth/authorize', response.location)
        
        # Check that a placeholder installation with a state has been created
        self.assertEqual(Installation.query.count(), 1)
        self.assertIsNotNone(Installation.query.first().install_state)

    @patch('project.main.oauth.trmnl.authorize_access_token')
    @patch('project.main.oauth.trmnl.get')
    def test_callback_and_webhook(self, mock_get, mock_authorize):
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
