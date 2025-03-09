import network
import socket
import time
import struct
import machine

from secrets import secrets

NTP_DELTA = 2208988800
host = "pool.ntp.org"

rtc=machine.RTC()

def set_time():
    # Get the external time reference
    NTP_QUERY = bytearray(48)
    NTP_QUERY[0] = 0x1B
    addr = socket.getaddrinfo(host, 123)[0][-1]
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.settimeout(1)
        res = s.sendto(NTP_QUERY, addr)
        msg = s.recv(48)
    finally:
        s.close()

    #Set our internal time
    val = struct.unpack("!I", msg[40:44])[0]
    tm = val - NTP_DELTA    
    t = time.gmtime(tm)
    rtc.datetime((t[0],t[1],t[2],t[6]+1,t[3],t[4],t[5],0))

wlan = network.WLAN(network.STA_IF)

# Set up Wifi connection details
ssid = secrets['ssid']
password = secrets['pw']
rp2.country('FR') # change to <your> country code
#ip = secrets['ip']
#netmask = secrets['netmask']
#gateway = secrets['gateway']
#dns = secrets['dns']

# Connect to Wifi
wlan.active(True) # activate the interface
if not wlan.isconnected(): # check if connected to an AP
    print('Connecting to network...')
    wlan.connect(ssid, password) # connect to an AP
    #wlan.ifconfig((ip,netmask,gateway,dns))
    while not wlan.isconnected(): # wait till we are connected
        print('.', end='')
        time.sleep(0.1)
    print()
    print('Connected:', wlan.isconnected())
else:
    print("Already connected!")

#Set our RTC
timestamp=rtc.datetime()
timestring="%04d-%02d-%02d %02d:%02d:%02d"%(timestamp[0:3] +
                                                timestamp[4:7])
print(timestring)
set_time()
timestamp=rtc.datetime()
timestring="%04d-%02d-%02d %02d:%02d:%02d"%(timestamp[0:3] +
                                                timestamp[4:7])
print(timestring)
# led_onboard = machine.Pin('LED', machine.Pin.OUT)
# led_onboard.value(0)
# 
# file = open("timestamps.txt", "a")
# 
# # Log some time
# while True:
#     timestamp=rtc.datetime()
#     timestring="%04d-%02d-%02d %02d:%02d:%02d"%(timestamp[0:3] +
#                                                 timestamp[4:7])
#     print(timestring)
#     file.write(timestring + "\n")
#     file.flush()
#     led_onboard.value(1)
#     time.sleep(0.01)
#     led_onboard.value(0)
#     time.sleep(30)
