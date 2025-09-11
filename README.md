# HarmonyOS NEXT Update Package Unpack Tool

**HarmonyOS NEXT 6** uses OpenHarmony_L2 package format for update package  
Official packaging tools can be found here: https://gitee.com/openharmony/update_packaging_tools  
The table below shows a general overview of the file structure. For the specific structure, please refer to the ImHex pattern file [`update_bin.hexpat`](update_bin.hexpat)

| Part | Description |
| --- | --- |
| header | contains product id and software version type should always be L2 here |
| time | date and time |
| component info | component info list with name, size, hash and other infos |
| package id |  |
| sign data |  |
| component chunk | component chunks listed in the order specified by the component info |

## How To (For update.bin): 
Codes For update.bin in [update_bin_unpacker.py](./update_bin_unpacker.py)

### Run
```
usage: update_bin_unpacker.py [-h] --input_file INPUT_FILE [--hash] [--output_dir OUTPUT_DIR]
example: python update_bin_unpacker.py -i ./update_full_base/update.bin --hash
```

---

**HarmonyOS NEXT 5** uses UPDATE.APP in update_full_base.zip, file structure is nearly the same as the Android version  
Based on legacy version file structure in https://github.com/YKG/huawei_UPDATE.APP_unpacktool
1. First `92` bytes `0x00` in file header
2. Then each block starts with `55AA5AA5`
3. `4` bytes for Block Header Length
4. `4` bytes Magic `0x00000001`
5. `8` bytes for Hardware ID
6. `4` bytes for Sequence (seems deprecated)
7. `4` bytes for Partition Data Length
8. `16` bytes for Date
9. `16` bytes for Time
10. `16` bytes for Partition Name
11. `16` bytes `0x00`
12. `2` bytes for Header Checksum (customized CRC16)
13. `2` bytes Constant `0x1000` for Data Checksum chunk size
14. `2` bytes `0x00`
15. `Header Length - 98` bytes for Data Checksum table (customized CRC16 per 0x1000 chunk)
16. `Data Length` bytes for Partition Data
17. Pad `0x00` to `4` bytes aligned
18. repeat step `2` to `17` until EOF

Partition Data larger than `4160749568` bytes will be splited to multiple blocks with same Partition Name (`4GB` with `496` block size, $$4160749568 = 4 \times 1024^3 \div 512 \times 496$$)  

## How To (For UPDATE.APP): 
### Building from source
Codes For UPDATE.APP in [update_app_unpacker](./update_app_unpacker)
```
pip install build
python -m build
pip install ./dist/update_app_unpacker-*.whl
```
### Run
```
usage: update-app-unpacker [-h] --input_file INPUT_FILE [--crc] [--output_dir OUTPUT_DIR]
example: update-app-unpacker -i ./update_full_base/UPDATE.APP --crc
```
Pure Python implementation included, you can run `python unpacker.py` directly, but CRC is slow in pure Python.