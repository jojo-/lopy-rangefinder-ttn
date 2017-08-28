# Water level with a LoPy
#
# Main script
#
# Author:  J. Barthelemy
# Version: 28 August 2017

import time
import socket
import binascii
import struct
import config
import gc
from machine import ADC, Pin, UART
from network import LoRa
from deepsleep import DeepSleep

# enabling garbage collector
gc.enable()

# setting up the pin 19 to start/stop the sensor (Pulled down, output)
pin_activation_sensor = Pin('P19', mode=Pin.OUT, pull=Pin.PULL_DOWN)

# setting up the Analog/Digital Converter with 12 bits
adc = ADC(bits=12)

# create an analog pin on P20 for the ultrasonic sensor
apin = adc.channel(pin='P20', attn=ADC.ATTN_11DB)

# create an analog pin on P16 for the battery voltage
batt = adc.channel(pin='P16', attn=ADC.ATTN_2_5DB)

# deep sleep
ds = DeepSleep()
# ... uncomment the next two lines if you want to set up auto off
# ds.set_min_voltage_limit(3.1)
# ds.enable_auto_poweroff()

# init Lorawan
lora = LoRa(mode=LoRa.LORAWAN, adr=False, tx_retries=0, device_class=LoRa.CLASS_A)

# init uart
uart1 = UART(1, baudrate=9600, timeout_chars=7)

def join_lora(force_join = False):
    '''Joining The Things Network '''

    # restore previous state
    if not force_join:
        lora.nvram_restore()

    # remove default channels
    for i in range(0, 72):
        lora.remove_channel(i)

    # adding the Australian channels
    for i in range(8, 15):
        lora.add_channel(i, frequency=915200000 + i * 200000, dr_min=0, dr_max=3)
    lora.add_channel(65, frequency=917500000, dr_min=4, dr_max=4)

    for i in range(0, 7):
        lora.add_channel(i, frequency=923300000 + i * 600000, dr_min=0, dr_max=3)

    if not lora.has_joined() or force_join == True:

        # create an OTA authentication params
        app_eui = binascii.unhexlify(config.APP_EUI.replace(' ',''))
        app_key = binascii.unhexlify(config.APP_KEY.replace(' ',''))

        # join a network using OTAA if not previously done
        lora.join(activation=LoRa.OTAA, auth=(app_eui, app_key), timeout=0)

        # wait until the module has joined the network
        attempt = 0
        while not lora.has_joined() and attempt < config.MAX_JOIN_ATTEMPT:
            time.sleep(2.5)
            attempt = attempt + 1

        # saving the state
        if not force_join:
            lora.nvram_save()

        # returning whether the join was successful
        if lora.has_joined():
            return True
        else:
            return False

    else:
        return True

def send_LPP_over_lora(val, bat):
   '''Sending water and battery levels over LoraWan using Cayenne LPP format'''

   # create a LoRa socket
   s = socket.socket(socket.AF_LORA, socket.SOCK_RAW)

   # set the LoRaWAN data rate
   s.setsockopt(socket.SOL_LORA, socket.SO_DR, config.DATA_RATE)

   # make the socket blocking
   s.setblocking(True)

   # selecting port
   s.bind(1)

   # creating LPP packets metadata
   # ... distance: channel and data type
   channel_dst = 1
   type_dst    = 2
   data_dst    = int(val * 0.1)

   # ... battery: channel and data type
   channel_bat = 2
   type_bat    = 2
   data_bat    = int(bat * 100)

   # sending the sensor data
   if not config.SEND_LOC:
       s.send(bytes([channel_dst, type_dst]) + struct.pack('>h', data_dst) +
              bytes([channel_bat, type_bat]) + struct.pack('>h', data_bat) )

   # sending the location data
   if config.SEND_LOC:

       # ... gps: channel and data type
       channel_gps = 3
       type_gps    = 136
       lat = int(config.LAT * 10000)
       lon = int(config.LON * 10000)
       alt = int(config.ALT * 100)

       # ... select port 2
       s.bind(2)

       # ... sending
       s.send(bytes([channel_gps, type_gps]) + struct.pack('>l', lat)[1:4] +
                                               struct.pack('>l', lon)[1:4] +
                                               struct.pack('>l', alt)[1:4])

   # closing the socket and saving the LoRa state
   s.close()
   if not config.FORCE_JOIN:
       lora.nvram_save()

def read_distance():
    '''Reading the distance using the ultrasonic sensor via serial port '''

    # waking it up
    # ... unlocking the pin
    pin_activation_sensor.hold(False)
    # ... set pin to High
    pin_activation_sensor.value(True)

    # waiting for the sensor to do a few readings
    time.sleep_ms(500)

    # reading the value from serial port (RS232)
    dist_raw = uart1.readline()
    dist = int(str(dist_raw).split('\\rR')[-2])

    # making it asleep by setting the pin to Low and locking its value
    pin_activation_sensor.value(False)
    pin_activation_sensor.hold(True)

    #return the distance in mm
    return dist

def read_battery_level():
    '''Getting the battery level'''

    # Reading the ADC level
    list_volt = list()
    for i in range(750):
        list_volt.append(batt.value())
    list_volt.sort()

    # Convert the ADC reading to volt and battery capacity left in percent
    volt = list_volt[749] * (1 / 0.327) * 1333.5 / 4095.0

    pct = (volt - 3000.0) / (4077.9 - 3000.0)

    # Set the lora battery level
    lora_bat_level = int(pct * 254)
    lora.set_battery_level(lora_bat_level)

    # Return the battery capacity in range [0, 100]
    return pct * 100

'''
################################################################################
#
# Main script
#
# 1. Read the distance from the sensor
# 2. Read battery value
# 3. Join Lorawan
# 4. Transmit the data if join was successful
# 5. Deepsleep for a given amount of time
#
################################################################################
'''

distance = read_distance()
battery  = read_battery_level()
if join_lora(config.FORCE_JOIN):
    for i in range(config.N_TX):
        send_LPP_over_lora(distance, battery)

gc.collect()
ds.go_to_sleep(config.INT_SAMPLING)
