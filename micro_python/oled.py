from machine import SoftI2C, Pin
import urtc
import ssd1306
import time

from gpio_pins import GPIO_OLED_SCL, GPIO_OLED_SDA, GPIO_RTC_SCL, GPIO_RTC_SDA

oled_width = 128
oled_height = 64
i2c_rtc = SoftI2C(scl=Pin(GPIO_RTC_SCL), sda=Pin(GPIO_RTC_SDA))
days_of_week = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']


class OLED:
    def __init__(self):
        __i2c_oled = SoftI2C(scl=Pin(GPIO_OLED_SCL), sda=Pin(GPIO_OLED_SDA))
        self.oled = ssd1306.SSD1306_I2C(oled_width, oled_height, __i2c_oled)
        self.rtc = urtc.DS1307(i2c_rtc)

    def debug(self):
        while True:
            # Get current time from the RTC
            current_datetime = self.rtc.datetime()

            # Format the date and time as strings
            formatted_date = '{:02d}-{:02d}-{:04d}'.format(current_datetime.day, current_datetime.month,
                                                           current_datetime.year)
            formatted_time = '{:02d}:{:02d}:{:02d}'.format(current_datetime.hour, current_datetime.minute,
                                                           current_datetime.second)
            formatted_day_week = days_of_week[current_datetime.weekday]

            # Clear the OLED display
            self.oled.fill(0)

            # Display the formatted date and time
            self.oled.text('Date: ' + formatted_day_week, 0, 0)
            self.oled.text(formatted_date, 0, 16)
            self.oled.text('Time: ' + formatted_time, 0, 32)
            self.oled.show()

            # Print the formatted date and time to the shell
            print('Formatted date:', formatted_date)
            print('Formatted time:', formatted_time)

            # Wait for 1 second
            time.sleep(1)


if __name__ == '__main__':
    oled = OLED()
    oled.debug()
