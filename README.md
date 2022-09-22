# Library rpi-rc522

[rpi-rc522](https://github.com/Mik3Rizzo/rpi-rc522) is a python library written to use the RC522 reader (chip MFRC522) 
on the Raspberry Pi. You can get this cheap NFC reader for less than 3€.

The library is derived from [RC522-Python](https://github.com/STEMinds/RC522-Python) by STEMinds, that is the
combination of two other legacy libraries:

- [pi-rc522](https://github.com/ondryaso/pi-rc522) library by Ondřej Ondryáš
- [MFRC522-Python](https://github.com/pimylifeup/MFRC522-python) by Mario Gomez

All the libraries above and this library as well are based on the Arduino's 
[MFRC522](https://github.com/miguelbalboa/rfid) one; look there for more detailed explanations.


## Improvements

This library is a cleaned, heavy refactored and re-designed version of the ones listed above.

- Simplified structure, with re-designed handy objects and methods ready to be used
- Cleaner code, with lots of comments and significant naming
- More exhaustive debug logs
- Fewer crashes and bugs


## Library structure

The library offers two handy objects:
- **RC522**: low level class that manages the RC522.
- **RC522Manager**: high level class to easily read/write data from/to the NFC tag.

There is also a collection of utils functions.

### Examples

In the `example` folder you can find examples showing how to perform basic NFC operation, like read or write a tag. The 
code is thoroughly commented and should be easy to understand.


## Install

The software requires a specific version of SPI-Py, included in the package. You can install it running the following 
commands from the root repo folder:

```
cd SPI-Py
sudo python3 setup.py install
```

Please, note that the SPI-Py is not related to this library and includes separated license.

To install the **rpi-rc522** library, run from the root repo folder:

```
sudo python3 setup.py install
```


## Pinout

| Name  | Pin #  | Pin name |
|:-----:|:------:|:--------:|
|  SDA  |   24   |  GPIO8   |
|  SCK  |   23   |  GPIO11  |
| MOSI  |   19   |  GPIO10  |
| MISO  |   21   |  GPIO9   |
|  IRQ  |  None  |   None   |
|  GND  | Ground |  Ground  |
|  RST  |   22   |  GPIO25  |
| 3.3V  |   1    |   3V3    |

You can use [this](https://www.raspberrypi-spy.co.uk/wp-content/uploads/2012/06/Raspberry-Pi-GPIO-Header-with-Photo.png) 
image for reference.


## About

**Michele Rizzo**, *Master's Degree Computer Engineering student at University of Brescia*.

Feel free to contact me by [mail](mailto:m.rizzo006@studenti.unibs.it) or visit my [Github](https://github.com/Mik3Rizzo/).