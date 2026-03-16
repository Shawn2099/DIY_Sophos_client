import subprocess
import socket
from urllib.parse import urlparse


def _iwgetid_command(interface=None):
    command = ["iwgetid"]
    if interface:
        command.append(interface)
    command.append("-r")
    return command


def current_ssid(interface=None):
    try:
        return subprocess.check_output(
            _iwgetid_command(interface)
        ).decode().strip()
    except (subprocess.CalledProcessError, FileNotFoundError, OSError):
        return None


def portal_reachable(portal_url, timeout_seconds=2):
    try:
        parsed = urlparse(portal_url)
        host = parsed.hostname
        port = parsed.port
        if not host:
            return False

        if port is None:
            port = 443 if parsed.scheme == "https" else 80

        with socket.create_connection((host, port), timeout=timeout_seconds):
            return True
    except OSError:
        return False