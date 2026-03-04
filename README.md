# PHASES.md — Implementation Plan

Reference: [context.md](context.md)

---

# PART A: HARDWARE PHASES

---

## Phase H1: Power System Setup

### H1.1 — Powerbank Circuit (Pi Side)
- Connect 22000mAh powerbank to Raspberry Pi 4 via USB-C
- Confirm Pi boots reliably and sustains under load
- Connect Pi Camera v2 to CSI port, verify recognized on boot

### H1.2 — 2S Battery Circuit (Motor Side)
- Connect 2S LiPo/Li-ion battery to L298N motor driver VCC input
- Confirm L298N onboard regulator outputs 5V (for servo and ultrasonic)
- Wire servo VCC and ultrasonic VCC from L298N 5V output

### H1.3 — Common Ground
- Connect a GND wire between Raspberry Pi GND and L298N GND
- This is critical — without common ground, GPIO signals will not work
- Verify with multimeter: Pi GND and motor-side GND read 0V difference

### H1.4 — Power Validation
- Power on both circuits simultaneously
- Confirm Pi boots, camera initializes, motors do not spin (no signal yet)
- Check for voltage drops under motor load using multimeter

---

## Phase H2: Motor and Chassis Assembly

### H2.1 — Chassis Build
- Mount 4x BO motors to robot chassis
- Attach wheels to motor shafts
- Mount L298N motor driver to chassis (use standoffs to avoid shorts)

### H2.2 — Motor Wiring to L298N
- Wire left-side motors (2) to L298N OUT1 and OUT2 (parallel)
- Wire right-side motors (2) to L298N OUT3 and OUT4 (parallel)
- This gives differential drive (tank-style steering)

### H2.3 — L298N Control Pins to Raspberry Pi
- Connect L298N IN1, IN2 (left motors) to Pi GPIO pins
- Connect L298N IN3, IN4 (right motors) to Pi GPIO pins
- Connect ENA, ENB to Pi GPIO PWM-capable pins (for speed control)
- Remove ENA/ENB jumpers to enable PWM speed control

### H2.4 — Pin Map (define and document)

| Function         | L298N Pin | Pi GPIO (BCM) |
|------------------|-----------|---------------|
| Left Forward     | IN1       | TBD           |
| Left Backward    | IN2       | TBD           |
| Right Forward    | IN3       | TBD           |
| Right Backward   | IN4       | TBD           |
| Left Speed (PWM) | ENA       | TBD           |
| Right Speed (PWM)| ENB       | TBD           |

### H2.5 — Motor Validation
- Manually set GPIO HIGH/LOW from Python to confirm:
  - Both sides spin forward
  - Both sides spin backward
  - Left-only and right-only for turning
  - PWM speed variation works

---

## Phase H3: Ultrasonic Sensor + Servo Mount

### H3.1 — Servo Mount
- Mount servo motor at the front of the chassis
- Attach ultrasonic sensor (HC-SR04) on top of the servo horn
- Servo allows ultrasonic to scan left, center, right

### H3.2 — Servo Wiring
- Servo signal wire → Pi GPIO pin (PWM-capable)
- Servo VCC → L298N 5V output
- Servo GND → common ground

### H3.3 — Ultrasonic Wiring
- TRIG → Pi GPIO pin
- ECHO → Pi GPIO pin (use voltage divider: 5V echo → 3.3V safe for Pi)
  - 1kΩ resistor between ECHO and GPIO
  - 2kΩ resistor between GPIO and GND
- VCC → L298N 5V output
- GND → common ground

### H3.4 — Pin Map (define and document)

| Function       | Component  | Pi GPIO (BCM) |
|----------------|------------|---------------|
| Servo Signal   | Servo      | TBD           |
| Ultrasonic TRIG| HC-SR04    | TBD           |
| Ultrasonic ECHO| HC-SR04    | TBD (via divider) |

### H3.5 — Sensor Validation
- Servo sweeps left (0°), center (90°), right (180°) from Python
- Ultrasonic reads distance at each position
- Readings are stable and consistent (±2 cm tolerance)

---

---

## Phase H5: Full Hardware Integration

### H5.1 — Mount Everything on Chassis
- Pi, powerbank, camera, L298N, battery, servo+ultrasonic
- Secure all wires (zip ties, tape) — loose wires cause intermittent failures
- Keep motor wires away from camera

### H5.2 — Full System Power-On Test
- Power on both circuits
- Manually run each subsystem test from SSH
- Confirm no interference between subsystems

---

# PART B: SOFTWARE PHASES

---

## Phase S1: Project Structure and Base Setup

