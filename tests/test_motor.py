# tests/test_motor.py — Manual validation for motor module
# Run on Raspberry Pi: python -m tests.test_motor

import time
from modules import motor
from config.settings import DEFAULT_SPEED, TURN_SPEED

DRIVE_TIME = 2   # seconds per movement test


def run():
    print("=== Motor Validation Test ===\n")
    motor.setup()

    try:
        print(f"[1] Forward at speed {DEFAULT_SPEED} for {DRIVE_TIME}s...")
        motor.forward()
        time.sleep(DRIVE_TIME)
        motor.stop()
        time.sleep(1)

        print(f"[2] Backward at speed {DEFAULT_SPEED} for {DRIVE_TIME}s...")
        motor.backward()
        time.sleep(DRIVE_TIME)
        motor.stop()
        time.sleep(1)

        print(f"[3] Turn left at speed {TURN_SPEED} for {DRIVE_TIME}s...")
        motor.turn_left(TURN_SPEED)
        time.sleep(DRIVE_TIME)
        motor.stop()
        time.sleep(1)

        print(f"[4] Turn right at speed {TURN_SPEED} for {DRIVE_TIME}s...")
        motor.turn_right(TURN_SPEED)
        time.sleep(DRIVE_TIME)
        motor.stop()
        time.sleep(1)

        print("[5] Speed ramp — forward 30 → 100...")
        for speed in range(30, 101, 10):
            print(f"     speed={speed}")
            motor.forward(speed)
            time.sleep(0.5)
        motor.stop()
        time.sleep(1)

        print("[6] Stop test — verify motors halt immediately...")
        motor.forward()
        time.sleep(0.5)
        motor.stop()

        print("\n=== All tests complete ===")

    except KeyboardInterrupt:
        print("\nInterrupted — stopping motors.")
    finally:
        motor.cleanup()


if __name__ == "__main__":
    run()
