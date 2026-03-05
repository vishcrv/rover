# modules/servo.py — Servo sweep control for obstacle scanning

import time
import threading
import RPi.GPIO as GPIO
from config.settings import (
    SERVO_PIN,
    SERVO_LEFT_ANGLE, SERVO_CENTER_ANGLE, SERVO_RIGHT_ANGLE,
    SERVO_SETTLE_TIME,
)

_pwm = None

# SG90/MG90S typical: 2.5% (0°) to 12.5% (180°)
_MIN_DUTY = 2.5
_MAX_DUTY = 12.5

# Sweeping state
_current_angle = SERVO_CENTER_ANGLE
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
    _current_angle = SERVO_CENTER_ANGLE
    look_center()


def _angle_to_duty(angle):
    """Convert angle (0–180) to duty cycle."""
    return _MIN_DUTY + (angle / 180) * (_MAX_DUTY - _MIN_DUTY)


def look_at(angle, wait_settle=True):
    """Rotate servo to a specific angle (0–180)."""
    global _current_angle
    _current_angle = angle
    duty = _angle_to_duty(angle)
    _pwm.ChangeDutyCycle(duty)
    if wait_settle:
        time.sleep(SERVO_SETTLE_TIME)
        _pwm.ChangeDutyCycle(0)  # stop signal to prevent jitter


def look_left():
    """Point ultrasonic sensor left."""
    look_at(SERVO_LEFT_ANGLE)


def look_center():
    """Point ultrasonic sensor forward."""
    look_at(SERVO_CENTER_ANGLE)


def look_right():
    """Point ultrasonic sensor right."""
    look_at(SERVO_RIGHT_ANGLE)


def get_current_angle():
    """Return the current angle of the servo."""
    return _current_angle


def _sweep_loop():
    """Continuously sweep the servo back and forth."""
    global _current_angle
    
    direction = 1  # 1 for right (increasing angle), -1 for left (decreasing)
    
    # Pre-calculate duty cycles to avoid jitter between steps in continuous motion
    while not _stop_sweep_event.is_set():
        if _pause_sweep_event.is_set():
            _pwm.ChangeDutyCycle(0) # stop jitter while paused
            time.sleep(0.1)
            continue
            
        next_angle = _current_angle + (direction * _SWEEP_STEP)
        
        if next_angle >= SERVO_RIGHT_ANGLE:
            next_angle = SERVO_RIGHT_ANGLE
            direction = -1
        elif next_angle <= SERVO_LEFT_ANGLE:
            next_angle = SERVO_LEFT_ANGLE
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
    _pwm.stop()
    GPIO.cleanup([SERVO_PIN])
