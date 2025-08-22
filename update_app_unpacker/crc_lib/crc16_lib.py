import os
import ctypes
import platform
import logging

from .crc16_lib_py import calc_partition_crc_from_file_py, verify_header_crc

_logger = logging.getLogger(__name__)

if platform.system() == "Windows":
    _lib_name = "crc16_lib.dll"
elif platform.system() == "Darwin":
    _lib_name = "libcrc16_lib.dylib"
else: # Linux
    _lib_name = "libcrc16_lib.so"

_lib_path = os.path.join(os.path.dirname(__file__), _lib_name)
_lib = None
_use_c_impl = False

try:
    _lib = ctypes.CDLL(_lib_path)
    _lib.calc_partition_crc_from_file_c.argtypes = [
        ctypes.c_char_p,     # file_path (const char*)
        ctypes.c_size_t,     # partition_start_pos (size_t)
        ctypes.c_size_t,     # partition_size (size_t)
        ctypes.c_size_t,     # chunk_size (size_t)
        ctypes.POINTER(ctypes.c_size_t) # out_num_crcs (size_t* - a pointer to size_t)
    ]
    _lib.calc_partition_crc_from_file_c.restype = ctypes.POINTER(ctypes.c_uint16)
    
    _use_c_impl = True
except (OSError, AttributeError) as e:
    pass

def verify_partition_crc_from_file(file_path: str, partition_start_pos: int, data_size: int, chunk_size: int, data_checksum: bytes, num_processes: int = 0) -> bool:

    if _use_c_impl:
        _logger.info("Successfully loaded C implementation.")
        num_crcs = ctypes.c_size_t(0)
        crc_sums_ptr = _lib.calc_partition_crc_from_file_c(file_path.encode(), partition_start_pos, data_size, chunk_size, ctypes.byref(num_crcs))
        if not crc_sums_ptr:
            raise(ValueError("CRC calculation failed in C library."))
        total_crc_size = num_crcs.value * ctypes.sizeof(ctypes.c_uint16)
        crc_of_partition = ctypes.string_at(crc_sums_ptr, total_crc_size)

        return crc_of_partition == data_checksum
    else:
        _logger.warning(f"Could not load C implementation. Falling back to Python implementation.")
        if num_processes == 0:
            num_processes = os.cpu_count() or 1
        crc_of_partition = calc_partition_crc_from_file_py(file_path, partition_start_pos, data_size, chunk_size, num_processes)
        return crc_of_partition == data_checksum
