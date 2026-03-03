# PROJECT_CONTEXT.md

# Project Title
Autonomous Red Object Detection Rover  
Platform: Raspberry Pi 4 + Pi Camera v2

---

# 1. Project Objective

Design and implement a fully autonomous mobile rover that:

- Starts moving automatically when powered ON
- Searches for a red-colored object using computer vision
- Stops when a valid red object is detected
- Captures an image
- Reads GPS coordinates
- Sends image + GPS data to PC over WiFi
- Continues mission for a defined time after detection (demo mode)
- Streams live camera feed to PC while powered ON
- Avoids obstacles using ultrasonic sensor mounted on a servo

---

# 2. Hardware Overview

## 2.1 Processing Unit
- Raspberry Pi 4
- Pi Camera Module v2
- 22000mAh Powerbank (powers Pi + Camera)

## 2.2 Locomotion System
- 4 × BO Motors
- L298N Motor Driver
- Robot chassis
- 2S Battery (powers motors, motor driver, servo, ultrasonic)

## 2.3 Sensors
- Ultrasonic sensor (front-mounted on servo for scanning)
- Servo motor (for directional obstacle scanning)
- GPS module (e.g., NEO-6M)

## 2.4 Communication
- WiFi (Raspberry Pi onboard)

---

# 3. Power Architecture

## 3.1 Power Separation

Powerbank (5V regulated)
→ Raspberry Pi 4  
→ Pi Camera v2  

2S Battery
→ L298N motor driver  
→ BO motors  
→ Servo  
→ Ultrasonic sensor  

Important:
- Common ground between Raspberry Pi and motor system required.
- Motor noise isolation recommended.

---

# 4. Functional Behavior

## 4.1 Startup Behavior

When powered ON:

1. Raspberry Pi boots.
2. Autonomous control script launches automatically.
3. Live camera streaming server starts.
4. Rover begins forward motion.

No manual trigger required.

---

## 4.2 Navigation and Obstacle Avoidance

### Default Motion
- Move forward continuously while searching.

### Obstacle Detection Logic
- Ultrasonic continuously measures distance.
- If obstacle detected within safe threshold:
  - Stop immediately.
  - Rotate servo left and right.
  - Compare distances.
  - Turn toward direction with maximum clearance.
  - Resume forward motion.

### Safe Distance Rule
Instead of fixed value, use adaptive threshold:

- Minimum emergency stop: 15 cm
- Standard avoidance trigger: 20–25 cm

System must ensure zero collision under normal conditions.

---

## 4.3 Red Object Detection

Using OpenCV:

1. Capture frame from Pi Camera v2.
2. Convert frame to HSV color space.
3. Apply red color threshold mask.
4. Detect contours.
5. Filter small contours (noise removal).
6. If contour area > predefined threshold:
   - Confirm detection.
   - Stop motors.
   - Capture high-resolution image.

Detection must be stable for a few frames before confirmation to prevent false positives.

---

## 4.4 Post-Detection Demo Mode

For demonstration clarity:

After red object detection:

1. Stop.
2. Capture image.
3. Read GPS coordinates.
4. Send image + GPS data to PC.
5. Resume movement for predefined duration (e.g., 30–60 seconds).
6. Continue obstacle avoidance.
7. End mission or loop based on configuration.

This is better for demo because:
- Judges see detection event.
- System shows recovery capability.
- Robot appears intelligent rather than terminating abruptly.

---

## 4.5 Data Transmission

When red object detected:

Send to PC:
- Captured image file
- GPS latitude and longitude
- Timestamp

Transmission method:
- HTTP POST request to PC server
OR
- Socket-based transfer

---

## 4.6 Live Video Streaming

While powered ON:

- Continuous video stream available from PC.
- Accessed via browser using IP address.
- Implemented using:
  - Flask + MJPEG stream
  OR
  - Lightweight streaming server

Streaming must not block:
- Motor control
- Obstacle detection
- Red detection logic

Multithreading required.

---

# 5. System State Flow

STATE 1: BOOT  
→ Initialize camera  
→ Initialize motors  
→ Initialize ultrasonic  
→ Initialize GPS  
→ Start streaming server  

STATE 2: SEARCH  
→ Move forward  
→ Check obstacle  
→ Avoid if necessary  
→ Process camera frame  

If red detected → STATE 3  

STATE 3: DETECTED  
→ Stop  
→ Capture image  
→ Read GPS  
→ Send data  
→ Resume movement (demo timer active)  

STATE 4: DEMO CONTINUE  
→ Continue navigation for fixed duration  
→ End mission or loop back  

---

# 6. Software Stack

- Python 3
- OpenCV
- Picamera2 (libcamera-based)
- RPi.GPIO or gpiozero
- Serial communication (pyserial) for GPS
- Flask (for streaming and data transfer)
- Threading or multiprocessing

---

# 7. Performance Expectations

- Real-time detection at minimum 15–20 FPS
- Obstacle reaction time < 200 ms
- No physical collision
- GPS accuracy within typical civilian limits (±2–5 meters outdoor)

---

# 8. Operational Environment

Recommended for demo:

- Indoor lab or controlled outdoor area
- Distinct red object
- Moderate lighting
- Stable WiFi coverage

GPS works best outdoors.

---

# 9. Constraints and Assumptions

- Red object is clearly distinguishable.
- Object is stationary.
- Flat terrain.
- No advanced mapping or SLAM.
- Rule-based navigation only.
- Single-object priority.

---

# 10. Final Defined Scope

This system includes:

- Autonomous movement
- Rule-based obstacle avoidance
- Color-based object detection
- Image capture
- GPS coordinate transmission
- Live video streaming

This system does NOT include:

- Machine learning object detection
- SLAM or mapping
- Path planning algorithms
- Multi-object classification

---

# System Context Locked

If this represents your intended system correctly, next step will be:

- PHASES.md Implementation Plan
- Folder Structure
- Threading Architecture
- Pin Mapping Plan
- Risk and Failure Handling Design