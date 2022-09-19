__version__ = "1.0.0"

try:
    from .rfid_reader import RFIDReader
    from .utils import get_block_address, get_block_repr, get_access_bits
    from .rfid_manager import RFIDManager
except RuntimeError:
    print("Must be used on Raspberry Pi")
