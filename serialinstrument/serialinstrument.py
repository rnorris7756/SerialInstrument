#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
serialinstrument.py: A class for interacting with laboratory instruments over an RS-232 port.
"""

import time
import serial
from enum import Enum

debug = True

# It may be useful to keep a list of known default values per instrument so that if you are using a single, known instrument, you can instantiate it like so:
# my_instrument = SerialInstrument(port = '/path/to/port', **instrument_defaults['my_device_string']).classify_instrument()
# This may be worth putting in its own module if the list of defaults gets long.
instrument_defaults = {'HEWLETT-PACKARD,34401A,0,11-5-2':{'baudrate':9600, 'parity':serial.PARITY_NONE, 'stopbits':serial.STOPBITS_ONE, 'bytesize':serial.EIGHTBITS, 'line_terminator':'\r\n'}
        }

multimeters = ['HEWLETT-PACKARD,34401A,0,11-5-2',
               'HEWLETT-PACKARD,34401A,0,10-5-2'
        ]

function_generators = ['HEWLETT-PACKARD,33120A,0,10.0-5.0-1.0'
        ]

power_supplies = ['Agilent Technologies,E3646A,0,1.4-5.0-1.0'
        ]

outputs = Enum('outputs', 'out1 out2')
voltage_range = Enum('voltage_range', 'low high')

class SerialInstrument():
    """docstring for SerialInstrument"""
    def __init__(self, port=None, baudrate = 9600, parity = serial.PARITY_NONE, stopbits = serial.STOPBITS_ONE, bytesize = serial.EIGHTBITS, ser = None, line_terminator = '\r\n', sleep_time = 0.5):
        self._port = port
        self._sleep_time = sleep_time
        self._instrument_type = 'unknown'
        self._line_terminator = line_terminator
        self._ser = None
        if ser is None:
            if port is None:
                self._ser = None
            else:
                self._ser = serial.Serial(
                        port=port,
                        baudrate=baudrate,
                        parity=parity,
                        stopbits=stopbits,
                        bytesize=bytesize
                        )
        else:
            self._ser = ser
        if not self._ser.isOpen():
            try:
                self._ser.open()
            except:
                print('Unexpected error when opening serial port')
        self.set_remote()
        if debug is True and port is not None:
            self.display_text(port[5:])
        self._identity = self.get_identity()

    @property
    def type(self):
        """Returns the type of instrument as a string.  An unknown instrument returns 'unknown'
        This is set up as a getter property only, since it is only useful for users or code that
        needs to determine an instrument's type."""
        return self._instrument_type

    def classify_instrument(self):
        """Searches the module's built-in lists for known devices and instantiates an object of that type.  Returns None if no matching device is found."""
        print(self._identity)
        if self._identity in multimeters:
            print('Instrument in multimeter list')
            return Multimeter.from_serial_instrument(self)
        elif self._identity in function_generators:
            print('Instrument in function generator list')
            return FunctionGenerator.from_serial_instrument(self)
        elif self._identity in power_supplies:
            print('Instrument in power supply list')
            return PowerSupply.from_serial_instrument(self)
        else:
            return None

    def write_to_serial(self, string):
        """Writes the input string to the serial port and ends with a line terminator."""
        serialcmd = string + self._line_terminator
        self._ser.write(serialcmd.encode())
        time.sleep(self._sleep_time)

    def read_from_serial(self):
        """Reads a reply from the SerialInstrument and returns it as a string"""
        output = b''
        time.sleep(self._sleep_time)
        while self._ser.inWaiting() > 0:
            output = output + self._ser.read(1)
            #A default ten powercycle delay means that some measurements may still be processing
            #by the time the read function is called.  This slows down the read but ensures that
            #it will finish (per my testing).  There is probably a better way to do this.  TODO
            time.sleep(0.06)
        return output.decode('utf-8').strip()

    def query_serial(self, string):
        """Sends the given query string to a device and returns the response.  A shortcut for write_to_serial followed by read_from_serial (this is exactly what it does)"""
        self.write_to_serial(string)
        response = self.read_from_serial()
        if debug is True:
            self.write_to_serial(':SYST:ERR?')
            error = self.read_from_serial()
            if error != '' and error is not None and error != '''+0,"No error"''':
                print('Error with query ' + string + ':')
                print(error)
        return response

    def enter_repl(self):
        """Enters a read-evaluate-print loop for testing/sending commands to serial instruments manually."""
        text_input = ''
        while True:
            text_input = input('>>')
            if text_input == 'exit':
                break
            #An alias for querying an instrument error string
            elif text_input == 'err?':
                self.write_to_serial(':SYST:ERR?')
                print(self.read_from_serial())
            else:
                self.write_to_serial(text_input)
                print(self.read_from_serial())

    def display_text(self, text):
        """Displays a string of text on the front of the device"""
        self.write_to_serial(':DISP:TEXT \'' + text + '\'')

    def set_local(self):
        """Sets the device in local operation mode."""
        self.write_to_serial(':SYST:LOC')

    def set_remote(self):
        """Sets the device in remote operation mode.  This is required on most instruments to begin executing commands."""
        self.write_to_serial(':SYST:REM')

    def get_identity(self):
        """Returns the identity string of the instrument."""
        return self.query_serial('*IDN?')

    def reset(self):
        """Resets the instrument to its power-on state."""
        self.write_to_serial('*RST')
        

    def __del__(self):
        """Clean up the serial connection (if still open) after we are done with the device."""
        if self._ser.isOpen():
            self.reset()
            self.set_local()
            self._ser.close()


