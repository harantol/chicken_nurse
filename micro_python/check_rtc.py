# Rui Santos & Sara Santos - Random Nerd Tutorials
# Complete project details at https://RandomNerdTutorials.com/raspberry-pi-pico-ds1307-rtc-micropython/

import time
import urtc
from machine import I2C, Pin, RTC
from gpio_pins import GPIO_RTC_SCL, GPIO_RTC_SDA

days_of_week = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']


# Initialize RTC (connected to I2C)
i2c = I2C(0, scl=Pin(GPIO_RTC_SCL), sda=Pin(GPIO_RTC_SDA))
rtc = urtc.DS1307(i2c)
# Set the current time using a specified time tuple

while True:
    print('Current date and time:')
    print(rtc.datetime())

    time.sleep(1)
