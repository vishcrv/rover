# tests/test_stream.py — Validation for live video streaming
# Run on Raspberry Pi: python -m tests.test_stream

import time
from modules import camera
from streaming import server as stream_server
from config.settings import STREAM_PORT


def run():
    print("=== Live Streaming Test ===\n")

    print("  Starting camera...")
    camera.setup()
    time.sleep(1)

    # Verify frames are available before starting server
    frame = camera.get_frame()
    if frame is not None:
        print(f"  Camera OK — frame shape: {frame.shape}")
    else:
        print("  WARNING: no frame yet, stream may take a moment to start")

    print(f"\n  Starting stream server on port {STREAM_PORT}...")
    print(f"  Open in browser:  http://<rover-ip>:{STREAM_PORT}/")
    print(f"  Direct feed:      http://<rover-ip>:{STREAM_PORT}/video")
    print(f"\n  Press Ctrl+C to stop.\n")

    try:
        stream_server.start(blocking=True)
    except KeyboardInterrupt:
        print("\n  Stopped.")
    finally:
        camera.cleanup()


if __name__ == "__main__":
    run()
