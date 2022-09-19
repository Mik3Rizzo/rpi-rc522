#!/usr/bin/env python

import RPi.GPIO as GPIO
import spi


RST_BCM_PIN = 25  # BOARD 22

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


class RFIDReader:
    """
    Represents an RC522 RFID Reader, connected through SPI.
    """

    AUTH_A = 0x60
    AUTH_B = 0x61

    # Status
    MI_OK = 0
    MI_NO_TAG_ERR = 1
    MI_ERR = 2

    def __init__(self, device='/dev/spidev0.0', speed=1000000, debug=False):

        self.authed = False

        self.debug = debug

        spi.openSPI(device=device, speed=speed)
        GPIO.setwarnings(self.debug)
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(RST_BCM_PIN, GPIO.OUT)
        GPIO.output(RST_BCM_PIN, 1)
        self.__init()

    def __init(self):

        GPIO.output(RST_BCM_PIN, 1)

        self.__reset()

        self.__dev_write(TModeReg, 0x8D)
        self.__dev_write(TPrescalerReg, 0x3E)
        self.__dev_write(TReloadRegL, 30)
        self.__dev_write(TReloadRegH, 0)

        self.__dev_write(TxAutoReg, 0x40)
        self.__dev_write(ModeReg, 0x3D)

        self.__set_antenna_on()

    @staticmethod
    def __dev_write(addr, val):
        spi.transfer(((addr << 1) & 0x7E, val))

    @staticmethod
    def __dev_read(addr):
        val = spi.transfer((((addr << 1) & 0x7E) | 0x80, 0))
        return val[1]

    def __reset(self):
        self.__dev_write(CommandReg, PCD_RESETPHASE)

    def __set_bitmask(self, reg, mask):
        tmp = self.__dev_read(reg)
        self.__dev_write(reg, tmp | mask)

    def __clear_bitmask(self, reg, mask):
        tmp = self.__dev_read(reg)
        self.__dev_write(reg, tmp & (~mask))

    def __set_antenna_on(self):
        temp = self.__dev_read(TxControlReg)
        if ~(temp & 0x03):
            self.__set_bitmask(TxControlReg, 0x03)

    def __set_antenna_off(self):
        self.__clear_bitmask(TxControlReg, 0x03)

    def __stop_crypto(self):
        self.__clear_bitmask(Status2Reg, 0x08)

    def __send_cmd(self, command, send_data):
        back_data = []
        back_len = 0
        status = self.MI_ERR
        irq_en = 0x00
        wait_i_rq = 0x00
        i = 0

        if command == PCD_AUTHENT:
            irq_en = 0x12
            wait_i_rq = 0x10
        if command == PCD_TRANSCEIVE:
            irq_en = 0x77
            wait_i_rq = 0x30

        self.__dev_write(CommIEnReg, irq_en | 0x80)
        self.__clear_bitmask(CommIrqReg, 0x80)
        self.__set_bitmask(FIFOLevelReg, 0x80)

        self.__dev_write(CommandReg, PCD_IDLE)

        while i < len(send_data):
            self.__dev_write(FIFODataReg, send_data[i])
            i = i + 1

        self.__dev_write(CommandReg, command)

        if command == PCD_TRANSCEIVE:
            self.__set_bitmask(BitFramingReg, 0x80)

        i = 2000

        while True:
            n = self.__dev_read(CommIrqReg)
            i = i - 1
            if ~((i != 0) and ~(n & 0x01) and ~(n & wait_i_rq)):
                break

        self.__clear_bitmask(BitFramingReg, 0x80)

        if i != 0:
            if (self.__dev_read(ErrorReg) & 0x1B) == 0x00:
                status = self.MI_OK

                if n & irq_en & 0x01:
                    status = self.MI_NO_TAG_ERR

                if command == PCD_TRANSCEIVE:
                    n = self.__dev_read(FIFOLevelReg)
                    last_bits = self.__dev_read(ControlReg) & 0x07
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
                        back_data.append(self.__dev_read(FIFODataReg))
                        i = i + 1
            else:
                status = self.MI_ERR

        return status, back_data, back_len

    def __calculate_crc(self, p_in_data):
        self.__clear_bitmask(DivIrqReg, 0x04)
        self.__set_bitmask(FIFOLevelReg, 0x80)
        i = 0
        while i < len(p_in_data):
            self.__dev_write(FIFODataReg, p_in_data[i])
            i = i + 1
        self.__dev_write(CommandReg, PCD_CALCCRC)
        i = 0xFF
        while True:
            n = self.__dev_read(DivIrqReg)
            i = i - 1
            if not ((i != 0) and not (n & 0x04)):
                break

        p_out_data = [self.__dev_read(CRCResultRegL), self.__dev_read(CRCResultRegM)]

        return p_out_data

    def request_tag(self, req_mode=0x26):
        tag_type = []

        self.__dev_write(BitFramingReg, 0x07)

        tag_type.append(req_mode)
        (status, back_data, back_bits) = self.__send_cmd(PCD_TRANSCEIVE, tag_type)

        if (status != self.MI_OK) | (back_bits != 0x10):
            status = self.MI_ERR

        return status, back_bits

    def anti_collision(self):
        ser_num_check = 0
        ser_num = []

        self.__dev_write(BitFramingReg, 0x00)

        ser_num.append(PICC_ANTICOLL)
        ser_num.append(0x20)

        (status, backData, backBits) = self.__send_cmd(PCD_TRANSCEIVE, ser_num)

        if status == self.MI_OK:
            i = 0
            if len(backData) == 5:
                while i < 4:
                    ser_num_check = ser_num_check ^ backData[i]
                    i = i + 1
                if ser_num_check != backData[i]:
                    status = self.MI_ERR
            else:
                status = self.MI_ERR

        return status, backData

    def auth(self, auth_mode, block_addr, sector_key, ser_num):

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
        (status, backData, backLen) = self.__send_cmd(PCD_AUTHENT, buff)

        # Check if an error occurred
        if not (status == self.MI_OK):
            print("[e] Authentication error")
        if not (self.__dev_read(Status2Reg) & 0x08) != 0:
            print("   (status2reg & 0x08) != 0")
        else:
            self.authed = True

        return status

    def deauth(self):
        """
        Calls __stop_crypto() if needed and cleanups GPIO.
        """
        if self.authed:
            self.__stop_crypto()
            self.authed = False

        GPIO.cleanup()

    def set_tag(self, uid):

        buf = [PICC_SElECTTAG, 0x70]

        i = 0
        while i < 5:  # TODO even if the tag has 4 bytes UID, 5 bytes are considered
            buf.append(uid[i])
            i = i + 1
        p_out = self.__calculate_crc(buf)
        buf.append(p_out[0])
        buf.append(p_out[1])
        (status, back_data, back_len) = self.__send_cmd(PCD_TRANSCEIVE, buf)

        if (status == self.MI_OK) and (back_len == 0x18):
            if self.debug:
                print(f"[i] back_data[0] (size): {back_data[0]}")
            return back_data[0]
        else:
            return 0

    def read_block(self, block_addr):
        """
        Reads a desired block.
        :param block_addr: block address number.
        :return: the status and the block's content as list of 8 bit int.
        """
        recv_data = [PICC_READ, block_addr]

        p_out = self.__calculate_crc(recv_data)
        recv_data.append(p_out[0])
        recv_data.append(p_out[1])
        (status, back_data, back_len) = self.__send_cmd(PCD_TRANSCEIVE, recv_data)
        if not (status == self.MI_OK):
            print("[e] Error while reading")

        return status, back_data

    def write_block(self, block_addr, write_data):

        buff = [PICC_WRITE, block_addr]

        crc = self.__calculate_crc(buff)
        buff.append(crc[0])
        buff.append(crc[1])
        (status, back_data, back_len) = self.__send_cmd(PCD_TRANSCEIVE, buff)

        if self.debug:
            print(f"[i] {back_len} (backdata & 0x0F) == 0x0A {(back_data[0] & 0x0F) == 0x0A}")

        if not (status == self.MI_OK) or not (back_len == 4) or not ((back_data[0] & 0x0F) == 0x0A):
            status = self.MI_ERR

        if status == self.MI_OK:
            i = 0
            buf = []
            while i < 16:
                buf.append(write_data[i])
                i = i + 1
            crc = self.__calculate_crc(buf)
            buf.append(crc[0])
            buf.append(crc[1])
            (status, back_data, back_len) = self.__send_cmd(PCD_TRANSCEIVE, buf)
            if not (status == self.MI_OK) or not (back_len == 4) or not ((back_data[0] & 0x0F) == 0x0A):
                print("[e] Error while writing")
            if status == self.MI_OK and self.debug:
                print("[i] Data written")
        return status

    # def dump_classic_1k(self, key, uid):
    #     i = 0
    #     while i < 64:
    #         status = self.auth(PICC_AUTHENT1A, i, key, uid)
    #         # Check if authenticated
    #         if status == MI_OK:
    #             self.read_block(i)
    #         else:
    #             print("Authentication error")
    #         i = i + 1
    #     return status

    # def wait_for_tag(self):
    #     # Scan for cards
    #     waiting = True
    #     while waiting:
    #         (status, TagType) = self.request_tag(PICC_REQIDL)
    #         # If a card is found
    #         if status == MI_OK:
    #             # card detected
    #             waiting = False
    #     self.__init()
