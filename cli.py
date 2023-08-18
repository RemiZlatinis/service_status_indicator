from subprocess import CalledProcessError
import click

from helpers import (is_unit_active,
                     is_unit_enabled,
                     format_time,
                     get_local_ip,
                     get_used_port,
                     print_qr_info,
                     get_new_token,
                     enable_unit,
                     disable_unit,
                     display_padded_text)
from database import DB
from service_registry import ServiceRegistry
from config import get_setting, set_setting


@click.group()
def cli():
    """Service Status Indicator CLI."""


@cli.command()
def status():
    """Check the status"""
    # API Status
    active = "✅ Active" if is_unit_active('api') else "❌ In-Active"
    enabled = "✅ Enabled" if is_unit_enabled('api') else "❌ Disable"
    print(f'API status:         [{active}] [{enabled}]')

    # Scheduler Status
    active = "✅ Active" if is_unit_active('scheduler') else "❌ In-Active"
    enabled = "✅ Enabled" if is_unit_enabled('scheduler') else "❌ Disable"
    print(f'Scheduler status:   [{active}] [{enabled}]')

    # Enabled Services Statuses
    print('-'*47)
    enabled_services = DB.get_enabled_services()
    if len(enabled_services) == 0:
        return print('There are no enabled services.')

    for service in enabled_services:
        if service['status'] == 'ok':
            service_status = '✅'
        elif service['status'] == 'update':
            service_status = ' ⬆️'
        elif service['status'] == 'warning':
            service_status = '⚠️'
        elif service['status'] == 'failure':
            service_status = '⛔'
        else:
            service_status = '❔'
        print(
            f'{service_status} {service["label"]} [{service.get("message", "")}]')


@cli.command()
@click.option('-d', '--details', is_flag=True, help='Display more details.')
def services(details):
    """List the available services and more."""
    enabled_services_ids = [service['id']
                            for service in DB.get_enabled_services()]
    for i, service in enumerate(ServiceRegistry.get_available_services()):
        info = "🟢 Enabled" if service['id'] in enabled_services_ids else "🔘 Disabled"
        print(f'{i+1}. {service["label"]} [{info}]')
        if details:
            default_interval = get_setting('default-refresh-interval')
            interval = service.get('interval', default_interval)
            display_padded_text(f'ID: {service["id"]}')
            display_padded_text(
                f'Refresh interval: {format_time(int(interval))}')
            display_padded_text(f'Script: \"{service["script"]}\"')
            display_padded_text(f'Description: {service.get("description")}\n')


@cli.command()
@click.argument('service_id', required=False)
def enable(service_id):
    """Enable API and Scheduler or the service with the given [ID]."""
    if service_id:
        error = ServiceRegistry.enable(service_id)
        if error:
            print(f'🙆 {error}\n')
            print('Tip: Use "ssi services -d" to list all services detailed. 😉')
        else:
            print(f'✅ Service {service_id} successfully enabled.')

    else:
        if not enable_unit('api'):
            print('❗ Couldn\'t enable API.')
        elif not enable_unit('scheduler'):
            print('❗ Couldn\'t enable Scheduler.')
        else:
            print('✅ API and Scheduler are enabled and active.')


@cli.command()
@click.argument('service_id', required=False)
def disable(service_id):
    """Disable API and Scheduler or the service with the given [ID]."""
    if service_id:
        error = ServiceRegistry.disable(service_id)
        if error:
            print(f'🙆 {error}\n')
            print('Tip: Use "ssi services -d" to list all services detailed. 😉')
        else:
            print(f'✔️  Service {service_id} is disabled.')
    else:
        if not disable_unit('api'):
            print("❗Couldn't disable API.")
        elif not disable_unit('scheduler'):
            print("❗Couldn't disable Scheduler.")
        else:
            print('API and Scheduler are disabled.')


@cli.command()
@click.option('-r', '--regenerate', is_flag=True, help='Regenerate token')
def connect(regenerate):
    """Display connection info (QR code) and more."""

    url = get_setting('url')
    if not url:
        url = f'http://{get_local_ip()}:{get_used_port()}/'

    token = get_setting('token')
    if regenerate:
        try:
            token = get_new_token()
            set_setting('token', token)
        except CalledProcessError as err:
            print(f'Error on token generation: {err}')
            exit(1)
    elif token == 'insecure':
        print('⚠️ Insecure authentication token ⚠️\n')
        print('Tip: Use "ssi connect -r" to regenerate a token 😉')
    elif not token:
        print('⚠️ Authentication token is missing ⚠️\n')
        print('Tip: Use "ssi connect -r" to regenerate a token 😉')

    print(f"""
          
            Connection Information
    --------------------------------------
    URL: {url}
    Token: {token}
""")
    print_qr_info({url, token})


@cli.command(hidden=True)
def get_enabled_services_ids():
    """
    Prints all the enabled services.

    This command is meant to be used during re-installation.
    """
    print(' '.join(s['id'] for s in DB.get_enabled_services()))


@cli.command(hidden=True)
@click.argument('ids', nargs=-1)
def bulk_enable(ids):
    """
    Bulk enables all services from the given ids.

    This command is meant to be used during re-installation.
    """
    for _id in ids:
        ServiceRegistry.enable(_id)


if __name__ == '__main__':
    cli(prog_name='ssi')
