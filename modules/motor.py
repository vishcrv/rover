# modules/motor.py — Motor control (forward, backward, turn, stop)

import RPi.GPIO as GPIO
from config.settings import (
    MOTOR_LEFT_FWD, MOTOR_LEFT_BWD,
    MOTOR_RIGHT_FWD, MOTOR_RIGHT_BWD,
    MOTOR_LEFT_PWM, MOTOR_RIGHT_PWM,
    PWM_FREQUENCY, DEFAULT_SPEED,
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
    _pwm_left.stop()
    _pwm_right.stop()
    GPIO.cleanup([
        MOTOR_LEFT_FWD, MOTOR_LEFT_BWD,
        MOTOR_RIGHT_FWD, MOTOR_RIGHT_BWD,
        MOTOR_LEFT_PWM, MOTOR_RIGHT_PWM,
    ])
