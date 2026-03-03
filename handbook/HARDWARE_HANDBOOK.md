# HARDWARE_HANDBOOK.md — Complete Build & Wiring Guide

Reference: [PHASES.md](PHASES.md) (Phases H1–H5) | [config/settings.py](config/settings.py)

---

# MASTER PIN MAP

Before anything, here is the complete pin assignment. Print this and keep it next to you while wiring.

## Raspberry Pi 4 GPIO — All Connections

| BCM GPIO | Physical Pin | Function            | Connects To              | Wire Color (suggested) |
|----------|-------------|----------------------|--------------------------|------------------------|
| GPIO 17  | Pin 11      | Left Motor Forward   | L298N IN1                | Orange                 |
| GPIO 27  | Pin 13      | Left Motor Backward  | L298N IN2                | Yellow                 |
| GPIO 22  | Pin 15      | Right Motor Forward  | L298N IN3                | Orange                 |
| GPIO 23  | Pin 16      | Right Motor Backward | L298N IN4                | Yellow                 |
| GPIO 12  | Pin 32      | Left Motor Speed PWM | L298N ENA                | Blue                   |
| GPIO 13  | Pin 33      | Right Motor Speed PWM| L298N ENB                | Blue                   |
| GPIO 18  | Pin 12      | Servo Signal         | Servo (signal wire)      | White                  |
| GPIO 24  | Pin 18      | Ultrasonic TRIG      | HC-SR04 TRIG             | Green                  |
| GPIO 25  | Pin 22      | Ultrasonic ECHO      | Voltage divider output   | Purple                 |
| GPIO 15  | Pin 10      | GPS RX (UART RXD)    | NEO-6M TX                | White                  |
| GPIO 14  | Pin 8       | GPS TX (UART TXD)    | NEO-6M RX (optional)     | Grey                   |
| GND      | Pin 6       | Common Ground (main) | L298N GND                | Black                  |
| GND      | Pin 9       | GPS Ground           | NEO-6M GND               | Black                  |
| GND      | Pin 14      | Ultrasonic divider   | Divider bottom resistor  | Black                  |
| 3.3V     | Pin 1       | GPS Power            | NEO-6M VCC               | Red                    |
| CSI Port | —           | Camera               | Pi Camera v2 ribbon      | —                      |

## Raspberry Pi 4 — Physical Pin Layout Reference

```
                    +-----+-----+
          3.3V [1]  | o   o |  [2] 5V
  (GPS VCC) 3.3V   |       |       5V
                    +-------+
   GPIO 2 (SDA) [3] | o   o | [4] 5V
                    +-------+
   GPIO 3 (SCL) [5] | o   o | [6] GND  ← COMMON GROUND TO L298N
                    +-------+
       GPIO 4   [7] | o   o | [8] GPIO 14 (TXD) → NEO-6M RX
                    +-------+
           GND  [9] | o   o | [10] GPIO 15 (RXD) ← NEO-6M TX
                    +-------+
      GPIO 17  [11] | o   o | [12] GPIO 18 → SERVO SIGNAL
   L298N IN1 ↗     +-------+      ↖ Servo
      GPIO 27  [13] | o   o | [14] GND ← Ultrasonic divider GND
   L298N IN2 ↗     +-------+
      GPIO 22  [15] | o   o | [16] GPIO 23
   L298N IN3 ↗     +-------+      ↖ L298N IN4
          3.3V [17] | o   o | [18] GPIO 24 → ULTRASONIC TRIG
                    +-------+
      GPIO 10  [19] | o   o | [20] GND
                    +-------+
       GPIO 9  [21] | o   o | [22] GPIO 25 ← ULTRASONIC ECHO (via divider)
                    +-------+
      GPIO 11  [23] | o   o | [24] GPIO 8
                    +-------+
           GND [25] | o   o | [26] GPIO 7
                    +-------+
       GPIO 0  [27] | o   o | [28] GPIO 1
                    +-------+
       GPIO 5  [29] | o   o | [30] GND
                    +-------+
       GPIO 6  [31] | o   o | [32] GPIO 12 → L298N ENA (Left PWM)
                    +-------+
      GPIO 13  [33] | o   o | [34] GND
   L298N ENB ↗     +-------+
      GPIO 19  [35] | o   o | [36] GPIO 16
                    +-------+
      GPIO 26  [37] | o   o | [38] GPIO 20
                    +-------+
           GND [39] | o   o | [40] GPIO 21
                    +-------+
```

---

# PHASE H1: POWER SYSTEM

## What You Need
- 1x Raspberry Pi 4 (4GB or 8GB)
- 1x 22000mAh Powerbank (must support 5V/3A output, USB-C)
- 1x Pi Camera Module v2
- 1x 2S LiPo/Li-ion battery (7.4V nominal, 8.4V fully charged)
- 1x L298N Motor Driver module
- Jumper wires (male-to-female, male-to-male)
- Multimeter

---

## Step 1.1 — Pi + Powerbank

### What to do
1. Take the USB-C cable from the powerbank.
2. Plug it into the Raspberry Pi 4 USB-C power port (the port at the bottom-left when looking at the board with the USB ports facing you).
3. Turn on the powerbank.
4. The Pi should show a red LED (power) and a green LED (activity/boot).

