import time
import threading
import pigpio
from config.settings import (
    SERVO_PIN,
    SERVO_LEFT_PW, SERVO_CENTER_PW, SERVO_RIGHT_PW,
    SERVO_MOVE_DELAY, SERVO_SCAN_STEP_PW, SERVO_SCAN_SETTLE,
)

_pi = None

# Sweeping state
_sweep_thread = None
_stop_sweep_event = threading.Event()
_pause_sweep_event = threading.Event()

# Track position for continuous servo: 0 = Full Right (Initial), max_ticks = Full Left
_offset_ticks = 0


def setup():
    """Initialize pigpio connection."""
    global _pi, _offset_ticks
    _pi = pigpio.pi()
    if not _pi.connected:
        raise RuntimeError(
            "pigpiod not running! Start with: sudo systemctl start pigpiod"
        )
    _offset_ticks = 0
    _pi.set_servo_pulsewidth(SERVO_PIN, 0)


def _do_ticks(pulsewidth, ticks):
    """Wait for `ticks` * 0.1s, checking for interrupts."""
    completed = 0
    _pi.set_servo_pulsewidth(SERVO_PIN, pulsewidth)
    for _ in range(int(ticks)):
        if _stop_sweep_event.is_set() or _pause_sweep_event.is_set():
            break
        time.sleep(0.1)
        completed += 1
    _pi.set_servo_pulsewidth(SERVO_PIN, 0)
    return completed


def _force_return_to_initial():
    """Uninterruptible return to 0 offset (Full Right start state)."""
    global _offset_ticks
    if _offset_ticks > 0:
        _pi.set_servo_pulsewidth(SERVO_PIN, SERVO_RIGHT_PW)
        time.sleep(_offset_ticks * 0.1)
        _pi.set_servo_pulsewidth(SERVO_PIN, 0)
        _offset_ticks = 0


def look_center():
    """Not applicable for timed continuous sweep."""
    pass


def _sweep_loop():
    """Continuously sweep the servo using timed moves."""
    global _offset_ticks
    ticks_per_move = max(1, int(SERVO_MOVE_DELAY / 0.1))

    while not _stop_sweep_event.is_set():
        if _pause_sweep_event.is_set():
            time.sleep(0.1)
            continue

        # Complete the Left sweep (up to ticks_per_move)
        if _offset_ticks < ticks_per_move:
            done = _do_ticks(SERVO_LEFT_PW, ticks_per_move - _offset_ticks)
            _offset_ticks += done

        if _stop_sweep_event.is_set() or _pause_sweep_event.is_set():
            _force_return_to_initial()
            continue

        # Complete the Right sweep (back to 0)
        if _offset_ticks > 0:
            done = _do_ticks(SERVO_RIGHT_PW, _offset_ticks)
            _offset_ticks -= done

        if _stop_sweep_event.is_set() or _pause_sweep_event.is_set():
            _force_return_to_initial()
            continue


def full_scan():
    """Perform a discrete scan and return {angle_approx: distance_cm}.

    Assumes we start at initial state (Offset 0 = Right).
    Moves in 4 equal timed steps to arrive at Full Left, measuring at each point.
    Then swiftly returns to initial state.
    """
    from modules import ultrasonic

    distances = {}
    ticks_per_move = max(1, int(SERVO_MOVE_DELAY / 0.1))
    steps = 4
    ticks_per_step = ticks_per_move / steps

    for i in range(steps + 1):
        # Calculate approximate angle: -50 (Right) to +50 (Left)
        angle_approx = -50 + (i / steps) * 100
        distances[angle_approx] = ultrasonic.get_distance()

        if i < steps:
            # Move slightly left
            _pi.set_servo_pulsewidth(SERVO_PIN, SERVO_LEFT_PW)
            time.sleep(ticks_per_step * 0.1)
            _pi.set_servo_pulsewidth(SERVO_PIN, 0)
            time.sleep(SERVO_SCAN_SETTLE)

    # Completely return to Full Right (initial state)
    _pi.set_servo_pulsewidth(SERVO_PIN, SERVO_RIGHT_PW)
    time.sleep(ticks_per_move * 0.1)
    _pi.set_servo_pulsewidth(SERVO_PIN, 0)

    return distances


def start_sweep():
    """Start the background sweep thread."""
    global _sweep_thread
    if _sweep_thread is None or not _sweep_thread.is_alive():
        _stop_sweep_event.clear()
        _pause_sweep_event.clear()
        _sweep_thread = threading.Thread(target=_sweep_loop, daemon=True)
        _sweep_thread.start()


def stop_sweep():
    """Stop the background sweep thread entirely and reset position."""
    _stop_sweep_event.set()
    if _sweep_thread is not None:
        _sweep_thread.join(timeout=3.0)
    _force_return_to_initial()


def pause_sweep():
    """Temporarily pause the sweeping and reset position."""
    _pause_sweep_event.set()


def resume_sweep():
    """Resume a paused sweep."""
    _pause_sweep_event.clear()


def cleanup():
    """Stop signal and release pigpio."""
    stop_sweep()
    time.sleep(0.5)
    _pi.stop()
