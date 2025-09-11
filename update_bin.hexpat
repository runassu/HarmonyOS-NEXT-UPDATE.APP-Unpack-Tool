// ImHex Pattern for update.bin

#include <std/string.pat>

#define UPGRADE_COMPINFO_SIZE_L2 87
#define COMPONENT_ADDR_SIZE_L2 32

enum HeaderTLVType : u16 {
   header_tlv_type_not_l2 = 0x11,
   header_tlv_type_l2 = 1,
};

enum ComponentType : u8 {
  IMG = 0,
  ZIP = 1,
  UNKNOWN = 0xFF
};

struct ComponentInfo {
  char component_name[COMPONENT_ADDR_SIZE_L2];
  u16 component_id;
  u8 component_res_type;
  u8 component_flag;
  ComponentType component_type;
  char component_version[10];
  u32 component_size;
  u32 component_original_size;
  char digest[32]; // sha256 of component
};

struct FileHeader {
  HeaderTLVType header_tlv_type; // phone should always be openharmony_l2 0x1
  u16 upgrade_pkg_header_size;
  u32 pkg_info_length;
  u32 update_file_version;
  char product_update_id[64];
  char software_version[64];
  u16 time_tlv_type; // time type is 2
  u16 upgrade_pkg_time_size;
  char date[16];
  char time[16];
  u16 compinfo_tlv_type; // compinfo type is 5
  u16 compinfo_len;
  u8 component_count = compinfo_len / UPGRADE_COMPINFO_SIZE_L2;
  ComponentInfo component_infos[component_count];
};

struct HashInfoHeader {
  u16 sign_tlv_type; // sign_tlv_type is 8
  u32 signdata_len;
  char signdata[signdata_len];
};

FileHeader file_header @ 0x0;
char describe_package_id[16] @ $;
HashInfoHeader hash_info_header @ $;

u8 chunk_index;

struct ChunkData {
  char chunk_data[file_header.component_infos[chunk_index].component_size] [[name(std::string::to_string(file_header.component_infos[chunk_index].component_name))]];
  chunk_index += 1;
};

ChunkData chunk_datas[file_header.component_count] @ $;
