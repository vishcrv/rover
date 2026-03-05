# main.py — Main controller (state machine)
# Auto-start: sudo systemctl enable rover.service

import signal
import time
import logging
import threading
from datetime import datetime
from enum import Enum, auto

from config.settings import DEFAULT_SPEED, DEMO_DURATION, STREAM_PORT
from modules import motor, ultrasonic, servo, camera, detector, transmitter
from modules.obstacle import check_and_avoid
from streaming import server as stream_server

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger("main")


# ---------------------------------------------------------------------------
# States
# ---------------------------------------------------------------------------
class State(Enum):
    BOOT = auto()
    SEARCH = auto()
    DETECTED = auto()
    DEMO_CONTINUE = auto()
    SHUTDOWN = auto()


# ---------------------------------------------------------------------------
# Shared state
# ---------------------------------------------------------------------------
_state = State.BOOT
_state_lock = threading.Lock()
_detection_event = threading.Event()
_shutdown_event = threading.Event()


def _get_state():
    with _state_lock:
        return _state


def _set_state(new_state):
    global _state
    with _state_lock:
        _state = new_state
    log.info("State → %s", new_state.name)


# ---------------------------------------------------------------------------
# Navigation thread
# ---------------------------------------------------------------------------
def _navigation_loop():
    """Move forward and avoid obstacles while in SEARCH or DEMO_CONTINUE."""
    while not _shutdown_event.is_set():
        state = _get_state()

        if state in (State.SEARCH, State.DEMO_CONTINUE):
            avoided = check_and_avoid()
            if not avoided:
                motor.forward(DEFAULT_SPEED)
            time.sleep(0.05)
        else:
            # Not navigating in this state — wait briefly
            time.sleep(0.1)


# ---------------------------------------------------------------------------
# Detection thread
# ---------------------------------------------------------------------------
def _detection_loop():
    """Process camera frames for red objects while in SEARCH state."""
    while not _shutdown_event.is_set():
        state = _get_state()

        if state != State.SEARCH:
            time.sleep(0.1)
            continue

        frame = camera.get_frame()
        if frame is None:
            time.sleep(0.05)
            continue

        confirmed = detector.check_confirmed(frame)
        if confirmed:
            log.info("RED OBJECT CONFIRMED — triggering detection event")
            _detection_event.set()

        time.sleep(0.02)  # ~50 checks/sec max, camera is ~20fps


# ---------------------------------------------------------------------------
# Boot
# ---------------------------------------------------------------------------
def _boot():
    """Initialize all modules and start background services."""
    log.info("Initializing modules...")

    motor.setup()
    log.info("  Motors OK")

    ultrasonic.setup()
    log.info("  Ultrasonic OK")

    servo.setup()
    log.info("  Servo OK")

    camera.setup()
    time.sleep(1)  # let camera warm up
    log.info("  Camera OK")

    stream_server.start(blocking=False)
    log.info("  Streaming server started on port %d", STREAM_PORT)


# ---------------------------------------------------------------------------
# Detection handling
# ---------------------------------------------------------------------------
def _handle_detection():
    """Stop, capture image, and send data to PC."""
    motor.stop()
    log.info("Motors stopped")

    # Capture image
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"detection_{ts}.jpg"
    image_path = camera.capture_image(filename)
    log.info("Image captured: %s", image_path)

    # Send to PC
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    success = transmitter.send_detection(image_path, timestamp)
    if success:
        log.info("Detection data sent to PC")
    else:
        log.warning("Failed to send detection data — continuing mission")

    # Reset detector for future detections
    detector.reset()
    _detection_event.clear()


# ---------------------------------------------------------------------------
# Graceful shutdown
# ---------------------------------------------------------------------------
def _shutdown():
    """Stop everything cleanly."""
    log.info("Shutting down...")
    _shutdown_event.set()

    motor.stop()
    log.info("  Motors stopped")

    camera.cleanup()
    log.info("  Camera released")

    servo.cleanup()
    ultrasonic.cleanup()
    motor.cleanup()
    log.info("  GPIO cleaned up")

    log.info("Shutdown complete.")


def _signal_handler(signum, frame):
    """Handle SIGINT/SIGTERM for clean exit."""
    log.info("Signal %d received", signum)
    _set_state(State.SHUTDOWN)
    _shutdown_event.set()


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    signal.signal(signal.SIGINT, _signal_handler)
    signal.signal(signal.SIGTERM, _signal_handler)

    try:
        # ---- BOOT ----
        _set_state(State.BOOT)
        _boot()

        # Start worker threads
        nav_thread = threading.Thread(target=_navigation_loop, daemon=True)
        det_thread = threading.Thread(target=_detection_loop, daemon=True)
        nav_thread.start()
        det_thread.start()
        log.info("Worker threads started")

        # ---- SEARCH ----
        _set_state(State.SEARCH)
        servo.start_sweep()

        while not _shutdown_event.is_set():
            state = _get_state()

            if state == State.SEARCH:
                # Wait for detection or shutdown
                if _detection_event.wait(timeout=0.5):
                    _set_state(State.DETECTED)

            elif state == State.DETECTED:
                servo.stop_sweep()
                _handle_detection()
                _set_state(State.DEMO_CONTINUE)

            elif state == State.DEMO_CONTINUE:
                log.info("Demo mode — continuing for %ds", DEMO_DURATION)
                # Run for DEMO_DURATION, checking for shutdown
                deadline = time.time() + DEMO_DURATION
                while time.time() < deadline:
                    if _shutdown_event.is_set():
                        break
                    time.sleep(0.5)

                if not _shutdown_event.is_set():
                    motor.stop()
                    log.info("Demo complete — returning to SEARCH")
                    _set_state(State.SEARCH)
                    servo.start_sweep()

            elif state == State.SHUTDOWN:
                break

    except Exception:
        log.exception("Unexpected error in main loop")
    finally:
        _shutdown()


if __name__ == "__main__":
    main()
