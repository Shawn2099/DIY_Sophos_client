from pathlib import Path
from typing import Optional
import os

import yaml


REQUIRED_KEYS = {
	"ssid",
	"portal_url",
	"username",
	"password",
	"check_interval",
	"cooldown",
}

OPTIONAL_DEFAULTS = {
	"request_timeout": 4,
	"reconnect_delay": 2,
	"network_error_base_sleep": 5,
	"network_error_max_sleep": 60,
	"log_level": "INFO",
	"log_file": "logs/sophos_wifi.log",
	"log_max_bytes": 1048576,
	"log_backup_count": 5,
	"log_to_stdout": True,
	"ssid_interface": "",
	"network_probe_enabled": True,
	"network_probe_timeout": 2,
}

ENV_OVERRIDES = {
	"SOPHOSDIY_SSID": "ssid",
	"SOPHOSDIY_PORTAL_URL": "portal_url",
	"SOPHOSDIY_USERNAME": "username",
	"SOPHOSDIY_PASSWORD": "password",
	"SOPHOSDIY_CHECK_INTERVAL": "check_interval",
	"SOPHOSDIY_COOLDOWN": "cooldown",
	"SOPHOSDIY_REQUEST_TIMEOUT": "request_timeout",
	"SOPHOSDIY_RECONNECT_DELAY": "reconnect_delay",
	"SOPHOSDIY_NETWORK_ERROR_BASE_SLEEP": "network_error_base_sleep",
	"SOPHOSDIY_NETWORK_ERROR_MAX_SLEEP": "network_error_max_sleep",
	"SOPHOSDIY_LOG_LEVEL": "log_level",
	"SOPHOSDIY_LOG_FILE": "log_file",
	"SOPHOSDIY_LOG_MAX_BYTES": "log_max_bytes",
	"SOPHOSDIY_LOG_BACKUP_COUNT": "log_backup_count",
	"SOPHOSDIY_LOG_TO_STDOUT": "log_to_stdout",
	"SOPHOSDIY_SSID_INTERFACE": "ssid_interface",
	"SOPHOSDIY_NETWORK_PROBE_ENABLED": "network_probe_enabled",
	"SOPHOSDIY_NETWORK_PROBE_TIMEOUT": "network_probe_timeout",
}


def _as_positive_int(config: dict, key: str) -> int:
	value = int(config[key])
	if value <= 0:
		raise ValueError(f"Config key '{key}' must be > 0")
	return value


def _as_positive_float(config: dict, key: str) -> float:
	value = float(config[key])
	if value <= 0:
		raise ValueError(f"Config key '{key}' must be > 0")
	return value


def _as_bool(value):
	if isinstance(value, bool):
		return value
	if isinstance(value, str):
		return value.strip().lower() in {"1", "true", "yes", "on"}
	return bool(value)


def _apply_env_overrides(config: dict) -> dict:
	merged = dict(config)
	for env_name, key in ENV_OVERRIDES.items():
		value = os.getenv(env_name)
		if value is not None and value != "":
			merged[key] = value
	return merged


def _normalize_config(config: dict) -> dict:
	normalized = dict(config)
	for key, default in OPTIONAL_DEFAULTS.items():
		normalized.setdefault(key, default)

	normalized["check_interval"] = _as_positive_int(normalized, "check_interval")
	normalized["cooldown"] = _as_positive_int(normalized, "cooldown")
	normalized["request_timeout"] = _as_positive_int(normalized, "request_timeout")
	normalized["reconnect_delay"] = _as_positive_int(normalized, "reconnect_delay")
	normalized["network_error_base_sleep"] = _as_positive_int(normalized, "network_error_base_sleep")
	normalized["network_error_max_sleep"] = _as_positive_int(normalized, "network_error_max_sleep")
	normalized["log_max_bytes"] = _as_positive_int(normalized, "log_max_bytes")
	normalized["log_backup_count"] = _as_positive_int(normalized, "log_backup_count")
	normalized["network_probe_timeout"] = _as_positive_float(normalized, "network_probe_timeout")

	if normalized["network_error_max_sleep"] < normalized["network_error_base_sleep"]:
		raise ValueError("Config key 'network_error_max_sleep' must be >= 'network_error_base_sleep'")

	normalized["log_level"] = str(normalized["log_level"]).upper()
	normalized["log_file"] = str(normalized["log_file"]).strip()
	normalized["log_to_stdout"] = _as_bool(normalized["log_to_stdout"])
	normalized["ssid_interface"] = str(normalized["ssid_interface"]).strip()
	normalized["network_probe_enabled"] = _as_bool(normalized["network_probe_enabled"])
	normalized["portal_url"] = str(normalized["portal_url"]).strip().rstrip("/")
	if not normalized["portal_url"].startswith(("http://", "https://")):
		raise ValueError("Config key 'portal_url' must start with http:// or https://")
	return normalized


def load_config(config_path: Optional[str] = None) -> dict:
	if config_path is None:
		project_root = Path(__file__).resolve().parent.parent
		config_file = project_root / "config" / "config.yaml"
	else:
		config_file = Path(config_path).expanduser().resolve()

	with config_file.open("r", encoding="utf-8") as handle:
		config = yaml.safe_load(handle) or {}

	config = _apply_env_overrides(config)

	missing = REQUIRED_KEYS - set(config.keys())
	if missing:
		missing_keys = ", ".join(sorted(missing))
		raise ValueError(f"Missing required config keys: {missing_keys}")

	return _normalize_config(config)
