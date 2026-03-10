# tests/test_detection.py — Validation for camera and leaf detection
# Run on Raspberry Pi: python -m tests.test_detection

import time
import cv2
from modules import camera
from modules import detector
from config.settings import DETECTION_CONFIRM_FRAMES


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


def test_leaf_detection():
    """Continuously check for leaf-like structures — prints detection status."""
    print("=== Leaf Detection Live Test ===")
    print("  Point camera at a leaf.")
    print("  Press Ctrl+C to stop.\n")

    camera.setup()
    time.sleep(1)

    try:
        while True:
            frame = camera.get_frame()
            if frame is None:
                continue

            leaves = detector.detect_leaves(frame)
            if leaves:
                for cnt, feat in leaves:
                    x, y, w, h = feat["bbox"]
                    print(
                        f"  LEAF DETECTED — area={feat['area']:.0f}px "
                        f"ar={feat['aspect_ratio']:.2f} "
                        f"sol={feat['solidity']:.2f} "
                        f"circ={feat['circularity']:.2f} "
                        f"bbox=({x},{y},{w},{h})"
                    )
            else:
                print("  . no leaf")

            time.sleep(0.2)
    except KeyboardInterrupt:
        print("\n  Stopped.")


def test_confirmed_detection():
    """Test multi-frame confirmation logic."""
    print("=== Confirmed Detection Test ===")
    print(f"  Need {DETECTION_CONFIRM_FRAMES} consecutive frames.")
    print("  Press Ctrl+C to stop.\n")

    camera.setup()
    detector.reset()
    time.sleep(1)

    try:
        while True:
            frame = camera.get_frame()
            if frame is None:
                continue

            confirmed, _ = detector.check_confirmed(frame)
            count = detector.get_consecutive_count()

            if confirmed:
                print(f"  >>> CONFIRMED ({count} frames) — detection is stable!")
                detector.reset()
                time.sleep(2)
            elif count > 0:
                print(f"  detecting... ({count}/{DETECTION_CONFIRM_FRAMES})")
            else:
                print("  . no leaf")

            time.sleep(0.1)
    except KeyboardInterrupt:
        print("\n  Stopped.")


def test_annotated_preview():
    """Show annotated frames in a local OpenCV window (for debugging on Pi with display)."""
    print("=== Annotated Preview Test ===")
    print("  Press 'q' to quit.\n")

    camera.setup()
    time.sleep(1)

    try:
        while True:
            frame = camera.get_frame()
            if frame is None:
                continue

            leaves = detector.detect_leaves(frame)
            annotated = detector.annotate_frame(frame, leaves)

            cv2.imshow("Leaf Detection", annotated)
            if cv2.waitKey(1) & 0xFF == ord("q"):
                break
    except KeyboardInterrupt:
        pass
    finally:
        cv2.destroyAllWindows()
        print("  Stopped.")


def run():
    print("Select test:")
    print("  1 — Camera feed (check frames)")
    print("  2 — Capture still image")
    print("  3 — Leaf detection (live, console)")
    print("  4 — Confirmed detection (multi-frame)")
    print("  5 — Annotated preview (OpenCV window)")

    choice = input("\nEnter choice (1-5): ").strip()

    try:
        if choice == "1":
            test_camera_feed()
        elif choice == "2":
            test_capture_image()
        elif choice == "3":
            test_leaf_detection()
        elif choice == "4":
            test_confirmed_detection()
        elif choice == "5":
            test_annotated_preview()
        else:
            print("Invalid choice.")
    finally:
        camera.cleanup()


if __name__ == "__main__":
    run()
