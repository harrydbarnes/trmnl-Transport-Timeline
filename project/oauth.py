from authlib.integrations.flask_client import OAuth
import os

oauth = OAuth()

def init_oauth(app):
    """Initialize the OAuth extension with the TRMNL provider.

    This function configures the `authlib` OAuth registry with the TRMNL client details.
    It reads `TRMNL_CLIENT_ID` and `TRMNL_CLIENT_SECRET` from environment variables.
    It sets up the access token URL, authorize URL, base API URL, and scopes.

    Args:
        app (Flask): The Flask application instance to initialize OAuth for.

    Returns:
        None
    """
    oauth.init_app(app)
    oauth.register(
        name='trmnl',
        client_id=os.environ.get('TRMNL_CLIENT_ID'),
        client_secret=os.environ.get('TRMNL_CLIENT_SECRET'),
        access_token_url='https://usetrmnl.com/api/oauth/token',
        authorize_url='https://usetrmnl.com/api/oauth/authorize',
        api_base_url='https://usetrmnl.com/api/',
        client_kwargs={'scope': 'read write'},
    )
