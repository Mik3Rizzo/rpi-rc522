#!/usr/bin/env python
from typing import Optional

from .rfid_reader import RFIDReader
from .utils import get_access_bits, get_block_address, get_block_repr


class RFIDManager:
    """
    Manages an RC522 NFC Reader.
    """

    DEFAULT_KEY = (0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF)
    DEFAULT_AUTH_BITS = (0xFF, 0x07, 0x80)
    DEFAULT_SECTORS_NUMBER = 16

    rfid_reader: Optional[RFIDReader] = None

    method = None
    key = None
    uid = None
    last_auth = None

    debug = False

    def __init__(self, rfid_reader, debug=False):

        self.rfid_reader = rfid_reader
        self.debug = debug

    def set_tag(self, uid):
        """
        Sets tag UID and calls RFIDReader.set_tag().
        Resets the auth if card is already set.
        :param uid: UID of the tag
        :return error state from method call
        """
        if self.debug:
            print(f"[i] Selecting UID {uid}")

        if self.uid is not None:
            self.reset_auth()

        self.uid = uid
        return self.rfid_reader.set_tag(uid)

    def set_auth(self, auth_method, key):
        """
        Sets the authentication info for the current tag.
        :param auth_method: KEY_A (0x60) or KEY_B (0x61)
        :param key: key of the tag
        """
        self.method = auth_method
        self.key = key

        if self.debug:
            print(f"[i] Changing key to {key} with method " + ("A" if auth_method == self.rfid_reader.AUTH_A else "B"))

    def reset_auth(self):
        """
        Resets the authentication info and deauths the RFIDReader.
        Calls stop_crypto() if RFID is in auth state.
        """
        self.method = None
        self.key = None
        self.last_auth = None

        self.rfid_reader.deauth()

        if self.debug:
            print("[i] Resetting auth info and de-authing the reader")

    def is_auth_set(self):
        """
        :return: True if the authentication info are set.
        """
        return (self.uid is not None) and (self.key is not None) and (self.method is not None)

    def auth(self, block_address, force=False):
        """
        Calls RFIDReader.auth() with saved auth information if needed.
        :param block_address: absolute address of the block
        :param force: True to force the auth even is it already authed
        :return error state from method call
        """
        auth_data = (block_address, self.method, self.key, self.uid)
        if (self.last_auth != auth_data) or force:
            if self.debug:
                print(f"[i] Calling reader.auth() on UID {self.uid}")
            self.last_auth = auth_data
            error = self.rfid_reader.auth(self.method, block_address, self.key, self.uid)
            return error
        else:
            if self.debug:
                print("[i] Not calling reader.auth() - already authed")
            return False

    def read_block(self, block_address: int) -> list[int] or bool:
        """
        Reads a specific block.
        Note: Tag and auth must be set. It does auth.
        :param block_address: block absolute address
        :return the read block as a list[int] or False in case of errors.
        """
        if not self.is_auth_set():
            return False

        error = self.auth(block_address)
        if not error:
            (error, data) = self.rfid_reader.read_block(block_address)
            if not error:
                return data
        else:
            print(f"[e] Error reading {get_block_repr(block_address)}")
            return False

    def write_block(self, block_address: int, new_bytes: list[int]) -> bool:
        """
        Writes new bytes to a specific block, keeping the old ones if None is passed.
        Note: Tag and auth must be set. It does auth.

        Example:
            write_block(1, [None, 0x1a, None, 0x00])
            will write the second and the fourth byte of the second block, leaving the other 14 bytes unaltered.

        :param block_address: block absolute address
        :param new_bytes: list of bytes to be written
        :return True iff the operation has been successful, False otherwise
        """
        if not self.is_auth_set():
            return False

        error = self.auth(block_address)
        if not error:
            (error, data) = self.rfid_reader.read_block(block_address)
            if not error:
                for i in range(len(new_bytes)):
                    if new_bytes[i] is not None:
                        if self.debug:
                            print(f"[i] Changing byte {i} - from {data[i]} to {new_bytes[i]}")
                        data[i] = new_bytes[i]

                error = self.rfid_reader.write_block(block_address, data)
                if self.debug:
                    print(f"[i] Writing {data} to {get_block_repr(block_address)}")
        return not error

    def write_trailer(self, sector_number, key_a=DEFAULT_KEY, access_bits=DEFAULT_AUTH_BITS,
                      user_data=0x69, key_b=DEFAULT_KEY):
        """
        Writes sector trailer (last block) of specified sector. Tag and auth must be set - does auth.
        If value is None, value of byte is kept.

        :param sector_number: number of the sector
        :param key_a: key A of the tag
        :param key_b: key B of the tag
        :param access_bits: access bits
        :param user_data: eventual user data to append after the access bits
        :return True iff the operation has been successful, False otherwise
        """
        address = get_block_address(sector_number, 3)
        return self.write_block(address, key_a[:6] + access_bits[:3] + (user_data,) + key_b[:6])

    def dump(self, sectors_number: int = DEFAULT_SECTORS_NUMBER) -> list[list[int] or bool]:
        """
        Dump the entire tag.
        :param sectors_number: number of sectors
        :return: dump data
        """
        dump = []
        for i in range(sectors_number * 4):
            dump.append(self.read_block(i))
        return dump
