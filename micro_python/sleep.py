import picosleep
import time
from machine import Pin

led = Pin("LED", Pin.OUT)
sleeptime = 1

while sleeptime <= 10:
    led.toggle()
    time.sleep(5)
    led.toggle()
    picosleep.seconds(sleeptime)
    sleeptime = sleeptime + 1