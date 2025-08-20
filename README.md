# HarmonyOS NEXT UPDATE.APP Unpack Tool
Unpack HarmonyOS NEXT UPDATE.APP in update_full_base.zip  
Based on legacy version file structure in https://github.com/YKG/huawei_UPDATE.APP_unpacktool
1. First `92` bytes `0x00` in file header
2. Then each block starts with `0x55AA5AA5`
3. `4` bytes for Block Header Length
4. `4` bytes Magic `0x01000000`
5. `8` bytes for Hardware ID
6. `4` bytes for Sequence (seems deprecated)
7. `4` bytes for Partition Data Length
8. `16` bytes for Date
9. `16` bytes for Time
10. `16` bytes for Partition Name
11. `16` bytes `0x00`
12. `2` bytes for Header Checksum (algorithm not found)
13. `2` bytes Constant `0x0010`
14. `2` bytes `0x00`
15. `Header Length - 98` bytes for Data Checksum (customized CRC16)
16. `Data Length` bytes for Partition Data
17. Pad `0x00` to `4` bytes aligned
18. repeat step `2` to `17` until EOF

Partition Data larger than `4160749568` bytes will be splited to multiple blocks with same Partition Name (`4GB` with `496` block size, $$4160749568 = 4 \times 1024^3 \div 512 \times 496$$)  
