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

# Green colour pre-filter (HSV)
GREEN_LOWER = (35, 50, 50)
GREEN_UPPER = (85, 255, 255)
USE_GREEN_MASK = True             # True = use green HSV mask; False = adaptive threshold
BLUR_KERNEL_SIZE = 5              # Gaussian blur kernel (must be odd)

# Canny edge detection
CANNY_LOW = 50                    # lower hysteresis threshold
CANNY_HIGH = 150                  # upper hysteresis threshold

# =============================================================================
# LEAF DETECTION — Shape Filtering
# =============================================================================

LEAF_MIN_AREA = 500               # pixels² — ignore tiny contours
LEAF_MAX_AREA = 100000            # pixels² — ignore huge blobs
LEAF_ASPECT_RATIO_MIN = 0.3      # width/height lower bound
LEAF_ASPECT_RATIO_MAX = 3.5      # width/height upper bound
LEAF_SOLIDITY_MIN = 0.5          # contour area / convex hull area
LEAF_CIRCULARITY_MIN = 0.15      # leaves are not perfectly circular
LEAF_CIRCULARITY_MAX = 0.85      # ... nor are they perfect circles

MIN_CONTOUR_AREA = 500            # legacy alias (used nowhere new)
DETECTION_CONFIRM_FRAMES = 5      # consecutive frames before confirming detection

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

PC_SERVER_IP = "172.16.61.52"   # PC's IP on the same network as the rover
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
