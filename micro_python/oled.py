from machine import SoftI2C, Pin
import ssd1306
import time
from math import floor
from local_time import init_rtc_ds3231

from gpio_pins import GPIO_OLED_SCL, GPIO_OLED_SDA

oled_width = 128
oled_height = 64
line_height = 16
days_of_week = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']


class OLED:
    def __init__(self, rtc=None):
        __i2c_oled = SoftI2C(scl=Pin(GPIO_OLED_SCL), sda=Pin(GPIO_OLED_SDA))
        self.oled = ssd1306.SSD1306_I2C(oled_width, oled_height, __i2c_oled)
        self.oled.fill(0)
        self.line_height = 16  # px
        self.lig_number = 0
        self.nb_lig = floor(oled_height / self.line_height)
        self.text: list[str] = []
        if rtc is not None:
            self.rtc = rtc
        else:
            self.rtc = init_rtc_ds3231()

    def print(self, text: str):        
        self.oled.fill(0)
        current_datetime = self.rtc.datetime()

        # Format the date and time as strings
        formatted_time = '{:02d}-{:02d}-{:02d} {:02d}:{:02d}'.format(current_datetime.day, current_datetime.month,
                                                                     int(str(current_datetime.year)[2:]), current_datetime.hour,
                                                                     current_datetime.minute)
        self.oled.text(formatted_time, 0, 0)
        self.text.append(text)
        if len(self.text) > self.nb_lig - 1:
            self.text.pop(0)
        for it, t in enumerate(self.text):
            self.oled.text(t, 0, (it + 1) * self.line_height)
            # if len(t) > 17:
            #   self.scroll()
        self.oled.show()

    def scroll(self):
        time.sleep(1)
        for i in range(oled_width):
            self.oled.scroll(-1, 0)
            self.oled.show()
            time.sleep(0.01)

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
            self.oled.fill(0)
            self.oled.text('Date: ' + formatted_day_week, 0, 0)
            self.oled.text(formatted_date, 0, line_height)
            self.oled.text('Time: ' + formatted_time, 0, 2 * line_height)
            self.oled.show()

            # Print the formatted date and time to the shell
            print('Formatted date:', formatted_date)
            print('Formatted time:', formatted_time)

            # Wait for 1 second
            time.sleep(1)


if __name__ == '__main__':
    oled = OLED()
    oled.debug()