### S1.1 — Folder Structure
```
rpa/
├── context.md
├── PHASES.md
├── CLAUDE.md
├── config/
│   └── settings.py          # All pins, thresholds, constants
├── modules/
│   ├── __init__.py
│   ├── motor.py              # Motor control (forward, backward, turn, stop)
│   ├── ultrasonic.py         # Distance measurement
│   ├── servo.py              # Servo sweep control
│   ├── obstacle.py           # Obstacle avoidance logic (uses ultrasonic + servo)
│   ├── camera.py             # Camera capture and frame provider
│   ├── detector.py           # Red object detection (OpenCV)
│   └── transmitter.py        # Send image to PC
├── streaming/
│   └── server.py             # Flask MJPEG streaming server
├── main.py                   # Main controller (state machine)
├── pc_server.py              # Runs on PC — receives image data
└── requirements.txt
```

### S1.2 — Configuration File (`config/settings.py`)
Define all constants in one place:
- GPIO pin numbers (motors, servo, ultrasonic)
- Motor speed defaults (PWM duty cycle)
- Ultrasonic thresholds (emergency: 15cm, avoidance: 25cm)
- Red HSV range (lower and upper bounds)
- Minimum contour area for detection
- Detection confirmation frame count

- PC server IP and port
- Demo mode duration (seconds)
- Streaming port

---

## Phase S2: Motor Control Module

### S2.1 — `modules/motor.py`
Functions to implement:
- `setup()` — initialize GPIO pins, set PWM frequency
- `forward(speed)` — both sides forward
- `backward(speed)` — both sides backward
- `turn_left(speed)` — right side forward, left side stop/backward
- `turn_right(speed)` — left side forward, right side stop/backward
- `stop()` — all motors stop
- `cleanup()` — stop motors and release GPIO

### S2.2 — Validation
- Call each function from a test script
- Confirm rover moves correctly in all directions
- Confirm `stop()` halts all motion immediately

---

## Phase S3: Ultrasonic + Servo + Obstacle Avoidance

### S3.1 — `modules/ultrasonic.py`
- `get_distance()` — trigger pulse, measure echo, return distance in cm
- Handle timeout (no echo = no obstacle or sensor error)
- Average multiple readings for stability

### S3.2 — `modules/servo.py`
- `look_left()` — rotate to ~30°
- `look_center()` — rotate to ~90°
- `look_right()` — rotate to ~150°
- `look_at(angle)` — rotate to specific angle
- Small delay after each move for servo to settle

### S3.3 — `modules/obstacle.py`
Obstacle avoidance logic combining ultrasonic + servo + motor:
```
function check_and_avoid():
    distance = get_distance()
    if distance <= EMERGENCY_STOP:
        stop()
        backward briefly
    if distance <= AVOIDANCE_THRESHOLD:
        stop()
        look_left() → measure left_distance
        look_right() → measure right_distance
        look_center() → reset
        if left_distance > right_distance:
            turn_left()
        else:
            turn_right()
        short turn duration
        resume forward
```

### S3.4 — Validation
- Place obstacles at various distances
- Confirm rover stops and turns away correctly
- Confirm no collision at normal operating speed

---

## Phase S4: Camera and Red Object Detection

### S4.1 — `modules/camera.py`
- `setup()` — initialize Picamera2, configure resolution and format
- `get_frame()` — return current frame as numpy array (for OpenCV)
- `capture_image(filename)` — save high-resolution image to file
- Camera runs continuously; frames shared via thread-safe mechanism

### S4.2 — `modules/detector.py`
Red detection pipeline:
```
function detect_red(frame):
    hsv = cv2.cvtColor(frame, COLOR_BGR2HSV)

    # Red wraps around hue 0/180, need two ranges
    lower_red1 = (0, 120, 70)
    upper_red1 = (10, 255, 255)
    lower_red2 = (170, 120, 70)
    upper_red2 = (180, 255, 255)

    mask1 = cv2.inRange(hsv, lower_red1, upper_red1)
    mask2 = cv2.inRange(hsv, lower_red2, upper_red2)
    mask = mask1 | mask2

    contours = cv2.findContours(mask, ...)
    filter contours by area > MIN_CONTOUR_AREA
    if valid contour found:
        return True, contour_data
    return False, None
```

### S4.3 — Multi-Frame Confirmation
- Detection must be `True` for N consecutive frames (e.g., 5 frames)
- Prevents false positives from lighting, reflections, or noise
- Use a simple counter: increment on detect, reset on no-detect

### S4.4 — Validation
- Point camera at red object → confirm detection
- Point at non-red objects → confirm no false positive
- Test under different lighting conditions
- Tune HSV ranges and contour area threshold as needed

