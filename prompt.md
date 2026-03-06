# Rover Navigation System Refinement

## Context

You are working on an **existing Raspberry Pi rover codebase** that already supports:

- BO motors for rover movement
- Ultrasonic sensor for obstacle detection
- Servo motor for rotating the ultrasonic sensor
- Raspberry Pi camera for color detection
- Basic obstacle avoidance logic

Your task is to **refine and improve the navigation logic** so that the rover behaves according to the specifications below.

Do **NOT rewrite the entire system unnecessarily**. Instead:
- Refactor existing logic
- Improve structure
- Implement the required navigation behaviors

---

# Rover Physical Specifications

- **Chassis Width:** 18–20 cm  
- **Chassis Length:** ~30 cm  
- **Ultrasonic sensor mounted on servo motor**
- **Servo scanning range:** -60° to +60° relative to forward direction

All navigation decisions must consider the rover width.

---

# Core Navigation Behavior

## 1. Initial Environment Scan

When the rover starts:

1. The **servo rotates the ultrasonic sensor from -60° to +60°**.
2. Collect distance readings across the scan.
3. Evaluate whether the **forward direction (0°)** is clear.

If **forward path is clear**:
- The rover **starts moving forward**.

If **forward path is blocked**:
- Perform a **full scan**
- Choose the direction with the **maximum clearance distance**
- Rotate rover toward that direction
- Begin forward movement

---

# 2. Continuous Scanning While Moving

While the rover is moving:

- The **servo continuously oscillates between -60° and +60°**
- The ultrasonic sensor continuously checks for obstacles.

This allows **real-time obstacle monitoring**.

---

# 3. Obstacle Detection

Define two distance thresholds:

- **Emergency Stop:** < 15 cm  
- **Obstacle Threshold:** < 25–30 cm

### Emergency Case (<15 cm)

1. Immediately **stop the motors**
2. **Reverse slightly**
3. Begin **path finding scan**

### Normal Obstacle Case (<25–30 cm)

1. **Stop rover immediately**
2. **Stop servo at the exact angle where obstacle was detected**
3. Start alternate path detection

---

# 4. Path Finding Logic

When an obstacle is detected:

1. Perform a **servo scan from -60° to +60°**
2. Divide scan results into **three zones**:

- **Left Zone**
- **Center Zone**
- **Right Zone**

3. Score each zone based on:
- Maximum distance
- Average distance

4. Select the **best available path**.

Movement sequence:

1. Reverse slightly
2. Rotate rover toward selected direction
3. Resume forward movement
4. Restart **continuous servo scanning**

---

# 5. Dynamic Turning

Turning should not be binary.

Instead:

- If obstacle detected at **+45°**, turn right proportionally
- If obstacle detected at **-30°**, turn left proportionally

This produces **smoother navigation**.

---

# 6. Red Object Detection (Camera System)

The Raspberry Pi camera continuously detects **red color objects**.

### When Red is Detected

1. **Stop rover immediately**
2. **Wait 2 seconds**
3. **Capture image**
4. **Send image to PC server**
5. **Wait 5 seconds**

After this process:

- The rover **must not move toward the red object**.

---

# 7. Red Object Direction Memory

When red is detected:

- Store the **servo angle where the red object was observed**

During path selection:

- Avoid choosing directions **within that angular sector**

Example:

If red detected at **+20°**

Avoid path between:

+10° to +30°


---

# 8. Post-Red Detection Navigation

After image capture:

1. Start ultrasonic servo scanning again
2. Perform environment scan
3. Choose a direction that satisfies:
   - No obstacle
   - Not toward red-object direction
4. Reverse slightly
5. Move toward the selected safe direction

---

# 9. Continuous Navigation Loop

The rover continuously cycles between these states.

Suggested navigation states:

IDLE
INITIAL_SCAN
MOVING_FORWARD
OBSTACLE_DETECTED
PATH_FINDING
RED_OBJECT_DETECTED
IMAGE_CAPTURE
AVOID_RED_DIRECTION


Use a **state machine architecture**.

---

# Implementation Requirements

## Non-blocking Operation

Servo scanning, ultrasonic readings, and motor control should not block each other.

Use:

- asynchronous loops
- threading
- event-driven logic

---

# Sensor Stability

To reduce noise:

- Average multiple ultrasonic readings
- Ignore outliers
- Add small delay between readings

---

# Servo Control

Servo should:

- Sweep smoothly between **-60° and +60°**
- Pause briefly at each step for accurate readings

---

# Code Structure

Refactor or organize modules similar to:

/navigation
navigation_controller.py
state_machine.py

/sensors
ultrasonic.py
camera_detection.py

/actuators
motor_controller.py
servo_controller.py

/utils
config.py


---

# Configuration Parameters

Keep important values configurable.

Example:

SERVO_SCAN_MIN = -60
SERVO_SCAN_MAX = 60

EMERGENCY_STOP_DISTANCE = 15
OBSTACLE_DISTANCE = 30

REVERSE_DISTANCE_CM = 5
ROVER_WIDTH_CM = 20


---

# Expected Output

Provide:

1. Updated navigation architecture
2. Refactored code modules
3. Clear explanation of changes
4. Any assumptions made

Focus on **clean modular design and reliable real-time behavior**.