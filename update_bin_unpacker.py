import os
import sys
import struct
import mmap
import argparse
import hashlib

UPGRADE_COMPINFO_SIZE_L2 = 87

def parse_and_export_file(file_path, output_dir, do_hash_check=False):

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
                current_offset = 0
                total_size = len(mm)
                file_count = 0

                # 1. Parse Header
                header_format = '<H H I I 64s 64s H H 16s 16s H H'
                header_size = struct.calcsize(header_format)

                (
                    header_tlv_type,
                    upgrade_pkg_header_size,
                    pkg_info_length,
                    update_file_version,
                    product_update_id,
                    software_version,
                    time_tlv_type,
                    upgrade_pkg_time_size,
                    date,
                    time,
                    compinfo_tlv_type,
                    compinfo_len
                ) = struct.unpack_from(header_format, view, current_offset)

                assert header_tlv_type == 1
                assert time_tlv_type == 2
                assert compinfo_tlv_type == 5

                current_offset += header_size

                # 2. Parse Component Info
                component_count = compinfo_len // UPGRADE_COMPINFO_SIZE_L2
                component_infos = []
                component_info_format = '<32s H B B B 10s I I 32s'
                component_info_size = struct.calcsize(component_info_format)

                for _ in range(component_count):
                    (
                        component_name_bytes,
                        component_id,
                        component_res_type,
                        component_flag,
                        component_type,
                        component_version,
                        component_size,
                        component_original_size,
                        digest
                    ) = struct.unpack_from(component_info_format, view, current_offset)

                    current_offset += component_info_size

                    component_info = {
                    'name': component_name_bytes.decode('utf-8').split('\x00')[0].replace('/', ''),
                    'size': component_size,
                    'digest': digest
                    }
                    component_infos.append(component_info)

                # 3. Skip describe package id
                current_offset += 16

                # 4. Skip sign data
                sign_info_format = '<HI'
                (sign_tlv_type, signdata_len) = struct.unpack_from(sign_info_format, view, current_offset)
                sign_info_size = struct.calcsize(sign_info_format) + signdata_len
                current_offset += sign_info_size
                assert sign_tlv_type == 8

                # 5. Component chunks
                for i in range(component_count):
                    chunk_data = view[current_offset: current_offset + component_infos[i]['size']]

                    if not component_infos[i]['name']:
                        print("Warning: Found an chunk with no filename. Skipping.")
                        current_offset += component_infos[i]['size']
                        continue

                    # verify Data Checksum
                    if do_hash_check:
                        if not hashlib.sha256(chunk_data).digest() == component_infos[i]['digest']:
                            del chunk_data
                            raise(ValueError("Component Chunk Hash check failed"))

                    # Write the component chunk to the output file
                    output_path = os.path.join(output_dir, component_infos[i]['name'])
                    with open(output_path, 'wb') as out_f:
                        out_f.write(chunk_data)
                    del chunk_data

                    print(f"Creating '{component_infos[i]['name']}' with {component_infos[i]['size']} bytes.")
                    file_count += 1

                    # Move offset past the data and padding
                    current_offset += component_infos[i]['size']

                del view
                print(f"\nParsing complete. Total file fragments processed: {file_count}")

    except FileNotFoundError:
        print(f"Error: File not found at {file_path}")
    except Exception as e:
        print(f"An unexpected error occurred")
        raise


def main():

    parser = argparse.ArgumentParser(description='Parse and export files from Huawei HarmonyOS NEXT update.bin')
    parser.add_argument('--input_file', '-i', type=str, required=True,
                        help='Input path to update.bin')
    parser.add_argument('--hash', action='store_true',
                        help='Enable Hash verification for partition data (default: off).')
    parser.add_argument('--output_dir', '-o', type=str, required=False,
                        help='Specify the output directory for extracted files. Defaults to "extracted_files" in the same directory as the input file.')
    args = parser.parse_args()

    parse_and_export_file(args.input_file, args.output_dir, args.hash)


if __name__ == "__main__":
    main()