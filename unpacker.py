import os
import struct
import mmap

def parse_and_export_file(file_path):
    try:
        with open(file_path, 'r+b') as f:
            with mmap.mmap(f.fileno(), length=0, access=mmap.ACCESS_READ) as mm:

                # Skip the initial 92 bytes of padding
                current_offset = 92
                total_size = len(mm)
                file_count = 0
                
                # Directory to save the extracted files
                output_dir = os.path.join(os.path.dirname(file_path), 'extracted_files')
                os.makedirs(output_dir, exist_ok=False)
                
                print(f"Exporting files to: {output_dir}")
                
                # Loop through each Block
                while current_offset < total_size:
                    try:
                        header_format = '<4s L L Q L L 16s 16s 16s 16s 2s H H'
                        header_size = struct.calcsize(header_format)
                        
                        if current_offset + header_size > total_size:
                            break
                            
                        header_unpacked = struct.unpack_from(header_format, mm, current_offset)
                        current_offset += header_size
                        
                        # Unpack the header fields
                        signature, headerLength, magicNumber, hardwareId, sequence, \
                        partitionDataLength, date, time, partitionName, blank1, \
                        headerChecksum, constant, blank2 = header_unpacked
                        
                        # TODO: verify Header Checksum

                        # Decode partitionName from bytes to string
                        file_name_bytes = partitionName.strip(b'\x00')
                        if not file_name_bytes:
                            print("Warning: Found an entry with no filename. Skipping.")
                            checksum_size = headerLength - 98
                            total_block_size = header_size + checksum_size + partitionDataLength
                            padding_length = (4 - (total_block_size % 4)) % 4
                            current_offset += checksum_size + partitionDataLength + padding_length
                            continue
                        
                        file_name_str = file_name_bytes.decode('utf-8', errors='ignore')
                        
                        # TODO: verify Data Checksum
                        checksum_size = headerLength - 98
                        current_offset += checksum_size

                        data = mm[current_offset : current_offset + partitionDataLength]
                        
                        # append if file exists
                        output_path = os.path.join(output_dir, file_name_str)
                        mode = 'ab' if os.path.exists(output_path) else 'wb'
                        action = "Appending to" if mode == 'ab' else "Creating"

                        # Write the data block to the output file
                        with open(output_path, mode) as out_f:
                            out_f.write(data)
                        
                        print(f"{action} '{file_name_str}' with {partitionDataLength} bytes.")
                        file_count += 1
                        
                        # Move offset past the data and padding
                        current_offset += partitionDataLength
                        total_block_size = header_size + checksum_size + partitionDataLength
                        padding_length = (4 - (total_block_size % 4)) % 4
                        current_offset += padding_length
                        
                    except struct.error as e:
                        print(f"Error parsing header at offset {current_offset}: {e}")
                        break
                    except Exception as e:
                        print(f"An unexpected error occurred during block parsing at offset {current_offset}: {e}")
                        break

            print(f"\nParsing complete. Total file fragments processed: {file_count}")

    except FileNotFoundError:
        print(f"Error: File not found at {file_path}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")

if __name__ == "__main__":
    # Replace file path with the path to your actual binary file
    input_file = './update_full_base/UPDATE.APP'
    parse_and_export_file(input_file)