# modules/ultrasonic.py — Distance measurement via HC-SR04

import time
import RPi.GPIO as GPIO
from config.settings import (
    ULTRASONIC_TRIG, ULTRASONIC_ECHO,
    ULTRASONIC_TIMEOUT, ULTRASONIC_SAMPLES,
)


def setup():
    """Initialize ultrasonic sensor GPIO pins."""
    GPIO.setmode(GPIO.BCM)
    GPIO.setwarnings(False)
    GPIO.setup(ULTRASONIC_TRIG, GPIO.OUT)
    GPIO.setup(ULTRASONIC_ECHO, GPIO.IN)
    GPIO.output(ULTRASONIC_TRIG, GPIO.LOW)
    time.sleep(0.05)  # let sensor settle


def _single_reading():
    """Take one distance reading. Returns distance in cm or None on timeout."""
    # Send 10µs trigger pulse
    GPIO.output(ULTRASONIC_TRIG, GPIO.HIGH)
    time.sleep(0.00001)
    GPIO.output(ULTRASONIC_TRIG, GPIO.LOW)

    # Wait for echo to go HIGH (pulse sent)
    deadline = time.time() + ULTRASONIC_TIMEOUT
    while GPIO.input(ULTRASONIC_ECHO) == GPIO.LOW:
        pulse_start = time.time()
        if pulse_start > deadline:
            return None

    # Wait for echo to go LOW (pulse returned)
    deadline = time.time() + ULTRASONIC_TIMEOUT
    while GPIO.input(ULTRASONIC_ECHO) == GPIO.HIGH:
        pulse_end = time.time()
        if pulse_end > deadline:
            return None

    # Distance = (time × speed_of_sound) / 2
    duration = pulse_end - pulse_start
    distance = (duration * 34300) / 2  # cm
    return distance


def get_distance():
    """Return averaged distance in cm. Filters out failed readings.

    Returns a large value (999) if all readings fail (no obstacle / sensor error).
    """
    readings = []
    for _ in range(ULTRASONIC_SAMPLES):
        d = _single_reading()
        if d is not None and 2 < d < 400:  # HC-SR04 valid range
            readings.append(d)
        time.sleep(0.01)  # small gap between samples

    if not readings:
        return 999  # no valid reading — assume clear path

    return sum(readings) / len(readings)


def cleanup():
    """Release ultrasonic GPIO pins."""
    GPIO.cleanup([ULTRASONIC_TRIG, ULTRASONIC_ECHO])
