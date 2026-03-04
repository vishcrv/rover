# tests/test_stream.py — Test streaming + capture + transmission without main.py
# Run on Raspberry Pi:  python -m tests.test_stream
# Then open browser:    http://<PI_IP>:8080

import time
from modules import camera
from streaming import server as stream_server


def test_stream_only():
    """Start camera + streaming server. Open http://<PI_IP>:8080 in browser."""
    print("=== Streaming Test ===\n")

    camera.setup()
    time.sleep(1)
    print("  Camera started")

    import subprocess
    ip = subprocess.getoutput("hostname -I").strip().split()[0]
    print(f"\n  Open in browser: http://{ip}:8080")
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
    """Stream + capture + send all together."""
    from datetime import datetime
    from modules import transmitter

    print("=== Stream + Capture + Send Test ===\n")
    print("  Make sure pc_server.py is running on your PC first!\n")

    camera.setup()
    time.sleep(1)
    print("  Camera started")

    # Start streaming in background
    stream_server.start(blocking=False)

    import subprocess
    ip = subprocess.getoutput("hostname -I").strip().split()[0]
    print(f"  Streaming at: http://{ip}:8080")
    print("  Will capture and send an image every 10 seconds.")
    print("  Press Ctrl+C to stop.\n")

    try:
        while True:
            time.sleep(10)
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            path = camera.capture_image(f"test_{ts}.jpg")
            print(f"  Captured: {path}")

            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            success = transmitter.send_detection(path, timestamp)
            print(f"  Sent: {'OK' if success else 'FAILED'}")
    except KeyboardInterrupt:
        print("\n  Stopped.")
    finally:
        camera.cleanup()


def run():
    print("Select test:")
    print("  1 — Stream only (view in browser)")
    print("  2 — Capture + send to PC")
    print("  3 — Stream + capture + send (all together)")

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