### Verify
- The Pi boots into the desktop or terminal (connect a monitor via micro-HDMI, or SSH in).
- Run from terminal:
  ```
  vcgencmd get_throttled
  ```
  - Output should be `throttled=0x0` — this means no undervoltage.
  - If you see `0x50005` or similar, the powerbank is not supplying enough current. Use a different powerbank or cable.

### Common Problems
| Symptom | Cause | Fix |
|---------|-------|-----|
| Pi doesn't boot | Powerbank in low-power mode | Press powerbank button, try a different USB port on it |
| Lightning bolt icon on screen | Undervoltage | Use a cable rated for 3A, shorter cable |
| Pi reboots randomly | Current drops under load | Use a higher capacity powerbank output |

---

## Step 1.2 — Pi Camera v2

### What to do
1. **Power off the Pi** (always power off before connecting the camera ribbon).
2. Locate the CSI camera port on the Pi — it's the long thin connector between the audio jack and the HDMI ports, labeled "CAMERA".
3. Gently pull up the black plastic clip on the CSI connector.
4. Insert the camera ribbon cable:
   - The blue side of the ribbon faces the Ethernet/USB ports.
   - The silver contacts face the HDMI ports.
5. Push the black clip back down to lock the ribbon.
6. Power on the Pi.

### Verify
SSH into the Pi and run:
```bash
# Check if camera is detected
libcamera-hello --list-cameras

# Expected output should show:
# Available cameras
# -----------------
# 0 : imx219 [3280x2464] ...

# Quick test — show preview for 3 seconds
libcamera-hello -t 3000

# Capture a test image
libcamera-still -o test.jpg
ls -la test.jpg
```

### Common Problems
| Symptom | Cause | Fix |
|---------|-------|-----|
| "No cameras available" | Ribbon not seated properly | Reseat ribbon, check blue side orientation |
| "Camera not detected" | Camera interface disabled | Run `sudo raspi-config` → Interface → Camera → Enable, reboot |
| Blurry image | Lens focus | Gently rotate the tiny lens on the camera module |

---

## Step 1.3 — 2S Battery + L298N

### L298N Module Layout
```
    +----------------------------------------------+
    |  L298N Motor Driver Module                    |
    |                                               |
    |  [OUT1] [OUT2]          [OUT3] [OUT4]         |
    |   Left motors            Right motors         |
    |                                               |
    |  +12V  GND  +5V                               |
    |   |     |    |     ← Power terminal block     |
    |   ↑     ↑    ↑                                |
    |  2S    Common  5V output (if jumper ON)        |
    | Battery GND   for servo & ultrasonic           |
    |                                               |
    |  [ENA]  [IN1] [IN2]  [IN3] [IN4]  [ENB]      |
    |   ↑      ↑     ↑      ↑     ↑      ↑         |
    |  Pi 12  Pi 17  Pi 27  Pi 22 Pi 23  Pi 13     |
    |                                               |
    | [5V JUMPER] ← Keep ON if battery ≤ 12V        |
    +----------------------------------------------+
```

### What to do

1. **Locate the L298N power terminal block** (3 screw terminals labeled `+12V`, `GND`, `+5V`).

2. **Connect the 2S battery:**
   - Battery positive (+) wire → `+12V` terminal. Tighten screw.
   - Battery negative (-) wire → `GND` terminal. Tighten screw.

