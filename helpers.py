from typing import Literal
import subprocess
import socket
import textwrap
import shutil

import qrcode


UNITS = {
    'api': 'service-status-indicator-api',
    'scheduler': 'service-status-indicator-scheduler'
}

Unit = Literal['api', 'scheduler']


def _run(cmd: str):
    """Runs a given command and returns the process"""
    mapped = cmd.split(' ')
    return subprocess.run(mapped, capture_output=True, text=True, check=True)


def is_unit_active(unit: Unit):
    try:
        result = _run(f"systemctl is-active {UNITS[unit]}")
        return result.stdout.strip() == 'active'
    except subprocess.CalledProcessError:
        return False


def is_unit_enabled(unit: Unit):
    try:
        result = _run(f"systemctl is-enabled {UNITS[unit]}")
        return result.stdout.strip() == 'enabled'
    except subprocess.CalledProcessError:
        return False


def enable_unit(unit: Unit):
    if is_unit_active(unit) and is_unit_enabled(unit):
        return True
    try:
        _run(f"systemctl enable --now {UNITS[unit]}")
    except subprocess.CalledProcessError:
        return False
    return True


def disable_unit(unit: Unit):
    try:
        _run(f"systemctl disable --now {UNITS[unit]}")
    except subprocess.CalledProcessError:
        return False
    return True


def format_time(seconds):
    hours = seconds // 3600
    seconds %= 3600
    minutes = seconds // 60
    seconds %= 60

    time_parts = []
    if hours > 0:
        time_parts.append(f"{hours}h")
    if minutes > 0:
        time_parts.append(f"{minutes}m")
    if seconds > 0:
        time_parts.append(f"{seconds}s")

    formatted_time = " ".join(time_parts)
    return formatted_time


def get_local_ip():
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as _socket:
        _socket.connect(("8.8.8.8", 80))
        local_ip = _socket.getsockname()[0]
        return local_ip


def get_used_port():
    with open('scripts/start-server.sh', encoding='utf8') as file:
        return file.read().split('0.0.0.0:')[1][0:4]


def print_qr_info(data: str):
    _qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    _qr.add_data(data)
    _qr.make(fit=True)
    _qr.print_ascii()


def get_new_token():
    result = subprocess.run(['bash', 'scripts/token_generator.sh'],
                            stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE,
                            check=True)
    return result.stdout.decode('utf-8').strip().splitlines()[-1]


def display_padded_text(text, padding=4, line_width=None, double_next_line_left_padding=True):
    terminal_width, _ = shutil.get_terminal_size()

    if line_width is None:
        line_width = terminal_width

    wrapped_lines = textwrap.wrap(text, width=line_width - (2 * padding))
    for i, line in enumerate(wrapped_lines):
        if i == 0 or not double_next_line_left_padding:
            padded_line = f"{' ' * padding}{line}{' ' * padding}"
        else:
            padded_line = f"{' ' * padding * 2}{line}{' ' * padding}"
        print(padded_line)
