# Rui Santos & Sara Santos - Random Nerd Tutorials
# Complete project details at https://RandomNerdTutorials.com/raspberry-pi-pico-ds1307-rtc-micropython/

import time
import urtc
from machine import I2C, Pin, RTC

days_of_week = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']

# Initialize RTC (connected to I2C)
from gpio_pins import GPIO_RTC_SCL, GPIO_RTC_SDA
i2c = I2C(0, scl=Pin(GPIO_RTC_SCL), sda=Pin(GPIO_RTC_SDA))
rtc = urtc.DS3231(i2c)
# Set the current time using a specified time tuple
# Time tupple: (year, month, day, day of week, hour, minute, seconds, milliseconds)
initial_time = (2024, 1, 30, 1, 12, 31, 3, 0)

# Or get the local time from the system
initial_time_tuple = time.localtime() #tuple (microPython)
initial_time_seconds = time.mktime(initial_time_tuple) # local time in seconds

# Convert to tuple compatible with the library
initial_time = urtc.seconds2tuple(initial_time_seconds)
print(initial_time)
# Sync the RTC
rtc.datetime((initial_time[0], initial_time[1],initial_time[2], initial_time[3],initial_time[4], initial_time[5],initial_time[6],initial_time[7]))
rtc2.datetime((initial_time[0], initial_time[1],initial_time[2], initial_time[3],initial_time[4], initial_time[5],initial_time[6],initial_time[7]))

while True:
    print('Current date and time:')
    print(rtc.datetime())
    print(rtc2.datetime())
    

    time.sleep(1)
