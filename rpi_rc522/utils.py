from typing import Any


def get_block_number(sector_num: int, relative_block_num: int) -> int:
    """
    Returns the block number starting from the relative block number and the sector number.
    :param sector_num: sector number (from 0 to SECTORS_NUMBER - 1)
    :param relative_block_num: relative block number (from 0 to 3)
    :return number of the block (from 0 to SECTORS_NUMBER * 4 - 1)
    """
    return sector_num * 4 + relative_block_num


def get_block_repr(block_number: int) -> str:
    """
    Returns block representation of a given block address, e.g.
    S01B03 for sector trailer in second sector.
    :return string representation
    """
    return f"S{(block_number - (block_number % 4)) // 4}B{block_number % 4}"


def get_access_bits(c0: tuple[int | Any, int | Any, int | Any, int | Any],
                    c1: tuple[int | Any, int | Any, int | Any, int | Any],
                    c2: tuple[int | Any, int | Any, int | Any, int | Any]) -> tuple[int | Any, int | Any, int | Any]:
    """
    Calculates the access bits for a sector trailer, based on their access conditions
    :param c0: access condition for block 0 of the sector
    :param c1: access condition for block 1 of the sector
    :param c2: access condition for block 2 of the sector
    :returns 3 bytes for the sector trailer
    """
    byte_6 = ((~c1[3] & 1) << 7) + ((~c1[2] & 1) << 6) + ((~c1[1] & 1) << 5) + ((~c1[0] & 1) << 4) + \
             ((~c0[3] & 1) << 3) + ((~c0[2] & 1) << 2) + ((~c0[1] & 1) << 1) + (~c0[0] & 1)
    byte_7 = ((c0[3] & 1) << 7) + ((c0[2] & 1) << 6) + ((c0[1] & 1) << 5) + ((c0[0] & 1) << 4) + \
             ((~c2[3] & 1) << 3) + ((~c2[2] & 1) << 2) + ((~c2[1] & 1) << 1) + (~c2[0] & 1)
    byte_8 = ((c2[3] & 1) << 7) + ((c2[2] & 1) << 6) + ((c2[1] & 1) << 5) + ((c2[0] & 1) << 4) + \
             ((c1[3] & 1) << 3) + ((c1[2] & 1) << 2) + ((c1[1] & 1) << 1) + (c1[0] & 1)
    return byte_6, byte_7, byte_8
