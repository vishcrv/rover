# config/settings.py — Central configuration for the rover

# =============================================================================
# GPIO PIN MAPPING (BCM numbering)
# =============================================================================

# Motor driver (L298N)
MOTOR_LEFT_FWD = 17      # IN1
MOTOR_LEFT_BWD = 27      # IN2
MOTOR_RIGHT_FWD = 22     # IN3
MOTOR_RIGHT_BWD = 23     # IN4
MOTOR_LEFT_PWM = 12      # ENA (hardware PWM)
MOTOR_RIGHT_PWM = 13     # ENB (hardware PWM)

# Servo (obstacle scanning)
SERVO_PIN = 24            # PWM capable

# Ultrasonic sensor (HC-SR04)
ULTRASONIC_TRIG = 25
ULTRASONIC_ECHO = 5       # wired through voltage divider (5V → 3.3V)

# =============================================================================
# MOTOR SETTINGS
# =============================================================================

PWM_FREQUENCY = 1000      # Hz
DEFAULT_SPEED = 60        # duty cycle 0–100
TURN_SPEED = 50           # duty cycle during turns
TURN_DURATION = 0.4       # seconds to turn before resuming forward

# =============================================================================
# ULTRASONIC / OBSTACLE AVOIDANCE
# =============================================================================

EMERGENCY_STOP_CM = 15    # immediate stop distance
AVOIDANCE_TRIGGER_CM = 25 # start avoidance maneuver
ULTRASONIC_TIMEOUT = 0.04 # seconds — max wait for echo (~6.8m range)
ULTRASONIC_SAMPLES = 3    # number of readings to average

# =============================================================================
# SERVO (pigpio pulsewidth control)
# =============================================================================

SERVO_LEFT_PW = 1580      # μs — tested left limit
SERVO_CENTER_PW = 1500    # μs — neutral center
SERVO_RIGHT_PW = 1420     # μs — tested right limit
SERVO_MOVE_DELAY = 1.0    # seconds — pause at each sweep position
SERVO_SCAN_STEP_PW = 20   # μs — step between scan readings
SERVO_SCAN_SETTLE = 0.3   # seconds — settle before ultrasonic read

# =============================================================================
# LEAF DETECTION — Preprocessing
# =============================================================================

# Green colour pre-filter (HSV) — tightened to reject synthetic/painted greens
# Hue 35–82 covers natural leaf greens; saturation ≥80 requires vivid colour
# (painted walls, faded plastic, and shadows all fall below S=80)
GREEN_LOWER = (35, 80, 40)        # (hue_min, sat_min, val_min)
GREEN_UPPER = (82, 255, 255)      # (hue_max, sat_max, val_max)
USE_GREEN_MASK = True             # True = use green HSV mask; False = adaptive threshold
BLUR_KERNEL_SIZE = 5              # Gaussian blur kernel (must be odd)

# Minimum fraction of green pixels within the bounding rect for a valid blob
# Rejects thin grass blades and sparse detections that happen to be green
GREEN_VEGETATION_RATIO = 0.25

# Canny edge detection
CANNY_LOW = 50                    # lower hysteresis threshold
CANNY_HIGH = 150                  # upper hysteresis threshold

# =============================================================================
# LEAF DETECTION — Shape Filtering
# =============================================================================

LEAF_MIN_AREA = 800               # pixels² — small blobs (noise, grass tips) rejected
LEAF_MAX_AREA = 100000            # pixels² — ignore huge blobs
LEAF_ASPECT_RATIO_MIN = 0.3      # width/height lower bound
LEAF_ASPECT_RATIO_MAX = 3.5      # width/height upper bound
LEAF_SOLIDITY_MIN = 0.60         # tightened: smoother convex boundary required (was 0.5)
LEAF_CIRCULARITY_MIN = 0.18      # slightly tighter lower bound (was 0.15)
LEAF_CIRCULARITY_MAX = 0.80      # slightly tighter upper bound (was 0.85)

# Extent = contour area / bounding-rect area
# Rejects thin elongated blades (grass) which fill very little of their bounding box
LEAF_EXTENT_MIN = 0.35

# Internal edge density — ratio of Canny edge pixels inside the blob to blob area.
# Real leaves have veins/texture scoring 0.04–0.15; flat uniform objects score ~0.
LEAF_EDGE_DENSITY_MIN = 0.04

MIN_CONTOUR_AREA = 800            # legacy alias kept in sync
DETECTION_CONFIRM_FRAMES = 8      # raised from 5 → 8 frames (0.4s at 20fps) to reduce transients

# =============================================================================
# CAMERA
# =============================================================================

CAMERA_WIDTH = 640
CAMERA_HEIGHT = 480
CAMERA_FPS = 20
CAPTURE_WIDTH = 1920      # high-res capture on detection
CAPTURE_HEIGHT = 1080
CAPTURE_DIR = "/home/raspberry/captures"

# =============================================================================
# DATA TRANSMISSION
# =============================================================================

PC_SERVER_IP = "172.16.61.127"   # PC's IP on the same network as the rover
PC_SERVER_PORT = 5000
PC_DETECTION_ENDPOINT = "/detection"
TRANSMIT_TIMEOUT = 5              # seconds — HTTP request timeout

# =============================================================================
# LIVE STREAMING
# =============================================================================

STREAM_HOST = "0.0.0.0"
STREAM_PORT = 8080

# =============================================================================
# DEMO MODE
# =============================================================================

DEMO_DURATION = 2         # seconds to continue after red detection
