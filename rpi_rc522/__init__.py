__version__ = "1.0.0"

try:
    from .rfid_reader import RFIDReader
    from .rfid_util import RFIDUtil
    from .rfid_tag import RFIDTag
except RuntimeError:
    print("Must be used on Raspberry Pi")
