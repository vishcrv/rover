# tests/test_detection.py — Validation for camera and red object detection
# Run on Raspberry Pi: python -m tests.test_detection

import time
import cv2
from sensors import camera_detection as camera
from sensors import camera_detection as detector


def test_camera_feed():
    """Capture and display a few frames to verify camera works."""
    print("=== Camera Feed Test ===\n")
    camera.setup()
    time.sleep(1)  # let camera warm up

    for i in range(5):
        frame = camera.get_frame()
        if frame is not None:
            print(f"  Frame {i+1}: shape={frame.shape}, dtype={frame.dtype}")
        else:
            print(f"  Frame {i+1}: None (not ready)")
        time.sleep(0.5)
    print()


def test_capture_image():
    """Capture a high-res still image."""
    print("=== Image Capture Test ===\n")
    camera.setup()
    time.sleep(1)

    path = camera.capture_image("test_capture.jpg")
    print(f"  Image saved to: {path}\n")


def test_red_detection():
    """Continuously check for red objects — prints detection status."""
    print("=== Red Detection Live Test ===")
    print("  Point camera at a red object.")
    print("  Press Ctrl+C to stop.\n")

    camera.setup()
    time.sleep(1)

    try:
        while True:
            frame = camera.get_frame()
            if frame is None:
                continue

            detected, contour = detector.detect_red(frame)
            if detected:
                area = cv2.contourArea(contour)
                x, y, w, h = cv2.boundingRect(contour)
                print(f"  RED DETECTED — area={area:.0f}px  bbox=({x},{y},{w},{h})")
            else:
                print("  . no red")

            time.sleep(0.2)
    except KeyboardInterrupt:
        print("\n  Stopped.")


def test_confirmed_detection():
    """Test multi-frame confirmation logic."""
    print("=== Confirmed Detection Test ===")
    print(f"  Need {detector.DETECTION_CONFIRM_FRAMES} consecutive frames.")
    print("  Press Ctrl+C to stop.\n")

    camera.setup()
    detector.reset()
    time.sleep(1)

    try:
        while True:
            frame = camera.get_frame()
            if frame is None:
                continue

            confirmed = detector.check_confirmed(frame)
            count = detector.get_consecutive_count()

            if confirmed:
                print(f"  >>> CONFIRMED ({count} frames) — detection is stable!")
                detector.reset()
                time.sleep(2)
            elif count > 0:
                print(f"  detecting... ({count}/{detector.DETECTION_CONFIRM_FRAMES})")
            else:
                print("  . no red")

            time.sleep(0.1)
    except KeyboardInterrupt:
        print("\n  Stopped.")


def run():
    print("Select test:")
    print("  1 — Camera feed (check frames)")
    print("  2 — Capture still image")
    print("  3 — Red detection (live)")
    print("  4 — Confirmed detection (multi-frame)")

    choice = input("\nEnter choice (1-4): ").strip()

    try:
        if choice == "1":
            test_camera_feed()
        elif choice == "2":
            test_capture_image()
        elif choice == "3":
            test_red_detection()
        elif choice == "4":
            test_confirmed_detection()
        else:
            print("Invalid choice.")
    finally:
        camera.cleanup()


if __name__ == "__main__":
    run()
