from flask import Flask, jsonify, request

from database import DB
from logger import log, error
from config import get_setting


TOKEN = get_setting('token')
DEFAULT_REFRESH_INTERVAL = get_setting("default-refresh-interval") or 60

if not TOKEN:
    error('Token is not configured. Exiting...')
    raise ValueError("Token is not configured.")


def create_app():
    """Service Status Indicator API"""
    app = Flask(__name__)

    @app.route('/services')
    def services():
        """Return the list of services along with there status"""
        # Check if is an authenticated request
        token = request.headers.get('Authorization')
        if token != f'Token {TOKEN}':
            return jsonify({'error': 'Unauthorized access'}), 401

        services = DB.get_enabled_services()
        for service in services:
            del service['running']
        return jsonify(services)

    log('API is listening...')
    return app


if __name__ == '__main__':
    create_app().run()
