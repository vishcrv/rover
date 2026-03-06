# modules/servo.py — Servo sweep control for obstacle scanning

import time
import threading
import RPi.GPIO as GPIO
from config.settings import (
    SERVO_PIN,
    SERVO_LEFT_ANGLE, SERVO_CENTER_ANGLE, SERVO_RIGHT_ANGLE,
    SERVO_SETTLE_TIME, SERVO_SCAN_STEP, OBSTACLE_SCAN_SETTLE,
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
    
    # Determine sweep boundaries (works regardless of which angle is larger)
    sweep_min = min(SERVO_LEFT_ANGLE, SERVO_RIGHT_ANGLE)
    sweep_max = max(SERVO_LEFT_ANGLE, SERVO_RIGHT_ANGLE)
    direction = 1  # 1 = increasing angle, -1 = decreasing angle
    
    while not _stop_sweep_event.is_set():
        if _pause_sweep_event.is_set():
            _pwm.ChangeDutyCycle(0)  # stop jitter while paused
            time.sleep(0.1)
            continue
            
        next_angle = _current_angle + (direction * _SWEEP_STEP)
        
        if next_angle >= sweep_max:
            next_angle = sweep_max
            direction = -1
        elif next_angle <= sweep_min:
            next_angle = sweep_min
            direction = 1
            
        look_at(next_angle, wait_settle=False)
        time.sleep(_SWEEP_DELAY)


def full_scan():
    """Perform a discrete scan and return {angle: distance_cm}.
    
    Steps the servo from left to right in SERVO_SCAN_STEP increments,
    taking an ultrasonic reading at each position.
    """
    from modules import ultrasonic  # local import to avoid circular
    
    distances = {}
    
    # Determine scan range (step from left → right regardless of which is numerically larger)
    scan_start = SERVO_LEFT_ANGLE
    scan_end = SERVO_RIGHT_ANGLE
    step = -SERVO_SCAN_STEP if scan_start > scan_end else SERVO_SCAN_STEP
    
    angle = scan_start
    while True:
        look_at(angle, wait_settle=True)
        time.sleep(OBSTACLE_SCAN_SETTLE)
        dist = ultrasonic.get_distance()
        # Convert servo angle to relative degrees (0 = forward)
        relative = angle - SERVO_CENTER_ANGLE
        distances[relative] = dist
        
        # Check if we've reached or passed the end
        if step > 0 and angle >= scan_end:
            break
        if step < 0 and angle <= scan_end:
            break
        angle += step
        # Clamp to end
        if step > 0 and angle > scan_end:
            angle = scan_end
        elif step < 0 and angle < scan_end:
            angle = scan_end
    
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
