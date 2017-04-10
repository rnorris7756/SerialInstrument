# SerialInstrument

SerialInstrument is a library for controlling common laboratory equipment via serial port. Basic support for HP/Agilent 34401a multimeters exists, as well as the 33120A function generator and E3646A dual-output power supply.

The listed devices above are supported explicitly because they are the instruments I have access to.  In theory, any SCPI-compliant instrument should be usable under the base SerialInstrument class, as long as the device baud rate, stop bits, etc. are set properly.

As a convenience, you can drop into a REPL for a connected device at any time by calling the `enter_repl()` method.  The REPL will send any text to the device and return a response (if any).  This is useful for debugging and trying out SCPI commands on your instrument.  In debug mode, the REPL will also check for any errors reported by the instrument and print them out.

An example of using a REPL:

```python
>>>from serialinstrument import *
>>>device1 = SerialInstrument('/dev/ttyUSB0')
>>>device1.enter_repl()
>>*IDN?
>>HEWLETT-PACKARD,34401A,0,11-5-2
>>exit
>>>
```

The `classify_instrument` method will attempt to search for the proper device ID and classify a SerialInstrument as the correct type of device.

```python
>>>mm = SerialInstrument('/dev/ttyUSB1').classify_instrument()
>>>mm.measure_vdc()
>>>+5.00000E0
```

This library is a work in progress.  It's meant to fulfill a particular purpose for me, so I will primarily work toward getting the code working for my purposes.  If you find any bugs or would like additional functionality, feel free to open an issue or submit a pull request.
