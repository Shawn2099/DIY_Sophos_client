#!/usr/bin/env bash
set -euo pipefail

SERVICE_NAME="${1:-sophos-wifi-client}"
RESTART_THRESHOLD="${HEALTHCHECK_RESTART_THRESHOLD:-6}"

if ! [[ "${RESTART_THRESHOLD}" =~ ^[0-9]+$ ]]; then
  RESTART_THRESHOLD=6
fi

SERVICE_STATE="$(systemctl is-active "${SERVICE_NAME}" 2>/dev/null || true)"
RESTART_COUNT="$(systemctl show "${SERVICE_NAME}" --property NRestarts --value 2>/dev/null || echo 0)"

if ! [[ "${RESTART_COUNT}" =~ ^[0-9]+$ ]]; then
  RESTART_COUNT=0
fi

if [[ "${SERVICE_STATE}" != "active" ]]; then
  logger -t "${SERVICE_NAME}-healthcheck" "ALERT: service state is '${SERVICE_STATE}'"
  echo "ALERT: ${SERVICE_NAME} state=${SERVICE_STATE}"
  exit 1
fi

if (( RESTART_COUNT >= RESTART_THRESHOLD )); then
  logger -t "${SERVICE_NAME}-healthcheck" "ALERT: restart count ${RESTART_COUNT} >= threshold ${RESTART_THRESHOLD}"
  echo "ALERT: ${SERVICE_NAME} restart_count=${RESTART_COUNT} threshold=${RESTART_THRESHOLD}"
  exit 1
fi

echo "OK: ${SERVICE_NAME} active restart_count=${RESTART_COUNT} threshold=${RESTART_THRESHOLD}"
