#!/usr/bin/env python

import RPi.GPIO as GPIO
import spi


class RC522:
    """
    Low level class that manages an RC522 RFID Reader, connected through SPI.
    """

    PIN_RST_BCM = 25  # BOARD 22
    MAX_LEN = 16

    # Commands
    CMD_IDLE = 0x00
    CMD_AUTHENTICATE = 0x0E
    CMD_RECEIVE = 0x08
    CMD_TRANSMIT = 0x04
    CMD_TRANSCEIVE = 0x0C
    CMD_RESET_PHASE = 0x0F
    CMD_CALC_CRC = 0x03

    # Actions
    ACT_REQ_IDL = 0x26
    ACT_REQ_ALL = 0x52
    ACT_ANTICOLL = 0x93
    ACT_SELECT_TAG = 0x93
    ACT_AUTH_1A = 0x60
    ACT_AUTH_1B = 0x61
    ACT_READ = 0x30
    ACT_WRITE = 0xA0
    ACT_DECREMENT = 0xC0
    ACT_INCREMENT = 0xC1
    ACT_RESTORE = 0xC2
    ACT_TRANSFER = 0xB0
    ACT_HALT = 0x50

    # Register addresses
    RESERVED_00 = 0x00
    REG_COMMAND = 0x01
    REG_COMM_I_EN = 0x02
    REG_DIVL_EN = 0x03
    REG_COMM_IRQ = 0x04
    REG_DIV_IRQ = 0x05
    REG_ERROR = 0x06
    REG_STATUS_1 = 0x07
    REG_STATUS_2 = 0x08
    REG_FIFO_DATA = 0x09
    REG_FIFO_LEVEL = 0x0A
    REG_WATER_LEVEL = 0x0B
    REG_CONTROL = 0x0C
    REG_BIT_FRAMING = 0x0D
    REG_COLLISION = 0x0E
    RESERVED_01 = 0x0F

    RESERVED_10 = 0x10
    REG_MODE = 0x11
    REG_TX_MODE = 0x12
    REG_RX_MODE = 0x13
    REG_TX_CONTROL = 0x14
    REG_TX_AUTO = 0x15
    REG_TX_SEL = 0x16
    REG_RX_SEL = 0x17
    REG_RX_THRESHOLD = 0x18
    REG_DEMOD = 0x19
    RESERVED_11 = 0x1A
    RESERVED_12 = 0x1B
    REG_MIFARE = 0x1C
    RESERVED_13 = 0x1D
    RESERVED_14 = 0x1E
    REG_SERIAL_SPEED = 0x1F

    RESERVED_20 = 0x20
    REG_CRC_RESULT_M = 0x21
    REG_CRC_RESULT_L = 0x22
    RESERVED_21 = 0x23
    REG_MOD_WIDTH = 0x24
    RESERVED_22 = 0x25
    REG_RFC_FG = 0x26
    REG_GS_N = 0x27
    REG_CW_GS_P = 0x28
    REG_MOD_GS_P = 0x29
    REG_T_MODE = 0x2A
    REG_T_PRESCALER = 0x2B
    REG_T_RELOAD_H = 0x2C
    REG_T_RELOAD_L = 0x2D
    REG_T_COUNTER_VALUE_H = 0x2E
    REG_T_COUNTER_VALUE_L = 0x2F

    RESERVED_30 = 0x30
    REG_TEST_SEL_1 = 0x31
    REG_TEST_SEL_2 = 0x32
    REG_TEST_PIN_EN = 0x33
    REG_TEST_PIN_VALUE = 0x34
    REG_TEST_BUS = 0x35
    REG_AUTO_TEST = 0x36
    REG_VERSION = 0x37
    REG_ANALOG_TEST = 0x38
    REG_TEST_DAC_1 = 0x39
    REG_TEST_DAC_2 = 0x3A
    REG_TEST_ADC = 0x3B
    RESERVED_31 = 0x3C
    RESERVED_32 = 0x3D
    RESERVED_33 = 0x3E
    RESERVED_34 = 0x3F

    # Status
    STATUS_OK = 0
    STATUS_NO_TAG_ERR = 1
    STATUS_ERR = 2

    def __init__(self, device="/dev/spidev0.0", speed=1000000, debug=False):

        self.authenticated = False
        self.debug = debug

        spi.openSPI(device=device, speed=speed)
        GPIO.setwarnings(self.debug)
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(self.PIN_RST_BCM, GPIO.OUT)
        GPIO.output(self.PIN_RST_BCM, 1)
        self.__init()

    def __init(self):

        GPIO.output(self.PIN_RST_BCM, 1)

        self.__reset()

        self.__dev_write(self.REG_T_MODE, 0x8D)
        self.__dev_write(self.REG_T_PRESCALER, 0x3E)
        self.__dev_write(self.REG_T_RELOAD_L, 30)
        self.__dev_write(self.REG_T_RELOAD_H, 0)

        self.__dev_write(self.REG_TX_AUTO, 0x40)
        self.__dev_write(self.REG_MODE, 0x3D)

        self.__set_antenna_on()

    @staticmethod
    def __dev_write(register, value):
        spi.transfer(((register << 1) & 0x7E, value))

    @staticmethod
    def __dev_read(register):
        val = spi.transfer((((register << 1) & 0x7E) | 0x80, 0))
        return val[1]

    def __reset(self):
        self.__dev_write(self.REG_COMMAND, self.CMD_RESET_PHASE)

    def __set_bitmask(self, register, mask):
        tmp = self.__dev_read(register)
        self.__dev_write(register, tmp | mask)

    def __clear_bitmask(self, register, mask):
        tmp = self.__dev_read(register)
        self.__dev_write(register, tmp & (~mask))

    def __set_antenna_on(self):
        temp = self.__dev_read(self.REG_TX_CONTROL)
        if ~(temp & 0x03):
            self.__set_bitmask(self.REG_TX_CONTROL, 0x03)

    def __set_antenna_off(self):
        self.__clear_bitmask(self.REG_TX_CONTROL, 0x03)

    def __stop_crypto(self):
        self.__clear_bitmask(self.REG_STATUS_2, 0x08)

    def __send_cmd(self, command, send_data):
        back_data = []
        back_len = 0
        status = self.STATUS_ERR
        irq_en = 0x00
        wait_irq = 0x00
        i = 0

        if command == self.CMD_AUTHENTICATE:
            irq_en = 0x12
            wait_irq = 0x10
        if command == self.CMD_TRANSCEIVE:
            irq_en = 0x77
            wait_irq = 0x30

        self.__dev_write(self.REG_COMM_I_EN, irq_en | 0x80)
        self.__clear_bitmask(self.REG_COMM_IRQ, 0x80)
        self.__set_bitmask(self.REG_FIFO_LEVEL, 0x80)

        self.__dev_write(self.REG_COMMAND, self.CMD_IDLE)

        while i < len(send_data):
            self.__dev_write(self.REG_FIFO_DATA, send_data[i])
            i = i + 1

        self.__dev_write(self.REG_COMMAND, command)

        if command == self.CMD_TRANSCEIVE:
            self.__set_bitmask(self.REG_BIT_FRAMING, 0x80)

        i = 2000

        while True:
            n = self.__dev_read(self.REG_COMM_IRQ)
            i = i - 1
            if ~((i != 0) and ~(n & 0x01) and ~(n & wait_irq)):
                break

        self.__clear_bitmask(self.REG_BIT_FRAMING, 0x80)

        if i != 0:
            if (self.__dev_read(self.REG_ERROR) & 0x1B) == 0x00:
                status = self.STATUS_OK

                if n & irq_en & 0x01:
                    status = self.STATUS_NO_TAG_ERR

                if command == self.CMD_TRANSCEIVE:
                    n = self.__dev_read(self.REG_FIFO_LEVEL)
                    last_bits = self.__dev_read(self.REG_CONTROL) & 0x07
                    if last_bits != 0:
                        back_len = (n - 1) * 8 + last_bits
                    else:
                        back_len = n * 8

                    if n == 0:
                        n = 1
                    if n > self.MAX_LEN:
                        n = self.MAX_LEN

                    i = 0
                    while i < n:
                        back_data.append(self.__dev_read(self.REG_FIFO_DATA))
                        i = i + 1
            else:
                status = self.STATUS_ERR

        return status, back_data, back_len

    def __calculate_crc(self, p_in_data):
        self.__clear_bitmask(self.REG_DIV_IRQ, 0x04)
        self.__set_bitmask(self.REG_FIFO_LEVEL, 0x80)
        i = 0
        while i < len(p_in_data):
            self.__dev_write(self.REG_FIFO_DATA, p_in_data[i])
            i = i + 1
        self.__dev_write(self.REG_COMMAND, self.CMD_CALC_CRC)
        i = 0xFF
        while True:
            n = self.__dev_read(self.REG_DIV_IRQ)
            i = i - 1
            if not ((i != 0) and not (n & 0x04)):
                break

        p_out_data = [self.__dev_read(self.REG_CRC_RESULT_L), self.__dev_read(self.REG_CRC_RESULT_M)]

        return p_out_data

    def request(self, req_mode=0x26):
        tag_type = []

        self.__dev_write(self.REG_BIT_FRAMING, 0x07)

        tag_type.append(req_mode)
        (status, back_data, back_bits) = self.__send_cmd(self.CMD_TRANSCEIVE, tag_type)

        if (status != self.STATUS_OK) | (back_bits != 0x10):
            status = self.STATUS_ERR

        return status, back_bits

    def anti_collision(self):
        ser_num_check = 0
        ser_num = []

        self.__dev_write(self.REG_BIT_FRAMING, 0x00)

        ser_num.append(self.ACT_ANTICOLL)
        ser_num.append(0x20)

        (status, back_data, back_bits) = self.__send_cmd(self.CMD_TRANSCEIVE, ser_num)  # back_data is the UID

        if status == self.STATUS_OK:
            i = 0
            if len(back_data) == 5:
                while i < 4:
                    ser_num_check = ser_num_check ^ back_data[i]
                    i = i + 1
                if ser_num_check != back_data[i]:
                    status = self.STATUS_ERR
            else:
                status = self.STATUS_ERR

        return status, back_data

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
        (status, backData, backLen) = self.__send_cmd(self.CMD_AUTHENTICATE, buff)

        # Check if an error occurred
        if not (status == self.STATUS_OK):
            print("[e] Authentication error")
        if not (self.__dev_read(self.REG_STATUS_2) & 0x08) != 0:
            print("   (status2reg & 0x08) != 0")
        else:
            self.authenticated = True

        return status

    def deauth(self):
        """
        Stops crypto and set the class attribute.
        """
        if self.authenticated:
            self.__stop_crypto()
            self.authenticated = False

    def select_tag(self, uid):

        buf = [self.ACT_SELECT_TAG, 0x70]

        i = 0
        while i < 5:  # TODO even if the tag has 4 bytes UID, 5 bytes are considered
            buf.append(uid[i])
            i = i + 1
        p_out = self.__calculate_crc(buf)
        buf.append(p_out[0])
        buf.append(p_out[1])
        (status, back_data, back_len) = self.__send_cmd(self.CMD_TRANSCEIVE, buf)

        if (status == self.STATUS_OK) and (back_len == 0x18):
            if self.debug:
                print(f"[d] back_data[0] (size): {back_data[0]}")
            return status
        else:
            return self.STATUS_ERR

    def read_block(self, block_addr):
        """
        Reads a desired block.
        :param block_addr: block address number.
        :return: the status and the block's content as list of 8 bit int.
        """
        recv_data = [self.ACT_READ, block_addr]

        p_out = self.__calculate_crc(recv_data)
        recv_data.append(p_out[0])
        recv_data.append(p_out[1])
        (status, back_data, back_len) = self.__send_cmd(self.CMD_TRANSCEIVE, recv_data)
        if not (status == self.STATUS_OK):
            print("[e] Error while reading")

        return status, back_data

    def write_block(self, block_addr, write_data):

        buff = [self.ACT_WRITE, block_addr]

        crc = self.__calculate_crc(buff)
        buff.append(crc[0])
        buff.append(crc[1])
        (status, back_data, back_len) = self.__send_cmd(self.CMD_TRANSCEIVE, buff)

        if self.debug:
            print(f"[d] {back_len} (backdata & 0x0F) == 0x0A {(back_data[0] & 0x0F) == 0x0A}")

        if not (status == self.STATUS_OK) or not (back_len == 4) or not ((back_data[0] & 0x0F) == 0x0A):
            status = self.STATUS_ERR

        if status == self.STATUS_OK:
            i = 0
            buf = []
            while i < 16:
                buf.append(write_data[i])
                i = i + 1
            crc = self.__calculate_crc(buf)
            buf.append(crc[0])
            buf.append(crc[1])
            (status, back_data, back_len) = self.__send_cmd(self.CMD_TRANSCEIVE, buf)
            if not (status == self.STATUS_OK) or not (back_len == 4) or not ((back_data[0] & 0x0F) == 0x0A):
                print("[e] Error while writing")
            if status == self.STATUS_OK and self.debug:
                print("[d] Data written")
        return status

    def wait_for_tag(self):
        # Scan for tags
        waiting = True
        while waiting:
            (status, tag_type) = self.request()
            # If a card is found
            if status == self.STATUS_OK:
                # card detected
                waiting = False
        self.__init()
