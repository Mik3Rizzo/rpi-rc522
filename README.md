# RPi-RFIDReader

[RPi-RFIDReader](https://github.com/Mik3Rizzo/rpi-rc522) is a python library written to use the RFIDReader chip on the Raspberry Pi.
You can get this cheap NFC reader chip for less than 3$.

It is derived from [RFIDReader-Python](https://github.com/STEMinds/RC522-Python) by STEMinds, that is the
combination of two other legacy libraries:

- [pi-rc522](https://github.com/ondryaso/pi-rc522) library by Ondřej Ondryáš
- [MFRC522-Python](https://github.com/pimylifeup/MFRC522-python) by Mario Gomez


## Library structure

This library is a cleaned, heavy refactored and sligthly improved version of the ones listed above.

It offers three handy objects:
- **RFIDReader**: low level class that manages the RFIDReader.
- **RFIDUtil**: util class.
- **RFIDManager**: high level class to easily read/write data from/to an NFC tag.

### Examples

In the `example` folder you can find examples showing how to read, write, and dump data from a chip. They are thoroughly 
commented, and should be easy to understand.

## Install

The software requires a version of SPI-Py.
Get source code from Github or install it running the following commands from this folder:

```
cd SPI-Py
sudo python3 setup.py install
```

The SPI-Py is not related to this library and includes separated license.

To install the RPi-RFIDReader library, run from the root folder:

```
sudo python3 setup.py install
```


## Pinout

| Name | Pin # | Pin name   |
|:------:|:-------:|:------------:|
| SDA  | 24    | GPIO8      |
| SCK  | 23    | GPIO11     |
| MOSI | 19    | GPIO10     |
| MISO | 21    | GPIO9      |
| IRQ  | None  | None       |
| GND  | Any   | Any Ground |
| RST  | 22    | GPIO25     |
| 3.3V | 1     | 3V3        |

You can use [this](http://i.imgur.com/y7Fnvhq.png) image for reference.


## About

**Michele Rizzo**, *Master's Degree Computer Engineering student at University of Brescia*.

Feel free to contact me by [mail](mailto:m.rizzo006@studenti.unibs.it) or visit my [Github](https://github.com/Mik3Rizzo/).