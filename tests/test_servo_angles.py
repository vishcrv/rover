import pigpio
import time

SERVO_PIN = 24

LEFT_PW   = 1580   # very tight arc
RIGHT_PW  = 1420   # very tight arc
MOVE_DELAY = 1.0

pi = pigpio.pi()

if not pi.connected:
    print("pigpiod not running! Start with: sudo systemctl start pigpiod")
    exit()

def move_servo(pulsewidth):
    pi.set_servo_pulsewidth(SERVO_PIN, pulsewidth)
    time.sleep(MOVE_DELAY)
    pi.set_servo_pulsewidth(SERVO_PIN, 0)
    time.sleep(0.05)

try:
    while True:
        print("Left")
        move_servo(LEFT_PW)
        print("Right")
        move_servo(RIGHT_PW)

except KeyboardInterrupt:
    pi.set_servo_pulsewidth(SERVO_PIN, 1500)
    time.sleep(0.5)
    pi.set_servo_pulsewidth(SERVO_PIN, 0)
    pi.stop()