from rfid_util import RFIDUtil


"""
Represents an RFID Tag.
"""

class RFIDTag:

    rfid_reader = None
    method = None
    key = None
    uid = None
    last_auth = None

    debug = False

    def __init__(self, rfid_reader):
        self.rfid_reader = rfid_reader

    def set_tag(self, uid):
        """
        Sets tag for further operations.
        Calls deauth() if card is already set.
        Calls RFID select_tag().
        Returns called select_tag() error state.
        """
        if self.debug:
            print(f"Selecting UID {uid}")

        if self.uid is not None:
            self.reset_auth()

        self.uid = uid
        return self.rfid_reader.select_tag(uid)

    def set_auth(self, auth_method, key):
        """
        Sets authentication info for current tag
        """
        self.method = auth_method
        self.key = key

        if self.debug:
            print("Changing used auth key to " + str(key) + " using method " + (
                "A" if auth_method == self.rfid_reader.auth_a else "B"))

    def reset_auth(self):
        """
        Resets authentication info. Calls stop_crypto() if RFID is in auth state
        """
        self.method = None
        self.key = None
        self.last_auth = None

        if self.debug:
            print("Changing auth key and method to None")

        if self.rfid_reader.authed:
            self.rfid_reader.stop_crypto()
            if self.debug:
                print("Stopping crypto1")

    def is_auth_set(self):
        return (self.uid is not None) and (self.key is not None) and (self.method is not None)

    def auth(self, block_address, force=False):
        """
        Calls RFID card_auth() with saved auth information if needed.
        Returns error state from method call.
        """
        auth_data = (block_address, self.method, self.key, self.uid)
        if (self.last_auth != auth_data) or force:
            if self.debug:
                print("Calling card_auth on UID " + str(self.uid))

            self.last_auth = auth_data
            return self.rfid_reader.card_auth(self.method, block_address, self.key, self.uid)
        else:
            if self.debug:
                print("Not calling card_auth - already authed")
            return False

    def write_trailer(self, sector, key_a=(0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF), auth_bits=(0xFF, 0x07, 0x80),
                      user_data=0x69, key_b=(0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF)):
        """
        Writes sector trailer (last block) of specified sector. Tag and auth must be set - does auth.
        If value is None, value of byte is kept.
        Returns error state.
        """
        addr = RFIDUtil.get_block_address(sector, 3)
        return self.write_block(addr, key_a[:6] + auth_bits[:3] + (user_data,) + key_b[:6])

    def write_block(self, block_address, new_bytes):
        """
        Rewrites block with new bytes, keeping the old ones if None is passed. Tag and auth must be set - does auth.
        Returns error state.
        """
        if not self.is_auth_set():
            return True

        error = self.auth(block_address)
        if not error:
            (error, data) = self.rfid_reader.read(block_address)
            if not error:
                for i in range(len(new_bytes)):
                    if new_bytes[i] is not None:
                        if self.debug:
                            print("Changing pos " + str(i) + " with current value " + str(data[i]) + " to " + str(
                                new_bytes[i]))

                        data[i] = new_bytes[i]

                error = self.rfid_reader.write(block_address, data)
                if self.debug:
                    print("Writing " + str(data) + " to " + RFIDUtil.get_block_repr(block_address))

        return error

    def read_block(self, block_address):
        """
        Prints sector/block number and contents of block. Tag and auth must be set - does auth.
        """
        if not self.is_auth_set():
            return True

        error = self.auth(block_address)
        if not error:
            (error, data) = self.rfid_reader.read(block_address)
            print(RFIDUtil.get_block_repr(block_address) + ": " + str(data))
        else:
            print("Error on " + RFIDUtil.get_block_repr(block_address))

    def dump(self, sectors=16):
        for i in range(sectors * 4):
            self.read_block(i)
