#pragma once

#include <stdint.h>
#include <stdbool.h>

#define LEDC_MAGIC_0 'L'
#define LEDC_MAGIC_1 'E'
#define LEDC_MAGIC_2 'D'
#define LEDC_MAGIC_3 'C'
#define LEDC_VERSION 0x01

typedef enum {
    LEDC_PACKET_PING = 0x01,
    LEDC_PACKET_FRAME = 0x10,
} ledc_packet_type_t;

typedef struct __attribute__((packed)) {
    uint8_t magic[4];
    uint8_t version;
    uint8_t type;
    uint8_t output_id_len;
    uint32_t payload_len_be;
} ledc_packet_header_t;

bool ledc_validate_header(const ledc_packet_header_t *header);