3. **Check the 5V regulator jumper:**
   - There is a small jumper cap near the `+12V` terminal.
   - **KEEP THIS JUMPER ON** — it enables the onboard 5V regulator.
   - This is only safe if the input voltage is ≤ 12V (2S battery = 7.4–8.4V, so it's fine).
   - The `+5V` terminal now **outputs** 5V (you'll use this for servo and ultrasonic).

4. **Do NOT connect the Pi to the L298N 5V output.** The Pi gets power from the powerbank only. Feeding 5V from two sources can damage the Pi.

### Verify
With the 2S battery connected and powerbank OFF (Pi not powered yet):
```
Using a multimeter:
1. Set to DC voltage mode.
2. Measure across +12V and GND terminals → should read 7.4–8.4V.
3. Measure across +5V and GND terminals → should read ~5.0V (±0.2V).
```

---

## Step 1.4 — Common Ground (CRITICAL)

### Why this matters
The Pi and L298N run on separate power supplies (powerbank vs 2S battery). Without a shared ground reference, the Pi's GPIO signals (3.3V) won't be understood by the L298N. **This is the #1 cause of "I wired everything but nothing works."**

### What to do
1. Take a male-to-female jumper wire (black).
2. Connect one end to **Raspberry Pi Physical Pin 6 (GND)**.
3. Connect the other end to the **L298N GND terminal** (the same terminal where the battery negative is connected — you can use the screw terminal or solder/crimp another wire to it).

### Verify
```
Using a multimeter:
1. Set to DC voltage mode.
2. Touch one probe to any Pi GND pin.
3. Touch the other probe to the L298N GND terminal.
4. Reading should be 0.00V (or very close to 0V).
   - If you see any voltage here, the ground connection is bad. Recheck.
```

---

## Step 1.5 — Full Power System Validation

### Do this before connecting ANY motors or sensors

1. Connect the powerbank to the Pi (USB-C).
2. Connect the 2S battery to the L298N.
3. Connect the common ground wire (Pi GND → L298N GND).
4. Turn on the powerbank — Pi should boot.

### Multimeter checklist

| Measurement | Probe + | Probe - | Expected |
|-------------|---------|---------|----------|
| 2S Battery | Battery + | Battery - | 7.4–8.4V |
| L298N 5V output | +5V terminal | GND terminal | 4.8–5.2V |
| Common ground | Pi Pin 6 | L298N GND | 0.00V |
| Pi 3.3V rail | Pi Pin 1 | Pi Pin 6 | 3.3V |

If all four measurements are correct, power system is good. Move to Phase H2.

---

# PHASE H2: MOTORS + L298N

## What You Need
- 4x BO Motors (3–6V DC geared motors)
- 1x Robot chassis (4WD)
- 4x Wheels
- 8x Jumper wires (for L298N control pins to Pi)
- Small screwdriver (for L298N screw terminals)

---

## Step 2.1 — Chassis Assembly

1. Mount the 4 BO motors into the chassis motor brackets.
   - Two motors on the left side, two on the right side.
   - Make sure all motors face the same direction (shafts pointing outward).
2. Attach wheels to the motor shafts.
3. Mount the L298N driver board on the chassis using standoffs or double-sided tape.
   - **Use standoffs** — if the L298N bottom touches the metal chassis, it can short circuit.

---

## Step 2.2 — Motor Wiring to L298N

### Understanding the L298N output terminals

The L298N has 4 output terminals:
```
[OUT1] [OUT2]     [OUT3] [OUT4]
  Left motors       Right motors
```

### Wiring

**Left side (2 motors in parallel):**
```
Left-Front Motor wire A ──┐
                          ├── twist together ──→ L298N OUT1 (screw terminal)
Left-Rear Motor wire A  ──┘

Left-Front Motor wire B ──┐
                          ├── twist together ──→ L298N OUT2 (screw terminal)
Left-Rear Motor wire B  ──┘
```

**Right side (2 motors in parallel):**
```
Right-Front Motor wire A ──┐
                           ├── twist together ──→ L298N OUT3 (screw terminal)
Right-Rear Motor wire A  ──┘

Right-Front Motor wire B ──┐
                           ├── twist together ──→ L298N OUT4 (screw terminal)
Right-Rear Motor wire B  ──┘
```

### How to connect parallel motors
- Strip about 1cm of insulation off each motor wire.
- Twist the two "A" wires of the same side together.
- Insert the twisted pair into the screw terminal and tighten firmly.
- Repeat for the "B" wires.

### Direction note
If a motor spins the wrong direction later during testing, simply swap its two wires at the screw terminal (swap A and B). Don't change any code.

---

## Step 2.3 — L298N Control Pins to Raspberry Pi

### Remove the ENA/ENB jumpers

The L298N has two small jumper caps on ENA and ENB:
```
[ENA jumper]  IN1  IN2    IN3  IN4  [ENB jumper]
```
- **Remove both jumper caps** (pull them off and keep them safe).
- Removing the jumpers lets us control motor speed via PWM from the Pi.
- If jumpers are left on, motors run at full speed only (no speed control).

### Wiring — L298N to Pi

Connect with male-to-female jumper wires:

| L298N Pin | → | Pi Physical Pin | Pi BCM GPIO | Function |
|-----------|---|----------------|-------------|----------|
| IN1       | → | Pin 11          | GPIO 17     | Left Forward |
| IN2       | → | Pin 13          | GPIO 27     | Left Backward |
| IN3       | → | Pin 15          | GPIO 22     | Right Forward |
| IN4       | → | Pin 16          | GPIO 23     | Right Backward |
| ENA       | → | Pin 32          | GPIO 12     | Left Speed (PWM) |
| ENB       | → | Pin 33          | GPIO 13     | Right Speed (PWM) |

### Wiring diagram
```
L298N                          Raspberry Pi 4
+-------------+                +------------------+
| IN1 --------+--- orange ---->| Pin 11 (GPIO 17) |
| IN2 --------+--- yellow ---->| Pin 13 (GPIO 27) |
| IN3 --------+--- orange ---->| Pin 15 (GPIO 22) |
| IN4 --------+--- yellow ---->| Pin 16 (GPIO 23) |
| ENA --------+--- blue ------>| Pin 32 (GPIO 12) |
| ENB --------+--- blue ------>| Pin 33 (GPIO 13) |
| GND --------+--- black ----->| Pin 6  (GND)     |  ← already done in H1
+-------------+                +------------------+
```

---

## Step 2.4 — Motor Testing

### Quick test (no project code needed)

SSH into the Pi and run Python interactively:

```python
python3
```

```python
import RPi.GPIO as GPIO
import time

GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)

# Setup direction pins
for pin in [17, 27, 22, 23]:
    GPIO.setup(pin, GPIO.OUT)
    GPIO.output(pin, GPIO.LOW)

# Setup PWM pins
GPIO.setup(12, GPIO.OUT)
GPIO.setup(13, GPIO.OUT)
pwm_left = GPIO.PWM(12, 1000)
pwm_right = GPIO.PWM(13, 1000)
pwm_left.start(0)
pwm_right.start(0)

# ---- TEST 1: Left motors forward ----
print("Left motors FORWARD...")
GPIO.output(17, GPIO.HIGH)  # IN1 high
GPIO.output(27, GPIO.LOW)   # IN2 low
pwm_left.ChangeDutyCycle(60)
time.sleep(2)
pwm_left.ChangeDutyCycle(0)
GPIO.output(17, GPIO.LOW)
print("Stopped")
time.sleep(1)

# ---- TEST 2: Right motors forward ----
print("Right motors FORWARD...")
GPIO.output(22, GPIO.HIGH)  # IN3 high
GPIO.output(23, GPIO.LOW)   # IN4 low
pwm_right.ChangeDutyCycle(60)
time.sleep(2)
pwm_right.ChangeDutyCycle(0)
GPIO.output(22, GPIO.LOW)
print("Stopped")
time.sleep(1)

# ---- TEST 3: All forward ----
print("ALL FORWARD...")
GPIO.output(17, GPIO.HIGH)
GPIO.output(22, GPIO.HIGH)
pwm_left.ChangeDutyCycle(60)
pwm_right.ChangeDutyCycle(60)
time.sleep(2)
pwm_left.ChangeDutyCycle(0)
pwm_right.ChangeDutyCycle(0)
GPIO.output(17, GPIO.LOW)
GPIO.output(22, GPIO.LOW)
print("Stopped")

# Cleanup
pwm_left.stop()
pwm_right.stop()
GPIO.cleanup()
print("Done!")
```

### Using the project test script

Once the project code is on the Pi:
```bash
cd /home/pi/rpa
python3 -m tests.test_motor
```

### What to check

| Test | Expected result | If wrong |
|------|----------------|----------|
| Left forward | Left wheels spin forward | Swap wire A and B on OUT1/OUT2 |
| Right forward | Right wheels spin forward | Swap wire A and B on OUT3/OUT4 |
| Left backward | Left wheels spin backward | Already handled if forward works |
| All forward | Rover moves forward in a straight line | If it curves, one side's motors may be wired differently — swap that side |
| PWM speed | Speed visibly changes between 30% and 100% | Check ENA/ENB jumpers are REMOVED |
| Stop | Wheels stop immediately | Check all direction pins go LOW |

### Troubleshooting

| Symptom | Cause | Fix |
|---------|-------|-----|
| No motor movement at all | Common ground missing | Connect Pi GND to L298N GND |
| Motors spin but very weakly | 2S battery low | Charge battery, check voltage |
| Only one side works | Bad connection on the other side | Check screw terminal connections |
| Motors spin at full speed, can't control | ENA/ENB jumpers still on | Remove jumper caps |
| Motors spin wrong direction | Wire polarity | Swap A and B wires at the screw terminal |
| Motors make noise but don't spin | Wheels too tight or motor stalled | Check if wheels spin freely by hand |

---

# PHASE H3: ULTRASONIC SENSOR + SERVO

## What You Need
- 1x HC-SR04 Ultrasonic sensor
- 1x SG90 or MG90S Servo motor
- 1x 1kΩ resistor (brown-black-red)
- 1x 2kΩ resistor (red-black-red) — or use 2x 1kΩ in series
- Jumper wires
- Small breadboard (optional, for the voltage divider)
- Hot glue or mounting bracket for servo

---

## Step 3.1 — Servo Motor

### Servo wire colors
Most servos have 3 wires:
```
Brown/Black = GND
Red         = VCC (power, 5V)
Orange/White = Signal (PWM)
```

### Wiring

| Servo Wire | → | Connects To | Notes |
|------------|---|-------------|-------|
| Brown/Black (GND) | → | L298N GND terminal | Common ground |
| Red (VCC) | → | L298N +5V terminal | Powered from motor battery via regulator |
| Orange (Signal) | → | Pi Pin 12 (GPIO 18) | PWM signal from Pi |

### Wiring diagram
```
Servo                     Connections
+-----------+
| GND ------+--- brown/black --→ L298N GND terminal
| VCC ------+--- red ----------→ L298N +5V terminal
| Signal ---+--- orange -------→ Pi Pin 12 (GPIO 18)
+-----------+
```

**Why power from L298N 5V and not from Pi?**
Servos draw high current spikes (up to 500mA). Drawing this from the Pi's 5V pin can cause voltage drops and crashes. The L298N 5V regulator can handle this load from the 2S battery.

---

## Step 3.2 — Ultrasonic Sensor (HC-SR04)

### HC-SR04 Pinout
```
+-------------------+
|  HC-SR04          |
|                   |
| VCC  TRIG  ECHO GND |
|  |    |     |    |  |
+--+----+-----+----+--+
```

### THE VOLTAGE DIVIDER (IMPORTANT)

The HC-SR04 ECHO pin outputs a 5V signal. The Raspberry Pi GPIO pins are **3.3V only**. Connecting 5V directly to a Pi GPIO **will permanently damage the Pi**.

You must use a voltage divider to drop the 5V ECHO signal to ~3.3V.

### Voltage divider circuit

```
HC-SR04 ECHO pin
       |
       |
    [1kΩ resistor]  (R1)
       |
       +----------→ Pi Pin 22 (GPIO 25)  ← safe 3.3V signal
       |
    [2kΩ resistor]  (R2)
       |
       |
     GND (Pi Pin 14)
```

**How it works:**
- Vout = Vin × R2 / (R1 + R2) = 5V × 2000 / (1000 + 2000) = 3.33V

**If you don't have a 2kΩ resistor:**
Use two 1kΩ resistors in series (end-to-end) to make 2kΩ.

### Building the divider

**Option A — On a mini breadboard:**
```
Breadboard layout:

Row 1:  HC-SR04 ECHO wire ──→ [=1kΩ=] ──→ Row 2
Row 2:  Junction point ──→ jumper wire to Pi GPIO 25 (Pin 22)
Row 2:  Also connects to ──→ [=2kΩ=] ──→ Row 3
Row 3:  GND wire ──→ Pi GND (Pin 14)
```

**Option B — Direct soldering (no breadboard):**
1. Solder the 1kΩ resistor to the ECHO wire.
2. At the junction between the two resistors, solder a wire going to Pi GPIO 25.
3. Solder the 2kΩ resistor from the junction to GND.
4. Wrap exposed connections with electrical tape or heat shrink.

### Full HC-SR04 Wiring

| HC-SR04 Pin | → | Connects To | Notes |
|-------------|---|-------------|-------|
| VCC | → | L298N +5V terminal | 5V power from motor battery regulator |
| TRIG | → | Pi Pin 18 (GPIO 24) | Direct connection, Pi sends 3.3V trigger (works fine for HC-SR04) |
| ECHO | → | Voltage divider → Pi Pin 22 (GPIO 25) | MUST go through divider, never direct |
| GND | → | L298N GND terminal | Common ground |

### Complete wiring diagram

```
HC-SR04                          Raspberry Pi 4
+-------------+                  +------------------+
| VCC --------+--- red --------->| L298N +5V        |
|             |                  |                  |
| TRIG -------+--- green ------->| Pin 18 (GPIO 24) |
|             |                  |                  |
| ECHO -------+--- [1kΩ] --+    |                  |
|             |             |    |                  |
|             |             +--->| Pin 22 (GPIO 25) |
|             |             |    |                  |
|             |          [2kΩ]   |                  |
|             |             |    |                  |
|             |            GND ->| Pin 14 (GND)     |
|             |                  |                  |
| GND --------+--- black ------>| L298N GND         |
+-------------+                  +------------------+
```

---

## Step 3.3 — Mount Servo + Ultrasonic

### Physical assembly

1. **Mount the servo** at the front-center of the chassis.
   - Use the servo mounting bracket (often included with the servo) or hot glue.
   - The servo horn (the white cross-shaped piece) should face upward.
   - The servo shaft should be at the front edge of the chassis so it can rotate freely.

2. **Mount the ultrasonic sensor on the servo horn:**
   - Attach the HC-SR04 to the servo horn using:
     - A small 3D-printed bracket, OR
     - Hot glue (apply glue to the back of the HC-SR04, press onto the servo horn), OR
     - A rubber band + cardboard bracket.
   - The two "eyes" (ultrasonic transducers) should face forward when the servo is at center (90°).

3. **Final position check:**
```
        [HC-SR04 eyes]
        [============]
             ||
          [servo]
    ========================
    |    ROVER CHASSIS      |
    | [L-motor]  [R-motor]  |
    ========================
```

---

## Step 3.4 — Servo Testing

SSH into the Pi:

```python
python3
```

```python
import RPi.GPIO as GPIO
import time

GPIO.setmode(GPIO.BCM)
GPIO.setup(18, GPIO.OUT)
pwm = GPIO.PWM(18, 50)  # 50 Hz for servo
pwm.start(0)

def set_angle(angle):
    duty = 2.5 + (angle / 180) * 10  # 2.5% to 12.5%
    pwm.ChangeDutyCycle(duty)
    time.sleep(0.5)
    pwm.ChangeDutyCycle(0)  # stop to prevent jitter

# Test: center → left → right → center
print("CENTER (90°)")
set_angle(90)
time.sleep(1)

print("LEFT (30°)")
set_angle(30)
time.sleep(1)

print("RIGHT (150°)")
set_angle(150)
time.sleep(1)

print("CENTER (90°)")
set_angle(90)
time.sleep(1)

pwm.stop()
GPIO.cleanup()
print("Done!")
```

### What to check

| Test | Expected | If wrong |
|------|----------|----------|
| Center (90°) | Ultrasonic faces straight ahead | Remount the horn at 90° |
| Left (30°) | Turns to the left | Swap left/right angles in code |
| Right (150°) | Turns to the right | Same as above |
| Smooth movement | No jittering or buzzing | Check power supply — servo needs clean 5V |

---

## Step 3.5 — Ultrasonic Testing

SSH into the Pi:

```python
python3
```

```python
import RPi.GPIO as GPIO
import time

GPIO.setmode(GPIO.BCM)
GPIO.setup(24, GPIO.OUT)   # TRIG
GPIO.setup(25, GPIO.IN)    # ECHO (through voltage divider)
GPIO.output(24, GPIO.LOW)
time.sleep(0.1)

def get_distance():
    # Send 10µs pulse
    GPIO.output(24, GPIO.HIGH)
    time.sleep(0.00001)
    GPIO.output(24, GPIO.LOW)

    # Wait for echo
    timeout = time.time() + 0.04
    while GPIO.input(25) == GPIO.LOW:
        pulse_start = time.time()
        if pulse_start > timeout:
            return -1

    timeout = time.time() + 0.04
    while GPIO.input(25) == GPIO.HIGH:
        pulse_end = time.time()
        if pulse_end > timeout:
            return -1

    distance = (pulse_end - pulse_start) * 34300 / 2
    return round(distance, 1)

# Take 10 readings
for i in range(10):
    d = get_distance()
    if d > 0:
        print(f"Reading {i+1}: {d} cm")
    else:
        print(f"Reading {i+1}: TIMEOUT (no echo)")
    time.sleep(0.5)

GPIO.cleanup()
```

### What to check

1. Place your hand 10cm from the sensor → should read ~10cm.
2. Place your hand 30cm away → should read ~30cm.
3. Point at a wall 1m away → should read ~100cm.
4. Point at open space → should read 300+ cm or timeout.

| Symptom | Cause | Fix |
|---------|-------|-----|
| Always reads -1 (timeout) | ECHO voltage divider wrong | Check resistor values and wiring |
| Always reads 0 or very small | TRIG not connected | Check GPIO 24 → TRIG wire |
| Readings wildly inaccurate | Loose connections | Reseat all ultrasonic wires |
| Readings jitter a lot | Reflective/angled surface | Test against a flat wall |

### Using the project test script
```bash
cd /home/pi/rpa
python3 -m tests.test_obstacle
# Choose option 1 (ultrasonic), 2 (servo), or 3 (combined scan)
```

---

# PHASE H4: GPS MODULE (NEO-6M)

## What You Need
- 1x NEO-6M GPS module (with antenna)
- 3x Jumper wires (female-to-female or as needed)

---

## Step 4.1 — Raspberry Pi UART Configuration

**You must do this before wiring the GPS.** The Pi's serial port is used for a login console by default — we need to disable that and enable the hardware UART.

### Configure via raspi-config
```bash
sudo raspi-config
```
1. Navigate to: **Interface Options** → **Serial Port**
2. "Would you like a login shell to be accessible over serial?" → **No**
3. "Would you like the serial port hardware to be enabled?" → **Yes**
4. Finish and **reboot**:
```bash
sudo reboot
```

### Verify UART is enabled
After reboot:
```bash
ls -la /dev/serial0
# Should show: /dev/serial0 -> ttyS0  (or ttyAMA0)

# Check boot config
grep uart /boot/config.txt
# Should show: enable_uart=1
```

---

## Step 4.2 — NEO-6M Wiring

### NEO-6M Module Pinout
```
+-------------------+
|  NEO-6M GPS       |
|                   |
|  VCC  RX  TX  GND |
+---+---+---+---+---+
```

### Wiring

| NEO-6M Pin | → | Connects To | Notes |
|------------|---|-------------|-------|
| VCC | → | Pi Pin 1 (3.3V) | NEO-6M works on 2.7V–3.6V. Use 3.3V NOT 5V from L298N |
| TX | → | Pi Pin 10 (GPIO 15 / RXD) | GPS transmits → Pi receives |
| RX | → | Pi Pin 8 (GPIO 14 / TXD) | Pi transmits → GPS receives (optional, for configuration) |
| GND | → | Pi Pin 9 (GND) | Ground |

### Wiring diagram
```
NEO-6M                        Raspberry Pi 4
+----------+                   +-------------------+
| VCC -----+--- red --------→ | Pin 1  (3.3V)     |
| TX ------+--- white ------→ | Pin 10 (GPIO 15)  |  ← Pi RXD receives from GPS TX
| RX ------+--- grey -------→ | Pin 8  (GPIO 14)  |  ← Pi TXD sends to GPS RX
| GND -----+--- black ------→ | Pin 9  (GND)      |
+----------+                   +-------------------+
```

**IMPORTANT — TX/RX crossover:**
- GPS **TX** goes to Pi **RX** (Pin 10 / GPIO 15). This is correct — it's a crossover.
- GPS **RX** goes to Pi **TX** (Pin 8 / GPIO 14). This is optional but wire it anyway.
- Do NOT connect TX-to-TX or RX-to-RX. That's wrong.

### GPS Antenna
- The NEO-6M usually comes with a small ceramic patch antenna connected via a tiny u.FL connector.
- Make sure the antenna is connected and placed **face-up** (the flat side with the square patch faces the sky).
- For first testing, go **outdoors**. GPS does not work indoors reliably.

---

## Step 4.3 — GPS Testing

### Raw serial test (no project code)
```bash
# Read raw data from GPS
cat /dev/serial0
```

You should see NMEA sentences scrolling:
```
$GPGGA,,,,,,0,,,,,,,,*66
$GPGSA,A,1,,,,,,,,,,,,,,,*1E
$GPRMC,,V,,,,,,,,,,N*53
```

- `$GPGGA,...,0,...` → the `0` means no fix yet.
- `$GPRMC,...,V,...` → `V` means void (no fix).

**Wait outdoors for 30–60 seconds (cold start). Once fix is acquired:**
```
$GPGGA,123456.00,1234.56789,N,07654.32100,E,1,08,1.2,45.0,M,...*XX
$GPRMC,123456.00,A,1234.56789,N,07654.32100,E,0.01,0.0,030326,...*XX
```

- Fix quality changes from `0` to `1` (or `2`).
- Status changes from `V` to `A` (active).
- You'll see latitude/longitude numbers.

### Python test (no project code)
```python
python3
```

```python
import serial
import time

ser = serial.Serial('/dev/serial0', 9600, timeout=1)
print("Reading GPS (Ctrl+C to stop)...")

try:
    while True:
        line = ser.readline().decode('ascii', errors='ignore').strip()
        if line.startswith('$GPGGA') or line.startswith('$GPRMC'):
            print(line)
except KeyboardInterrupt:
    pass
finally:
    ser.close()
```

### Using the project test script
```bash
cd /home/pi/rpa
python3 -m tests.test_gps
# Choose option 1 (raw NMEA) or 2 (parsed coordinates)
```

### What to check

| Test | Expected | If wrong |
|------|----------|----------|
| `cat /dev/serial0` shows data | NMEA sentences appear | Check TX→RX wiring, UART enabled |
| Fix acquired outdoors | Lat/lon numbers appear | Wait longer, check antenna, go more open sky |
| Coordinates match phone GPS | Within ±5 meters | Normal — civilian GPS accuracy |

### Troubleshooting

| Symptom | Cause | Fix |
|---------|-------|-----|
| No output at all | UART not enabled | Rerun `raspi-config`, reboot |
| Garbled characters | Wrong baud rate | NEO-6M default is 9600, verify |
| Never gets a fix | Indoor / antenna issue | Go outdoors, check antenna connector |
| `Permission denied` on /dev/serial0 | User not in dialout group | `sudo usermod -aG dialout pi` then reboot |

---

# PHASE H5: FULL INTEGRATION

## Step 5.1 — Mounting Checklist

Mount everything on the chassis in this order:

### Layer 1 — Bottom (motors already mounted)
- [x] 4x BO motors in chassis brackets
- [x] Wheels attached

### Layer 2 — Main platform
- [ ] L298N motor driver (use standoffs, screws, or strong double-sided tape)
- [ ] 2S Battery (secure with velcro strap or zip tie — it must NOT slide around)

### Layer 3 — Top
- [ ] Raspberry Pi 4 (use standoffs or a mounting plate)
- [ ] Powerbank (beside or on top of Pi, secure with velcro/zip tie)
- [ ] Pi Camera v2 (mount at front, facing forward, slightly downward ~10-15°)
- [ ] NEO-6M GPS (mount on top, antenna face up, away from motors)

### Front
- [ ] Servo motor (front-center, screwed or hot-glued)
- [ ] HC-SR04 on servo horn (hot glue or bracket)

---

## Step 5.2 — Wiring Cleanup

Loose wires are the #1 cause of problems on a moving robot. Do this:

1. **Bundle wires** with zip ties or cable wraps — group by function:
   - Motor wires (thick, carry current)
   - GPIO signal wires (thin, L298N control)
   - Sensor wires (servo, ultrasonic, GPS)
   - Power wires (battery, powerbank)

2. **Keep motor wires away from:**
   - The GPS antenna (causes interference with satellite signal)
   - The Pi Camera ribbon cable (can cause video noise)
   - The ultrasonic sensor wires

3. **Secure the Pi Camera ribbon cable** — it's fragile. Use tape to hold it against the chassis so it doesn't get caught in wheels.

4. **Check every screw terminal** — give each one a gentle tug to make sure wires are secure.

---

## Step 5.3 — Complete Connection Summary

```
+------------------------------------------------------------------+
|                        ROVER WIRING SUMMARY                       |
+------------------------------------------------------------------+
|                                                                    |
|  POWERBANK (22000mAh)                                             |
|  └── USB-C ──→ Raspberry Pi 4                                     |
|                                                                    |
|  2S BATTERY (7.4V)                                                |
|  ├── (+) ──→ L298N +12V terminal                                  |
|  └── (-) ──→ L298N GND terminal                                   |
|                                                                    |
|  L298N +5V output ──→ Servo VCC (red wire)                        |
|  L298N +5V output ──→ HC-SR04 VCC                                 |
|  L298N GND ──→ Servo GND (brown wire)                              |
|  L298N GND ──→ HC-SR04 GND                                        |
|  L298N GND ──→ Pi Pin 6 (GND) *** COMMON GROUND ***               |
|                                                                    |
|  L298N OUT1/OUT2 ──→ Left motors (parallel)                        |
|  L298N OUT3/OUT4 ──→ Right motors (parallel)                       |
|                                                                    |
|  L298N IN1 ──→ Pi Pin 11 (GPIO 17)                                |
|  L298N IN2 ──→ Pi Pin 13 (GPIO 27)                                |
|  L298N IN3 ──→ Pi Pin 15 (GPIO 22)                                |
|  L298N IN4 ──→ Pi Pin 16 (GPIO 23)                                |
|  L298N ENA ──→ Pi Pin 32 (GPIO 12)  [jumper REMOVED]              |
|  L298N ENB ──→ Pi Pin 33 (GPIO 13)  [jumper REMOVED]              |
|                                                                    |
|  Servo Signal ──→ Pi Pin 12 (GPIO 18)                              |
|                                                                    |
|  HC-SR04 TRIG ──→ Pi Pin 18 (GPIO 24)                             |
|  HC-SR04 ECHO ──→ [1kΩ]──→ Pi Pin 22 (GPIO 25)                   |
|                        └──→ [2kΩ] ──→ Pi Pin 14 (GND)             |
|                                                                    |
|  NEO-6M VCC ──→ Pi Pin 1 (3.3V)                                   |
|  NEO-6M TX  ──→ Pi Pin 10 (GPIO 15 / RXD)                        |
|  NEO-6M RX  ──→ Pi Pin 8  (GPIO 14 / TXD)                        |
|  NEO-6M GND ──→ Pi Pin 9  (GND)                                   |
|                                                                    |
|  Pi Camera v2 ──→ Pi CSI Port (ribbon cable)                       |
|                                                                    |
+------------------------------------------------------------------+
```

---

## Step 5.4 — Full System Power-On Test

### Pre-flight checklist (do before every power-on)

- [ ] All screw terminals tight
- [ ] Camera ribbon seated and locked
- [ ] ENA/ENB jumpers removed from L298N
- [ ] Common ground wire connected (Pi GND → L298N GND)
- [ ] Voltage divider on ECHO line (1kΩ + 2kΩ)
- [ ] GPS antenna connected and face-up
- [ ] 2S battery charged (>7V)
- [ ] Powerbank charged
- [ ] Wheels off the ground (prop up the chassis for first test)

### Power-on sequence
1. Turn on the powerbank → Pi boots.
2. Connect the 2S battery (or flip its switch) → L298N powered.
3. SSH into the Pi:
   ```
   ssh pi@<rover-ip>
   ```

### Run each subsystem test

```bash
cd /home/pi/rpa

# Test 1: Motors
python3 -m tests.test_motor
# Wheels should spin (robot is propped up, not on the ground)

# Test 2: Servo + Ultrasonic
python3 -m tests.test_obstacle
# Choose 1 for ultrasonic, 2 for servo, 3 for combined scan

# Test 3: Camera
python3 -m tests.test_detection
# Choose 1 to verify frames, 2 to capture an image

# Test 4: GPS (go outdoors)
python3 -m tests.test_gps
# Choose 1 for raw, 2 for parsed coordinates

# Test 5: Streaming
python3 -m tests.test_stream
# Open http://<rover-ip>:8080/ in browser on your PC

# Test 6: Data transmission (run pc_server.py on PC first)
# On PC:
python3 pc_server.py
# On rover:
python3 -m tests.test_transmit
```

### Pass criteria

| Subsystem | Pass condition |
|-----------|---------------|
| Motors | All 4 wheels spin correctly in all directions |
| Servo | Sweeps left/center/right, smooth movement |
| Ultrasonic | Reads distances accurately (±3cm), no timeouts |
| Camera | Frames captured, shape = (480, 640, 3) |
| GPS | Gets a fix outdoors, coordinates are valid |
| Streaming | Live video visible in browser, low latency |
| Transmission | Image + GPS received by PC server |

---

## Step 5.5 — First Ground Test

Once all subsystems pass individually:

1. Place the rover on the ground.
2. Set up an obstacle (box, wall) about 50cm in front.
3. Place a red object (ball, cup, cloth) 1–2 meters away.
4. Start `pc_server.py` on your PC.
5. Run the full system:
   ```bash
   cd /home/pi/rpa
   python3 main.py
   ```
6. Open `http://<rover-ip>:8080/` in your browser to watch the live feed.
7. Watch the rover:
   - It should move forward.
   - It should detect and avoid the obstacle.
   - It should detect the red object, stop, and send data to your PC.
   - It should resume for 60 seconds (demo mode).

### Emergency stop
Press `Ctrl+C` in the SSH terminal. The signal handler will stop all motors and clean up.

---

# QUICK REFERENCE CARD

Print this and tape it to your workbench.

```
╔══════════════════════════════════════════════════════╗
║              ROVER PIN QUICK REFERENCE               ║
╠══════════════════════════════════════════════════════╣
║                                                      ║
║  MOTORS (L298N → Pi)                                ║
║  IN1 → GPIO 17 (Pin 11)    Left Forward             ║
║  IN2 → GPIO 27 (Pin 13)    Left Backward            ║
║  IN3 → GPIO 22 (Pin 15)    Right Forward             ║
║  IN4 → GPIO 23 (Pin 16)    Right Backward            ║
║  ENA → GPIO 12 (Pin 32)    Left PWM  [remove jumper] ║
║  ENB → GPIO 13 (Pin 33)    Right PWM [remove jumper] ║
║                                                      ║
║  SERVO                                               ║
║  Signal → GPIO 18 (Pin 12)                           ║
║  VCC → L298N 5V  |  GND → L298N GND                 ║
║                                                      ║
║  ULTRASONIC (HC-SR04)                                ║
║  TRIG → GPIO 24 (Pin 18)                             ║
║  ECHO → 1kΩ → GPIO 25 (Pin 22) → 2kΩ → GND (Pin14) ║
║  VCC → L298N 5V  |  GND → L298N GND                 ║
║                                                      ║
║  GPS (NEO-6M)                                        ║
║  TX → GPIO 15 (Pin 10)  Pi RXD                      ║
║  RX → GPIO 14 (Pin 8)   Pi TXD                      ║
║  VCC → 3.3V (Pin 1)  |  GND → Pi GND (Pin 9)       ║
║                                                      ║
║  CAMERA → CSI port (ribbon, blue side to USB)        ║
║  POWER  → Powerbank USB-C to Pi                      ║
║  COMMON GND → Pi Pin 6 ↔ L298N GND terminal         ║
║                                                      ║
╚══════════════════════════════════════════════════════╝
```
