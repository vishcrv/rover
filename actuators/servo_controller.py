# actuators/servo_controller.py — Servo sweep control for obstacle scanning

import time
import threading
import RPi.GPIO as GPIO
from utils.config import (
    SERVO_PIN,
    SERVO_LEFT_ANGLE, SERVO_CENTER_ANGLE, SERVO_RIGHT_ANGLE,
    SERVO_SCAN_MIN, SERVO_SCAN_MAX,
    SERVO_SETTLE_TIME,
)

_pwm = None

# SG90/MG90S typical: 2.5% (0°) to 12.5% (180°)
_MIN_DUTY = 2.5
_MAX_DUTY = 12.5

# Sweeping state
_current_angle = 0 # 0 is straight forward
_sweep_thread = None
_stop_sweep_event = threading.Event()
_pause_sweep_event = threading.Event()
_SWEEP_STEP = 5       # degrees per tick
_SWEEP_DELAY = 0.05   # seconds per tick (adjust for speed)


def setup():
    """Initialize servo GPIO and center the servo."""
    global _pwm, _current_angle
    GPIO.setmode(GPIO.BCM)
    GPIO.setwarnings(False)
    GPIO.setup(SERVO_PIN, GPIO.OUT)
    _pwm = GPIO.PWM(SERVO_PIN, 50)  # 50 Hz for servo
    _pwm.start(0)
    look_center()


def _angle_to_duty(angle_rel_forward):
    """
    Convert relative angle to absolute duty cycle.
    0 degrees is forward (90 abs).
    -90 degrees is left (0 abs).
    +90 degrees is right (180 abs).
    """
    abs_angle = angle_rel_forward + 90
    abs_angle = max(0, min(180, abs_angle)) # clamp to 0-180
    return _MIN_DUTY + (abs_angle / 180) * (_MAX_DUTY - _MIN_DUTY)


def look_at(angle_rel_forward, wait_settle=True):
    """Rotate servo to a specific relative angle (-90 to +90)."""
    global _current_angle
    _current_angle = angle_rel_forward
    duty = _angle_to_duty(angle_rel_forward)
    _pwm.ChangeDutyCycle(duty)
    if wait_settle:
        time.sleep(SERVO_SETTLE_TIME)
        _pwm.ChangeDutyCycle(0)  # stop signal to prevent jitter


def look_left():
    """Point ultrasonic sensor left."""
    look_at(SERVO_SCAN_MIN)


def look_center():
    """Point ultrasonic sensor forward."""
    look_at(0)


def look_right():
    """Point ultrasonic sensor right."""
    look_at(SERVO_SCAN_MAX)


def get_current_angle():
    """Return the current relative angle of the servo."""
    return _current_angle


def _sweep_loop():
    """Continuously sweep the servo back and forth between SCAN_MIN and SCAN_MAX."""
    global _current_angle
    
    direction = 1  # 1 for right (increasing angle), -1 for left (decreasing)
    
    # Pre-calculate duty cycles to avoid jitter between steps in continuous motion
    while not _stop_sweep_event.is_set():
        if _pause_sweep_event.is_set():
            _pwm.ChangeDutyCycle(0) # stop jitter while paused
            time.sleep(0.1)
            continue
            
        next_angle = _current_angle + (direction * _SWEEP_STEP)
        
        if next_angle >= SERVO_SCAN_MAX:
            next_angle = SERVO_SCAN_MAX
            direction = -1
        elif next_angle <= SERVO_SCAN_MIN:
            next_angle = SERVO_SCAN_MIN
            direction = 1
            
        look_at(next_angle, wait_settle=False) # Don't sleep long, just continuous
        time.sleep(_SWEEP_DELAY)


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
        _sweep_thread.join(timeout=1.0)
    look_center()


def pause_sweep():
    """Temporarily pause the sweeping (e.g. during an avoidance maneuver)."""
    _pause_sweep_event.set()


def resume_sweep():
    """Resume a paused sweep."""
    _pause_sweep_event.clear()


def cleanup():
    """Center servo, stop PWM, release GPIO."""
    stop_sweep()
    if _pwm:
        _pwm.stop()
    GPIO.cleanup([SERVO_PIN])
