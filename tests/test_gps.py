# tests/test_gps.py — Validation for GPS module
# Run on Raspberry Pi: python -m tests.test_gps

import time
from modules import gps_reader


def test_raw_serial():
    """Read and print raw NMEA sentences from GPS module."""
    import serial
    from config.settings import GPS_SERIAL_PORT, GPS_BAUD_RATE

    print("=== Raw NMEA Output ===")
    print("  Press Ctrl+C to stop.\n")

    ser = serial.Serial(GPS_SERIAL_PORT, GPS_BAUD_RATE, timeout=1)
    try:
        while True:
            line = ser.readline().decode("ascii", errors="ignore").strip()
            if line:
                print(f"  {line}")
    except KeyboardInterrupt:
        print("\n  Stopped.")
    finally:
        ser.close()


def test_parsed_coordinates():
    """Start GPS reader and print parsed coordinates every 2 seconds."""
    print("=== Parsed GPS Coordinates ===")
    print("  Waiting for fix (may take 30-60s outdoors)...")
    print("  Press Ctrl+C to stop.\n")

    gps_reader.setup()

    try:
        while True:
            lat, lon = gps_reader.get_coordinates()
            if gps_reader.has_fix():
                print(f"  FIX:  lat={lat:.6f}  lon={lon:.6f}")
            else:
                print("  . waiting for fix...")
            time.sleep(2)
    except KeyboardInterrupt:
        print("\n  Stopped.")
    finally:
        gps_reader.cleanup()


def run():
    print("Select test:")
    print("  1 — Raw NMEA sentences")
    print("  2 — Parsed coordinates (lat/lon)")

    choice = input("\nEnter choice (1-2): ").strip()

    if choice == "1":
        test_raw_serial()
    elif choice == "2":
        test_parsed_coordinates()
    else:
        print("Invalid choice.")


if __name__ == "__main__":
    run()
