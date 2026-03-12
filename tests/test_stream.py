# tests/test_stream.py — Test streaming + capture + transmission without main.py
# Run on Raspberry Pi:  python -m tests.test_stream
# Then open browser:    http://<PI_IP>:8080
#
# The stream at /video shows the LEAF DETECTION PREVIEW with contour
# overlays, bounding boxes, and labels — powered by streaming/server.py's
# _detection_render_loop.

import time
from modules import camera, detector
from streaming import server as stream_server


def test_stream_only():
    """Start camera + streaming server with leaf-detection preview.

    Open http://<PI_IP>:8080 in browser to see the annotated stream
    with contour overlays, bounding boxes, and leaf labels.
    """
    print("=== Leaf Detection Preview Stream ===\n")

    camera.setup()
    time.sleep(1)
    print("  Camera started")

    import subprocess
    ip = subprocess.getoutput("hostname -I").strip().split()[0]
    print(f"\n  Leaf-detection preview: http://{ip}:8080")
    print("  Raw camera feed:        http://{ip}:8080/video_raw")
    print("  Press Ctrl+C to stop.\n")

    try:
        stream_server.start(blocking=True)
    except KeyboardInterrupt:
        print("\n  Stopped.")
    finally:
        camera.cleanup()


def test_capture_and_send():
    """Capture an image and send it to PC server."""
    from datetime import datetime
    from modules import transmitter

    print("=== Capture + Send Test ===\n")
    print("  Make sure pc_server.py is running on your PC first!\n")

    camera.setup()
    time.sleep(2)
    print("  Camera started")

    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"test_{ts}.jpg"
    path = camera.capture_image(filename)
    print(f"  Image saved: {path}")

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    success = transmitter.send_detection(path, timestamp)

    if success:
        print("  SUCCESS — image sent to PC server")
    else:
        print("  FAILED — check pc_server.py is running and IP is correct")

    camera.cleanup()


def test_stream_and_send():
    """Stream leaf-detection preview + capture & send ONLY when leaves are detected."""
    from datetime import datetime
    from modules import transmitter

    print("=== Leaf Detection Stream + Auto-Capture Test ===\n")
    print("  Make sure pc_server.py is running on your PC first!\n")

    camera.setup()
    time.sleep(1)
    print("  Camera started")

    # Start streaming in background (serves annotated leaf-detection preview)
    stream_server.start(blocking=False)

    import subprocess
    ip = subprocess.getoutput("hostname -I").strip().split()[0]
    print(f"  Leaf-detection preview: http://{ip}:8080")
    print("  Captures are triggered ONLY when leaves are detected.")
    print("  Press Ctrl+C to stop.\n")

    try:
        while True:
            frame = camera.get_frame()
            if frame is None:
                time.sleep(0.05)
                continue

            # Only capture+send when OpenCV leaf detection finds leaf-like structures
            leaves = detector.detect_leaves(frame)
            if leaves:
                ts = datetime.now().strftime("%Y%m%d_%H%M%S")
                path = camera.capture_image(f"leaf_{ts}.jpg")
                print(f"  Leaf detected ({len(leaves)} found) — captured: {path}")

                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                success = transmitter.send_detection(path, timestamp)
                print(f"  Sent: {'OK' if success else 'FAILED'}")

                # Cooldown to avoid spamming captures for the same leaf
                time.sleep(5)
            else:
                time.sleep(0.1)  # check ~10 times/sec when no leaf present
    except KeyboardInterrupt:
        print("\n  Stopped.")
    finally:
        camera.cleanup()


def run():
    print("Select test:")
    print("  1 — Leaf-detection preview stream (view in browser)")
    print("  2 — Capture + send to PC")
    print("  3 — Leaf-detection stream + auto-capture on detection")

    choice = input("\nEnter choice (1-3): ").strip()

    if choice == "1":
        test_stream_only()
    elif choice == "2":
        test_capture_and_send()
    elif choice == "3":
        test_stream_and_send()
    else:
        print("Invalid choice.")


if __name__ == "__main__":
    run()
