#!/usr/bin/env python
# -*- coding: utf8 -*-
#
#    Copyright 2014,2018 Mario Gomez <mario.gomez@teubi.co> for MFRC522-Python
#    Copyright (c) 2016 Ondřej Ondryáš {ondryaso} for pi-rc522
#    Copyright (c) 2020 STEMinds for modifications and combining both libraries
#
#    This file contains parts from MFRC522-Python and pi-rc522
#    MFRC522-Python and pi-rc522 is a simple Python implementation for
#    the MFRC522 NFC Card Reader for the Raspberry Pi.
#
#    MFRC522-Python and pi-rc522 are free software: you can redistribute it and/or modify
#    it under the terms of the GNU Lesser General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    MFRC522-Python and pi-rc522 is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Lesser General Public License for more details.
#
#    You should have received a copy of the GNU Lesser General Public License
#    along with MFRC522-Python and pi-rc522.  If not, see <http://www.gnu.org/licenses/>.
#
#    Original git of MFRC522-Python: https://github.com/mxgxw/MFRC522-python
#    Original git of pi-rc522: https://github.com/ondryaso/pi-rc522

import RPi.GPIO as GPIO
import spi


NRSTPD = 22

MAX_LEN = 16

PCD_IDLE = 0x00
PCD_AUTHENT = 0x0E
PCD_RECEIVE = 0x08
PCD_TRANSMIT = 0x04
PCD_TRANSCEIVE = 0x0C
PCD_RESETPHASE = 0x0F
PCD_CALCCRC = 0x03

PICC_REQIDL = 0x26
PICC_REQALL = 0x52
PICC_ANTICOLL = 0x93
PICC_SElECTTAG = 0x93
PICC_AUTHENT1A = 0x60
PICC_AUTHENT1B = 0x61
PICC_READ = 0x30
PICC_WRITE = 0xA0
PICC_DECREMENT = 0xC0
PICC_INCREMENT = 0xC1
PICC_RESTORE = 0xC2
PICC_TRANSFER = 0xB0
PICC_HALT = 0x50

MI_OK = 0
MI_NOTAGERR = 1
MI_ERR = 2

Reserved00 = 0x00
CommandReg = 0x01
CommIEnReg = 0x02
DivlEnReg = 0x03
CommIrqReg = 0x04
DivIrqReg = 0x05
ErrorReg = 0x06
Status1Reg = 0x07
Status2Reg = 0x08
FIFODataReg = 0x09
FIFOLevelReg = 0x0A
WaterLevelReg = 0x0B
ControlReg = 0x0C
BitFramingReg = 0x0D
CollReg = 0x0E
Reserved01 = 0x0F

Reserved10 = 0x10
ModeReg = 0x11
TxModeReg = 0x12
RxModeReg = 0x13
TxControlReg = 0x14
TxAutoReg = 0x15
TxSelReg = 0x16
RxSelReg = 0x17
RxThresholdReg = 0x18
DemodReg = 0x19
Reserved11 = 0x1A
Reserved12 = 0x1B
MifareReg = 0x1C
Reserved13 = 0x1D
Reserved14 = 0x1E
SerialSpeedReg = 0x1F

Reserved20 = 0x20
CRCResultRegM = 0x21
CRCResultRegL = 0x22
Reserved21 = 0x23
ModWidthReg = 0x24
Reserved22 = 0x25
RFCfgReg = 0x26
GsNReg = 0x27
CWGsPReg = 0x28
ModGsPReg = 0x29
TModeReg = 0x2A
TPrescalerReg = 0x2B
TReloadRegH = 0x2C
TReloadRegL = 0x2D
TCounterValueRegH = 0x2E
TCounterValueRegL = 0x2F

Reserved30 = 0x30
TestSel1Reg = 0x31
TestSel2Reg = 0x32
TestPinEnReg = 0x33
TestPinValueReg = 0x34
TestBusReg = 0x35
AutoTestReg = 0x36
VersionReg = 0x37
AnalogTestReg = 0x38
TestDAC1Reg = 0x39
TestDAC2Reg = 0x3A
TestADCReg = 0x3B
Reserved31 = 0x3C
Reserved32 = 0x3D
Reserved33 = 0x3E
Reserved34 = 0x3F


