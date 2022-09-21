#!/usr/bin/env python
from typing import Optional

from .rc522 import RC522
from .utils import get_block_number, get_block_repr


class RC522Manager:
    """
    High level class that manages an RC522 RFID Reader.
    """
    DEFAULT_DEV = "/dev/spidev0.0"
    DEFAULT_SPEED = 1000000
    DEFAULT_AUTH_METHOD = RC522.ACT_AUTH_A  # use KEY_A
    DEFAULT_KEY = (0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF)
    DEFAULT_AUTH_BITS = (0xFF, 0x07, 0x80)
    DEFAULT_SECTORS_NUMBER = 16

    rfid_reader: RC522 = None
    scanning: bool = False

    uid: bytes | None = None
    key: bytes | None = None
    auth_method: int | None = None
    last_auth_data: tuple[int | None, int | None, bytes | None, bytes | None] | None = None

    debug: bool = False

    def __init__(self, device=DEFAULT_DEV, speed=DEFAULT_SPEED, debug=False):

        self.rfid_reader = RC522(device=device, speed=speed, debug=debug)
        self.debug = debug

    def scan(self, scan_once: bool = False) -> (int, list[int] | bytes | None):
        """
        Scans for a tag once or until a tag appears.
        It performs anti-collision.
        :param scan_once: True to scan one time, False to scan until a tag appears
        :return status: 0 = OK, 1 = NO_TAG_ERROR, 2 = ERROR
                uid_data: UID of the tag (4 bytes) concatenated with checksum (1 byte), 5 bytes total
        """
        uid_data = None
        self.scanning = True

        if scan_once:
            # Request tag
            (status, tag_type) = self.rfid_reader.request_tag_once()
        else:
            # Wait for the tag
            (status, tag_type) = self.rfid_reader.wait_for_tag()

        if status == self.rfid_reader.STATUS_OK:  # there is a tag
            # Perform anti-collision
            (status, uid_data) = self.rfid_reader.anti_collision()

        self.scanning = False
        return status, uid_data

    def select_tag(self, uid_data: list[int] | bytes) -> int:
        """
        Selects a tag.
        Resets the auth if the tag's UID is already set.
        :param uid_data: UID of the tag (4 bytes) concatenated with checksum (1 byte), 5 bytes total
        :return status: 0 = OK, 1 = NO_TAG_ERROR, 2 = ERROR
        """
        if self.uid is not None:
            self.reset_auth()

        status = self.rfid_reader.select_tag(uid_data)
        if status == self.rfid_reader.STATUS_OK:
            self.uid = bytes(uid_data[0:4])
            if self.debug:
                print(f"[d] Selected UID {self.uid.hex()}")

        return status

    def is_auth_set(self) -> bool:
        """
        :return: True if the authentication info are set.
        """
        return (self.uid is not None) and (self.key is not None) and (self.auth_method is not None)

    def set_auth(self, auth_method: int = DEFAULT_AUTH_METHOD, key: list[int] | bytes = DEFAULT_KEY):
        """
        Sets the authentication info for the current tag.
        :param auth_method: KEY_A (0x60) or KEY_B (0x61)
        :param key: key of the tag
        """
        self.auth_method = auth_method
        self.key = bytes(key)

        if self.debug:
            print(f"[d] Set key {self.key.hex()}, method {'A' if auth_method == self.rfid_reader.ACT_AUTH_A else 'B'}")

    def reset_auth(self):
        """
        Resets the authentication info and de-auths the RC522 reader.
        """
        self.auth_method = None
        self.key = None
        self.last_auth_data = None
        self.rfid_reader.deauth()

        if self.debug:
            print("[d] Resetting auth info and de-authing the reader")

    def auth(self, block_number: int, force: bool = False) -> int:
        """
        Authenticates a certain block using the saved auth info, only if needed.
        :param block_number: number of the block (from 0 to SECTORS_NUMBER * 4 - 1)
        :param force: True to force the auth even it is already authenticated
        :return status: 0 = OK, 1 = NO_TAG_ERROR, 2 = ERROR
        """
        auth_data = (block_number, self.auth_method, self.key, self.uid)
        status = self.rfid_reader.STATUS_OK

        if (self.last_auth_data != auth_data) or force:
            if self.debug:
                print(f"[d] Calling reader.auth() on UID {self.uid.hex()}")
            self.last_auth_data = auth_data
            status = self.rfid_reader.auth(self.auth_method, block_number, self.key, self.uid)
        else:
            if self.debug:
                print("[d] Not calling reader.auth() - already authenticated")
        return status

    def read_block(self, block_number: int) -> (int, bytes | None):
        """
        Reads a specific block.
        Note: Tag and auth must be set, since it does auth.
        :param block_number: number of the block (from 0 to SECTORS_NUMBER * 4 - 1)
        :return status: 0 = OK, 1 = NO_TAG_ERROR, 2 = ERROR
                read_data: read data
        """
        status = self.rfid_reader.STATUS_ERR
        read_data = None

        if not self.is_auth_set():
            return status, read_data

        # Do authentication
        status = self.auth(block_number)
        if status == self.rfid_reader.STATUS_OK:
            (status, read_data) = self.rfid_reader.read_block(block_number)
        else:
            print(f"[e] Error reading {get_block_repr(block_number)}")

        return status, bytes(read_data)

    def write_block(self, block_number: int, new_bytes: list[int]) -> int:
        """
        Writes bytes to a specific block, keeping the old ones if None is passed.
        Note: Tag and auth must be set, since it does auth.

        Example:
            write_block(block_number=1, new_bytes=[None, 0x1a, None, 0x00])
            will write the second and the fourth byte of the second block, leaving the other 14 bytes unaltered.

        :param block_number: number of the block (from 0 to SECTORS_NUMBER * 4 - 1)
        :param new_bytes: list of bytes to be written
        :return status: 0 = OK, 1 = NO_TAG_ERROR, 2 = ERROR
        """
        if not self.is_auth_set():
            return self.rfid_reader.STATUS_ERR

        # Do authentication
        status = self.auth(block_number)
        if status == self.rfid_reader.STATUS_OK:
            # Read previous block
            (status, block_data) = self.rfid_reader.read_block(block_number)
            if status == self.rfid_reader.STATUS_OK:
                for i in range(len(new_bytes)):
                    # Overwrite block_data if the new_byte is not None
                    if new_bytes[i] is not None:
                        if self.debug:
                            print(f"[d] Changing byte {i} - from {block_data[i]} to {new_bytes[i]}")
                        block_data[i] = new_bytes[i]

                # Write the new block with changed bytes (block_data)
                status = self.rfid_reader.write_block(block_number, block_data)
                if self.debug:
                    print(f"[d] Writing {bytes(block_data).hex()} to {get_block_repr(block_number)}")
        return status

    def write_trailer(self, sector_number: int,
                      key_a: list[int] | bytes = DEFAULT_KEY,
                      access_bits: list[int] | bytes = DEFAULT_AUTH_BITS,
                      user_data: int = 0x69,
                      key_b: list[int] | bytes = DEFAULT_KEY):
        """
        Writes sector trailer (last block) of specified sector. Tag and auth must be set - does auth.
        If value is None, value of byte is kept.
        :param sector_number: number of the sector
        :param key_a: key A of the tag
        :param key_b: key B of the tag
        :param access_bits: access bits
        :param user_data: eventual user data to append after the access bits
        :return status: 0 = OK, 1 = NO_TAG_ERROR, 2 = ERROR
        """
        block_number = get_block_number(sector_number, relative_block_num=3)
        trailer = key_a[:6] + access_bits[:3] + [user_data] + key_b[:6]
        return self.write_block(block_number, trailer)

    def dump(self, sectors_number: int = DEFAULT_SECTORS_NUMBER) -> (int, list[bytes]):
        """
        Dumps the entire tag.
        :param sectors_number: number of sectors
        :return: status: 0 = OK, 1 = NO_TAG_ERROR, 2 = ERROR
                 dump: dump data
        """
        status = self.rfid_reader.STATUS_ERR
        dump = []
        for i in range(sectors_number * 4):
            (status, data) = self.read_block(i)
            dump.append(data)
        return status, dump
