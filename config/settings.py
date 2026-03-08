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
# RED OBJECT DETECTION (HSV)
# =============================================================================

# Red wraps around hue 0/180 — two ranges needed
RED_LOWER_1 = (0, 70, 50)
RED_UPPER_1 = (10, 255, 255)
RED_LOWER_2 = (170, 70, 50)
RED_UPPER_2 = (180, 255, 255)

MIN_CONTOUR_AREA = 500            # pixels² — ignore smaller contours as noise
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

PC_SERVER_IP = "172.16.61.71"     # PC's IP on the same network as the rover
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
