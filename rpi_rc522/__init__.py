__version__ = "1.0.0"

try:
    from .rc522 import RC522
    from .rc522manager import RC522Manager
    from .utils import get_block_address, get_block_repr, get_access_bits
except RuntimeError:
    print("Must be used on Raspberry Pi")
