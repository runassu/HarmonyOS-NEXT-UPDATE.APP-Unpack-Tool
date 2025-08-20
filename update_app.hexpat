// ImHex Pattern for UPDATE.APP

import std.mem;
import type.magic;

char ZeroPadding[92] @ 0x00;
struct BlockHeader {
   type::Magic<"\x55\xAA\x5A\xA5"> [[name("Signature")]];
   u32 headerLength [[name("Header Length")]];
   type::Magic<"\x01\x00\x00\x00"> [[name("Magic Number")]];
   char hardwareId[8] [[name("Hardware ID")]];
   u32 sequence [[name("Sequence out of use?")]];
   u32 dataLength [[name("Partition Data Length")]];
   char date[16] [[name("Date")]];
   char time[16] [[name("Time")]];
   char partitionName[16] [[name("Partition Name")]];
   char blank1[16] [[name("Blank1 16 bytes 0x00")]];
   char headerChecksum[2] [[name("Header Checksum")]];
   type::Magic<"\x00\x10"> [[name("Constant (0x1000)")]];
   char blank2[2] [[name("Blank 2 bytes 0x00")]];
   char checksum[headerLength - 98] [[name("Data Checksum")]];
};

struct Block {
   BlockHeader blockHeader;
   char data[blockHeader.dataLength];
   char Padding[(4 - ($ % 4)) % 4];
} [[name(blockHeader.partitionName)]];

Block block[while($ < std::mem::size())] @ $;
