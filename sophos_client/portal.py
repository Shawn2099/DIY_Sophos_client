import requests
import time
import logging
import xml.etree.ElementTree as ET


LOGGER = logging.getLogger(__name__)
SESSION = requests.Session()


def _headers():
    return {"User-Agent": "Mozilla/5.0"}


def _request_timeout(cfg):
    return cfg.get("request_timeout", 4)


def _base_url(cfg):
    return cfg["portal_url"].rstrip("/")


def _extract_status(response_text):
    try:
        root = ET.fromstring(response_text)
        status = root.findtext("status")
        if status:
            return status.strip().upper()
    except ET.ParseError:
        pass

    upper_text = response_text.upper()
    if "LIVE" in upper_text:
        return "LIVE"
    if "LOGIN" in upper_text:
        return "LOGIN"
    return None


def _extract_message(response_text):
    try:
        root = ET.fromstring(response_text)
        message = root.findtext("message")
        if message:
            return message.strip()
    except ET.ParseError:
        pass
    return None


def _post(cfg, endpoint, data):
    return SESSION.post(
        _base_url(cfg) + endpoint,
        data=data,
        headers=_headers(),
        timeout=_request_timeout(cfg),
    )

def portal_state(cfg):

    ts=str(int(time.time()*1000))

    try:
        r = _post(
            cfg,
            "/login.xml",
            {
                "mode":191,
                "username":cfg["username"],
                "password":cfg["password"],
                "a":ts,
                "producttype":0
            },
        )
    except requests.RequestException:
        LOGGER.warning("Portal state check failed", exc_info=True)
        return "UNKNOWN"

    status = _extract_status(r.text)

    if status == "LIVE":
        return "AUTHENTICATED"

    if status == "LOGIN":
        return "AUTH_REQUIRED"

    LOGGER.warning("Unknown portal state response: %s", r.text[:200])

    return "UNKNOWN"


def login(cfg):

    ts=str(int(time.time()*1000))

    try:
        r = _post(
            cfg,
            "/login.xml",
            {
                "mode":191,
                "username":cfg["username"],
                "password":cfg["password"],
                "a":ts,
                "producttype":0
            },
        )
    except requests.RequestException:
        LOGGER.warning("Login request failed", exc_info=True)
        return False

    status = _extract_status(r.text)
    ok = status == "LIVE"
    if not ok:
        message = _extract_message(r.text)
        LOGGER.warning("Login did not return LIVE status=%s message=%s", status, message)
    return ok


def logout(cfg):

    ts=str(int(time.time()*1000))

    try:
        r = _post(
            cfg,
            "/logout.xml",
            {
                "mode":193,
                "username":cfg["username"],
                "a":ts,
                "producttype":0
            },
        )
    except requests.RequestException:
        LOGGER.warning("Logout request failed", exc_info=True)
        return False

    status = _extract_status(r.text)
    ok = status == "LOGIN"
    if not ok:
        message = _extract_message(r.text)
        LOGGER.warning("Logout did not return LOGIN status=%s message=%s", status, message)
    return ok