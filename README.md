# ttn-lopy-water-level

A rangefinder sensor for The Things Network using a LoPy and a MB7360 ultrasonic rangefinder.

To convert the RS232 signal from the MB7360 to a TTL one for the LoPy, a MAX3232 board is also used.

The file `main.py` also include a function to send the data using the Cayenne LPP format to be used with the Cayenne Integration of The Things Networks.
