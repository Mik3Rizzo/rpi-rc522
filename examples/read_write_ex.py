#!/usr/bin/env python

import time
from rpi_rc522 import RC522, RC522Manager

rc522 = RC522()

tag = RC522Manager(rc522)

key = [0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF]

while True:

    # Wait for tag
    rc522.wait_for_tag()
    # Request tag
    (error, data) = rc522._request_tag()

    if not error:
        print("Detected tag")
        (error, uid) = rc522.anti_collision()

        if not error:
            print(f"UID: {uid[0]}{uid[1]}{uid[2]}{uid[3]}")

            # Set tag as used in util. This will call RC522.select_tag(uid)
            tag.select_tag(uid)

            # Save authorization info (key B). It doesn't call RC522.auth(), that's called when needed
            tag.set_auth(rc522.ACT_AUTH_A, key)

            # Read block 4, RC522.card_auth() will be called now
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
