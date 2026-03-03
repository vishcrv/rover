# modules/gps_reader.py — GPS serial reading and NMEA parsing

import threading
import serial
from config.settings import GPS_SERIAL_PORT, GPS_BAUD_RATE, GPS_READ_INTERVAL

_serial = None
_lock = threading.Lock()
_latitude = None
_longitude = None
_running = False
_thread = None


def setup():
    """Open serial port and start background GPS reading thread."""
    global _serial, _running, _thread

    _serial = serial.Serial(GPS_SERIAL_PORT, GPS_BAUD_RATE, timeout=1)

    _running = True
    _thread = threading.Thread(target=_read_loop, daemon=True)
    _thread.start()


def _read_loop():
    """Continuously read NMEA sentences and update coordinates."""
    global _latitude, _longitude

    while _running:
        try:
            line = _serial.readline().decode("ascii", errors="ignore").strip()
        except (serial.SerialException, OSError):
            continue

        if not line:
            continue

        # Parse $GPGGA or $GPRMC — both contain lat/lon
        if line.startswith("$GPGGA") or line.startswith("$GNGGA"):
            coords = _parse_gpgga(line)
        elif line.startswith("$GPRMC") or line.startswith("$GNRMC"):
            coords = _parse_gprmc(line)
        else:
            continue

        if coords:
            with _lock:
                _latitude, _longitude = coords


def _parse_gpgga(sentence):
    """Parse $GPGGA sentence. Returns (lat, lon) or None."""
    try:
        parts = sentence.split(",")
        # parts[2]=lat, parts[3]=N/S, parts[4]=lon, parts[5]=E/W, parts[6]=fix
        fix = parts[6]
        if fix == "0":  # no fix
            return None

        lat = _nmea_to_decimal(parts[2], parts[3])
        lon = _nmea_to_decimal(parts[4], parts[5])
        return (lat, lon)
    except (IndexError, ValueError):
        return None


def _parse_gprmc(sentence):
    """Parse $GPRMC sentence. Returns (lat, lon) or None."""
    try:
        parts = sentence.split(",")
        # parts[2]=status (A=active, V=void)
        if parts[2] != "A":
            return None

        lat = _nmea_to_decimal(parts[3], parts[4])
        lon = _nmea_to_decimal(parts[5], parts[6])
        return (lat, lon)
    except (IndexError, ValueError):
        return None


def _nmea_to_decimal(raw, direction):
    """Convert NMEA coordinate (ddmm.mmmm) to decimal degrees.

    Example: '1234.5678', 'N' → 12.576130
    """
    if not raw or not direction:
        raise ValueError("empty coordinate")

    # Determine split: latitude has 2-digit degrees, longitude has 3-digit
    if direction in ("N", "S"):
        deg = float(raw[:2])
        minutes = float(raw[2:])
    else:  # E, W
        deg = float(raw[:3])
        minutes = float(raw[3:])

    decimal = deg + minutes / 60

    if direction in ("S", "W"):
        decimal = -decimal

    return round(decimal, 6)


def get_coordinates():
    """Return the latest GPS coordinates.

    Returns:
        (latitude, longitude) as floats, or (None, None) if no fix.
    """
    with _lock:
        return (_latitude, _longitude)


def has_fix():
    """Return True if valid GPS coordinates are available."""
    with _lock:
        return _latitude is not None and _longitude is not None


def cleanup():
    """Stop the reading thread and close the serial port."""
    global _running
    _running = False
    if _thread is not None:
        _thread.join(timeout=2)
    if _serial is not None and _serial.is_open:
        _serial.close()
