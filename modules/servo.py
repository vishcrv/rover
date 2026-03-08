# modules/servo.py — Servo sweep control using pigpio (hardware PWM)

import time
import threading
import pigpio
from config.settings import (
    SERVO_PIN,
    SERVO_LEFT_PW, SERVO_CENTER_PW, SERVO_RIGHT_PW,
    SERVO_MOVE_DELAY, SERVO_SCAN_STEP_PW, SERVO_SCAN_SETTLE,
)

_pi = None
_current_pw = SERVO_CENTER_PW

# Sweeping state
_sweep_thread = None
_stop_sweep_event = threading.Event()
_pause_sweep_event = threading.Event()


def setup():
    """Initialize pigpio connection and center the servo."""
    global _pi, _current_pw
    _pi = pigpio.pi()
    if not _pi.connected:
        raise RuntimeError(
            "pigpiod not running! Start with: sudo systemctl start pigpiod"
        )
    _current_pw = SERVO_CENTER_PW
    look_center()


def _move(pulsewidth):
    """Set servo to a pulsewidth, hold for MOVE_DELAY, then stop signal."""
    global _current_pw
    _current_pw = pulsewidth
    _pi.set_servo_pulsewidth(SERVO_PIN, pulsewidth)
    time.sleep(SERVO_MOVE_DELAY)
    _pi.set_servo_pulsewidth(SERVO_PIN, 0)  # stop signal to prevent jitter
    time.sleep(0.05)


def look_at(pulsewidth, wait=True):
    """Rotate servo to a specific pulsewidth (μs).

    Args:
        pulsewidth: Target position in microseconds (typically 1000–2000).
        wait: If True, hold position for MOVE_DELAY then stop signal.
              If False, just set position immediately (for continuous sweep).
    """
    global _current_pw
    _current_pw = pulsewidth
    _pi.set_servo_pulsewidth(SERVO_PIN, pulsewidth)
    if wait:
        time.sleep(SERVO_MOVE_DELAY)
        _pi.set_servo_pulsewidth(SERVO_PIN, 0)
        time.sleep(0.05)


def look_left():
    """Point ultrasonic sensor left."""
    look_at(SERVO_LEFT_PW)


def look_center():
    """Point ultrasonic sensor forward."""
    look_at(SERVO_CENTER_PW)


def look_right():
    """Point ultrasonic sensor right."""
    look_at(SERVO_RIGHT_PW)


def get_current_pw():
    """Return the current pulsewidth of the servo."""
    return _current_pw


def _sweep_loop():
    """Continuously sweep the servo between left and right limits."""
    while not _stop_sweep_event.is_set():
        if _pause_sweep_event.is_set():
            _pi.set_servo_pulsewidth(SERVO_PIN, 0)
            time.sleep(0.1)
            continue

        _move(SERVO_LEFT_PW)
        if _stop_sweep_event.is_set() or _pause_sweep_event.is_set():
            break

        _move(SERVO_RIGHT_PW)
        if _stop_sweep_event.is_set() or _pause_sweep_event.is_set():
            break


def full_scan():
    """Perform a discrete scan and return {pw_offset: distance_cm}.

    Steps the servo across its range in SERVO_SCAN_STEP_PW increments,
    taking an ultrasonic reading at each position.

    Returns a dict where keys are pulsewidth offsets from center
    (negative = right of center, positive = left of center).
    """
    from modules import ultrasonic  # local import to avoid circular

    distances = {}

    # Determine scan direction
    pw_min = min(SERVO_LEFT_PW, SERVO_RIGHT_PW)
    pw_max = max(SERVO_LEFT_PW, SERVO_RIGHT_PW)

    pw = pw_min
    while pw <= pw_max:
        look_at(pw, wait=True)
        time.sleep(SERVO_SCAN_SETTLE)
        dist = ultrasonic.get_distance()
        # Offset relative to center (positive = left, negative = right)
        offset = pw - SERVO_CENTER_PW
        distances[offset] = dist
        pw += SERVO_SCAN_STEP_PW

    look_center()
    return distances


def start_sweep():
    """Start the background sweep thread."""
    global _sweep_thread
    if _sweep_thread is None or not _sweep_thread.is_alive():
        _stop_sweep_event.clear()
        _pause_sweep_event.clear()
        _sweep_thread = threading.Thread(target=_sweep_loop, daemon=True)
        _sweep_thread.start()


def stop_sweep():
    """Stop the background sweep thread entirely."""
    _stop_sweep_event.set()
    if _sweep_thread is not None:
        _sweep_thread.join(timeout=2.0)
    look_center()


def pause_sweep():
    """Temporarily pause the sweeping (e.g. during an avoidance maneuver)."""
    _pause_sweep_event.set()


def resume_sweep():
    """Resume a paused sweep."""
    _pause_sweep_event.clear()


def cleanup():
    """Center servo, stop signal, release pigpio."""
    stop_sweep()
    _pi.set_servo_pulsewidth(SERVO_PIN, SERVO_CENTER_PW)
    time.sleep(0.5)
    _pi.set_servo_pulsewidth(SERVO_PIN, 0)
    _pi.stop()
