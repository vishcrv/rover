# main.py — Main entry point
# Auto-start: sudo systemctl enable rover.service

import signal
import time
import logging

from utils.config import STREAM_PORT
from actuators import motor_controller, servo_controller
from sensors import ultrasonic, camera_detection
from navigation.state_machine import StateMachine, State
from navigation.navigation_controller import NavigationController
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

# Global instances
sm = StateMachine()
nav = NavigationController(sm)

# ---------------------------------------------------------------------------
# Boot
# ---------------------------------------------------------------------------
def _boot():
    """Initialize all modules and start background services."""
    log.info("Initializing modules...")

    motor_controller.setup()
    log.info("  Motors OK")

    ultrasonic.setup()
    log.info("  Ultrasonic OK")

    servo_controller.setup()
    log.info("  Servo OK")

    camera_detection.setup()
    time.sleep(1)  # let camera warm up
    log.info("  Camera OK")

    stream_server.start(blocking=False)
    log.info("  Streaming server started on port %d", STREAM_PORT)


# ---------------------------------------------------------------------------
# Graceful shutdown
# ---------------------------------------------------------------------------
def _shutdown():
    """Stop everything cleanly."""
    log.info("Shutting down...")
    
    # Trigger shutdown state to cleanly exit loops
    sm.set_state(State.SHUTDOWN)
    nav.stop()

    motor_controller.cleanup()
    log.info("  Motors stopped and cleaned up")

    camera_detection.cleanup()
    log.info("  Camera released")

    servo_controller.cleanup()
    ultrasonic.cleanup()
    log.info("  Sensors/Actuators cleaned up")

    log.info("Shutdown complete.")


def _signal_handler(signum, frame):
    """Handle SIGINT/SIGTERM for clean exit."""
    log.info("Signal %d received", signum)
    sm.set_state(State.SHUTDOWN)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    signal.signal(signal.SIGINT, _signal_handler)
    signal.signal(signal.SIGTERM, _signal_handler)

    try:
        # ---- BOOT ----
        sm.set_state(State.BOOT)
        _boot()

        # Start Navigation Thread
        nav.start()
        log.info("Navigation controller started")

        # ---- INITIAL SCAN ----
        sm.set_state(State.INITIAL_SCAN)

        # Keep main thread alive for serving streaming gracefully and handling interrupts
        while sm.get_state() != State.SHUTDOWN:
            time.sleep(1.0)

    except Exception:
        log.exception("Unexpected error in main loop")
    finally:
        _shutdown()


if __name__ == "__main__":
    main()
