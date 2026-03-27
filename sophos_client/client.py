import time
import logging
import signal
import threading
from pathlib import Path
from logging.handlers import RotatingFileHandler, QueueHandler, QueueListener
import queue
from sophos_client.config import load_config
from sophos_client.network import current_ssid, portal_reachable
from sophos_client.portal import login, logout, portal_state
from sophos_client.state import AUTHENTICATED, CONNECTED, DISCONNECTED, NETWORK_ERROR

def _get_error_wait_seconds(cfg, has_authenticated_once, error_streak):
    if not has_authenticated_once:
        return min(cfg["startup_fast_retry_seconds"], cfg["network_error_base_sleep"])
    return _backoff_sleep(
        cfg["network_error_base_sleep"],
        cfg["network_error_max_sleep"],
        error_streak,
    )


LOGGER = logging.getLogger(__name__)


def _configure_logging(cfg):
    level = getattr(logging, str(cfg["log_level"]).upper(), logging.INFO)
    formatter = logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s")

    root_logger = logging.getLogger()
    root_logger.setLevel(level)
    root_logger.handlers.clear()

    log_file = Path(cfg["log_file"]).expanduser()
    if not log_file.is_absolute():
        project_root = Path(__file__).resolve().parent.parent
        log_file = project_root / log_file
    log_file.parent.mkdir(parents=True, exist_ok=True)
    file_handler = RotatingFileHandler(
        log_file,
        maxBytes=cfg["log_max_bytes"],
        backupCount=cfg["log_backup_count"],
    )
    file_handler.setFormatter(formatter)

    # Use a non-blocking queue for log writes with a bound to prevent slow writers from causing OOM
    log_queue = queue.Queue(1000)
    queue_handler = QueueHandler(log_queue)
    root_logger.addHandler(queue_handler)
    listener = QueueListener(log_queue, file_handler)
    listener.start()

    if cfg.get("log_to_stdout", True):
        stream_handler = logging.StreamHandler()
        stream_handler.setFormatter(formatter)
        root_logger.addHandler(stream_handler)


def _backoff_sleep(base_seconds, max_seconds, error_streak):
    wait_seconds = min(base_seconds * (2 ** max(error_streak - 1, 0)), max_seconds)
    return wait_seconds


def _sleep_or_stop(stop_event, seconds):
    return stop_event.wait(timeout=seconds)


def _install_signal_handlers(stop_flag, stop_event):
    def _handler(signum, _frame):
        stop_flag["running"] = False
        stop_event.set()
        LOGGER.info("Received signal %s, shutting down", signum)

    signal.signal(signal.SIGINT, _handler)
    signal.signal(signal.SIGTERM, _handler)


def main(config_path=None):
    cfg = load_config(config_path)
    _configure_logging(cfg)
    stop_flag = {"running": True}
    stop_event = threading.Event()
    _install_signal_handlers(stop_flag, stop_event)

    state = DISCONNECTED
    last_attempt = 0.0
    error_streak = 0
    has_authenticated_once = False

    LOGGER.info("Sophos WiFi client started")



    last_portal_reachable = False
    while stop_flag["running"]:
        ssid_check_enabled = cfg.get("ssid_check_enabled", True)
        if ssid_check_enabled:
            ssid = current_ssid(cfg.get("ssid_interface"))
            if ssid != cfg["ssid"]:
                if state != DISCONNECTED:
                    LOGGER.info("Disconnected from target SSID (current=%s)", ssid)
                state = DISCONNECTED
                error_streak = 0
                if _sleep_or_stop(stop_event, 2):
                    break
                continue

        # Always use direct IP for portal_url
        portal_url = cfg["portal_url"].strip()
        if cfg.get("network_probe_enabled", True):
            reachable = portal_reachable(
                portal_url,
                timeout_seconds=cfg["network_probe_timeout"],
            )
            if not reachable:
                state = NETWORK_ERROR
                error_streak += 1
                wait_seconds = _get_error_wait_seconds(cfg, has_authenticated_once, error_streak)
                LOGGER.warning("Portal host is unreachable, backing off for %ss", wait_seconds)
                last_portal_reachable = False
                if _sleep_or_stop(stop_event, wait_seconds):
                    break
                continue
            # If portal just became reachable, retry immediately
            if not last_portal_reachable:
                LOGGER.info("Portal became reachable, retrying immediately")
                last_portal_reachable = True
        else:
            last_portal_reachable = True

        pstate = portal_state(cfg)

        if pstate == "AUTHENTICATED":
            if state != AUTHENTICATED:
                LOGGER.info("Portal session is authenticated")
            state = AUTHENTICATED
            has_authenticated_once = True
            error_streak = 0
            if _sleep_or_stop(stop_event, cfg["check_interval"]):
                break
            continue

        if pstate == "AUTH_REQUIRED":
            now = time.monotonic()

            if now - last_attempt < cfg["cooldown"]:
                LOGGER.info("Cooldown active, skipping reconnect")
                if _sleep_or_stop(stop_event, 5):
                    break
                continue

            LOGGER.info("Session expired, reconnecting")

            if not has_authenticated_once:
                logout_ok = True
                login_ok = login(cfg)
            else:
                logout_ok = logout(cfg)
                if _sleep_or_stop(stop_event, cfg["reconnect_delay"]):
                    break
                login_ok = login(cfg)

            LOGGER.info("Reconnect result logout_ok=%s login_ok=%s", logout_ok, login_ok)

            last_attempt = now
            if login_ok:
                state = CONNECTED
                has_authenticated_once = True
                error_streak = 0
            else:
                state = NETWORK_ERROR
                error_streak += 1
                wait_seconds = _get_error_wait_seconds(cfg, has_authenticated_once, error_streak)
                LOGGER.warning("Login failed, backing off for %ss", wait_seconds)
                if _sleep_or_stop(stop_event, wait_seconds):
                    break
                continue

        if pstate == "UNKNOWN":
            state = NETWORK_ERROR
            error_streak += 1
            wait_seconds = _get_error_wait_seconds(cfg, has_authenticated_once, error_streak)
            LOGGER.warning("Portal state unknown, backing off for %ss", wait_seconds)
            if _sleep_or_stop(stop_event, wait_seconds):
                break
            continue

        if _sleep_or_stop(stop_event, cfg["check_interval"]):
            break

    LOGGER.info("Sophos WiFi client stopped")


if __name__ == "__main__":
    main()