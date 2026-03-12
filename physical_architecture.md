# Rover Physical System Architecture

## Core Platforms
The physical architecture is split between a mobile robot (Rover) based on a single-board computer and a stationary remote computing device (PC Server).

### 1. Rover Onboard Computer
**Raspberry Pi (Model implied: 4)**
*   Acts as the central control unit for all physical onboard systems.
*   Interfaces with modules using general-purpose input/output (GPIO).
*   Powered by an onboard battery pack capable of supplying stable voltage to the Pi and various logic paths.

### 2. Drive System (Differential Drive)
**L298N Motor Driver Controller**
*   Controls the direction and speed of the DC motors.
*   **Wiring**: 
    *   Left Motors direction pins (IN1, IN2) connected to Pi GPIO 17 & 27.
    *   Right Motors direction pins (IN3, IN4) connected to Pi GPIO 22 & 23.
    *   Speed control relies on hardware PWM pins Enable A (GPIO 12) and Enable B (GPIO 13).
*   **DC Motors**: 4-wheel drive system where the two left motors share a driver channel, and the two right motors share the other. Navigation uses skid-steering (tank controls).

### 3. Perception & Environment Sensing
**Ultrasonic Range Sensor (HC-SR04)**
*   Used for obstacle avoidance and distance measurement in front of the rover.
*   **Wiring**:
    *   Trigger pin connected directly to GPIO 25.
    *   Echo pin (5V logic) requires a **Voltage Divider** to step down to 3.3V logic before connecting to GPIO 5 to safely interface with the Raspberry Pi.

**Scanning System Servo Motor**
*   Mounts the ultrasonic sensor, allowing it to sweep side-to-side (center, left limit, right limit) to measure multiple paths.
*   **Wiring**: Connected to an independent PWM capable pin (GPIO 24). Hardware timing control is handled by the `pigpio` daemon.

**Camera Module**
*   **Device**: Compatible Pi Camera Module using the `Picamera2` pipeline.
*   Used for low-latency RGB video streaming and high-resolution JPEG capture (1920x1080) for leaf/weed identification. 

### 4. Remote PC Server (Offboard Compute)
**Workstation / Server PC**
*   Receives high-resolution image bursts transmitted over the local Wi-Fi network.
*   Physically separated due to the intensive floating-point loads required for the Support Vector Machine (SVM) weed classification model, preventing performance drops in the Rover's tight control loops.
*   Communicates with the rover via REST API endpoints over IPv4 (`172.16.61.172:5000`).

## Power Architecture Flow
While not explicitly mapped in the software configurations, a typical deployment for this architecture implies:
1.  **High-Current Source (e.g., 2S-3S LiPo or Battery Pack)**: Powers the L298N motor driver for raw DC motor movement.
2.  **Logic Power Step-down (5V regulator / BEC)**: Supplies 5V to the Raspberry Pi and the Servo motor.
3.  **Sensor Power**: The HC-SR04 and Camera draw 5V & 3.3V directly from the Raspberry Pi logic rails respectively.
