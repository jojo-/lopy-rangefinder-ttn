# Water level with a LoPy
#
# Configuration for The Things Network
#
# Author:  J. Barthelemy
# Version: 28 August 2017

# credentials
APP_EUI = 'XX'
APP_KEY = 'YY'

# max number of connection attemps to TTN
MAX_JOIN_ATTEMPT = const(50)

# number of packets to be transmit with the same data  (retries)
N_TX = const(3)

# data rate used to send message via LoRaWAN:
# 1 (slowest - longest range) to 4 (fastest - smallest range)
DATA_RATE = const(4)

# sampling interval (in seconds)
INT_SAMPLING = const(60 * 15)

# GPS coordinates
LAT = -34.4079
LON = 150.8785
ALT = 27.00

# Set flag to true if you want to force the join to The Things Network
# and have access to the REPL interface
FORCE_JOIN = False
SEND_LOC   = False
