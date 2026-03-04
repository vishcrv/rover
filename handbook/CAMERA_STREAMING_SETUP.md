# 📷 Camera, Picture Transmission & Live Streaming — Setup Guide

Complete guide for setting up picture capture, sending detection images to your PC, and streaming live video from the rover.

---

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Hardware Setup — Pi Camera v2](#1-hardware-setup--pi-camera-v2)
3. [Software Dependencies](#2-software-dependencies)
4. [Taking a Picture](#3-taking-a-picture)
5. [Sending Pictures to PC](#4-sending-pictures-to-pc)
6. [Live Video Streaming](#5-live-video-streaming)
7. [Running Everything Together](#6-running-everything-together)
8. [Troubleshooting](#7-troubleshooting)

---

## Prerequisites

| Item | Details |
|------|---------|
| **Board** | Raspberry Pi 4 (any RAM variant) |
| **Camera** | Pi Camera Module v2 (CSI ribbon cable) |
| **OS** | Raspberry Pi OS (Bookworm or Bullseye, 64-bit recommended) |
| **Network** | Both Pi and PC must be on the **same WiFi network** |
| **Python** | Python 3.9+ (comes pre-installed on Pi OS) |

---

## 1. Hardware Setup — Pi Camera v2

### 1.1 — Connect the Camera

1. **Power off** the Raspberry Pi completely.
2. Locate the **CSI camera port** — the long, thin black connector between the HDMI ports and the 3.5mm audio jack.
3. Gently pull up the plastic clip on the CSI connector.
4. Insert the ribbon cable with the **blue side facing the USB/Ethernet ports** (metal contacts facing the HDMI ports).
5. Push the clip back down to lock the cable in place.
6. Power on the Pi.

> **⚠️ IMPORTANT:** Never connect or disconnect the camera ribbon cable while the Pi is powered on — this can damage the camera or the Pi.

### 1.2 — Enable the Camera

On **Raspberry Pi OS Bookworm** (2023+), the camera is enabled by default via `libcamera`. No manual steps needed.

On **Raspberry Pi OS Bullseye**, run:

```bash
sudo raspi-config
```

Navigate to: **Interface Options → Camera → Enable**, then reboot.

### 1.3 — Verify the Camera

```bash
# Quick test — capture a JPEG image
libcamera-jpeg -o test.jpg

# Check the image
ls -la test.jpg
```

If you see `test.jpg` with a non-zero file size, your camera is working.

You can also run:

```bash
# List detected cameras
libcamera-hello --list-cameras
```

Expected output should show `imx219` (the Pi Camera v2 sensor).

---

## 2. Software Dependencies

### 2.1 — System Packages

```bash
# Update package lists
sudo apt update

# Install required system packages
sudo apt install -y python3-picamera2 python3-opencv python3-flask python3-requests
```

> **💡 TIP:** On Pi OS Bookworm, `picamera2` comes pre-installed. The above command ensures all dependencies are present.

### 2.2 — Python Packages (if using a virtual environment)

If you're using a virtual environment instead of system packages:

```bash
cd ~/rover
python3 -m venv venv --system-site-packages
source venv/bin/activate
pip install -r requirements.txt
```

The `--system-site-packages` flag is **critical** — `picamera2` relies on system-level `libcamera` bindings that can't be installed via pip alone.

### 2.3 — Verify Installation

```bash
python3 -c "from picamera2 import Picamera2; print('Picamera2 OK')"
python3 -c "import cv2; print(f'OpenCV {cv2.__version__} OK')"
python3 -c "import flask; print(f'Flask {flask.__version__} OK')"
python3 -c "import requests; print(f'Requests {requests.__version__} OK')"
```

All four lines should print "OK" without any errors.

---

## 3. Taking a Picture

### 3.1 — Quick Test (standalone script)

Create a test script or use the built-in test:

```python
# quick_capture.py — Run on the Pi
from picamera2 import Picamera2
import time

cam = Picamera2()

# Configure for still image capture
config = cam.create_still_configuration(
    main={"size": (1920, 1080), "format": "RGB888"}
)
cam.configure(config)
cam.start()

# Let the camera warm up (auto-exposure needs ~1 second)
time.sleep(2)

# Capture and save
cam.capture_file("my_photo.jpg")
print("Photo saved: my_photo.jpg")

cam.stop()
cam.close()
```

Run it:

```bash
python3 quick_capture.py
```

### 3.2 — Using the Rover's Camera Module

The rover's camera module (`modules/camera.py`) provides a more integrated way:

```python
# test_camera_module.py — Run from the rover project root
from modules import camera

# Initialize the camera (starts continuous capture in background)
camera.setup()

# Wait for camera warmup
import time
time.sleep(2)

# Capture a high-res image
path = camera.capture_image("test_capture.jpg")
print(f"Image saved to: {path}")

# Get a frame as a numpy array (for processing)
frame = camera.get_frame()
if frame is not None:
    print(f"Frame shape: {frame.shape}")  # (480, 640, 3)

# Cleanup
camera.cleanup()
```

Run from the project root:

```bash
cd ~/rover
python3 test_camera_module.py
```

### 3.3 — How It Works Internally

The camera module architecture:

```
┌─────────────────────────────────────────────────────┐
│                  camera.setup()                     │
│                                                     │
│  1. Initializes Picamera2                          │
│  2. Configures preview mode (640×480, RGB888)       │
│  3. Starts continuous capture in background thread  │
│  4. Creates capture directory (/home/pi/captures)   │
└─────────────────────────────────────────────────────┘
         │                           │
         ▼                           ▼
┌─────────────────┐       ┌────────────────────┐
│  get_frame()    │       │  capture_image()   │
│                 │       │                    │
│ Returns latest  │       │ Saves full-res     │
│ 640×480 frame   │       │ JPEG to disk       │
│ (for detection  │       │ (for transmission) │
│  & streaming)   │       │                    │
└─────────────────┘       └────────────────────┘
```

**Key settings** (in `config/settings.py`):

| Setting | Value | Purpose |
|---------|-------|---------|
| `CAMERA_WIDTH` | 640 | Preview/stream width |
| `CAMERA_HEIGHT` | 480 | Preview/stream height |
| `CAMERA_FPS` | 20 | Target framerate |
| `CAPTURE_WIDTH` | 1920 | Still capture width |
| `CAPTURE_HEIGHT` | 1080 | Still capture height |
| `CAPTURE_DIR` | `/home/pi/captures` | Where images are saved |

---

## 4. Sending Pictures to PC

The rover captures images and sends them to a Flask server running on your PC.

### 4.1 — Find Your PC's IP Address

On your **PC** (the receiving end):

**Windows:**
```bash
ipconfig
```
Look for `IPv4 Address` under your WiFi adapter (e.g., `192.168.1.100`).

**Linux/Mac:**
```bash
hostname -I
```

### 4.2 — Configure the Rover

On the **Raspberry Pi**, edit the settings file:

```bash
nano ~/rover/config/settings.py
```

Update the PC server IP to match your PC's IP:

```python
# DATA TRANSMISSION
PC_SERVER_IP = "192.168.1.100"    # ← Change to YOUR PC's IP address
PC_SERVER_PORT = 5000
PC_DETECTION_ENDPOINT = "/detection"
TRANSMIT_TIMEOUT = 5
```

### 4.3 — Start the PC Server

On your **PC**, run:

```bash
cd rover
python pc_server.py
```

You should see:

```
Starting PC server...
Saving images to: /path/to/received_detections/
Listening on 0.0.0.0:5000
```

> **💡 TIP:** Make sure your PC's firewall allows incoming connections on port 5000. On Windows, you may need to allow Python through the firewall when prompted.

### 4.4 — Test the Transmission

On the **Raspberry Pi**, run the transmission test:

```bash
cd ~/rover
python3 -m tests.test_transmit
```

If successful, you'll see:

```
=== Transmission Test ===

  Image:     /tmp/test_transmit.jpg
  Timestamp: 2026-03-05 04:00:00

  SUCCESS — PC server received the data.
```

And on the **PC server** terminal:

```
==================================================
  DETECTION RECEIVED
  Time:      2026-03-05 04:00:00
  Image:     received_detections/detection_2026-03-05_04-00-00.jpg
  Size:      1234 bytes
==================================================
```

### 4.5 — How Transmission Works

```
┌──────────────────────┐         HTTP POST          ┌──────────────────────┐
│    RASPBERRY PI      │  ─────────────────────→   │      YOUR PC          │
│                      │   multipart/form-data      │                      │
│  transmitter.py      │                            │   pc_server.py       │
│                      │   Fields:                  │                      │
│  send_detection(     │   • image: JPEG file       │   /detection         │
│    image_path,       │   • timestamp: string      │   endpoint           │
│    timestamp         │                            │                      │
│  )                   │  ←─────────────────────    │   Saves image to     │
│                      │    200 OK / error           │   received_detections│
└──────────────────────┘                            └──────────────────────┘
```

---

## 5. Live Video Streaming

The rover runs an MJPEG streaming server that lets you watch the live camera feed from any browser on the same network.

### 5.1 — Start the Streaming Server

**Option A: Standalone (for testing)**

```bash
cd ~/rover
python3 -c "
from modules import camera
from streaming import server

camera.setup()
import time; time.sleep(1)
print('Camera started, launching stream server...')
server.start(blocking=True)
"
```

**Option B: As part of the full rover system**

```bash
cd ~/rover
python3 main.py
```

The streaming server starts automatically during the BOOT phase.

### 5.2 — Access the Live Stream

Open a web browser on **any device on the same WiFi network** and navigate to:

```
http://<ROVER_IP>:8080
```

For example, if your Pi's IP is `192.168.1.50`:

```
http://192.168.1.50:8080
```

This shows a simple page with the embedded live video feed.

To get just the raw video stream (useful for embedding in other applications):

```
http://192.168.1.50:8080/video
```

### 5.3 — Find Your Pi's IP Address

On the **Raspberry Pi**:

```bash
hostname -I
```

This will output something like `192.168.1.50` — use this IP in the browser URL.

### 5.4 — How Streaming Works

```
┌─────────────────────────────────────────────────────────────┐
│                    RASPBERRY PI                              │
│                                                              │
│  camera.py                    streaming/server.py            │
│  ┌──────────────────┐        ┌──────────────────────────┐   │
│  │ Background thread │        │  Flask MJPEG Server      │   │
│  │ captures frames   │───────→│  Port 8080               │   │
│  │ at ~20 FPS        │        │                          │   │
│  │                   │        │  GET /       → HTML page │   │
│  │  get_frame()      │        │  GET /video  → MJPEG     │   │
│  └──────────────────┘        └──────────────────────────┘   │
│          │                              │                    │
│          ▼                              ▼                    │
│   Also used by                   Sends JPEG frames          │
│   detector.py                    continuously over           │
│   (red object                    HTTP via multipart          │
│    detection)                    boundary                    │
└─────────────────────────────────────────────────────────────┘
                                          │
                                          ▼
                                ┌──────────────────┐
                                │   YOUR BROWSER   │
                                │                  │
                                │  <img> tag loads │
                                │  /video endpoint │
                                │  → live feed!    │
                                └──────────────────┘
```

**Key settings** (in `config/settings.py`):

| Setting | Value | Purpose |
|---------|-------|---------|
| `STREAM_HOST` | `0.0.0.0` | Listen on all interfaces |
| `STREAM_PORT` | `8080` | HTTP port for the stream |

The MJPEG stream:
- Reads frames from the **same shared camera** used by the detection module
- Converts RGB → BGR → JPEG (quality 70%) for each frame
- Sends frames as a `multipart/x-mixed-replace` HTTP response
- Works in **any modern browser** — no plugins or special software needed

---

## 6. Running Everything Together

### 6.1 — Manual Start

**Step 1:** Start the PC server on your computer:

```bash
python pc_server.py
```

**Step 2:** SSH into the Raspberry Pi and start the rover:

```bash
ssh pi@<ROVER_IP>
cd ~/rover
python3 main.py
```

**Step 3:** Open the live stream in your browser:

```
http://<ROVER_IP>:8080
```

### 6.2 — Auto-Start on Boot (systemd)

To make the rover start automatically when the Pi powers on:

```bash
# Copy the service file
sudo cp ~/rover/rover.service /etc/systemd/system/

# Enable auto-start
sudo systemctl enable rover.service

# Start now (without reboot)
sudo systemctl start rover.service

# Check status
sudo systemctl status rover.service
```

To view logs:

```bash
# Live log output
journalctl -u rover.service -f

# Last 50 lines
journalctl -u rover.service -n 50
```

To stop:

```bash
sudo systemctl stop rover.service
```

### 6.3 — What Happens During a Detection

When the rover detects a red object, this sequence runs automatically:

```
1. Detection thread confirms red object (5 consecutive frames)
2. Motors STOP
3. Camera captures high-resolution image (1920×1080)
   → Saved to /home/pi/captures/detection_YYYYMMDD_HHMMSS.jpg
4. Image + timestamp sent via HTTP POST to PC server
   → Saved on PC in received_detections/ folder
5. Detection resets, rover resumes movement (demo mode)
```

---

## 7. Troubleshooting

### Camera Issues

| Problem | Solution |
|---------|----------|
| `No cameras available` | Check ribbon cable connection. Re-seat it with Pi powered off. |
| `Camera is not enabled` | Run `sudo raspi-config` → Interface → Camera → Enable, then reboot. |
| `Failed to import picamera2` | Install: `sudo apt install -y python3-picamera2` |
| Black/dark images | Camera needs ~1–2 seconds to warm up for auto-exposure. Add `time.sleep(2)` after `start()`. |
| Image is rotated | Some mounts flip the image. Add `cam.set_controls({"Transform": libcamera.Transform(hflip=1, vflip=1)})` |

### Transmission Issues

| Problem | Solution |
|---------|----------|
| `Connection refused` | Make sure `pc_server.py` is running on the PC. Check the IP address in `config/settings.py`. |
| `Connection timed out` | Pi and PC must be on the **same WiFi network**. Check with `ping <PC_IP>` from the Pi. |
| `Firewall blocking` | Windows: Allow Python through firewall. Linux: `sudo ufw allow 5000`. |
| `No image received (400)` | The image file doesn't exist. Check `CAPTURE_DIR` path and permissions. |

### Streaming Issues

| Problem | Solution |
|---------|----------|
| Can't access `http://<IP>:8080` | Check Pi IP with `hostname -I`. Ensure you're on the same network. |
| Stream is laggy | Reduce `CAMERA_WIDTH`/`CAMERA_HEIGHT` in settings. Lower JPEG quality in `streaming/server.py`. |
| Stream works but detection doesn't | Camera frames are shared — both should work. Check detection HSV settings. |
| `Address already in use` | Another process is using port 8080. Kill it: `sudo fuser -k 8080/tcp` |

### General Tips

- **Always test components individually** before running `main.py`
- **Use SSH** to access the Pi remotely: `ssh pi@<ROVER_IP>`
- **Check logs** with: `journalctl -u rover.service -f`
- **Quick network test**: `ping <PC_IP>` from the Pi, `ping <PI_IP>` from the PC
