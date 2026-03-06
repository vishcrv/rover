# navigation/state_machine.py — Navigation States Definitions

import logging
import threading
from enum import Enum, auto

log = logging.getLogger("state_machine")

class State(Enum):
    BOOT = auto()
    IDLE = auto()
    INITIAL_SCAN = auto()
    MOVING_FORWARD = auto()
    OBSTACLE_DETECTED = auto()
    PATH_FINDING = auto()
    RED_OBJECT_DETECTED = auto()
    IMAGE_CAPTURE = auto()
    AVOID_RED_DIRECTION = auto()
    SHUTDOWN = auto()

class StateMachine:
    """Thread-safe state manager for the rover."""
    
    def __init__(self):
        self._state = State.BOOT
        self._lock = threading.Lock()
        
    def get_state(self):
        """Get the current state safely."""
        with self._lock:
            return self._state
            
    def set_state(self, new_state):
        """Set a new state safely and log the transition."""
        with self._lock:
            if self._state != new_state:
                log.info("State Transition: %s → %s", self._state.name, new_state.name)
                self._state = new_state
