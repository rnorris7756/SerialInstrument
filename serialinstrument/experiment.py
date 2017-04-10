#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
experiment.py: set up and run an automated experiment for measuring the hyperfine structure of rubidium.
"""

from serialinstrument import SerialInstrument
from serial.tools import list_ports

if __name__ == '__main__':
    serial_devices = list_ports.comports()
    print("Found" + str(len(serial_devices)) + " connected serial devices")
    instruments = []
    for device in serial_devices:
        instruments.append(SerialInstrument(port = device.device))
    print("Device IDs:")
    for instrument in instruments:
        print(instrument._identity + " on " + instrument._port)


