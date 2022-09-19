#!/usr/bin/env python
from typing import Optional

from .rc522 import RC522
from .utils import get_block_address, get_block_repr


class RC522Manager:
    """
    High level class that manages an RC522 RFID Reader.
    """
    DEFAULT_DEV = "/dev/spidev0.0"
    DEFAULT_SPEED = 1000000
    DEFAULT_AUTH_METHOD = 0x60  # use KEY_A
    DEFAULT_KEY = (0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF)
    DEFAULT_AUTH_BITS = (0xFF, 0x07, 0x80)
    DEFAULT_SECTORS_NUMBER = 16

    rfid_reader: Optional[RC522] = None
    auth_method = None
    uid = None
    key = None
    last_auth = None

    debug = False

    def __init__(self, device=DEFAULT_DEV, speed=DEFAULT_SPEED, debug=False):

        self.rfid_reader = RC522(device=device, speed=speed, debug=debug)
        self.debug = debug

    def scan_once(self) -> (int, bytes):
        """
        Scans once for a tag.
        If there is one, requests it and performs anti-collision.
        :return status: STATUS_MI_OK = 0
                        STATUS_MI_NO_TAG_ERR = 1
                        STATUS_MI_ERR = 2
                uid: UID of the found tag
        """
        uid = []
        # Request tag
        (status, tag_type) = self.rfid_reader.request_tag()
        if status == self.rfid_reader.MI_STATUS_OK:  # there is a tag
            # Perform anti-collision
            (status, uid) = self.rfid_reader.anti_collision()
            if status == self.rfid_reader.MI_STATUS_OK:
                return status, uid
        return status, uid

    def wait_for_tag(self):
        """
        Waits for a tag to appear.
        It performs anti-collision.
        :return: status: STATUS_MI_OK = 0
                        STATUS_MI_NO_TAG_ERR = 1
                        STATUS_MI_ERR = 2
                uid: UID of the found tag
        """
        self.rfid_reader.wait_for_tag()
        (status, uid) = self.rfid_reader.anti_collision()
        if status == self.rfid_reader.MI_STATUS_OK:
            return status, uid

    def select_tag(self, uid: list[int] or bytes) -> int:
        """
        Selects a tag, setting the relative class attribute.
        Resets the auth if the tag's UID is already set.
        :param uid: UID of the tag
        :return status: STATUS_MI_OK = 0
                        STATUS_MI_NO_TAG_ERR = 1
                        STATUS_MI_ERR = 2
        """
        if self.uid is not None:
            self.reset_auth()

        status = self.rfid_reader.select_tag(uid)
        if status == self.rfid_reader.MI_STATUS_OK:
            self.uid = uid

        if self.debug:
            print(f"[d] Selected UID {bytes(uid).hex()}")
        return status

    def is_auth_set(self) -> bool:
        """
        :return: True if the authentication info are set.
        """
        return (self.uid is not None) and (self.key is not None) and (self.auth_method is not None)

    def set_auth(self, auth_method: int = DEFAULT_AUTH_METHOD, key: list[int] or bytes = DEFAULT_KEY):
        """
        Sets the authentication info for the current tag.
        :param auth_method: KEY_A (0x60) or KEY_B (0x61)
        :param key: key of the tag
        """
        self.auth_method = auth_method
        self.key = key

        if self.debug:
            print(f"[d] Set key {bytes(key).hex()}, method {'A' if auth_method == self.rfid_reader.AUTH_A else 'B'}")

    def reset_auth(self):
        """
        Resets the authentication info and de-auths the RC522.
        Calls stop_crypto() if RFID is in auth state.
        """
        self.auth_method = None
        self.key = None
        self.last_auth = None
        self.rfid_reader.deauth()

        if self.debug:
            print("[d] Resetting auth info and de-authing the reader")

    def auth(self, block_address: int, force: bool = False) -> int:
        """
        Authenticates a certain block using the saved auth info, only if needed.
        :param block_address: absolute address of the block
        :param force: True to force the auth even is it already authed
        :return status: STATUS_MI_OK = 0
                        STATUS_MI_NO_TAG_ERR = 1
                        STATUS_MI_ERR = 2
        """
        auth_data = (block_address, self.auth_method, self.key, self.uid)
        status = RC522.MI_STATUS_OK

        if (self.last_auth != auth_data) or force:
            if self.debug:
                print(f"[d] Calling reader.auth() on UID {bytes(self.uid).hex()}")
            self.last_auth = auth_data
            status = self.rfid_reader.auth(self.auth_method, block_address, self.key, self.uid)
        else:
            if self.debug:
                print("[d] Not calling reader.auth() - already authed")
        return status

    def read_block(self, block_address: int) -> (int, list[int]):
        """
        Reads a specific block.
        Note: Tag and auth must be set, since it does auth.
        :param block_address: absolute address of the block
        :return status: STATUS_MI_OK = 0
                        STATUS_MI_NO_TAG_ERR = 1
                        STATUS_MI_ERR = 2
                read data (eventually empty)
        """
        data = []
        status = RC522.MI_STATUS_ERR

        if not self.is_auth_set():
            return status, data

        status = self.auth(block_address)
        if status == RC522.MI_STATUS_OK:
            (status, data) = self.rfid_reader.read_block(block_address)
        else:
            print(f"[e] Error reading {get_block_repr(block_address)}")

        return status, data

    def write_block(self, block_address: int, new_bytes: list[int]) -> int:
        """
        Writes new bytes to a specific block, keeping the old ones if None is passed.
        Note: Tag and auth must be set. It does auth.

        Example:
            write_block(1, [None, 0x1a, None, 0x00])
            will write the second and the fourth byte of the second block, leaving the other 14 bytes unaltered.

        :param block_address: absolute address of the block
        :param new_bytes: list of bytes to be written
        :return status: STATUS_MI_OK = 0
                        STATUS_MI_NO_TAG_ERR = 1
                        STATUS_MI_ERR = 2
        """
        if not self.is_auth_set():
            return RC522.MI_STATUS_ERR

        status = self.auth(block_address)
        if status == RC522.MI_STATUS_OK:
            (status, data) = self.rfid_reader.read_block(block_address)
            if status == RC522.MI_STATUS_OK:
                for i in range(len(new_bytes)):
                    if new_bytes[i] is not None:
                        if self.debug:
                            print(f"[d] Changing byte {i} - from {data[i]} to {new_bytes[i]}")
                        data[i] = new_bytes[i]

                status = self.rfid_reader.write_block(block_address, data)
                if self.debug:
                    print(f"[d] Writing {bytes(data).hex()} to {get_block_repr(block_address)}")
        return status

    def write_trailer(self, sector_number: int,
                      key_a: list[int] or bytes = DEFAULT_KEY,
                      access_bits: list[int] or bytes = DEFAULT_AUTH_BITS,
                      user_data: int = 0x69,
                      key_b: list[int] or bytes = DEFAULT_KEY):
        """
        Writes sector trailer (last block) of specified sector. Tag and auth must be set - does auth.
        If value is None, value of byte is kept.

        :param sector_number: number of the sector
        :param key_a: key A of the tag
        :param key_b: key B of the tag
        :param access_bits: access bits
        :param user_data: eventual user data to append after the access bits
        :return status: STATUS_MI_OK = 0
                        STATUS_MI_NO_TAG_ERR = 1
                        STATUS_MI_ERR = 2
        """
        address = get_block_address(sector_number, 3)
        return self.write_block(address, key_a[:6] + access_bits[:3] + (user_data,) + key_b[:6])

    def dump(self, sectors_number: int = DEFAULT_SECTORS_NUMBER) -> list[list[int]]:
        """
        Dumps the entire tag.
        :param sectors_number: number of sectors
        :return: dump data
        """
        dump = []
        for i in range(sectors_number * 4):
            (status, data) = self.read_block(i)
            dump.append(data)
        return dump
