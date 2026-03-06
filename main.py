# main.py — Main controller (state machine)
# Auto-start: sudo systemctl enable rover.service

import signal
import time
import logging
import threading
from datetime import datetime
from enum import Enum, auto

from config.settings import DEFAULT_SPEED, STREAM_PORT, AVOIDANCE_TRIGGER_CM, TURN_SPEED, TURN_DURATION
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
    """Move forward and avoid obstacles while in SEARCH state."""
    while not _shutdown_event.is_set():
        state = _get_state()

        if state == State.SEARCH:
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
    """Stop → wait 2s → capture → wait 10s → scan → turn → resume."""
    # 1. Stop all motors and servo sweep
    motor.stop()
    servo.stop_sweep()
    log.info("Motors and servo stopped for detection")

    # 2. Wait 2 seconds (hold still for a stable image)
    log.info("Holding still for 2 seconds...")
    time.sleep(2.0)

    # 3. Capture image and send to PC
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"detection_{ts}.jpg"
    image_path = camera.capture_image(filename)
    log.info("Image captured: %s", image_path)

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    success = transmitter.send_detection(image_path, timestamp)
    if success:
        log.info("Detection data sent to PC")
    else:
        log.warning("Failed to send detection data — continuing mission")

    # Reset detector for future detections
    detector.reset()
    _detection_event.clear()

    # 4. Wait 10 seconds (all motors stopped)
    log.info("Waiting 10 seconds post-detection...")
    for _ in range(100):  # 100 × 0.1s = 10s, checking for shutdown
        if _shutdown_event.is_set():
            return
        time.sleep(0.1)

    # 5. Perform full servo scan to find best direction
    log.info("Performing post-detection scan...")
    distances = servo.full_scan()
    log.info("Scan results: %s", distances)

    # 6. Pick best direction and turn toward it
    best_angle = 0
    best_dist = -1
    for angle, dist in distances.items():
        if dist > best_dist:
            best_dist = dist
            best_angle = angle

    log.info("Best direction: %d° (%.1f cm)", best_angle, best_dist)

    if best_dist > AVOIDANCE_TRIGGER_CM and best_angle != 0:
        if best_angle < 0:
            motor.turn_left(TURN_SPEED)
        else:
            motor.turn_right(TURN_SPEED)

        turn_time = TURN_DURATION * (abs(best_angle) / 50.0)
        turn_time = max(turn_time, 0.2)
        time.sleep(turn_time)
        motor.stop()

    log.info("Post-detection maneuver complete — resuming SEARCH")


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
                _handle_detection()
                # Return to SEARCH after detection handling
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
