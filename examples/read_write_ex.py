#!/usr/bin/env python

import time
from rpi_rc522 import RFIDReader, RFIDTag, RFIDUtil

reader = RFIDReader()
util = RFIDUtil
tag = RFIDTag(reader)

key = [0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF]

while True:

    # Wait for tag
    reader.wait_for_tag()
    # Request tag
    (error, data) = reader.request()

    if not error:
        print("Detected tag")
        (error, uid) = reader.anticoll()

        if not error:
            print(f"UID: {uid[0]}{uid[1]}{uid[2]}{uid[3]}")

            # Set tag as used in util. This will call RFIDReader.select_tag(uid)
            tag.set_tag(uid)

            # Save authorization info (key B). It doesn't call RFIDReader.card_auth(), that's called when needed
            tag.set_auth(reader.auth_b, key)

            # Read block 4, RFIDReader.card_auth() will be called now
            block_data = tag.read_block(4)
            print(block_data)  # list of int
            print([hex(x) for x in block_data])  # list of hex

            # Write only the 3rd, 4th and 5th byte of the block 9 (sector 2, block 1)
            tag.write_block(9, [None, None, 0xAB, 0xCD, 0xEF])

            # Let's see what do we have in whole tag
            dump_data = tag.dump()
            print(dump_data)

            # We must stop crypto
            tag.reset_auth()

            time.sleep(1)
