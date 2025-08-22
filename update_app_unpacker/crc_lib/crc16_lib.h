#ifndef CRC16_LIB_H
#define CRC16_LIB_H

#include <stdint.h>
#include <stddef.h>

typedef struct {
    uint16_t initial_sum;
    uint16_t polynomial;
    uint16_t xor_value;
    uint16_t table[256];
} UpdateCrc16;

void UpdateCrc16_init(UpdateCrc16 *crc, uint16_t initial_sum, uint16_t polynomial, uint16_t xor_value);

uint16_t compute_sum(const UpdateCrc16 *crc, const uint8_t *data, size_t data_len);

uint16_t* verify_partition_crc_from_file(const char *file_path, size_t partition_start_pos, size_t partition_size, size_t chunk_size, size_t *out_num_crcs);

#endif // CRC16_LIB_H
