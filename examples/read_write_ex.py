#!/usr/bin/env python
import time
from rpi_rc522 import RC522Manager


reader = RC522Manager()
key = [0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF]

while True:

    print("1 >>> scan() --- Scanning until a tag appears...")
    (status, uid_data) = reader.scan(scan_once=False)  # uid_data is 5 bytes: UID (4 bytes) | checksum (1 byte)

    if status == reader.STATUS_OK:
        print(f"Found tag {uid_data[0:4]}")

        print("2 >>> select_tag(...) --- Select the tag")
        status = reader.select_tag(uid_data)

        if status == reader.STATUS_OK:
            print("Tag selected")

            print("3 >>> set_auth(...) --- Set authentication info")
            reader.set_auth(key=key)
            print("Authentication info set")

            print("read_block(...) --- Read a block")
            block_number = 5
            print(f"Reading block {block_number}...")
            (status, read_data) = reader.read_block(block_number)

            if status == reader.STATUS_OK:
                print(f"Block {block_number}: {bytes(read_data).hex()}")

            print("write_block(...) --- Write a block")
            # Write only the 3rd, 4th and 5th byte of the block 4 (sector 1, block 0)
            to_write = [None, None, 0xAB, 0xCD, 0xEF]
            print(f"Writing {to_write} to block {block_number} ...")
            status = reader.write_block(block_number, to_write)

            # Read the new content
            if status == reader.STATUS_OK:
                (status, read_data) = reader.read_block(block_number)
                if status == reader.STATUS_OK:
                    print(f"Block {block_number} new data: {bytes(read_data).hex()}")

            print("dump() --- Dump the entire tag")
            (status, dump_data) = reader.dump()
            if status == reader.STATUS_OK:
                print("Entire dump:")
                print(dump_data)

            time.sleep(1)
