# Water level with a LoPy
#
# Boot script
#
# Author:  J. Barthelemy
# Version: 04 July 2017

from machine import UART
import pycom
import os
from network import WLAN

NANO_GATEWAY = False          # is the lopy joining a TTN nano gateway
MAX_JOIN_ATTEMPT = 50         # max number of connection attemps to TTN
INT_SAMPLING = 1000 * 60 * 15 # sampling interval

# deactivate wifi
wlan = WLAN()
wlan.deinit()

# disabling the heartbeat
pycom.heartbeat(False)

# setting up the communication interface
uart = UART(0, 115200)
os.dupterm(uart)