---

---

## Phase S6: Data Transmission

### S6.1 — `modules/transmitter.py` (Rover Side)
- `send_detection(image_path, timestamp)`:
  - HTTP POST to PC server with multipart form data
  - Include image file and timestamp
  - Handle connection errors (retry once, then continue mission)

### S6.2 — `pc_server.py` (PC Side)
- Flask app running on PC
- `POST /detection` endpoint:
  - Receives image file and timestamp
  - Saves image to disk with timestamp filename
  - Returns 200 OK

### S6.3 — Validation
- Run PC server on laptop
- Send test image from rover
- Confirm image received and saved correctly

---

## Phase S7: Live Video Streaming

### S7.1 — `streaming/server.py`
- Flask app running on the rover
- Route `/video` serves MJPEG stream
- Generator function yields JPEG frames continuously
- Frames sourced from the same camera instance used by detector (shared resource)

### S7.2 — Thread Safety
- Camera frames shared between detection thread and streaming thread
- Use `threading.Lock` or `threading.Event` for safe frame access
- Streaming must not starve detection of frames

### S7.3 — Validation
- Start streaming server
- Open `http://<rover-ip>:port/video` in browser
- Confirm live feed visible with acceptable latency
- Confirm detection still works while streaming

---

## Phase S8: Main Controller (State Machine)

### S8.1 — `main.py`
The central orchestrator. Manages all threads and state transitions.

```
Threads:
  1. Navigation thread     — motor control + obstacle avoidance (loop)
  2. Detection thread      — camera frames + red detection (loop)
  3. Streaming thread      — Flask MJPEG server

Shared State:
  - current_state: BOOT | SEARCH | DETECTED | DEMO_CONTINUE
  - latest_frame: numpy array (thread-safe)
  - detection_flag: threading.Event

State Machine Logic:
  BOOT:
    → setup all modules
    → start streaming server thread
    → transition to SEARCH

  SEARCH:
    → navigation thread: forward + obstacle avoidance
    → detection thread: process frames, check for red
    → on confirmed detection: set detection_flag → DETECTED

  DETECTED:
    → stop motors
    → capture high-res image
    → send image to PC via transmitter
    → start demo timer
    → transition to DEMO_CONTINUE

  DEMO_CONTINUE:
    → resume forward + obstacle avoidance
    → run for configured duration (e.g., 60 seconds)
    → on timer expiry: stop motors → END (or loop to SEARCH)
```

### S8.2 — Auto-Start on Boot
- Create a systemd service or use `rc.local` / crontab `@reboot`
- Service runs `main.py` on Pi boot
- Ensure script waits for network (for streaming) before full start

### S8.3 — Graceful Shutdown
- Handle `SIGINT` / `SIGTERM`
- Stop all motors
- Release camera
- Cleanup GPIO
- Stop Flask server

---

## Phase S9: Integration Testing

### S9.1 — Subsystem Integration
Test combinations incrementally:
1. Motors + obstacle avoidance (no camera) — rover navigates without crashing
2. Camera + detection (no motors) — red detection works reliably
3. Motors + obstacle + detection — rover navigates and detects red, stops on detection
4. Add transmission — data reaches PC
5. Add streaming — full system running

### S9.2 — Full System Test
- Power on rover in test area with red object placed
- Rover should:
  - Start automatically
  - Stream video (verify from PC browser)
  - Navigate and avoid obstacles
  - Detect red object and stop
  - Send image to PC
  - Resume movement for demo duration
  - Stop after demo timer expires

### S9.3 — Edge Cases to Test

- Red object at edge of frame — detection should still trigger
- Multiple obstacles in sequence — rover should navigate through
- WiFi drop during transmission — rover should not crash, retry or skip
- Low battery — observe behavior, ensure no erratic motor behavior

---

## Phase S10: Tuning and Demo Preparation

### S10.1 — Parameter Tuning
- HSV red range — adjust for demo environment lighting
- Contour area threshold — balance sensitivity vs false positives
- Obstacle distances — tune for rover speed and reaction time
- Motor speed — find balance between coverage speed and obstacle safety
- Demo timer duration — enough to show intelligence, not too long

### S10.2 — Demo Checklist
- [ ] Rover starts on power-on without any manual input
- [ ] Live stream accessible from PC browser
- [ ] Rover avoids all obstacles without collision
- [ ] Red object detected, rover stops
- [ ] Image received on PC
- [ ] Rover resumes after detection
- [ ] System runs full demo without crash or hang
- [ ] Graceful shutdown on power off or kill signal
