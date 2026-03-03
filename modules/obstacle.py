# modules/obstacle.py — Obstacle avoidance logic (ultrasonic + servo + motor)

import time
from config.settings import (
    EMERGENCY_STOP_CM, AVOIDANCE_TRIGGER_CM,
    TURN_SPEED, TURN_DURATION, DEFAULT_SPEED,
)
from modules import ultrasonic, servo, motor

_BACKUP_TIME = 0.3  # seconds to reverse after emergency stop


def check_and_avoid():
    """Check for obstacles and maneuver around them.

    Returns:
        True  — obstacle was detected and avoidance was performed.
        False — path is clear, no action taken.
    """
    distance = ultrasonic.get_distance()

    if distance > AVOIDANCE_TRIGGER_CM:
        return False  # clear path

    # -- Obstacle within range --
    motor.stop()

    # Emergency: too close — back up first
    if distance <= EMERGENCY_STOP_CM:
        motor.backward(TURN_SPEED)
        time.sleep(_BACKUP_TIME)
        motor.stop()

    # Scan left and right to find best direction
    servo.look_left()
    left_distance = ultrasonic.get_distance()

    servo.look_right()
    right_distance = ultrasonic.get_distance()

    servo.look_center()  # reset for forward sensing

    # Turn toward the side with more clearance
    if left_distance >= right_distance:
        motor.turn_left(TURN_SPEED)
    else:
        motor.turn_right(TURN_SPEED)

    time.sleep(TURN_DURATION)
    motor.stop()

    return True
