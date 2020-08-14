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

class RFID(object):

  NRSTPD = 22

  MAX_LEN = 16

  PCD_IDLE       = 0x00
  PCD_AUTHENT    = 0x0E
  PCD_RECEIVE    = 0x08
  PCD_TRANSMIT   = 0x04
  PCD_TRANSCEIVE = 0x0C
  PCD_RESETPHASE = 0x0F
  PCD_CALCCRC    = 0x03

  PICC_REQIDL    = 0x26
  PICC_REQALL    = 0x52
  PICC_ANTICOLL  = 0x93
  PICC_SElECTTAG = 0x93
  PICC_AUTHENT1A = 0x60
  PICC_AUTHENT1B = 0x61
  PICC_READ      = 0x30
  PICC_WRITE     = 0xA0
  PICC_DECREMENT = 0xC0
  PICC_INCREMENT = 0xC1
  PICC_RESTORE   = 0xC2
  PICC_TRANSFER  = 0xB0
  PICC_HALT      = 0x50

  # support old code variables
  auth_a = 0x60
  auth_b = 0x61

  MI_OK       = 0
  MI_NOTAGERR = 1
  MI_ERR      = 2

  Reserved00     = 0x00
  CommandReg     = 0x01
  CommIEnReg     = 0x02
  DivlEnReg      = 0x03
  CommIrqReg     = 0x04
  DivIrqReg      = 0x05
  ErrorReg       = 0x06
  Status1Reg     = 0x07
  Status2Reg     = 0x08
  FIFODataReg    = 0x09
  FIFOLevelReg   = 0x0A
  WaterLevelReg  = 0x0B
  ControlReg     = 0x0C
  BitFramingReg  = 0x0D
  CollReg        = 0x0E
  Reserved01     = 0x0F

  Reserved10     = 0x10
  ModeReg        = 0x11
  TxModeReg      = 0x12
  RxModeReg      = 0x13
  TxControlReg   = 0x14
  TxAutoReg      = 0x15
  TxSelReg       = 0x16
  RxSelReg       = 0x17
  RxThresholdReg = 0x18
  DemodReg       = 0x19
  Reserved11     = 0x1A
  Reserved12     = 0x1B
  MifareReg      = 0x1C
  Reserved13     = 0x1D
  Reserved14     = 0x1E
  SerialSpeedReg = 0x1F

  Reserved20        = 0x20
  CRCResultRegM     = 0x21
  CRCResultRegL     = 0x22
  Reserved21        = 0x23
  ModWidthReg       = 0x24
  Reserved22        = 0x25
  RFCfgReg          = 0x26
  GsNReg            = 0x27
  CWGsPReg          = 0x28
  ModGsPReg         = 0x29
  TModeReg          = 0x2A
  TPrescalerReg     = 0x2B
  TReloadRegH       = 0x2C
  TReloadRegL       = 0x2D
  TCounterValueRegH = 0x2E
  TCounterValueRegL = 0x2F

  Reserved30      = 0x30
  TestSel1Reg     = 0x31
  TestSel2Reg     = 0x32
  TestPinEnReg    = 0x33
  TestPinValueReg = 0x34
  TestBusReg      = 0x35
  AutoTestReg     = 0x36
  VersionReg      = 0x37
  AnalogTestReg   = 0x38
  TestDAC1Reg     = 0x39
  TestDAC2Reg     = 0x3A
  TestADCReg      = 0x3B
  Reserved31      = 0x3C
  Reserved32      = 0x3D
  Reserved33      = 0x3E
  Reserved34      = 0x3F

  authed = False

  serNum = []

  def __init__(self, device='/dev/spidev0.0', speed=1000000):

    spi.openSPI(device=device,speed=speed)
    GPIO.setmode(GPIO.BOARD)
    GPIO.setup(self.NRSTPD, GPIO.OUT)
    GPIO.output(self.NRSTPD, 1)
    self.init()

  def init(self):

    GPIO.output(self.NRSTPD, 1)

    self.reset();

    self.dev_write(self.TModeReg, 0x8D)
    self.dev_write(self.TPrescalerReg, 0x3E)
    self.dev_write(self.TReloadRegL, 30)
    self.dev_write(self.TReloadRegH, 0)

    self.dev_write(self.TxAutoReg, 0x40)
    self.dev_write(self.ModeReg, 0x3D)

    self.set_antenna_on()

  def reset(self):
    authed = False
    self.dev_write(self.CommandReg, self.PCD_RESETPHASE)

  def dev_write(self, addr, val):
    spi.transfer(((addr<<1)&0x7E,val))

  def dev_read(self, addr):
    val = spi.transfer((((addr<<1)&0x7E) | 0x80,0))
    return val[1]

  def set_bitmask(self, reg, mask):
    tmp = self.dev_read(reg)
    self.dev_write(reg, tmp | mask)

  def clear_bitmask(self, reg, mask):
    tmp = self.dev_read(reg);
    self.dev_write(reg, tmp & (~mask))

  def set_antenna_on(self):
    temp = self.dev_read(self.TxControlReg)
    if(~(temp & 0x03)):
      self.set_bitmask(self.TxControlReg, 0x03)

  def set_antenna_off(self):
    self.clear_bitmask(self.TxControlReg, 0x03)

  def card_write(self,command,sendData):
    backData = []
    backLen = 0
    status = self.MI_ERR
    irqEn = 0x00
    waitIRq = 0x00
    lastBits = None
    n = 0
    i = 0

    if command == self.PCD_AUTHENT:
      irqEn = 0x12
      waitIRq = 0x10
    if command == self.PCD_TRANSCEIVE:
      irqEn = 0x77
      waitIRq = 0x30

    self.dev_write(self.CommIEnReg, irqEn|0x80)
    self.clear_bitmask(self.CommIrqReg, 0x80)
    self.set_bitmask(self.FIFOLevelReg, 0x80)

    self.dev_write(self.CommandReg, self.PCD_IDLE);

    while(i<len(sendData)):
      self.dev_write(self.FIFODataReg, sendData[i])
      i = i+1

    self.dev_write(self.CommandReg, command)

    if command == self.PCD_TRANSCEIVE:
      self.set_bitmask(self.BitFramingReg, 0x80)

    i = 2000
    while True:
      n = self.dev_read(self.CommIrqReg)
      i = i - 1
      if ~((i!=0) and ~(n&0x01) and ~(n&waitIRq)):
        break

    self.clear_bitmask(self.BitFramingReg, 0x80)

    if i != 0:
      if (self.dev_read(self.ErrorReg) & 0x1B)==0x00:
        status = self.MI_OK

        if n & irqEn & 0x01:
          status = self.MI_NOTAGERR

        if command == self.PCD_TRANSCEIVE:
          n = self.dev_read(self.FIFOLevelReg)
          lastBits = self.dev_read(self.ControlReg) & 0x07
          if lastBits != 0:
            backLen = (n-1)*8 + lastBits
          else:
            backLen = n*8

          if n == 0:
            n = 1
          if n > self.MAX_LEN:
            n = self.MAX_LEN

          i = 0
          while i<n:
            backData.append(self.dev_read(self.FIFODataReg))
            i = i + 1;
      else:
        status = self.MI_ERR

    return (status,backData,backLen)


  def request(self, reqMode=0x26):
    status = None
    backBits = None
    TagType = []

    self.dev_write(self.BitFramingReg, 0x07)

    TagType.append(reqMode);
    (status,backData,backBits) = self.card_write(self.PCD_TRANSCEIVE, TagType)

    if ((status != self.MI_OK) | (backBits != 0x10)):
      status = self.MI_ERR

    return (status,backBits)


  def anticoll(self):
    backData = []
    serNumCheck = 0

    serNum = []

    self.dev_write(self.BitFramingReg, 0x00)

    serNum.append(self.PICC_ANTICOLL)
    serNum.append(0x20)

    (status,backData,backBits) = self.card_write(self.PCD_TRANSCEIVE,serNum)

    if(status == self.MI_OK):
      i = 0
      if len(backData)==5:
        while i<4:
          serNumCheck = serNumCheck ^ backData[i]
          i = i + 1
        if serNumCheck != backData[i]:
          status = self.MI_ERR
      else:
        status = self.MI_ERR

    return (status,backData)

  def calculate_crc(self, pIndata):
    self.clear_bitmask(self.DivIrqReg, 0x04)
    self.set_bitmask(self.FIFOLevelReg, 0x80);
    i = 0
    while i<len(pIndata):
      self.dev_write(self.FIFODataReg, pIndata[i])
      i = i + 1
    self.dev_write(self.CommandReg, self.PCD_CALCCRC)
    i = 0xFF
    while True:
      n = self.dev_read(self.DivIrqReg)
      i = i - 1
      if not ((i != 0) and not (n&0x04)):
        break
    pOutData = []
    pOutData.append(self.dev_read(self.CRCResultRegL))
    pOutData.append(self.dev_read(self.CRCResultRegM))
    return pOutData

  def select_tag(self, serNum):
    backData = []
    buf = []
    buf.append(self.PICC_SElECTTAG)
    buf.append(0x70)
    i = 0
    while i<5:
      buf.append(serNum[i])
      i = i + 1
    pOut = self.calculate_crc(buf)
    buf.append(pOut[0])
    buf.append(pOut[1])
    (status, backData, backLen) = self.card_write(self.PCD_TRANSCEIVE, buf)

    if (status == self.MI_OK) and (backLen == 0x18):
      print("Size: " + str(backData[0]))
      return    backData[0]
    else:
      return 0

  def card_auth(self, authMode, BlockAddr, Sectorkey, serNum):
    buff = []

    # First byte should be the authMode (A or B)
    buff.append(authMode)

    # Second byte is the trailerBlock (usually 7)
    buff.append(BlockAddr)

    # Now we need to append the authKey which usually is 6 bytes of 0xFF
    i = 0
    while(i < len(Sectorkey)):
      buff.append(Sectorkey[i])
      i = i + 1
    i = 0

    # Next we append the first 4 bytes of the UID
    while(i < 4):
      buff.append(serNum[i])
      i = i +1

    # Now we start the authentication itself
    (status, backData, backLen) = self.card_write(self.PCD_AUTHENT,buff)

    # Check if an error occurred
    if not(status == self.MI_OK):
      print("AUTH ERROR!!")
    if not (self.dev_read(self.Status2Reg) & 0x08) != 0:
      print("AUTH ERROR(status2reg & 0x08) != 0")
    else:
      self.authed = True

    # Return the status
    return status

  def stop_crypto(self):
    self.clear_bitmask(self.Status2Reg, 0x08)
    self.authed = False

  def cleanup(self):
    """
    Calls stop_crypto() if needed and cleanups GPIO.
    """
    if self.authed:
        self.stop_crypto()
    GPIO.cleanup()

  def halt(self):
    """Switch state to HALT"""

    buf = []
    buf.append(self.act_end)
    buf.append(0)

    crc = self.calculate_crc(buf)
    self.clear_bitmask(0x08, 0x80)
    self.card_write(self.mode_transrec, buf)
    self.clear_bitmask(0x08, 0x08)
    self.authed = False

  def read(self, blockAddr):
    recvData = []
    recvData.append(self.PICC_READ)
    recvData.append(blockAddr)
    pOut = self.calculate_crc(recvData)
    recvData.append(pOut[0])
    recvData.append(pOut[1])
    (status, backData, backLen) = self.card_write(self.PCD_TRANSCEIVE, recvData)
    if not(status == self.MI_OK):
      print("Error while reading!")
    i = 0
    if len(backData) == 16:
      print("Sector "+str(blockAddr)+" "+str(backData))

    return (status, backData)

  def write(self, blockAddr, writeData):
    buff = []
    buff.append(self.PICC_WRITE)
    buff.append(blockAddr)
    crc = self.calculate_crc(buff)
    buff.append(crc[0])
    buff.append(crc[1])
    (status, backData, backLen) = self.card_write(self.PCD_TRANSCEIVE, buff)
    if not(status == self.MI_OK) or not(backLen == 4) or not((backData[0] & 0x0F) == 0x0A):
        status = self.MI_ERR

    print("%s backdata &0x0F == 0x0A %s" % (backLen, backData[0]&0x0F))
    if status == self.MI_OK:
        i = 0
        buf = []
        while i < 16:
            buf.append(writeData[i])
            i = i + 1
        crc = self.calculate_crc(buf)
        buf.append(crc[0])
        buf.append(crc[1])
        (status, backData, backLen) = self.card_write(self.PCD_TRANSCEIVE,buf)
        if not(status == self.MI_OK) or not(backLen == 4) or not((backData[0] & 0x0F) == 0x0A):
            print("Error while writing")
        if status == self.MI_OK:
            print("Data written")
    return status

  def dumpClassic1K(self, key, uid):
    i = 0
    while i < 64:
        status = self.card_auth(self.PICC_AUTHENT1A, i, key, uid)
        # Check if authenticated
        if status == self.MI_OK:
            self.read(i)
        else:
            print("Authentication error")
        i = i+1
    return status

  def wait_for_tag(self):
    # Scan for cards
    waiting = True
    while waiting:
        (status,TagType) = self.request(self.PICC_REQIDL)
        # If a card is found
        if status == self.MI_OK:
            # card detected
            waiting = False
    self.init()

  def util(self):
    """
    Creates and returns RFIDUtil object for this RFID instance.
    If module is not present, returns None.
    """
    try:
        from .util import RFIDUtil
        return RFIDUtil(self)
    except ImportError:
            return None
