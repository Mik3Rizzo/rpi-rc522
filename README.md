# RC522-Python library

This library is the combination of 2 legacy libraries that were developed by Mario Gomez and Ondřej Ondryáš.

The pirc522 library by Ondřej Ondryáš contained a full package that can be easily installed into the raspberry pi.

The MFRC522-Python script by Mario Gomez is another very nice code, written into MFRC522.py file that should be imported every time from the same directory.

The pirc522 library stopped working due to changes in the raspberry pi system but the MFRC522 kept on working perfectly well.
We at STEMinds combined both libraries, the pirc522 easy package with the MFRC522-Python working code to create an update RC-522 library for the Raspberry Pi

## About MFRC522-python

A small class to interface with the NFC reader Module MFRC522 on the Raspberry Pi. This is a Python port of the example code for the NFC module MF522-AN.
Git link for the official [MFRC522-python](https://github.com/mxgxw/MFRC522-python/blob/master/README.md) library.

## About pirc522

pi-rc522 consists of two Python classes for controlling an SPI RFID module "RC522" using Raspberry Pi or Beaglebone Black. You can get this module on AliExpress or Ebay for $3.

pi-rc522 is based on [MFRC522-python](https://github.com/mxgxw/MFRC522-python/blob/master/README.md).

Note: begale-bone support removed at RC522-Python library.

## Requirements

The software requires a version of SPI-Py, find it in the SPI-Py folder
To install, from this folder run the following commands:
Or get source code from Github:

```
cd SPI-Py
sudo python3 setup.py install
```

The SPI-Py is not related to RC522-Python and includes separated license.

## Examples
This repository includes a couple of examples showing how to read, write, and dump data from a chip. They are thoroughly commented, and should be easy to understand.

## Pins
You can use [this](http://i.imgur.com/y7Fnvhq.png) image for reference.

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


## License

This Repository is licensed under GNU LESSER GENERAL PUBLIC LICENSE.
The repository is based on pi-rc522 which is licensed under MIT and MFRC522-Python which is based on GNU.
because pi-rc522 to begin with is based on MFRC522-Python which is licensed under GNU, this library will also be licensed under GNU.

Copyright 2014,2018 Mario Gomez <mario.gomez@teubi.co> for MFRC522-Python
Copyright (c) 2016 Ondřej Ondryáš {ondryaso} for pi-rc522
Copyright (c) 2020 STEMinds for modifications and combining both libraries

This file contains parts from MFRC522-Python and pi-rc522
MFRC522-Python and pi-rc522 is a simple Python implementation for
the MFRC522 NFC Card Reader for the Raspberry Pi.

MFRC522-Python and pi-rc522 are free software: you can redistribute it and/or modify
it under the terms of the GNU Lesser General Public License as published by
the Free Software Foundation, either version 3 of the License, or (at your option) any later version.

MFRC522-Python and pi-rc522 is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU Lesser General Public License for more details.

You should have received a copy of the GNU Lesser General Public License
along with MFRC522-Python and pi-rc522.  If not, see <http://www.gnu.org/licenses/>.

Original git of MFRC522-Python: [MFRC522-python](https://github.com/mxgxw/MFRC522-python).
Original git of pi-rc522: [pi-rc522](https://github.com/ondryaso/pi-rc522).
