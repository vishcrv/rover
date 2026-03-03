# modules/servo.py — Servo sweep control for obstacle scanning

import time
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


def setup():
    """Initialize servo GPIO and center the servo."""
    global _pwm
    GPIO.setmode(GPIO.BCM)
    GPIO.setwarnings(False)
    GPIO.setup(SERVO_PIN, GPIO.OUT)
    _pwm = GPIO.PWM(SERVO_PIN, 50)  # 50 Hz for servo
    _pwm.start(0)
    look_center()


def _angle_to_duty(angle):
    """Convert angle (0–180) to duty cycle."""
    return _MIN_DUTY + (angle / 180) * (_MAX_DUTY - _MIN_DUTY)


def look_at(angle):
    """Rotate servo to a specific angle (0–180) and wait for it to settle."""
    duty = _angle_to_duty(angle)
    _pwm.ChangeDutyCycle(duty)
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


def cleanup():
    """Center servo, stop PWM, release GPIO."""
    look_center()
    _pwm.stop()
    GPIO.cleanup([SERVO_PIN])
