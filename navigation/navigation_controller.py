# navigation/navigation_controller.py — Main Navigation Logic Loop

import time
import logging
import threading
from datetime import datetime

from navigation.state_machine import State
from utils.config import (
    SERVO_SCAN_MIN, SERVO_SCAN_MAX,
    EMERGENCY_STOP_DISTANCE, OBSTACLE_DISTANCE,
    REVERSE_DISTANCE_CM, DEFAULT_SPEED, TURN_SPEED, TURN_DURATION,
)
from actuators import motor_controller as motor
from actuators import servo_controller as servo
from sensors import ultrasonic, camera_detection
from utils import transmitter

log = logging.getLogger("navigation_controller")

class NavigationController:
    """Handles the high-level navigation logic using a non-blocking state machine."""
    
    def __init__(self, state_machine):
        self.sm = state_machine
        self._running = False
        self._thread = None
        self._forbidden_angles = []  # List of angles where red objects were found
        
    def start(self):
        """Start the navigation loop in a background thread."""
        self._running = True
        self._thread = threading.Thread(target=self._loop, daemon=True)
        self._thread.start()
        
    def stop(self):
        """Stop the navigation loop safely."""
        self._running = False
        if self._thread:
            self._thread.join(timeout=2.0)
            
    def _loop(self):
        """Main navigation loop representing the continuous cycle."""
        while self._running:
            state = self.sm.get_state()
            
            if state == State.IDLE:
                time.sleep(0.1)
                
            elif state == State.INITIAL_SCAN:
                self._handle_initial_scan()
                
            elif state == State.MOVING_FORWARD:
                self._handle_moving_forward()
                
            elif state == State.OBSTACLE_DETECTED:
                self._handle_obstacle_detected()
                
            elif state == State.PATH_FINDING:
                self._handle_path_finding()
                
            elif state == State.RED_OBJECT_DETECTED:
                self._handle_red_object_detected()
                
            elif state == State.IMAGE_CAPTURE:
                self._handle_image_capture()
                
            elif state == State.AVOID_RED_DIRECTION:
                self._handle_avoid_red_direction()
                
            elif state == State.SHUTDOWN:
                break
                
            else:
                time.sleep(0.1)
                
    # --- State Handlers ---
    
    def _handle_initial_scan(self):
        """Perform a full environment scan on startup."""
        log.info("Starting INITIAL_SCAN...")
        servo.stop_sweep()
        
        # 1. Servo rotates from -60 to +60
        distances = self._perform_full_scan()
        
        # 3. Evaluate forward direction (0 deg)
        center_dist = distances.get(0, 0)
        
        if center_dist > OBSTACLE_DISTANCE:
            # Forward path is clear
            log.info("Forward clear. Moving forward.")
            self.sm.set_state(State.MOVING_FORWARD)
        else:
            # Forward blocked, chooose direction with max clearance
            log.info("Forward blocked. Falling back to PATH_FINDING.")
            self.sm.set_state(State.PATH_FINDING)
            
    def _handle_moving_forward(self):
        """Continuous scanning while moving forward."""
        # Ensure sweep is active and moving
        servo.start_sweep()
        motor.forward(DEFAULT_SPEED)
        
        # Continuous monitoring
        while self.sm.get_state() == State.MOVING_FORWARD and self._running:
            # 6. Red Object Detection check
            if camera_detection.is_red_detected():
                log.info("Red object detected while moving! Transitioning state.")
                self.sm.set_state(State.RED_OBJECT_DETECTED)
                return
                
            # 3. Obstacle Detection check
            dist = ultrasonic.get_distance()
            if dist < EMERGENCY_STOP_DISTANCE:
                log.warning("EMERGENCY STOP! Dist: %.1fcm", dist)
                motor.stop()
                motor.backward(TURN_SPEED)
                time.sleep(0.3) # reverse slightly
                motor.stop()
                self.sm.set_state(State.PATH_FINDING)
                return
                
            elif dist < OBSTACLE_DISTANCE:
                log.info("Obstacle detected! Dist: %.1fcm", dist)
                motor.stop()
                servo.pause_sweep() # Stop at exact angle
                self.sm.set_state(State.OBSTACLE_DETECTED)
                return
                
            time.sleep(0.05)
            
    def _handle_obstacle_detected(self):
        """Normal obstacle case (<30 cm). Immediate stop already handled."""
        log.info("Obstacle detected, transitioning to path finding.")
        # We paused the sweep at the exact angle, so let's use that information optionally
        _angle = servo.get_current_angle()
        log.info("Obstacle is at roughly %d degrees.", _angle)
        self.sm.set_state(State.PATH_FINDING)
        
    def _handle_path_finding(self):
        """Evaluate best escape path after obstacle detection."""
        log.info("Starting PATH_FINDING scan...")
        servo.stop_sweep() # ensure we have control
        
        # 1. Perform servo scan from -60 to +60
        distances = self._perform_full_scan()
        
        # 2. Divide results into zones
        # Zone definition based on angle: 
        # Left: < -20, Center: [-20, 20], Right: > 20
        zones = {"Left": [], "Center": [], "Right": []}
        
        for angle, dist in distances.items():
            if angle < -20:
                zones["Left"].append(dist)
            elif angle > 20:
                zones["Right"].append(dist)
            else:
                zones["Center"].append(dist)
                
        # 3. Score each zone
        best_zone = None
        best_score = -1
        target_angle = 0
        
        for name, readings in zones.items():
            if not readings:
                continue
            max_d = max(readings)
            avg_d = sum(readings) / len(readings)
            score = (max_d * 0.4) + (avg_d * 0.6) # Weighted score
            
            # 7. Red Object Direction Memory check
            # Avoid picking a zone if its central angle is forbidden
            zone_center = {"Left": -45, "Center": 0, "Right": 45}[name]
            if self._is_angle_forbidden(zone_center):
                log.info("Zone %s rejected due to red object memory.", name)
                score = -1
                
            if score > best_score:
                best_score = score
                best_zone = name
                target_angle = zone_center
                
        if best_zone and best_score > OBSTACLE_DISTANCE:
            log.info("Best zone is %s. Selecting angle %d.", best_zone, target_angle)
            # 4. Select best available path
            motor.backward(TURN_SPEED)
            time.sleep(0.2) # Reverse slightly
            motor.stop()
            
            # Dynamic turning based on the selected angle
            motor.turn_dynamic(-target_angle) # we invert target_angle because turning away from obstacle
            time.sleep(TURN_DURATION * (abs(target_angle) / 60.0)) 
            motor.stop()
            
            self.sm.set_state(State.MOVING_FORWARD)
        else:
            log.warning("No safe path found. Reversing and rescanning...")
            motor.backward(TURN_SPEED)
            time.sleep(1.0)
            motor.stop()
            # Loop back into path finding
            self.sm.set_state(State.PATH_FINDING)
            
    def _handle_red_object_detected(self):
        """Red Object detected."""
        # 1. Stop rover immediately
        motor.stop()
        servo.pause_sweep()
        
        # Store exact angle
        red_angle = servo.get_current_angle()
        self._forbidden_angles.append(red_angle)
        log.info("Red object forbidden angle stored: %d", red_angle)
        
        # 2. Wait 2 seconds
        time.sleep(2.0)
        self.sm.set_state(State.IMAGE_CAPTURE)
        
    def _handle_image_capture(self):
        """Capture and send red object image."""
        # 3. Capture image
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"detection_{ts}.jpg"
        image_path = camera_detection.capture_image(filename)
        log.info("Image captured: %s", image_path)

        # 4. Send image to PC server
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        success = transmitter.send_detection(image_path, timestamp)
        if success:
            log.info("Detection data sent to PC")
            
        camera_detection.reset_detection() # clear for next
        
        # 5. Wait 5 seconds
        time.sleep(5.0)
        
        self.sm.set_state(State.AVOID_RED_DIRECTION)
        
    def _handle_avoid_red_direction(self):
        """Post-Red Detection Navigation."""
        log.info("Avoiding red object direction...")
        # 1. Start ultrasonic scanning (we do a manual scan as per rules)
        distances = self._perform_full_scan()
        
        # 3. Choose direction satisfying no obstacle & not red
        best_angle = None
        best_dist = -1
        
        for angle, dist in distances.items():
            if dist > OBSTACLE_DISTANCE and not self._is_angle_forbidden(angle):
                if dist > best_dist:
                    best_dist = dist
                    best_angle = angle
                    
        # 4. Reverse slightly
        motor.backward(TURN_SPEED)
        time.sleep(0.3)
        motor.stop()
        
        if best_angle is not None:
            # 5. Move toward safe direction
            motor.turn_dynamic(-best_angle)
            time.sleep(TURN_DURATION * (abs(best_angle) / 60.0))
            motor.stop()
            self.sm.set_state(State.MOVING_FORWARD)
        else:
            self.sm.set_state(State.PATH_FINDING)
            
    # --- Helper methods ---
    def _perform_full_scan(self):
        """Perform a discrete scan returning dictionary of angle to distance."""
        distances = {}
        for angle in range(SERVO_SCAN_MIN, SERVO_SCAN_MAX + 1, 15):
            servo.look_at(angle, wait_settle=True)
            dist = ultrasonic.get_distance()
            distances[angle] = dist
            log.debug("Scan %d deg -> %.1f cm", angle, dist)
        servo.look_center()
        return distances

    def _is_angle_forbidden(self, test_angle, tolerance=10):
        """Check if an angle falls within a forbidden sector (tolerance degrees)."""
        for forbidden in self._forbidden_angles:
            if abs(test_angle - forbidden) <= tolerance:
                return True
        return False
