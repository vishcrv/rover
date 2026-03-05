# modules/obstacle.py — Obstacle avoidance logic (ultrasonic + servo + motor)

import time
from config.settings import (
    EMERGENCY_STOP_CM, AVOIDANCE_TRIGGER_CM,
    TURN_SPEED, TURN_DURATION, DEFAULT_SPEED,
)
from modules import ultrasonic, servo, motor
from config.settings import SERVO_CENTER_ANGLE

_BACKUP_TIME = 0.3  # seconds to reverse after emergency stop


def check_and_avoid():
    """Check for obstacles and maneuver around them based on active sweep angle.

    Returns:
        True  — obstacle was detected and avoidance was performed.
        False — path is clear, no action taken.
    """
    distance = ultrasonic.get_distance()

    if distance > AVOIDANCE_TRIGGER_CM:
        return False  # clear path

    # -- Obstacle within range --
    motor.stop()
    servo.pause_sweep()

    # Emergency: too close — back up first
    if distance <= EMERGENCY_STOP_CM:
        motor.backward(TURN_SPEED)
        time.sleep(_BACKUP_TIME)
        motor.stop()

    # Determine turn direction based on current sweep angle
    current_angle = servo.get_current_angle()
    
    # If the servo is looking left (angle < center), obstacle is on the left -> turn right
    # If the servo is looking right (angle > center), obstacle is on the right -> turn left
    if current_angle < SERVO_CENTER_ANGLE:
        motor.turn_right(TURN_SPEED)
    else:
        motor.turn_left(TURN_SPEED)

    time.sleep(TURN_DURATION)
    motor.stop()
    
    servo.resume_sweep()
    return True