class FunctionGenerator(SerialInstrument):
    """Defines a function generator from an RS-232 port"""
    def __init__(self, **kwargs):
        super(FunctionGenerator, self).__init__(**kwargs)
    @classmethod
    def from_serial_instrument(self, instrument):
        """Takes a SerialInstrument and converts it into a FunctionGenerator"""
        return FunctionGenerator(ser=instrument._ser)


class Multimeter(SerialInstrument):
    """docstring for Multimeter"""
    def __init__(self, **kwargs):
        super(Multimeter, self).__init__(**kwargs)
    
    @classmethod
    def from_serial_instrument(self, instrument):
        """Takes a SerialInstrument and converts it into a Multimeter"""
        return Multimeter(ser=instrument._ser)

    def configure_vdc(self, rng, res, unit = 'V'):
        """Configures the multimeter to read DC voltage with range rng and resolution res"""
        self.write_to_serial(':conf:volt:dc ' + str(rng) + ',' + str(res))# + unit)

    def measure_vdc(self, rng = 'DEF', res = 'DEF', unit = 'V', samp = 1):
       """Performs one measurement of DC voltage using the multimeter with the range defined in RNG and the resolution defined in RES."""
       self.configure_vdc(rng, res, unit)
       self.write_to_serial(':samp:coun ' + str(samp))
       if samp == 1:
         return float(self.query_serial('read?'))
       else:
         samples = self.query_serial('read?').split(',')
         sampleresult = []
         for sample in samples:
             sampleresult.append(float(sample))
         return sampleresult

    def configure_adc(self, rng, res, unit = 'A'):
        """Configures the multimeter to read DC voltage with range rng and resolution res"""
        self.write_to_serial(':conf:curr:dc ' + str(rng) + ',' + str(res))# + unit)

    def measure_adc(self, rng = 'DEF', res = 'DEF', unit = 'A', samp = 1):
       """Performs one measurement of DC amperage using the multimeter with the range defined in RNG and the resolution defined in RES."""
       self.configure_adc(rng, res, unit)
       self.write_to_serial(':samp:coun ' + str(samp))
       if samp == 1:
         return float(self.query_serial('read?'))
       else:
         samples = self.query_serial('read?').split(',')
         sampleresult = []
         for sample in samples:
             sampleresult.append(float(sample))
         return sampleresult
    

class PowerSupply(SerialInstrument):
    """A DC power supply as a subclass of a SerialInstrument."""

    def __init__(self, **kwargs):
        super(PowerSupply, self).__init__(**kwargs)
        self._output_state = {outputs.out1 : False, outputs.out2 : False}
        self._selected_output = None
        self._voltage_output_range = None
        self.write_to_serial('*RST')

    @classmethod
    def from_serial_instrument(self, instrument):
        """Takes a SerialInstrument and converts it into a PowerSupply"""
        return PowerSupply(ser=instrument._ser)

    def set_output_voltage(self, output_voltage, output_port = outputs.out1):
        """Sets the output voltage on the desired port.  Several if statements are used here to reduce unnecessary serial writes."""
        if abs(output_voltage) < 8.0 and self._voltage_output_range != voltage_range.low:
            self.write_to_serial(':volt:rang low')
            self._voltage_output_range = voltage_range.low
        elif abs(output_voltage) >= 8.0 and self._voltage_output_range != voltage_range.high:
            self.write_to_serial(':volt:rang high')
            self._voltage_output_range = voltage_range.high

        if self._output_state[output_port] is False:
            self.write_to_serial(':outp:stat on')

        if self._selected_output != output_port:
            self.write_to_serial(':inst:sel ' + output_port.name)
            self._selected_output = output_port

        self.write_to_serial(':volt ' + str(output_voltage))

    def set_output_current(self, output_current, output_port = outputs.out1):
        """Sets the output current on the desired port.  Several if statements are used here to reduce unnecessary serial writes."""
        #If the voltage is in the low limit, current will probably be limited.  So, always set to high voltage here.
        #This should probably be smarter in a future release, so that it only goes to high voltage if low voltage is insufficient to drive the desired current.
        self.set_output_voltage(20.0 , output_port)

        if self._output_state[output_port] is False:
            self.write_to_serial(':outp:stat on')

        if self._selected_output != output_port:
            self.write_to_serial(':inst:sel ' + output_port.name)
            self._selected_output = output_port

        self.write_to_serial(':curr ' + str(output_current))


if __name__ == '__main__':
    from serial.tools import list_ports
    serial_devices = list_ports.comports()
    print("Found" + str(len(serial_devices)) + " connected serial devices")
    instruments = []
    for device in serial_devices:
        instruments.append(SerialInstrument(port = device.device))
    print("Device IDs:")
    for instrument in instruments:
        print(instrument._identity + " on " + instrument._port)
    inst = []
    for instrument in instruments:
        inst.append(instrument.classify_instrument())
