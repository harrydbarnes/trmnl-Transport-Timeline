from authlib.integrations.flask_client import OAuth
import os

oauth = OAuth()

def init_oauth(app):
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
