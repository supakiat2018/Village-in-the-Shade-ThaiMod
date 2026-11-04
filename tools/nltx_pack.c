#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <string.h>
#include "lz4_src/lz4.h"
#include "lz4_src/lz4hc.h"

int main(int argc, char** argv) {
    if (argc < 3) {
        printf("Usage: nltx_pack <input.dds> <output.nltx> [compression_level: 1-12]\n");
        return 1;
    }
    const char* dds_path = argv[1];
    const char* out_path = argv[2];
    int clevel = (argc >= 4) ? atoi(argv[3]) : 12;

    FILE* fdds = fopen(dds_path, "rb");
    if (!fdds) {
        printf("Error: Could not open %s\n", dds_path);
        return 1;
    }
    fseek(fdds, 0, SEEK_END);
    long dds_sz = ftell(fdds);
    fseek(fdds, 148, SEEK_SET); // Skip 148 bytes DDS header
    uint32_t raw_sz = (uint32_t)(dds_sz - 148);

    uint8_t* raw_buf = (uint8_t*)malloc(raw_sz);
    fread(raw_buf, 1, raw_sz, fdds);
    fclose(fdds);

    printf("Read %u bytes raw BC7 from %s\n", raw_sz, dds_path);
    int max_dst = LZ4_compressBound(raw_sz);
    uint8_t* comp_buf = (uint8_t*)malloc(max_dst);

    int comp_len = LZ4_compress_HC((const char*)raw_buf, (char*)comp_buf, (int)raw_sz, max_dst, clevel);
    printf("LZ4 HC (level %d): %d bytes (raw %u bytes)\n", clevel, comp_len, raw_sz);

    // Build YKCMP_V1 header (20 bytes)
    uint8_t yk_hdr[20];
    memcpy(yk_hdr, "YKCMP_V1", 8);
    *(uint32_t*)(yk_hdr + 8) = 9;
    *(uint32_t*)(yk_hdr + 12) = comp_len + 20;
    *(uint32_t*)(yk_hdr + 16) = raw_sz;

    // Build NMPLTEX1 header (128 bytes)
    uint8_t nmpl_hdr[128];
    memset(nmpl_hdr, 0, 128);
    memcpy(nmpl_hdr, "NMPLTEX1", 8);
    *(uint32_t*)(nmpl_hdr + 0x10) = 0x66;
    *(uint32_t*)(nmpl_hdr + 0x14) = 0x00800006;
    *(uint32_t*)(nmpl_hdr + 0x18) = 4096;
    *(uint32_t*)(nmpl_hdr + 0x1C) = 4096;
    uint8_t extra[8] = { 0x04, 0x00, 0xFF, 0xFF, 0x00, 0x01, 0x01, 0x00 };
    memcpy(nmpl_hdr + 0x20, extra, 8);
    *(uint32_t*)(nmpl_hdr + 0x2C) = raw_sz;
    *(uint32_t*)(nmpl_hdr + 0x30) = comp_len + 20;
    *(uint32_t*)(nmpl_hdr + 0x34) = 128;

    FILE* fout = fopen(out_path, "wb");
    if (!fout) {
        printf("Error: Could not open %s for writing\n", out_path);
        return 1;
    }
    fwrite(nmpl_hdr, 1, 128, fout);
    fwrite(yk_hdr, 1, 20, fout);
    fwrite(comp_buf, 1, comp_len, fout);
    fclose(fout);

    long total_sz = 128 + 20 + comp_len;
    long limit = 13590835;
    printf("Output written to: %s (%ld bytes)\n", out_path, total_sz);
    printf("Limit in game:     %ld bytes\n", limit);
    printf("Diff from limit:   %+ld bytes\n", total_sz - limit);
    if (total_sz <= limit) {
        printf(">>> SUCCESS: FITS WITHIN GAME LIMIT!\n");
    } else {
        printf(">>> WARNING: Still exceeds by %ld bytes\n", total_sz - limit);
    }

    free(raw_buf);
    free(comp_buf);
    return 0;
}
