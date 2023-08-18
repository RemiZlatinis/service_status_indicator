from pathlib import Path
import subprocess
import json
import asyncio

from logger import log, error, debug
from database import DB
from config import get_setting


DEFAULT_SERVICES = Path('/etc/service-status-indicator/services/default.json')
USERS_SERVICES = Path('/etc/service-status-indicator/services/users.json')


class ServiceRegistry:
    @staticmethod
    def get_available_services() -> list[dict]:
        all_available = []
        with open(DEFAULT_SERVICES, encoding='utf8') as file:
            services = list(json.load(file))
            for service in services:
                required = ['id', 'label', 'script']
                if any(not service.get(field) for field in required):
                    print('Fields ["id", "label", "script"] are required!')
                    print('Please fix services/default.json')
                    break
            else:
                all_available += (services)
        with open(USERS_SERVICES, encoding='utf8') as file:
            services = list(json.load(file))
            for service in services:
                required = ['id', 'label', 'script']
                if any(not service.get(field) for field in required):
                    print('Fields ["id", "label", "script"] are required!')
                    print('Please fix services/users.json')
                    break
            else:
                all_available += (services)
        return all_available

    @staticmethod
    def enable(_id: str) -> str | None:
        """
        Enables the service with the given ID

        Returns `None` on success or an `error message`
        """
        # Check if service is available
        for service in ServiceRegistry.get_available_services():
            if service['id'] == _id:
                # Service is available
                DB.save_service(_id, service['label'], True, False)
                log(f'Service "{_id}" enabled.', do_not_print=True)
                break
        else:
            return f'❌ There is no service id \"{_id}\" available!'

    @staticmethod
    def disable(_id: str) -> str | None:
        """
        Disables the service with the given ID

        Returns `None` on success or an `error message`
        """
        # Check if service is available
        for service in ServiceRegistry.get_available_services():
            if service['id'] == _id:
                # Service is available
                saved_service = DB.get_service(_id)
                if saved_service and saved_service.get('enabled'):
                    DB.save_service(_id, service['label'], False, False)
                    log(f'Service "{_id}" disabled.', do_not_print=True)
                else:
                    log(f'Service "{_id}" is already disabled.',
                        do_not_print=True)
                saved_service = DB.get_service(_id)
                break
        else:
            return f'❌ There is no service id \"{_id}\" available!'

    @staticmethod
    async def refresh_enabled_services_async():
        services = DB.get_enabled_services()
        for service in services:
            if not service['running']:
                _id = service['id']
                DB.set_running(_id)
                asyncio.create_task(keep_refreshing(_id))
                DB.set_running(_id, False)


async def keep_refreshing(_id):
    """Keep refreshing while is enabled"""
    available_services = ServiceRegistry.get_available_services()

    for available in available_services:
        if available['id'] == _id:
            service = available
            break
    else:
        service = None

    while DB.get_service(_id)['enabled']:
        try:
            result = subprocess.run(['bash', service['script']],
                                    stdout=subprocess.PIPE,
                                    stderr=subprocess.PIPE,
                                    check=True)
            status = result.stdout.decode('utf-8').strip().splitlines()[-1]
            message = None
            if "message=" in status:
                status, message = status.split(' message=')
            DB.set_status(_id, status, message)
            debug(f'Service {_id} refreshed.')
        except subprocess.CalledProcessError as err:
            error(err.stderr.decode('utf-8').strip())
        finally:
            interval = service.get(
                'interval',
                get_setting('default-refresh-interval'))
            await asyncio.sleep(interval)
