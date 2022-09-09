#!/usr/bin/env python
# -*- coding: utf8 -*-
#
#    Copyright (c) 2016 Ondřej Ondryáš {ondryaso} for pi-rc522
#    Original git of pi-rc522: https://github.com/ondryaso/pi-rc522

class RFIDUtil:

    @staticmethod
    def get_block_address(sector_num, relative_block_num):
        """
        Returns block address of a relative block in a sector.
        """
        return sector_num * 4 + relative_block_num

    @staticmethod
    def get_block_repr(block_address):
        """
        Returns block representation of a given block address, e.g.
        S01B03 for sector trailer in second sector.
        """
        return f"S{(block_address - (block_address % 4) / 4)}B{block_address % 4}"

    @staticmethod
    def get_access_bits(c1, c2, c3):
        """
        Calculates the access bits for a sector trailer based on their access conditions
        c1, c2, c3, c4 are 4 items tuples containing the values for each block
        returns the 3 bytes for the sector trailer
        """
        byte_6 = ((~c2[3] & 1) << 7) + ((~c2[2] & 1) << 6) + ((~c2[1] & 1) << 5) + ((~c2[0] & 1) << 4) + \
                 ((~c1[3] & 1) << 3) + ((~c1[2] & 1) << 2) + ((~c1[1] & 1) << 1) + (~c1[0] & 1)
        byte_7 = ((c1[3] & 1) << 7) + ((c1[2] & 1) << 6) + ((c1[1] & 1) << 5) + ((c1[0] & 1) << 4) + \
                 ((~c3[3] & 1) << 3) + ((~c3[2] & 1) << 2) + ((~c3[1] & 1) << 1) + (~c3[0] & 1)
        byte_8 = ((c3[3] & 1) << 7) + ((c3[2] & 1) << 6) + ((c3[1] & 1) << 5) + ((c3[0] & 1) << 4) + \
                 ((c2[3] & 1) << 3) + ((c2[2] & 1) << 2) + ((c2[1] & 1) << 1) + (c2[0] & 1)
        return byte_6, byte_7, byte_8