class RFIDReader(object):

    # support old code variables
    auth_a = 0x60
    auth_b = 0x61

    authed = False
    serNum = []

    def __init__(self, device='/dev/spidev0.0', speed=1000000):

        spi.openSPI(device=device, speed=speed)
        GPIO.setmode(GPIO.BOARD)
        GPIO.setup(NRSTPD, GPIO.OUT)
        GPIO.output(NRSTPD, 1)
        self.init()

    def init(self):

        GPIO.output(NRSTPD, 1)

        self.reset()

        self.dev_write(TModeReg, 0x8D)
        self.dev_write(TPrescalerReg, 0x3E)
        self.dev_write(TReloadRegL, 30)
        self.dev_write(TReloadRegH, 0)

        self.dev_write(TxAutoReg, 0x40)
        self.dev_write(ModeReg, 0x3D)

        self.set_antenna_on()

    def reset(self):
        self.dev_write(CommandReg, PCD_RESETPHASE)

    def dev_write(self, addr, val):
        spi.transfer(((addr << 1) & 0x7E, val))

    def dev_read(self, addr):
        val = spi.transfer((((addr << 1) & 0x7E) | 0x80, 0))
        return val[1]

    def set_bitmask(self, reg, mask):
        tmp = self.dev_read(reg)
        self.dev_write(reg, tmp | mask)

    def clear_bitmask(self, reg, mask):
        tmp = self.dev_read(reg)
        self.dev_write(reg, tmp & (~mask))

    def set_antenna_on(self):
        temp = self.dev_read(TxControlReg)
        if ~(temp & 0x03):
            self.set_bitmask(TxControlReg, 0x03)

    def set_antenna_off(self):
        self.clear_bitmask(TxControlReg, 0x03)

    def card_write(self, command, send_data):
        back_data = []
        back_len = 0
        status = MI_ERR
        irq_en = 0x00
        wait_i_rq = 0x00
        i = 0

        if command == PCD_AUTHENT:
            irq_en = 0x12
            wait_i_rq = 0x10
        if command == PCD_TRANSCEIVE:
            irq_en = 0x77
            wait_i_rq = 0x30

        self.dev_write(CommIEnReg, irq_en | 0x80)
        self.clear_bitmask(CommIrqReg, 0x80)
        self.set_bitmask(FIFOLevelReg, 0x80)

        self.dev_write(CommandReg, PCD_IDLE)

        while i < len(send_data):
            self.dev_write(FIFODataReg, send_data[i])
            i = i + 1

        self.dev_write(CommandReg, command)

        if command == PCD_TRANSCEIVE:
            self.set_bitmask(BitFramingReg, 0x80)

        i = 2000

        while True:
            n = self.dev_read(CommIrqReg)
            i = i - 1
            if ~((i != 0) and ~(n & 0x01) and ~(n & wait_i_rq)):
                break

        self.clear_bitmask(BitFramingReg, 0x80)

        if i != 0:
            if (self.dev_read(ErrorReg) & 0x1B) == 0x00:
                status = MI_OK

                if n & irq_en & 0x01:
                    status = MI_NOTAGERR

                if command == PCD_TRANSCEIVE:
                    n = self.dev_read(FIFOLevelReg)
                    last_bits = self.dev_read(ControlReg) & 0x07
                    if last_bits != 0:
                        back_len = (n - 1) * 8 + last_bits
                    else:
                        back_len = n * 8

                    if n == 0:
                        n = 1
                    if n > MAX_LEN:
                        n = MAX_LEN

                    i = 0
                    while i < n:
                        back_data.append(self.dev_read(FIFODataReg))
                        i = i + 1
            else:
                status = MI_ERR

        return status, back_data, back_len

    def request(self, req_mode=0x26):
        tag_type = []

        self.dev_write(BitFramingReg, 0x07)

        tag_type.append(req_mode)
        (status, backData, backBits) = self.card_write(PCD_TRANSCEIVE, tag_type)

        if (status != MI_OK) | (backBits != 0x10):
            status = MI_ERR

        return status, backBits

    def anticoll(self):
        ser_num_check = 0
        ser_num = []

        self.dev_write(BitFramingReg, 0x00)

        ser_num.append(PICC_ANTICOLL)
        ser_num.append(0x20)

        (status, backData, backBits) = self.card_write(PCD_TRANSCEIVE, ser_num)

        if status == MI_OK:
            i = 0
            if len(backData) == 5:
                while i < 4:
                    ser_num_check = ser_num_check ^ backData[i]
                    i = i + 1
                if ser_num_check != backData[i]:
                    status = MI_ERR
            else:
                status = MI_ERR

        return status, backData

    def calculate_crc(self, p_in_data):
        self.clear_bitmask(DivIrqReg, 0x04)
        self.set_bitmask(FIFOLevelReg, 0x80)
        i = 0
        while i < len(p_in_data):
            self.dev_write(FIFODataReg, p_in_data[i])
            i = i + 1
        self.dev_write(CommandReg, PCD_CALCCRC)
        i = 0xFF
        while True:
            n = self.dev_read(DivIrqReg)
            i = i - 1
            if not ((i != 0) and not (n & 0x04)):
                break

        p_out_data = [self.dev_read(CRCResultRegL), self.dev_read(CRCResultRegM)]

        return p_out_data

    def select_tag(self, ser_num):

        buf = [PICC_SElECTTAG, 0x70]

        i = 0
        while i < 5:
            buf.append(ser_num[i])
            i = i + 1
        p_out = self.calculate_crc(buf)
        buf.append(p_out[0])
        buf.append(p_out[1])
        (status, backData, backLen) = self.card_write(PCD_TRANSCEIVE, buf)

        if (status == MI_OK) and (backLen == 0x18):
            print("Size: " + str(backData[0]))
            return backData[0]
        else:
            return 0

    def card_auth(self, auth_mode, block_addr, sector_key, ser_num):

        # First byte should be the authMode (A or B), the second is the trailerBlock (usually 7)
        buff = [auth_mode, block_addr]

        # Now we need to append the authKey which usually is 6 bytes of 0xFF
        i = 0
        while i < len(sector_key):
            buff.append(sector_key[i])
            i = i + 1
        i = 0

        # Next we append the first 4 bytes of the UID
        while i < 4:
            buff.append(ser_num[i])
            i = i + 1

        # Now we start the authentication itself
        (status, backData, backLen) = self.card_write(PCD_AUTHENT, buff)

        # Check if an error occurred
        if not (status == MI_OK):
            print("AUTH ERROR!!")
        if not (self.dev_read(Status2Reg) & 0x08) != 0:
            print("AUTH ERROR(status2reg & 0x08) != 0")
        else:
            self.authed = True

        # Return the status
        return status

    def stop_crypto(self):
        self.clear_bitmask(Status2Reg, 0x08)
        self.authed = False

    def cleanup(self):
        """
        Calls stop_crypto() if needed and cleanups GPIO.
        """
        if self.authed:
            self.stop_crypto()
        GPIO.cleanup()

    def read(self, block_addr):

        recv_data = [PICC_READ, block_addr]

        p_out = self.calculate_crc(recv_data)
        recv_data.append(p_out[0])
        recv_data.append(p_out[1])
        (status, back_data, back_len) = self.card_write(PCD_TRANSCEIVE, recv_data)
        if not (status == MI_OK):
            print("Error while reading!")

        #if len(back_data) == 16:
        #    print("Sector " + str(block_addr) + " " + str(back_data))

        return status, back_data

    def write(self, block_addr, write_data):

        buff = [PICC_WRITE, block_addr]

        crc = self.calculate_crc(buff)
        buff.append(crc[0])
        buff.append(crc[1])
        (status, back_data, back_len) = self.card_write(PCD_TRANSCEIVE, buff)

        if not (status == MI_OK) or not (back_len == 4) or not ((back_data[0] & 0x0F) == 0x0A):
            status = MI_ERR

        print("%s backdata &0x0F == 0x0A %s" % (back_len, back_data[0] & 0x0F))
        if status == MI_OK:
            i = 0
            buf = []
            while i < 16:
                buf.append(write_data[i])
                i = i + 1
            crc = self.calculate_crc(buf)
            buf.append(crc[0])
            buf.append(crc[1])
            (status, back_data, back_len) = self.card_write(PCD_TRANSCEIVE, buf)
            if not (status == MI_OK) or not (back_len == 4) or not ((back_data[0] & 0x0F) == 0x0A):
                print("Error while writing")
            if status == MI_OK:
                print("Data written")
        return status

    def dump_classic_1k(self, key, uid):
        i = 0
        while i < 64:
            status = self.card_auth(PICC_AUTHENT1A, i, key, uid)
            # Check if authenticated
            if status == MI_OK:
                self.read(i)
            else:
                print("Authentication error")
            i = i + 1
        return status

    def wait_for_tag(self):
        # Scan for cards
        waiting = True
        while waiting:
            (status, TagType) = self.request(PICC_REQIDL)
            # If a card is found
            if status == MI_OK:
                # card detected
                waiting = False
        self.init()
