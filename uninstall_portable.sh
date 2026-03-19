#!/usr/bin/env bash
set -euo pipefail

INSTALL_DIR="${1:-/opt/sophos-wifi-client}"
SERVICE_NAME="sophos-wifi-client"
HEALTHCHECK_SERVICE_NAME="${SERVICE_NAME}-healthcheck"
HEALTHCHECK_TIMER_NAME="${HEALTHCHECK_SERVICE_NAME}.timer"
SERVICE_FILE="/etc/systemd/system/${SERVICE_NAME}.service"
HEALTHCHECK_SERVICE_FILE="/etc/systemd/system/${HEALTHCHECK_SERVICE_NAME}.service"
HEALTHCHECK_TIMER_FILE="/etc/systemd/system/${HEALTHCHECK_TIMER_NAME}"
ENV_FILE="/etc/default/${SERVICE_NAME}"
CONFIG_DIR="/etc/sophos-wifi-client"
PURGE_CONFIG="${PURGE_CONFIG:-false}"

echo "Stopping and disabling ${SERVICE_NAME}..."
sudo systemctl stop "${SERVICE_NAME}" 2>/dev/null || true
sudo systemctl disable "${SERVICE_NAME}" 2>/dev/null || true
sudo systemctl stop "${HEALTHCHECK_TIMER_NAME}" 2>/dev/null || true
sudo systemctl disable "${HEALTHCHECK_TIMER_NAME}" 2>/dev/null || true

if [[ -f "${SERVICE_FILE}" ]]; then
  sudo rm -f "${SERVICE_FILE}"
fi
if [[ -f "${HEALTHCHECK_SERVICE_FILE}" ]]; then
  sudo rm -f "${HEALTHCHECK_SERVICE_FILE}"
fi
if [[ -f "${HEALTHCHECK_TIMER_FILE}" ]]; then
  sudo rm -f "${HEALTHCHECK_TIMER_FILE}"
fi

sudo systemctl daemon-reload

if [[ -d "${INSTALL_DIR}" ]]; then
  echo "Removing install dir: ${INSTALL_DIR}"
  sudo rm -rf "${INSTALL_DIR}"
fi

if [[ -f "${ENV_FILE}" ]]; then
  echo "Keeping env file: ${ENV_FILE}"
fi

if [[ "${PURGE_CONFIG}" == "true" ]]; then
  echo "Purging config directory: ${CONFIG_DIR}"
  sudo rm -rf "${CONFIG_DIR}"
else
  echo "Keeping config directory: ${CONFIG_DIR}"
  echo "Set PURGE_CONFIG=true if you want to remove it."
fi

echo "Uninstall complete."
