import sqlite3
import typing

from logger import log, error
from models import ServiceStatus

DATABASE_FILENAME = '/etc/service-status-indicator/.data.db'


class DB():
    @staticmethod
    def initialize(logging=True):
        try:
            with sqlite3.connect(DATABASE_FILENAME) as conn:
                cursor = conn.cursor()
                valid_status = typing.get_args(ServiceStatus)
                query = f'''
                    CREATE TABLE IF NOT EXISTS services (
                        id TEXT UNIQUE,
                        label TEXT,
                        enabled BOOLEAN,
                        running BOOLEAN,
                        status TEXT CHECK(status IN {valid_status}),
                        message TEXT
                    );
                '''
                cursor.execute(query)
                if logging:
                    log('Database initialized.')
        except sqlite3.OperationalError as err:
            if logging:
                if 'table services already exists' in str(err):
                    log('Database already initialized.')
                else:
                    error(f"Error on database initialize: {err}")

    @staticmethod
    def get_enabled_services():
        """
        Returns all `enabled` services.

        Raises:
            OperationalError: When database is unreachable.

        Returns a list of dictionaries. Example: 
        `{'id': 'unique-string',
        'label': 'Service Label',
        'running': bool,
        'status': 'ok' | 'update' | 'warning' | 'failure',
        'message': Any as string
        }`
        """
        with sqlite3.connect(DATABASE_FILENAME) as conn:
            enabled_services = []
            try:
                cursor = conn.cursor()
                query = '''
                    SELECT id, label, running, status, message 
                    FROM services
                    WHERE enabled = 1
                    ORDER BY id;
                '''
                cursor.execute(query)
                rows = cursor.fetchall()

                for row in rows:
                    _id, label, running, status, message = row
                    enabled_services.append({
                        'id': _id,
                        'label': label,
                        'running': bool(running),
                        'status': status,
                        'message': message,
                    })
            except sqlite3.OperationalError as err:
                error(f'Error on getting services: {err}')
            return enabled_services

    @staticmethod
    def save_service(_id: str,
                     label: str,
                     enabled: bool,
                     running: bool,
                     status: ServiceStatus = None,
                     message: str = None):
        """Creates or overrides the service with given ID."""
        with sqlite3.connect(DATABASE_FILENAME) as conn:
            try:
                cursor = conn.cursor()
                query = '''
                    INSERT OR REPLACE 
                    INTO services (id, label, enabled, running, status, message) 
                    VALUES (?, ?, ?, ?, ?, ?)
                '''
                cursor.execute(
                    query, (_id, label, enabled, running, status, message))
                conn.commit()
            except sqlite3.OperationalError as err:
                error(f'Error on saving service: {err}')

    @staticmethod
    def get_service(_id: str):
        """Return the service with given ID or None"""
        with sqlite3.connect(DATABASE_FILENAME) as conn:
            try:
                cursor = conn.cursor()
                query = 'SELECT * FROM services WHERE id = ?'
                cursor.execute(query, (_id,))
                _id, label, enabled, running, status, message = cursor.fetchone()
                return {
                    'id': _id,
                    'label': label,
                    'enabled': bool(enabled),
                    'running': bool(running),
                    'status': status,
                    'message': message,
                }
            except sqlite3.OperationalError as err:
                error(f'Error on saving service: {err}')
            except TypeError:
                return None

    @staticmethod
    def set_running(_id, running: bool = True):
        saved = DB.get_service(_id)
        DB.save_service(
            saved['id'],
            saved['label'],
            saved['enabled'],
            running,
            saved['status'],
            saved['message'])

    @staticmethod
    def set_status(_id, status: ServiceStatus, message=None):
        if status not in typing.get_args(ServiceStatus):
            error(f'Invalid status returned from {_id} script')
            return
        saved = DB.get_service(_id)
        DB.save_service(
            saved['id'],
            saved['label'],
            saved['enabled'],
            saved['running'],
            status,
            message)
