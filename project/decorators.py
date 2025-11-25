from functools import wraps
from flask import request, jsonify
from .models import Installation

def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
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
