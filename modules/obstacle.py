# modules/obstacle.py — Obstacle avoidance logic (ultrasonic + servo + motor)

import time
import logging
from config.settings import (
    EMERGENCY_STOP_CM, AVOIDANCE_TRIGGER_CM,
    TURN_SPEED, TURN_DURATION,
)
from modules import ultrasonic, servo, motor

log = logging.getLogger("obstacle")

_BACKUP_TIME = 0.3  # seconds to reverse after emergency stop


def check_and_avoid():
    """Check for obstacles and perform intelligent avoidance.

    Returns:
        True  — obstacle was detected and avoidance was performed.
        False — path is clear, no action taken.
    """
    distance = ultrasonic.get_distance()

    if distance > AVOIDANCE_TRIGGER_CM:
        return False  # clear path

    # -- Obstacle within range --
    motor.stop()
    servo.stop_sweep()
    log.info("Obstacle at %.1f cm — stopping and scanning.", distance)

    # Emergency: too close — back up first
    if distance <= EMERGENCY_STOP_CM:
        log.info("Emergency backup!")
        motor.backward(TURN_SPEED)
        time.sleep(_BACKUP_TIME)
        motor.stop()

    # Perform a full scan to find the best escape direction
    distances = servo.full_scan()
    log.info("Scan results: %s", distances)

    # Pick the direction with the longest clear distance
    # Keys are pw offsets from center (positive = left, negative = right)
    best_offset = 0
    best_dist = -1
    for offset, dist in distances.items():
        if dist > best_dist:
            best_dist = dist
            best_offset = offset

    log.info("Best direction: %+d μs offset (%.1f cm)", best_offset, best_dist)

    if best_dist > AVOIDANCE_TRIGGER_CM:
        # Turn toward the best direction
        # best_offset: positive = left of center, negative = right of center
        if best_offset > 0:
            motor.turn_left(TURN_SPEED)
        elif best_offset < 0:
            motor.turn_right(TURN_SPEED)

        # Turn duration proportional to how far off-center
        turn_time = TURN_DURATION * (abs(best_offset) / 80.0)
        turn_time = max(turn_time, 0.2)  # minimum turn
        time.sleep(turn_time)
        motor.stop()
    else:
        # No clear path found — reverse more and try again next cycle
        log.warning("No clear path found, reversing further.")
        motor.backward(TURN_SPEED)
        time.sleep(0.5)
        motor.stop()

    # Resume sweeping
    servo.start_sweep()
    return True
