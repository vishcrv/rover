# actuators/motor_controller.py — Motor control (forward, backward, turn, stop)

import RPi.GPIO as GPIO
import time
from utils.config import (
    MOTOR_LEFT_FWD, MOTOR_LEFT_BWD,
    MOTOR_RIGHT_FWD, MOTOR_RIGHT_BWD,
    MOTOR_LEFT_PWM, MOTOR_RIGHT_PWM,
    PWM_FREQUENCY, DEFAULT_SPEED,
    SERVO_SCAN_MIN, SERVO_SCAN_MAX
)

_pwm_left = None
_pwm_right = None


def setup():
    """Initialize motor GPIO pins and PWM channels."""
    global _pwm_left, _pwm_right

    GPIO.setmode(GPIO.BCM)
    GPIO.setwarnings(False)

    # Direction pins
    for pin in (MOTOR_LEFT_FWD, MOTOR_LEFT_BWD,
                MOTOR_RIGHT_FWD, MOTOR_RIGHT_BWD):
        GPIO.setup(pin, GPIO.OUT)
        GPIO.output(pin, GPIO.LOW)

    # PWM speed pins
    GPIO.setup(MOTOR_LEFT_PWM, GPIO.OUT)
    GPIO.setup(MOTOR_RIGHT_PWM, GPIO.OUT)
    _pwm_left = GPIO.PWM(MOTOR_LEFT_PWM, PWM_FREQUENCY)
    _pwm_right = GPIO.PWM(MOTOR_RIGHT_PWM, PWM_FREQUENCY)
    _pwm_left.start(0)
    _pwm_right.start(0)


def _set_left(forward, speed):
    """Drive left motors. forward=True for forward, False for backward."""
    GPIO.output(MOTOR_LEFT_FWD, GPIO.HIGH if forward else GPIO.LOW)
    GPIO.output(MOTOR_LEFT_BWD, GPIO.LOW if forward else GPIO.HIGH)
    _pwm_left.ChangeDutyCycle(speed)


def _set_right(forward, speed):
    """Drive right motors. forward=True for forward, False for backward."""
    GPIO.output(MOTOR_RIGHT_FWD, GPIO.HIGH if forward else GPIO.LOW)
    GPIO.output(MOTOR_RIGHT_BWD, GPIO.LOW if forward else GPIO.HIGH)
    _pwm_right.ChangeDutyCycle(speed)


def forward(speed=DEFAULT_SPEED):
    """Both sides forward."""
    _set_left(True, speed)
    _set_right(True, speed)


def backward(speed=DEFAULT_SPEED):
    """Both sides backward."""
    _set_left(False, speed)
    _set_right(False, speed)


def turn_left(speed=DEFAULT_SPEED):
    """Pivot left — right side forward, left side backward."""
    _set_left(False, speed)
    _set_right(True, speed)


def turn_right(speed=DEFAULT_SPEED):
    """Pivot right — left side forward, right side backward."""
    _set_left(True, speed)
    _set_right(False, speed)


def turn_dynamic(obstacle_angle, base_speed=DEFAULT_SPEED):
    """
    Dynamic Turning.
    Turning should not be binary.
    Instead:
    - If obstacle detected at +45°, turn right proportionally
    - If obstacle detected at -30°, turn left proportionally

    obstacle_angle relative to forward (0). Range: SERVO_SCAN_MIN to SERVO_SCAN_MAX (-60 to +60).
    A positive angle means the obstacle is to the right, so we turn left.
    A negative angle means the obstacle is to the left, so we turn right.

    To clear it smoothly, we vary the speed proportionally.
    """
    # Normalize proportional factor based on max scanning range (60 deg)
    # The farther off-center the obstacle is, the stronger we might want to turn away from it.
    abs_angle = abs(obstacle_angle)
    max_angle = max(abs(SERVO_SCAN_MIN), abs(SERVO_SCAN_MAX))

    # Turn intensity ranges from 0.5 to 1.0 depending on angle
    turn_intensity = 0.5 + 0.5 * (abs_angle / max_angle) if max_angle > 0 else 1.0

    speed = max(20, min(100, base_speed * turn_intensity))

    if obstacle_angle > 0:
        # Obstacle is on right side -> turn left
        turn_left(speed)
    else:
        # Obstacle is on left side -> turn right
        turn_right(speed)


def stop():
    """Stop all motors immediately."""
    GPIO.output(MOTOR_LEFT_FWD, GPIO.LOW)
    GPIO.output(MOTOR_LEFT_BWD, GPIO.LOW)
    GPIO.output(MOTOR_RIGHT_FWD, GPIO.LOW)
    GPIO.output(MOTOR_RIGHT_BWD, GPIO.LOW)
    _pwm_left.ChangeDutyCycle(0)
    _pwm_right.ChangeDutyCycle(0)


def cleanup():
    """Stop motors, release PWM, and clean up GPIO."""
    stop()
    if _pwm_left:
        _pwm_left.stop()
    if _pwm_right:
        _pwm_right.stop()
    GPIO.cleanup([
        MOTOR_LEFT_FWD, MOTOR_LEFT_BWD,
        MOTOR_RIGHT_FWD, MOTOR_RIGHT_BWD,
        MOTOR_LEFT_PWM, MOTOR_RIGHT_PWM,
    ])
