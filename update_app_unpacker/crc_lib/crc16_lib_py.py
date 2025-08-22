import sys
import struct
import mmap
import os
import multiprocessing as mp

class UpdateCrc16:
    """
    Customized CRC16
    """
    def __init__(self, initial_sum=0xFFFF, polynomial=0x8408, xor_value=0xFFFF):
        self._polynomial = polynomial
        self._xor_value = xor_value
        self._initial_sum = initial_sum
        self._table = self._initialize_table()

    def _initialize_table(self):

        table = [0] * 256
        for i in range(256):
            value = 0
            temp = i
            for _ in range(8):
                if ((value ^ temp) & 0x0001) != 0:
                    value = (value >> 1) ^ self._polynomial
                else:
                    value >>= 1
                temp >>= 1
            table[i] = value
        return table

    def compute_sum(self, mv: memoryview) -> int:

        current_sum = self._initial_sum
        for byte in mv:
            current_sum = ((current_sum >> 8) ^ self._table[(current_sum ^ byte) & 0xFF]) & 0xFFFF
        final_sum = (current_sum ^ self._xor_value) & 0xFFFF
        
        return final_sum


def _compute_chunk_crc_in_process(args: tuple) -> tuple:

    file_path, absolute_start_pos, absolute_end_pos = args

    with open(file_path, 'rb') as f:
        with mmap.mmap(f.fileno(), length=0, access=mmap.ACCESS_READ) as mm:
            chunk_mv = memoryview(mm)[absolute_start_pos: absolute_end_pos]
            crc_calculator = UpdateCrc16()
            crc_for_chunk = crc_calculator.compute_sum(chunk_mv)
            del chunk_mv
            return absolute_start_pos, crc_for_chunk


def calc_partition_crc_from_file_py(file_path: str, partition_start_pos: int, data_size: int, chunk_size: int, num_processes: int) -> bytes:

    total_chunks = (data_size + chunk_size - 1) // chunk_size
    
    # Store arguments for each chunk calculation
    chunk_tasks = []
    
    for i in range(0, data_size, chunk_size):
        # Calculate the absolute start and end positions for the chunk
        absolute_start_pos = partition_start_pos + i
        absolute_end_pos = min(partition_start_pos + i + chunk_size, partition_start_pos + data_size)
        chunk_tasks.append((file_path, absolute_start_pos, absolute_end_pos))

    # Use a Pool to manage worker processes
    with mp.Pool(processes=num_processes) as pool:
        
        computed_crc_sums = {}
        completed_tasks = 0
        
        # Using imap_unordered to get results as they are ready
        for start_pos, crc_sum in pool.imap_unordered(_compute_chunk_crc_in_process, chunk_tasks):
            computed_crc_sums[start_pos] = crc_sum
            completed_tasks += 1

            if completed_tasks % 1000 == 0 or completed_tasks == total_chunks:
                progress = completed_tasks / total_chunks * 100
                sys.stdout.write(f"Verifying Checksum: {progress:.2f}%...\r")
                sys.stdout.flush()

    sys.stdout.write("\n")
    
    # Sort results by their start position to ensure correct order
    # The keys need to be relative to the partition, so subtract partition_start_pos
    sorted_relative_positions = sorted(computed_crc_sums.keys())
    sorted_crc_sums = [computed_crc_sums[pos] for pos in sorted_relative_positions]
    
    computed_crc_bytes = struct.pack(f'<{len(sorted_crc_sums)}H', *sorted_crc_sums)
    
    return computed_crc_bytes


def verify_header_crc(header_data: memoryview) -> bool:

    crc_pos = 92
    header_size = 98

    temp_header_data = bytearray(header_data)
    temp_header_mv = memoryview(bytearray(temp_header_data))

    expected_crc_bytes = temp_header_mv[crc_pos : crc_pos + 2]
    expected_crc = struct.unpack('<H', expected_crc_bytes)[0]
    
    struct.pack_into('<H', temp_header_mv, crc_pos, 0x0000)
    
    crc_calculator = UpdateCrc16(initial_sum=0xFFFF, polynomial=0x8408, xor_value=0xFFFF)
    computed_crc = crc_calculator.compute_sum(temp_header_mv)
    return computed_crc == expected_crc
