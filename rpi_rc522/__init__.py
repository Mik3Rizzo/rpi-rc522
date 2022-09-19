__version__ = "1.0.0"

try:
    from .rc522 import RC522
    from .utils import get_block_address, get_block_repr, get_access_bits
    from .rc522manager import RC522Manager
except RuntimeError:
    print("Must be used on Raspberry Pi")
