import os
import sys
import struct
import mmap
import argparse
try:
    from .crc_lib import verify_partition_crc_from_file, verify_header_crc
except ImportError:
    from crc_lib import verify_partition_crc_from_file, verify_header_crc

def parse_and_export_file(file_path, output_dir, do_crc_check=False):
                
    # Directory to save the extracted files
    if not output_dir:
        output_dir = os.path.join(os.path.dirname(file_path), 'extracted_files')
    try:
        os.makedirs(output_dir, exist_ok=False)
        print(f"Exporting files to: {output_dir}")
    except FileExistsError as e:
        print(f"Output dir {output_dir} exists.")
        return

    try:
        with open(file_path, 'rb') as f:
            with mmap.mmap(f.fileno(), length=0, access=mmap.ACCESS_READ) as mm:
                view = memoryview(mm)

                # Skip the initial 92 bytes of padding
                current_offset = 92
                total_size = len(mm)
                file_count = 0

                # Loop through each Block
                while current_offset < total_size:

                    try:
                        header_format = '<4s L L Q L L 16s 16s 16s 16s 2s H H'
                        header_size = struct.calcsize(header_format)
                        
                        if current_offset + header_size > total_size:
                            break
                        
                        # Check Header Checksum
                        header = view[current_offset : current_offset + header_size]
                        if not verify_header_crc(header):
                            raise(ValueError("Header CRC check failed"))
                        del header

                        header_unpacked = struct.unpack_from(header_format, view, current_offset)
                        current_offset += header_size
                        
                        # Unpack the header fields
                        signature, header_length, magic_number, hardware_id, sequence, \
                        partition_data_length, partiton_date, partition_time, partition_name, blank1, \
                        header_checksum, chunk_size, blank2 = header_unpacked

                        assert signature == b"\x55\xAA\x5A\xA5"
                        assert magic_number == 1

                        # Decode partition_name from bytes to string
                        file_name_bytes = partition_name.strip(b'\x00')
                        if not file_name_bytes:
                            print("Warning: Found an entry with no filename. Skipping.")
                            checksum_size = header_length - 98
                            total_block_size = header_size + checksum_size + partition_data_length
                            padding_length = (4 - (total_block_size % 4)) % 4
                            current_offset += checksum_size + partition_data_length + padding_length
                            continue
                        
                        file_name_str = file_name_bytes.decode('utf-8', errors='ignore')
                        
                        checksum_size = header_length - 98

                        data_checksum = bytearray(view[current_offset : current_offset + checksum_size])
                        current_offset += checksum_size

                        data = view[current_offset : current_offset + partition_data_length]

                        # verify Data Checksum
                        if do_crc_check:
                            num_processes = os.cpu_count() or 1
                            if not verify_partition_crc_from_file(file_path, current_offset, partition_data_length, chunk_size, data_checksum, num_processes):
                                raise(ValueError("Data Partition CRC check failed"))

                        del data_checksum

                        # append if file exists
                        output_path = os.path.join(output_dir, file_name_str)
                        mode = 'ab' if os.path.exists(output_path) else 'wb'
                        action = "Appending to" if mode == 'ab' else "Creating"

                        # Write the data block to the output file
                        with open(output_path, mode) as out_f:
                            out_f.write(data)
                        del data

                        print(f"{action} '{file_name_str}' with {partition_data_length} bytes.")
                        file_count += 1
                        
                        # Move offset past the data and padding
                        current_offset += partition_data_length
                        total_block_size = header_size + checksum_size + partition_data_length
                        padding_length = (4 - (total_block_size % 4)) % 4
                        current_offset += padding_length
                        
                    except struct.error as e:
                        print(f"Error parsing header at offset {current_offset}: {e}")
                        break
                    except Exception as e:
                        print(f"An unexpected error occurred during block parsing at offset {current_offset}: {e}")
                        raise
                        break
            del view
            print(f"\nParsing complete. Total file fragments processed: {file_count}")

    except FileNotFoundError:
        print(f"Error: File not found at {file_path}")
    except Exception as e:
        print(f"An unexpected error occurred")
        raise


def main():

    parser = argparse.ArgumentParser(description='Parse and export files from Huawei HarmonyOS NEXT UPDATE.APP')
    parser.add_argument('--input_file', '-i', type=str, required=True, 
                        help='Input path to UPDATE.APP')
    parser.add_argument('--crc', action='store_true', 
                        help='Enable CRC verification for partition data (default: off).')
    parser.add_argument('--output_dir', '-o', type=str, required=False, 
                        help='Specify the output directory for extracted files. Defaults to "extracted_files" in the same directory as the input file.')
    args = parser.parse_args()
    
    parse_and_export_file(args.input_file, args.output_dir, args.crc)


if __name__ == "__main__":
    main()
