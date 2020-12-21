# HeatingController

## General

OpenTherm server with ESP8266 to control the central heating though REST / Web. Note that this equipment is NOT a thermostat itself. It allows you to create a thermostat yourself and use WiFi / Rest to communicate with the heating equipment. Or connect a regular thermostat in pass-through mode and override / change settings through the Web interface.

Very much work in progress. I just started :-)

Finally, this should work together with [my HeatingController](https://github.com/patrickvbe/HeatingController), which is in finished state.

## Hardware

I based the hardware on info from https://github.com/jpraus/arduino-opentherm. To make it 3.3V compatible for the ESP, I changed this (as described on that page):
* Replace R11 resistor with 4k7 resistor (instead of 10k)
* Connect 3.3V to VLOGIC

