# modules/transmitter.py — Send image + GPS data to PC

import os
import logging
import requests
from config.settings import (
    PC_SERVER_IP, PC_SERVER_PORT,
    PC_DETECTION_ENDPOINT, TRANSMIT_TIMEOUT,
)

log = logging.getLogger(__name__)

_MAX_RETRIES = 1


def _build_url():
    return f"http://{PC_SERVER_IP}:{PC_SERVER_PORT}{PC_DETECTION_ENDPOINT}"


def send_detection(image_path, latitude, longitude, timestamp):
    """Send detection data to the PC server via HTTP POST.

    Args:
        image_path: Full path to the captured image file.
        latitude:   GPS latitude (float or None).
        longitude:  GPS longitude (float or None).
        timestamp:  ISO format timestamp string.

    Returns:
        True if the server acknowledged (200 OK), False otherwise.
    """
    url = _build_url()

    data = {
        "latitude": str(latitude) if latitude is not None else "",
        "longitude": str(longitude) if longitude is not None else "",
        "timestamp": timestamp,
    }

    for attempt in range(_MAX_RETRIES + 1):
        try:
            with open(image_path, "rb") as img:
                files = {"image": (os.path.basename(image_path), img, "image/jpeg")}
                resp = requests.post(url, data=data, files=files, timeout=TRANSMIT_TIMEOUT)

            if resp.status_code == 200:
                log.info("Detection sent successfully")
                return True

            log.warning("Server returned %d: %s", resp.status_code, resp.text)

        except requests.ConnectionError:
            log.warning("Connection failed (attempt %d/%d)", attempt + 1, _MAX_RETRIES + 1)
        except requests.Timeout:
            log.warning("Request timed out (attempt %d/%d)", attempt + 1, _MAX_RETRIES + 1)
        except OSError as e:
            log.error("File error: %s", e)
            return False

    log.error("Failed to send detection after %d attempts", _MAX_RETRIES + 1)
    return False
