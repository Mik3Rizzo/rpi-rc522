#!/usr/bin/env python
import time

import RPi.GPIO as GPIO
import spi


class RC522:
    """
    Low level class that manages an RC522 RFID Reader (based on the MFRC522 chip), connected through SPI.

    Note: this is based on the Arduino's .cpp RFID library.
    Look here for further code explanation:
    https://github.com/miguelbalboa/rfid  (MFRC522.h and MFRC522.cpp)
    """

    PIN_RST_BCM = 25  # BOARD 22
    MAX_LEN = 16

    # Commands word
    CMD_IDLE = 0x00             # no action, cancel the current command
    CMD_MEM = 0x01              # store 25 unsigned char into the internal buffer
    CMD_GEN_ID = 0x02           # generates a 10 unsigned char random ID number
    CMD_CALC_CRC = 0x03         # CRC Calculate or self-test
    CMD_TRANSMIT = 0x04         # transmit data
    CMD_NO_CMD_CHANGE = 0x07    # no command change
    CMD_RECEIVE = 0x08          # receive data
    CMD_TRANSCEIVE = 0x0C       # transmit and receive data
    CMD_AUTHENTICATE = 0x0E     # authentication key
    CMD_SOFT_RESET = 0x0F       # reset


    # Actions
    ACT_REQ_IDL = 0x26          # find the antenna area does not enter hibernation
    ACT_REQ_ALL = 0x52          # find all the tags in the antenna area
    ACT_ANTI_COLL = 0x93        # anti-collision
    ACT_SELECT_TAG = 0x93       # tag selection
    ACT_AUTH_A = 0x60           # authentication key A
    ACT_AUTH_B = 0x61           # authentication key B
    ACT_READ = 0x30             # read bock
    ACT_WRITE = 0xA0            # write block
    ACT_DECREMENT = 0xC0        # decrement
    ACT_INCREMENT = 0xC1        # increment
    ACT_RESTORE = 0xC2          # transfer block data to the buffer
    ACT_TRANSFER = 0xB0         # save data in the buffer
    ACT_HALT = 0x50             # sleep

    # Register addresses
    # Page0: command and status
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
    # Page1: command
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
    # Page2: configuration
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
    REG_TIMER_MODE = 0x2A
    REG_TIMER_PRESCALER = 0x2B
    REG_TIMER_RELOAD_H = 0x2C
    REG_TIMER_RELOAD_L = 0x2D
    REG_TIMER_COUNTER_VALUE_H = 0x2E
    REG_TIMER_COUNTER_VALUE_L = 0x2F
    # Page3: test register
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
    STATUS_OK = 0               # everything is OK
    STATUS_NO_TAG_ERR = 1       # no tag error
    STATUS_ERR = 2              # general error

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

        # Timer: TPrescaler*TreloadVal/6.78MHz = 24ms, f(Timer) = 6.78MHz/TPreScale
        self.__dev_write(self.REG_TIMER_MODE, 0x8D)         # Tauto=1, timer starts automatically at the end of the transmission in all communication modes at all speeds
        self.__dev_write(self.REG_TIMER_PRESCALER, 0x3E)    # TModeReg[3..0] + TPrescalerReg
        self.__dev_write(self.REG_TIMER_RELOAD_H, 0x00)     # reload timer with 0x0030,  i.e. 48ms before timeout
        self.__dev_write(self.REG_TIMER_RELOAD_L, 0x30)

        self.__dev_write(self.REG_TX_AUTO, 0x40)            # Default 0x00. Force a 100 % ASK modulation independent of the ModGsPReg register setting
        self.__dev_write(self.REG_MODE, 0x3D)               # Default 0x3F. Set the preset value for the CRC coprocessor for the CalcCRC command to 0x6363 (ISO 14443-3 part 6.2.4)

        self.__set_antenna_on()                             # re-enable the antenna driver pins, disabled by __reset

    @staticmethod
    def __dev_write(register, value):
        spi.transfer(((register << 1) & 0x7E, value))

    @staticmethod
    def __dev_read(register):
        val = spi.transfer((((register << 1) & 0x7E) | 0x80, 0))
        return val[1]

    def __reset(self):
        self.__dev_write(self.REG_COMMAND, self.CMD_SOFT_RESET)

    def __set_bitmask(self, register, mask):
        tmp = self.__dev_read(register)
        self.__dev_write(register, tmp | mask)

    def __clear_bitmask(self, register, mask):
        tmp = self.__dev_read(register)
        self.__dev_write(register, tmp & (~mask))

    def __set_antenna_on(self):
        """
        Turns the antenna on by enabling pins TX1 and TX2.
        After a __reset() these pins are disabled.
        """
        temp = self.__dev_read(self.REG_TX_CONTROL)
        if ~(temp & 0x03):
            self.__set_bitmask(self.REG_TX_CONTROL, 0x03)

    def __set_antenna_off(self):
        """
        Turns the antenna off by disabling pins TX1 and TX2.
        """
        self.__clear_bitmask(self.REG_TX_CONTROL, 0x03)

    def __stop_crypto(self):
        self.__clear_bitmask(self.REG_STATUS_2, 0x08)

    def __send_cmd(self, command, command_data):
        """
        Sends a command to a tag.
        :param command: command to the MFRC522 chip, needed to send a command to the tag
        :param command_data: data that is needed to complete the command
        :return status: status of the calculation
                        0 = OK
                        1 = NO_TAG_ERROR
                        2 = ERROR
                result: result data returned by the tag
                result_len_bits: number of valid bits in the resulting value
        """
        result = []
        result_bits_len = 0
        status = self.STATUS_ERR
        irq_en = 0x00
        wait_irq = 0x00
        n = 0

        if command == self.CMD_AUTHENTICATE:
            irq_en = 0x12
            wait_irq = 0x10
        if command == self.CMD_TRANSCEIVE:
            irq_en = 0x77
            wait_irq = 0x30

        self.__dev_write(self.REG_COMM_I_EN, irq_en | 0x80)     # interrupt request
        self.__clear_bitmask(self.REG_COMM_IRQ, 0x80)           # clear all interrupt requests bits
        self.__set_bitmask(self.REG_FIFO_LEVEL, 0x80)           # FlushBuffer=1, FIFO initialization

        self.__dev_write(self.REG_COMMAND, self.CMD_IDLE)       # no action, cancel the current command

        for i in range(len(command_data)):
            self.__dev_write(self.REG_FIFO_DATA, command_data[i])

        self.__dev_write(self.REG_COMMAND, command)

        if command == self.CMD_TRANSCEIVE:
            self.__set_bitmask(self.REG_BIT_FRAMING, 0x80)      # StartSend=1, transmission of data starts

        # Waiting for the command to complete, so we can receive data
        ms_timeout = 25  # 25 ms
        stop = False
        while not stop:
            n = self.__dev_read(self.REG_COMM_IRQ)
            # CommIRqReg[7..0]
            # Set1 TxIRq RxIRq IdleIRq HiAlerIRq LoAlertIRq ErrIRq TimerIRq
            ms_timeout -= 1
            if ~((ms_timeout != 0) and ~(n & 0x01) and ~(n & wait_irq)):
                stop = True
            time.sleep(0.01)  # wait 1ms

        self.__clear_bitmask(self.REG_BIT_FRAMING, 0x80)            # StartSend=0

        if ms_timeout != 0:  # request did not time out
            if (self.__dev_read(self.REG_ERROR) & 0x1B) == 0x00:    # BufferOvfl Collerr CRCErr ProtocolErr
                status = self.STATUS_OK

                if n & irq_en & 0x01:
                    status = self.STATUS_NO_TAG_ERR

                if command == self.CMD_TRANSCEIVE:
                    n = self.__dev_read(self.REG_FIFO_LEVEL)
                    last_bits = self.__dev_read(self.REG_CONTROL) & 0x07
                    if last_bits != 0:
                        result_bits_len = (n - 1) * 8 + last_bits
                    else:
                        result_bits_len = n * 8

                    if n == 0:
                        n = 1
                    if n > self.MAX_LEN:
                        n = self.MAX_LEN

                    # Reading the received data from FIFO
                    for i in range(n):
                        result.append(self.__dev_read(self.REG_FIFO_DATA))
            else:
                status = self.STATUS_ERR

        return status, result, result_bits_len

    def __calculate_crc(self, data):
        """
        Calculates the CRC value for some data that should be sent to a tag.
        :param data: data to calculate the CRC for
        :return: result: result of the CRC calculation
        """
        self.__clear_bitmask(self.REG_DIV_IRQ, 0x04)            # CRCIrq = 0
        self.__set_bitmask(self.REG_FIFO_LEVEL, 0x80)           # clear the FIFO pointer

        for i in range(len(data)):
            self.__dev_write(self.REG_FIFO_DATA, data[i])

        self.__dev_write(self.REG_COMMAND, self.CMD_CALC_CRC)

        i = 0xFF
        stop = False
        while not stop:
            n = self.__dev_read(self.REG_DIV_IRQ)
            i = i - 1
            if not ((i != 0) and not (n & 0x04)):  # CRCIrq = 1
                stop = True
        # Read the result from the CRC calculation
        result = [self.__dev_read(self.REG_CRC_RESULT_L), self.__dev_read(self.REG_CRC_RESULT_M)]
        return result

    def request_tag(self, req_mode=0x26):
        """
        Checks to see if there is a tag in the vicinity.
        :param req_mode: mode of the request
        :return status: status of the request
                        0 = OK
                        1 = NO_TAG_ERROR
                        2 = ERROR
                tag_type: if we find a tag, this will be the type of that tag
                        0x4400 = Mifare_UltraLight
                        0x0400 = Mifare_One(S50)
                        0x0200 = Mifare_One(S70)
                        0x0800 = Mifare_Pro(X)
                        0x4403 = Mifare_DESFire
        """
        self.__dev_write(self.REG_BIT_FRAMING, 0x07)        # TxLastBists = BitFramingReg[2..0]

        cmd_data = [req_mode]
        (status, tag_type, bits_len) = self.__send_cmd(self.CMD_TRANSCEIVE, cmd_data)

        if (status != self.STATUS_OK) | (bits_len != 0x10):  # tag_type has to be 0x10 = 16 bits (2 bytes) length
            status = self.STATUS_ERR

        return status, tag_type

    def anti_collision(self):
        """
        Handles collisions that might occur if there are multiple tags available.
        :return status: status of the request
                        0 = OK
                        1 = NO_TAG_ERROR
                        2 = ERROR
        :return status: status of the collision detection
                        0 = OK
                        1 = NO_TAG_ERROR
                        2 = ERROR
                uid_data: UID of the tag (4 bytes) concatenated with checksum (1 byte), 5 bytes total
        """
        uid_checksum = 0
        self.__dev_write(self.REG_BIT_FRAMING, 0x00)           # TxLastBits = BitFramingReg[2..0]

        cmd_data = [self.ACT_ANTI_COLL, 0x20]
        (status, uid_data, bits_len) = self.__send_cmd(self.CMD_TRANSCEIVE, cmd_data)

        # uid_data = UID (4 bytes) | checksum (1 byte) -> 5 bytes total
        # checksum = XOR (^) of the 4 bytes of the UID

        if status == self.STATUS_OK:
            if len(uid_data) == 5:  # the uid_data has the correct size (5 bytes)
                # Compute the checksum of the received UID
                for i in range(4):
                    uid_checksum = uid_checksum ^ uid_data[i]
                # The checksum should be the same as the one provided from the tag (uid_data[4]).
                if uid_checksum != uid_data[4]:
                    status = self.STATUS_ERR
            else:
                status = self.STATUS_ERR

        return status, uid_data

    def select_tag(self, uid_data):
        """
        Selects a given tag.
        :param uid_data: UID of the tag (4 bytes) concatenated with checksum (1 byte), 5 bytes total
        :return status: status of the tag selection
                        0 = OK
                        1 = NO_TAG_ERROR
                        2 = ERROR
        """

        cmd_data = [self.ACT_SELECT_TAG, 0x70]

        for i in range(5):
            cmd_data.append(uid_data[i])

        crc = self.__calculate_crc(cmd_data)
        cmd_data.append(crc[0])
        cmd_data.append(crc[1])

        (status, res, res_bits_len) = self.__send_cmd(self.CMD_TRANSCEIVE, cmd_data)

        if (status == self.STATUS_OK) and (res_bits_len == 0x18):  # 0x18 = 24 bits
            if self.debug:
                print(f"[d] res[0] (size): {res[0]}")
            return status
        else:
            return self.STATUS_ERR

    def auth(self, auth_mode, block_address, key, uid):
        """
        Performs the authentication for a given block.
        :param auth_mode: 0x60 (AUTH_A) or 0x61 (AUTH_B)
        :param block_address: block absolute address
        :param key: key for the authentication
        :param uid: UID of the tag, truncated if > 4 bytes
        :return status: status of the authentication
                        0 = OK
                        1 = NO_TAG_ERROR
                        2 = ERROR
        """
        cmd_data = [auth_mode, block_address]

        # Append the key, which usually is 6 bytes of 0xFF
        for i in range(len(key)):
            cmd_data.append(key[i])

        # Append the first 4 bytes of the UID
        for i in range(4):
            cmd_data.append(uid[i])

        # Start the authentication itself
        (status, result, bits_len) = self.__send_cmd(self.CMD_AUTHENTICATE, cmd_data)

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

    # TODO continue refactoring from here
    # - renaming
    # - fix request_tag return
    # - huge commenting (looking arduino lib)

    def read_block(self, block_address):
        """
        Reads a desired block.
        :param block_address: block absolute address
        :return status: status of the read operation
                        0 = OK
                        1 = NO_TAG_ERROR
                        2 = ERROR
                read_data: read data
        """
        cmd_data = [self.ACT_READ, block_address]
        crc = self.__calculate_crc(cmd_data)
        cmd_data.append(crc[0])
        cmd_data.append(crc[1])

        (status, read_data, bits_len) = self.__send_cmd(self.CMD_TRANSCEIVE, cmd_data)

        if not (status == self.STATUS_OK):
            print("[e] Error while reading")
        return status, read_data

    def write_block(self, block_address, data):
        """
        Writes data to a desired block.
        :param block_address: block absolute address
        :param data: data to be written
        :return status: status of the write operation
                        0 = OK
                        1 = NO_TAG_ERROR
                        2 = ERROR
        """

        cmd_data = [self.ACT_WRITE, block_address]
        crc = self.__calculate_crc(cmd_data)
        cmd_data.append(crc[0])
        cmd_data.append(crc[1])

        (status, back_data, bits_len) = self.__send_cmd(self.CMD_TRANSCEIVE, cmd_data)

        if self.debug:
            print(f"[d] {bits_len} (backdata & 0x0F) == 0x0A {(back_data[0] & 0x0F) == 0x0A}")

        if not (status == self.STATUS_OK) or not (bits_len == 4) or not ((back_data[0] & 0x0F) == 0x0A):
            status = self.STATUS_ERR

        if status == self.STATUS_OK:
            cmd_data = []
            for i in range(16):
                cmd_data.append(data[i])

            crc = self.__calculate_crc(cmd_data)
            cmd_data.append(crc[0])
            cmd_data.append(crc[1])

            (status, back_data, bits_len) = self.__send_cmd(self.CMD_TRANSCEIVE, cmd_data)

            if not (status == self.STATUS_OK) or not (bits_len == 4) or not ((back_data[0] & 0x0F) == 0x0A):
                print("[e] Error while writing")
            if status == self.STATUS_OK and self.debug:
                print("[d] Data written")
        return status

    def wait_for_tag(self):
        # Scan for tags
        waiting = True
        while waiting:
            (status, tag_type) = self.request_tag()
            # If a card is found
            if status == self.STATUS_OK:
                # card detected
                waiting = False
        self.__init()
