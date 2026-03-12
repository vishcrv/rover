# Rover System Architecture

## Overview
The Rover system is designed to autonomously navigate, avoid obstacles, detect leaves/weeds, stream live video to a web interface, and transmit detection data to a centralized PC server for further classification using a trained Support Vector Machine (SVM) model. It operates across two main environments: the onboard Raspberry Pi (rover) and a remote PC server.

## Folder Structure
- `config/`: Central configuration.
- `modules/`: Core hardware control modules (motors, servo, camera, sensors) and on-device edge detection logic.
- `streaming/`: MJPEG live video streaming server.
- `tests/`: Unit test suite covering all hardware components.
- `weed detection/`: Offline machine learning pipeline, training scripts, preprocessing modules, and saved SVM models (`.pkl` files).
- Root Level: `main.py` (rover state machine), `pc_server.py` (PC side receiver), `weed_classifier.py` (PC classifier wrapper), and `rover.service` (systemd auto-start).

---

## Core Components

### 1. Main Controller (`main.py`)
The main script manages the rover's state machine using a multithreaded architecture to ensure navigation and detection work seamlessly.
- **States:** `BOOT`, `SEARCH`, `DETECTED`, `SHUTDOWN`.
- **Navigation Loop:** Continuously moves the rover forward while triggering obstacle avoidance maneuvers (checking ultrasonic sensor input).
- **Detection Loop:** Asynchronously grabs camera frames, invokes the edge detector, and identifies leaf-like shapes.
- **Action Sequence on Detection:** Stop motors -> Capture high-res image -> Post image to PC Server -> Wait (demo duration) -> Perform full-range servo scan for clear paths -> Turn towards best direction -> Resume Search.

### 2. Edge Detection Pipeline (`modules/detector.py`, `modules/leaf_*.py`)
The onboard detection relies on OpenCV image processing instead of heavy deep learning models to maintain high FPS on the Raspberry Pi:
- **Preprocessing:** Color masking (HSV green range) combined with adaptive thresholding and Gaussian blur (`leaf_preprocessor.py`).
- **Edge Extraction:** Canny edge detection generates robust object outlines.
- **Contour Filtering:** Extensive geometric constraint checks, eliminating non-leaf objects based on Area, Aspect Ratio, Solidity, and Circularity (`leaf_filter.py`).
- **Annotation:** Overlays green bounding boxes, contour lines, and text labels indicating area size directly onto the video feed.

### 3. Hardware Modules (`modules/`)
Provides hardware abstraction layers using `RPi.GPIO` and `pigpio`.
- `motor.py`: Manages the L298N motor driver using hardware PWM signals for fine speed control during turning and driving.
- `servo.py`: Uses precise pulsewidth logic to sweep the ultrasonic sensor for wide-angle environment scanning.
- `ultrasonic.py`: Handles distance estimation using HC-SR04 sonar pulses, mapping echoes to centimeters.
- `camera.py`: Integrates `Picamera2` for low-latency RGB frame capturing and high-resolution JPEG bursts.
- `obstacle.py`: Implements logic comparing sonar distance against `AVOIDANCE_TRIGGER_CM` to trigger emergency stops.
- `transmitter.py`: REST HTTP client responsible for sending captured images to the PC Server webhook.

### 4. Live Streaming (`streaming/server.py`)
Provides real-time visualization of what the rover sees and how it interprets the environment.
- Run as an integrated Flask MJPEG server directly on the rover (Port 8080).
- Employs a background rendering thread to ensure video streaming doesn't block the main control loop.
- Exposes two routes: `/video` (annotated frames with object detections) and `/video_raw` (original camera feed).

### 5. Centralized PC Server (`pc_server.py`, `weed_classifier.py`)
Responsible for computationally heavy analysis such as evaluating machine learning models.
- Flask webhook listener running on a designated PC workstation (Port 5000).
- Accepts POST requests containing timestamps and high-res images (`/detection`).
- **Classifier (`weed_classifier.py`):** Loads a pre-trained Support Vector Machine (SVM) from `weed detection/models/`. It processes the received image using the same step-by-step feature extraction pipeline used in training, outputting weed probabilities.
- **Data Logging:** Generates `detection_logs.json` containing the image path, geographical coordinates (simulated list mapping), weed labels, and confidence probability.

### 6. Configuration & System Context (`config/settings.py`)
Functions as the global state and tuning repository.
- GPIO pin mappings and PWM frequency setups.
- Operational logic variables: default motor speeds, turn times, minimum sonar safe distances, and servo sweep limits.
- Computer vision thresholds for HSV ranges, Canny cutoffs, and leaf boundary ratios.
- Network values like PC target IPs and Streaming endpoints.
- Auto-started via an OS-level `rover.service` daemon configuration.
