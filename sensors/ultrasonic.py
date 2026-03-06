# sensors/ultrasonic.py — Distance measurement via HC-SR04

import time
import threading
import RPi.GPIO as GPIO
from utils.config import (
    ULTRASONIC_TRIG, ULTRASONIC_ECHO,
    ULTRASONIC_TIMEOUT, ULTRASONIC_SAMPLES,
)

_running = False
_thread = None
_latest_distance = 999
_lock = threading.Lock()


def setup():
    """Initialize ultrasonic sensor GPIO pins and start sampling thread."""
    global _running, _thread
    GPIO.setmode(GPIO.BCM)
    GPIO.setwarnings(False)
    GPIO.setup(ULTRASONIC_TRIG, GPIO.OUT)
    GPIO.setup(ULTRASONIC_ECHO, GPIO.IN)
    GPIO.output(ULTRASONIC_TRIG, GPIO.LOW)
    time.sleep(0.05)  # let sensor settle
    
    _running = True
    _thread = threading.Thread(target=_sampling_loop, daemon=True)
    _thread.start()


def _single_reading():
    """Take one distance reading. Returns distance in cm or None on timeout."""
    # Send 10µs trigger pulse
    GPIO.output(ULTRASONIC_TRIG, GPIO.HIGH)
    time.sleep(0.00001)
    GPIO.output(ULTRASONIC_TRIG, GPIO.LOW)

    # Wait for echo to go HIGH (pulse sent)
    pulse_start = time.time()
    deadline = pulse_start + ULTRASONIC_TIMEOUT
    while GPIO.input(ULTRASONIC_ECHO) == GPIO.LOW:
        pulse_start = time.time()
        if pulse_start > deadline:
            return None

    # Wait for echo to go LOW (pulse returned)
    pulse_end = time.time()
    deadline = pulse_end + ULTRASONIC_TIMEOUT
    while GPIO.input(ULTRASONIC_ECHO) == GPIO.HIGH:
        pulse_end = time.time()
        if pulse_end > deadline:
            return None

    # Distance = (time × speed_of_sound) / 2
    duration = pulse_end - pulse_start
    distance = (duration * 34300) / 2  # cm
    return distance


def _sampling_loop():
    """Continuously sample distance to provide latest non-blocking reading."""
    global _latest_distance
    while _running:
        readings = []
        for _ in range(ULTRASONIC_SAMPLES):
            if not _running:
                break
            d = _single_reading()
            if d is not None and 2 < d < 400:  # HC-SR04 valid range
                readings.append(d)
            time.sleep(0.01)  # small gap between samples

        with _lock:
            if not readings:
                _latest_distance = 999  # no valid reading — assume clear path
            else:
                _latest_distance = sum(readings) / len(readings)


def get_distance():
    """Return the latest average distance asynchronously. Very fast, does not block."""
    with _lock:
        return _latest_distance


def cleanup():
    """Release ultrasonic GPIO pins."""
    global _running
    _running = False
    if _thread is not None:
        _thread.join(timeout=1.0)
    GPIO.cleanup([ULTRASONIC_TRIG, ULTRASONIC_ECHO])
