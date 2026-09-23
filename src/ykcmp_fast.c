#include <stdint.h>
#include <stdlib.h>
#include <string.h>

__declspec(dllexport) int decompress_ykcmp_type4_c(
    const uint8_t* payload, uint32_t src_len,
    uint8_t* dst, uint32_t uncomp_sz
) {
    uint32_t src_idx = 0;
    uint32_t dst_len = 0;
    while (src_idx < src_len && dst_len < uncomp_sz) {
        uint8_t b = payload[src_idx++];
        if ((b & 0x80) == 0) {
            uint32_t length = b;
            for (uint32_t i = 0; i < length && src_idx < src_len && dst_len < uncomp_sz; i++) {
                dst[dst_len++] = payload[src_idx++];
            }
        } else if ((b & 0x40) == 0) {
            uint32_t length = ((b >> 4) & 3) + 1;
            uint32_t offset = (b & 0x0F) + 1;
            for (uint32_t i = 0; i < length && dst_len < uncomp_sz; i++) {
                dst[dst_len] = (offset <= dst_len) ? dst[dst_len - offset] : 0;
                dst_len++;
            }
        } else if ((b & 0x20) == 0) {
            uint32_t length = (b & 0x1F) + 2;
            if (src_idx < src_len) {
                uint8_t b1 = payload[src_idx++];
                uint32_t offset = b1 + 1;
                for (uint32_t i = 0; i < length && dst_len < uncomp_sz; i++) {
                    dst[dst_len] = (offset <= dst_len) ? dst[dst_len - offset] : 0;
                    dst_len++;
                }
            }
        } else {
            if (src_idx + 1 < src_len) {
                uint8_t b1 = payload[src_idx++];
                uint8_t b2 = payload[src_idx++];
                uint32_t length = (((b & 0x1F) << 4) | (b1 >> 4)) + 3;
                uint32_t offset = (((b1 & 0x0F) << 8) | b2) + 1;
                for (uint32_t i = 0; i < length && dst_len < uncomp_sz; i++) {
                    dst[dst_len] = (offset <= dst_len) ? dst[dst_len - offset] : 0;
                    dst_len++;
                }
            }
        }
    }
    return (int)dst_len;
}

/* Fast hash table for LZSS match finding */
#define HASH_BITS 16
#define HASH_SIZE (1 << HASH_BITS)
#define HASH_MASK (HASH_SIZE - 1)

static inline uint32_t hash3(const uint8_t* p) {
    return ((uint32_t)p[0] << 10 ^ (uint32_t)p[1] << 5 ^ (uint32_t)p[2]) & HASH_MASK;
}

__declspec(dllexport) int compress_ykcmp_type4_c(
    const uint8_t* src, uint32_t src_len,
    uint8_t* dst, uint32_t dst_max
) {
    int32_t head[HASH_SIZE];
    int32_t prev[65536]; /* ring buffer of previous positions for offsets <= 4096 */
    memset(head, -1, sizeof(head));

    uint32_t in_pos = 0;
    uint32_t out_pos = 0;
    uint32_t lit_start = 0;

    while (in_pos < src_len) {
        /* Find longest match */
        uint32_t best_len = 0;
        uint32_t best_off = 0;

        if (in_pos + 3 <= src_len) {
            uint32_t h = hash3(src + in_pos);
            int32_t cur = head[h];
            int chain_len = 64;

            while (cur != -1 && chain_len-- > 0) {
                uint32_t off = in_pos - cur;
                if (off > 4096) break;

                /* Check match length */
                uint32_t max_m = src_len - in_pos;
                if (max_m > 515) max_m = 515;

                uint32_t m = 0;
                while (m < max_m && src[cur + m] == src[in_pos + m]) {
                    m++;
                }

                if (m > best_len) {
                    /* Only accept if beneficial */
                    if (off <= 16 && m >= 2) {
                        best_len = (m > 4) ? 4 : m;
                        best_off = off;
                    } else if (off <= 256 && m >= 2) {
                        best_len = (m > 33) ? 33 : m;
                        best_off = off;
                    } else if (m >= 3) {
                        best_len = m;
                        best_off = off;
                    }
                    if (best_len == 515) break;
                }

                cur = prev[cur & 0xFFFF];
            }
        }

        if (best_len >= 2) {
            /* Flush any pending literals */
            while (lit_start < in_pos) {
                uint32_t lit_len = in_pos - lit_start;
                if (lit_len > 127) lit_len = 127;
                if (out_pos + 1 + lit_len > dst_max) return -1;
                dst[out_pos++] = (uint8_t)lit_len;
                memcpy(dst + out_pos, src + lit_start, lit_len);
                out_pos += lit_len;
                lit_start += lit_len;
            }

            /* Emit match */
            if (best_off <= 16 && best_len <= 4) {
                if (out_pos + 1 > dst_max) return -1;
                dst[out_pos++] = 0x80 | ((best_len - 1) << 4) | (best_off - 1);
            } else if (best_off <= 256 && best_len <= 33) {
                if (out_pos + 2 > dst_max) return -1;
                dst[out_pos++] = 0xC0 | (best_len - 2);
                dst[out_pos++] = (uint8_t)(best_off - 1);
            } else {
                if (out_pos + 3 > dst_max) return -1;
                uint32_t l = best_len - 3;
                uint32_t o = best_off - 1;
                dst[out_pos++] = 0xE0 | ((l >> 4) & 0x1F);
                dst[out_pos++] = ((l & 0x0F) << 4) | ((o >> 8) & 0x0F);
                dst[out_pos++] = (uint8_t)(o & 0xFF);
            }

            /* Advance positions and update hash */
            for (uint32_t k = 0; k < best_len; k++) {
                if (in_pos + 3 <= src_len) {
                    uint32_t h = hash3(src + in_pos);
                    prev[in_pos & 0xFFFF] = head[h];
                    head[h] = (int32_t)in_pos;
                }
                in_pos++;
            }
            lit_start = in_pos;
        } else {
            /* Literal: update hash and advance */
            if (in_pos + 3 <= src_len) {
                uint32_t h = hash3(src + in_pos);
                prev[in_pos & 0xFFFF] = head[h];
                head[h] = (int32_t)in_pos;
            }
            in_pos++;

            if (in_pos - lit_start >= 127) {
                if (out_pos + 128 > dst_max) return -1;
                dst[out_pos++] = 127;
                memcpy(dst + out_pos, src + lit_start, 127);
                out_pos += 127;
                lit_start = in_pos;
            }
        }
    }

    /* Flush trailing literals */
    while (lit_start < in_pos) {
        uint32_t lit_len = in_pos - lit_start;
        if (lit_len > 127) lit_len = 127;
        if (out_pos + 1 + lit_len > dst_max) return -1;
        dst[out_pos++] = (uint8_t)lit_len;
        memcpy(dst + out_pos, src + lit_start, lit_len);
        out_pos += lit_len;
        lit_start += lit_len;
    }

    return (int)out_pos;
}
