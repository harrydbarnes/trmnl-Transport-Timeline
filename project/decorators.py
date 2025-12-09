from functools import wraps
from flask import request, jsonify
from .models import Installation

def token_required(f):
    """Decorator to require a valid Bearer token for a route.

    This decorator checks for the 'Authorization' header in the request.
    It expects the header to be in the format 'Bearer <token>'.
    It verifies the token against the `Installation` database.
    If the token is missing or invalid, it returns a 401 Unauthorized response.
    If valid, it passes the corresponding `Installation` object to the decorated function.

    Args:
        f (function): The view function to decorate.

    Returns:
        function: The wrapped function that includes authentication checks.
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        """The wrapper function performing the authentication check.

        Args:
            *args: Positional arguments for the view function.
            **kwargs: Keyword arguments for the view function.

        Returns:
            Response: A Flask response object (JSON error or the result of the view function).
        """
        token = None
        if 'Authorization' in request.headers:
            token = request.headers['Authorization'].split(' ')[1]

        if not token:
            return jsonify({'message': 'Token is missing!'}), 401

        installation = Installation.query.filter_by(access_token=token).first()

        if not installation:
            return jsonify({'message': 'Token is invalid!'}), 401

        return f(installation, *args, **kwargs)
    return decorated
