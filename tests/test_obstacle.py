# tests/test_obstacle.py — Validation for ultrasonic, servo, and obstacle avoidance
# Run on Raspberry Pi: python -m tests.test_obstacle

import time
from modules import ultrasonic, servo, motor


def test_ultrasonic():
    """Read distance 10 times and print results."""
    print("=== Ultrasonic Sensor Test ===\n")
    ultrasonic.setup()
    for i in range(10):
        d = ultrasonic.get_distance()
        print(f"  Reading {i+1}: {d:.1f} cm")
        time.sleep(0.5)
    print()


def test_servo():
    """Sweep servo left → center → right → center."""
    print("=== Servo Sweep Test ===\n")
    servo.setup()

    print("  Looking LEFT...")
    servo.look_left()
    time.sleep(1)

    print("  Looking CENTER...")
    servo.look_center()
    time.sleep(1)

    print("  Looking RIGHT...")
    servo.look_right()
    time.sleep(1)

    print("  Back to CENTER...")
    servo.look_center()
    print()


def test_scan():
    """Scan left/center/right and report distances at each position."""
    print("=== Directional Scan Test ===\n")
    servo.setup()
    ultrasonic.setup()

    servo.look_left()
    left = ultrasonic.get_distance()
    print(f"  Left:   {left:.1f} cm")

    servo.look_center()
    center = ultrasonic.get_distance()
    print(f"  Center: {center:.1f} cm")

    servo.look_right()
    right = ultrasonic.get_distance()
    print(f"  Right:  {right:.1f} cm")

    servo.look_center()
    print()


def test_obstacle_avoidance():
    """Run obstacle avoidance in a loop — rover moves forward and avoids obstacles."""
    from modules.obstacle import check_and_avoid

    print("=== Obstacle Avoidance Live Test ===")
    print("  Rover will move forward and avoid obstacles.")
    print("  Press Ctrl+C to stop.\n")

    motor.setup()
    servo.setup()
    ultrasonic.setup()

    try:
        while True:
            avoided = check_and_avoid()
            if avoided:
                print("  [!] Obstacle avoided")
            else:
                motor.forward()
            time.sleep(0.1)
    except KeyboardInterrupt:
        print("\n  Stopped.")
    finally:
        motor.stop()


def run():
    print("Select test:")
    print("  1 — Ultrasonic readings")
    print("  2 — Servo sweep")
    print("  3 — Directional scan (servo + ultrasonic)")
    print("  4 — Live obstacle avoidance (motors active)")

    choice = input("\nEnter choice (1-4): ").strip()

    try:
        if choice == "1":
            test_ultrasonic()
        elif choice == "2":
            test_servo()
        elif choice == "3":
            test_scan()
        elif choice == "4":
            test_obstacle_avoidance()
        else:
            print("Invalid choice.")
    finally:
        # Clean up whichever modules were initialized
        try:
            motor.cleanup()
        except Exception:
            pass
        try:
            servo.cleanup()
        except Exception:
            pass
        try:
            ultrasonic.cleanup()
        except Exception:
            pass


if __name__ == "__main__":
    run()
