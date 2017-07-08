# Water level with a LoPy
#
# Main script
#
# Author:  J. Barthelemy
# Version: 04 July 2017

import time
from machine import ADC, Pin, deepsleep
from network import LoRa
import socket
import binascii
import struct
import pycom

# setting up the Analog/Digital Converter with 10 bits for the ultrasonic sensor
adc = ADC(bits=10)
# create an analog pin on P20
apin = adc.channel(pin='P20',attn=ADC.ATTN_11DB)

# setting up the pins to start/stop the sensor
# ... Pin 19 is pulled down and is set to be an output
pin_activation_sensor = Pin('P19', mode=Pin.OUT, pull=Pin.PULL_DOWN)
# ... holding the pin value during deep sleep
pin_activation_sensor.hold(True)

# init Lorawan
lora = LoRa(mode=LoRa.LORAWAN, public=1, adr=0, tx_retries=0, device_class=LoRa.CLASS_A)

def read_distance():
    '''Reading distance using the ultrasonic sensor'''

    # waking it up
    pin_activation_sensor.value(True)
    time.sleep_us(50)

    # reading 10 values
    list_dist = list()
    for i in range(11):
        list_dist.append(apin() * 5)
        time.sleep_us(50)

    # sorting them
    list_dist.sort()

    # making it asleep
    pin_activation_sensor.value(False)

    # returning the median distance
    return list_dist[5]

def join_lora():
    '''Joining The Things Network '''

    # create an OTA authentication params
    app_eui = binascii.unhexlify('XX XX XX XX XX XX XX XX'.replace(' ',''))
    app_key = binascii.unhexlify('XX XX XX XX XX XX XX XX XX XX XX XX XX XX XX XX'.replace(' ',''))

    # remove default channels
    for i in range(0,72):
        lora.remove_channel(i)

    # adding the Australian channels
    if NANO_GATEWAY:
        print('... using a nano gateway')
        for i in range(3):
            lora.add_channel(i, frequency=918000000, dr_min=0, dr_max=3)
    else:
        print('... using a TTN gateway')
        for i in range(8,15):
            lora.add_channel(i, frequency = 915200000 + i * 200000, dr_min=0, dr_max=3)
        lora.add_channel(65, frequency=917500000, dr_min=4, dr_max=4)

        for i in range(0,7):
            lora.add_channel(i, frequency=923300000 + i * 600000, dr_min=0, dr_max=3)

    # join a network using OTAA
    lora.join(activation=LoRa.OTAA, auth=(app_eui, app_key), timeout=0)

    # wait until the module has joined the network
    pycom.rgbled(0x7f7f00)
    attempt = 0
    while not lora.has_joined() and attempt < MAX_JOIN_ATTEMPT:
        time.sleep(2.5)
        print('Not joined yet...')
        attempt = attempt + 1

    if lora.has_joined():
        print('TTN joined!')
        pycom.rgbled(0x000000)
        return True
    else:
        print('Could not join TTN!')
        pycom.rgbled(0x7f0000)
        return False

def get_battery_level():
    '''Getting the battery level'''
    # see https://forum.pycom.io/topic/226/lopy-adcs/6

    # read the lopy schematic to see what is the voltage divider applied
    # do not forget to use the proper attenuation
    # then use adc to read the value on pin 16 and depending on the resolution
    # i.e. the number of bits used by the ADC, compute the voltage of the
    # LiPo battery.
    # We might need to test to see what is the voltage of the battery at which
    # it stops to work.

    return 1000

def send_values_over_lora(val, bat, port=1):
    '''Sending the water and battery levels over LoraWan on a given port'''

    # create a LoRa socket
    s = socket.socket(socket.AF_LORA, socket.SOCK_RAW)

    # set the LoRaWAN data rate
    s.setsockopt(socket.SOL_LORA, socket.SO_DR, 4)

    # selecting non-confirmed type of messages
    s.setsockopt(socket.SOL_LORA, socket.SO_CONFIRMED, False)

    # make the socket non blocking
    s.setblocking(False)

    # selecting port
    s.bind(port)

    # Sending some packets
    s.send(b'{0};{1}'.format(val, bat))

def send_LPP_over_lora(val, bat, port=2):
    '''Sending the water and battery levels over LoraWan on a given port using Cayenne LPP format'''

   # create a LoRa socket
   s = socket.socket(socket.AF_LORA, socket.SOCK_RAW)

   # set the LoRaWAN data rate
   s.setsockopt(socket.SOL_LORA, socket.SO_DR, 4)

   # make the socket non blocking
   s.setblocking(False)

   # selecting port
   s.bind(port)

   # creating LPP packets metadata
   # ... distance: channel and data type
   channel_dst    = 1
   data_dst       = 2
   # ... battery: channel and data type
   channel_bat    = 2
   data_bat       = 2

   # sending the packet
   s.send(bytes([channel_dst, data_dst]) + struct.pack('>h',val * 10) +
          bytes([channel_bat, data_bat]) + struct.pack('>h',bat * 10))


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
battery  = get_battery_level()
if join_lora():
    #send_values_over_lora(distance, battery)
    send_LPP_over_lora(distance, battery)

deepsleep(INT_SAMPLING)
