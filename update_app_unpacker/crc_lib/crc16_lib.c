#include "crc16_lib.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <fcntl.h>
#include <unistd.h>
#include <sys/stat.h>
#include <sys/mman.h>

static void _initialize_table(UpdateCrc16 *crc) {
    for (int i = 0; i < 256; i++) {
        uint16_t value = 0;
        uint16_t temp = i;
        for (int j = 0; j < 8; j++) {
            if (((value ^ temp) & 0x0001) != 0) {
                value = (value >> 1) ^ crc->polynomial;
            } else {
                value >>= 1;
            }
            temp >>= 1;
        }
        crc->table[i] = value;
    }
}

void UpdateCrc16_init(UpdateCrc16 *crc, uint16_t initial_sum, uint16_t polynomial, uint16_t xor_value) {
    crc->initial_sum = initial_sum;
    crc->polynomial = polynomial;
    crc->xor_value = xor_value;
    _initialize_table(crc);
}

uint16_t compute_sum(const UpdateCrc16 *crc, const uint8_t *data, size_t data_len) {
    uint16_t current_sum = crc->initial_sum;
    for (size_t i = 0; i < data_len; i++) {
        current_sum = ((current_sum >> 8) ^ crc->table[(current_sum ^ data[i]) & 0xFF]) & 0xFFFF;
    }
    return (current_sum ^ crc->xor_value) & 0xFFFF;
}

uint16_t* calc_partition_crc_from_file_c(const char *file_path, size_t partition_start_pos, size_t partition_size, size_t chunk_size, size_t *out_num_crcs) {
    // Open the file.
    int fd = open(file_path, O_RDONLY);
    if (fd == -1) {
        perror("Error opening file");
        *out_num_crcs = 0;
        return NULL;
    }

    struct stat sb;
    if (fstat(fd, &sb) == -1) {
        perror("Error getting file status");
        close(fd);
        *out_num_crcs = 0;
        return NULL;
    }

    if (partition_start_pos + partition_size > sb.st_size) {
        fprintf(stderr, "Error: Partition extends beyond file size.\n");
        close(fd);
        *out_num_crcs = 0;
        return NULL;
    }

    // Memory map the entire file.
    uint8_t *mm = mmap(NULL, sb.st_size, PROT_READ, MAP_SHARED, fd, 0);
    if (mm == MAP_FAILED) {
        perror("Error memory-mapping file");
        close(fd);
        *out_num_crcs = 0;
        return NULL;
    }

    // Initialize the CRC calculator with default values.
    UpdateCrc16 crc_calculator;
    UpdateCrc16_init(&crc_calculator, 0xFFFF, 0x8408, 0xFFFF);

    // Calculate the number of chunks to pre-allocate memory.
    size_t num_chunks = (partition_size + chunk_size - 1) / chunk_size;
    uint16_t *computed_crc_sums = (uint16_t*)malloc(num_chunks * sizeof(uint16_t));
    if (computed_crc_sums == NULL) {
        perror("Error allocating memory");
        munmap(mm, sb.st_size);
        close(fd);
        *out_num_crcs = 0;
        return NULL;
    }

    for (size_t i = 0; i < num_chunks; i++) {
        size_t start_offset = partition_start_pos + i * chunk_size;
        size_t current_chunk_size = (i == num_chunks - 1) ? 
                                    (partition_size - i * chunk_size) : 
                                    chunk_size;
        
        if ((i + 1) % 1000 == 0 || (i + 1) == num_chunks) {
            float progress = (float)(i + 1) / num_chunks * 100.0f;
            fprintf(stdout, "Verifying Checksum: %.2f%%...\r", progress);
            fflush(stdout); // Flush the output buffer
        }

        computed_crc_sums[i] = compute_sum(&crc_calculator, mm + start_offset, current_chunk_size);
    }

    fprintf(stdout, "\n");
    
    munmap(mm, sb.st_size);
    close(fd);

    *out_num_crcs = num_chunks;
    return computed_crc_sums;
}
