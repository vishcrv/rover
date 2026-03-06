# tests/test_transmit.py — Validation for data transmission
# Run on Raspberry Pi:  python -m tests.test_transmit
# Run on PC first:      python pc_server.py

import os
from datetime import datetime
from utils import transmitter


def test_send():
    """Send a test image to the PC server."""
    print("=== Transmission Test ===\n")

    # Use a test image — create a small one if none exists
    test_image = "/tmp/test_transmit.jpg"
    if not os.path.exists(test_image):
        try:
            import cv2
            import numpy as np
            # Create a small red test image
            img = np.zeros((100, 100, 3), dtype=np.uint8)
            img[:, :, 2] = 255  # red channel
            cv2.imwrite(test_image, img)
            print(f"  Created test image: {test_image}")
        except ImportError:
            print("  ERROR: No test image and OpenCV not available to create one.")
            print(f"  Place a .jpg file at {test_image} and retry.")
            return

    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    print(f"  Image:     {test_image}")
    print(f"  Timestamp: {ts}")
    print()

    success = transmitter.send_detection(test_image, ts)

    if success:
        print("  SUCCESS — PC server received the data.")
    else:
        print("  FAILED — check that pc_server.py is running on the PC")
        print(f"           and PC_SERVER_IP in utils/config.py is correct.")


def run():
    test_send()


if __name__ == "__main__":
    run()
