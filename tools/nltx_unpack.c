#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <string.h>
#include "lz4_src/lz4.h"

#pragma pack(push, 1)
typedef struct {
    uint32_t magic;
    uint32_t size;
    uint32_t flags;
    uint32_t height;
    uint32_t width;
    uint32_t pitchOrLinearSize;
    uint32_t depth;
    uint32_t mipMapCount;
    uint32_t reserved1[11];
    struct {
        uint32_t size;
        uint32_t flags;
        uint32_t fourCC;
        uint32_t rgbBitCount;
        uint32_t rBitMask;
        uint32_t gBitMask;
        uint32_t bBitMask;
        uint32_t aBitMask;
    } ddspf;
    uint32_t caps;
    uint32_t caps2;
    uint32_t caps3;
    uint32_t caps4;
    uint32_t reserved2;
} DDS_HEADER;

typedef struct {
    uint32_t dxgiFormat;
    uint32_t resourceDimension;
    uint32_t miscFlag;
    uint32_t arraySize;
    uint32_t miscFlags2;
} DDS_HEADER_DXT10;
#pragma pack(pop)

int main(int argc, char** argv) {
    if (argc < 3) {
        printf("Usage: nltx_unpack <in.nltx> <out.dds>\n");
        return 1;
    }
    const char* in_path = argv[1];
    const char* out_path = argv[2];

    FILE* fin = fopen(in_path, "rb");
    if (!fin) {
        printf("Could not open %s\n", in_path);
        return 1;
    }
    fseek(fin, 0, SEEK_END);
    long sz = ftell(fin);
    fseek(fin, 0, SEEK_SET);

    uint8_t* in_buf = (uint8_t*)malloc(sz);
    fread(in_buf, 1, sz, fin);
    fclose(fin);

    if (sz < 148 || memcmp(in_buf, "NMPLTEX1", 8) != 0 || memcmp(in_buf + 128, "YKCMP_V1", 8) != 0) {
        printf("Invalid NLTX format!\n");
        free(in_buf);
        return 1;
    }

    uint32_t comp_len_plus_20 = *(uint32_t*)(in_buf + 128 + 12);
    uint32_t raw_sz = *(uint32_t*)(in_buf + 128 + 16);
    uint32_t comp_len = comp_len_plus_20 - 20;

    uint8_t* comp_data = in_buf + 148;
    uint8_t* raw_buf = (uint8_t*)malloc(raw_sz);

    int decomp_sz = LZ4_decompress_safe((const char*)comp_data, (char*)raw_buf, comp_len, raw_sz);
    if (decomp_sz != (int)raw_sz) {
        printf("Decompression failed! Got %d, expected %u\n", decomp_sz, raw_sz);
        free(in_buf);
        free(raw_buf);
        return 1;
    }
    printf("Decompressed %u bytes successfully!\n", raw_sz);

    // Build DDS header (DX10 BC7_UNORM)
    uint8_t dds_hdr[148];
    memset(dds_hdr, 0, 148);
    dds_hdr[0] = 'D'; dds_hdr[1] = 'D'; dds_hdr[2] = 'S'; dds_hdr[3] = ' ';
    DDS_HEADER* dh = (DDS_HEADER*)(dds_hdr + 4);
    dh->size = 124;
    dh->flags = 0x00081007; // CAPS | HEIGHT | WIDTH | PIXELFORMAT | LINEARSIZE
    dh->height = 4096;
    dh->width = 4096;
    dh->pitchOrLinearSize = raw_sz;
    dh->depth = 1;
    dh->mipMapCount = 1;
    dh->ddspf.size = 32;
    dh->ddspf.flags = 0x00000004; // DDPF_FOURCC
    dh->ddspf.fourCC = 0x30315844; // 'DX10'
    dh->caps = 0x00001000; // DDSCAPS_TEXTURE

    DDS_HEADER_DXT10* d10 = (DDS_HEADER_DXT10*)(dds_hdr + 128);
    d10->dxgiFormat = 98; // DXGI_FORMAT_BC7_UNORM
    d10->resourceDimension = 3; // D3D10_RESOURCE_DIMENSION_TEXTURE2D
    d10->miscFlag = 0;
    d10->arraySize = 1;
    d10->miscFlags2 = 0;

    FILE* fout = fopen(out_path, "wb");
    if (!fout) {
        printf("Could not write %s\n", out_path);
        free(in_buf);
        free(raw_buf);
        return 1;
    }
    fwrite(dds_hdr, 1, 148, fout);
    fwrite(raw_buf, 1, raw_sz, fout);
    fclose(fout);

    printf("Wrote %s successfully!\n", out_path);
    free(in_buf);
    free(raw_buf);
    return 0;
}
