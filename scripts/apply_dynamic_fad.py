import os, sys

c_file = r'C:\Users\Supakiat\Desktop\Village-in-the-Shade-ThaiMod\src\text_dump.c'
dev_c_file = r'C:\Users\Supakiat\Desktop\Village_in_the_Shade_ThaiMod_Dev\src\text_dump.c'

with open(c_file, 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Define replacement for lines 869-1090
old_start_marker = "/* ==================================================================\n * FAD Container Sub-File Mapping (fairy_1_00.dat / resident_lang_jp.fad)\n * ================================================================== */"
old_end_marker = "static const FadSubFile* lookup_fad_subfile(uint64_t offset)\n{\n    for (size_t i = 0; i < sizeof(g_fad_subfiles) / sizeof(g_fad_subfiles[0]); i++) {\n        if (g_fad_subfiles[i].offset == offset) {\n            return &g_fad_subfiles[i];\n        }\n    }\n    return NULL;\n}"

if old_start_marker not in content:
    print("ERROR: old_start_marker not found!")
    sys.exit(1)

if old_end_marker not in content:
    print("ERROR: old_end_marker not found!")
    sys.exit(1)

start_idx = content.find(old_start_marker)
end_idx = content.find(old_end_marker) + len(old_end_marker)

new_fad_section = """/* ==================================================================
 * FAD Container Dynamic Resolution & Sub-File Mapping
 * ================================================================== */
typedef struct {
    int toc_index;
    const char* filename;
    const char* alt_filename;
    uint16_t width;
    uint16_t height;
} FadMappingDef;

static const FadMappingDef g_fad_mapping_defs[] = {
    {   0, "ui_0020_カレンダー.nltx", "ui_0020_カレンダー_thai.nltx", 1024, 1024 },
    {  10, "ui_0070_buttonicon_text.nltx", "ui_0070_buttonicon_text_thai.nltx", 512, 256 },
    {  22, "ui_1070_メッセージポップアップtext0.nltx", "ui_1070_メッセージポップアップtext0_thai.nltx", 512, 128 },
    {  23, "04_掟の張り紙A.nltx", "04_掟の張り紙A_thai.nltx", 2200, 1300 },
    {  26, "ui_2030_詳細ポップアップ.nltx", "ui_2030_詳細ポップアップ_thai.nltx", 512, 512 },
    {  27, "ui_1153_ウィンドウ.nltx", "ui_1153_ウィンドウ_thai.nltx", 1024, 1024 },
    {  34, "ui_0010_itemcategory.nltx", "ui_0010_itemcategory_thai.nltx", 512, 1024 },
    {  36, "ui_5090_掲示板.nltx", "ui_5090_掲示板_thai.nltx", 2048, 2048 },
    {  38, "ui_9000_01.nltx", "ui_9000_01_thai.nltx", 1024, 2048 },
    {  40, "ui_0060_Charaname24pxB.nltx", "ui_0060_Charaname24pxB_thai.nltx", 1024, 512 },
    {  47, "ui_0010_nameplate.nltx", "ui_0010_nameplate_thai.nltx", 512, 512 },
    {  49, "ui_9000_02.nltx", "ui_9000_02_thai.nltx", 1024, 2048 },
    {  51, "ui_0010_itemcategory03.nltx", "ui_0010_itemcategory03_thai.nltx", 256, 512 },
    {  94, "タイトル白.nltx", "title_white.nltx", 2048, 1280 },
    { 101, "名前_steam版_04.nltx", "名前_steam版_04_thai.nltx", 1024, 2048 },
    { 105, "ui_5080_00.nltx", "ui_5080_00_thai.nltx", 2048, 2048 },
    { 112, "ui_5100_bandolPU01.nltx", "ui_5100_bandolPU01_thai.nltx", 256, 256 },
    { 117, "ui_1170_投げ銭_text.nltx", "ui_1170_投げ銭_text_thai.nltx", 256, 128 },
    { 119, "ui_0120_汎用テキスト01.nltx", "ui_0120_汎用テキスト01_thai.nltx", 512, 256 },
    { 120, "ui_5010_チラシ01.nltx", "ui_5010_チラシ01_thai.nltx", 1024, 1024 },
    { 121, "ui_5010_チラシ02.nltx", "ui_5010_チラシ02_thai.nltx", 1024, 1024 },
    { 122, "ui_5010_チラシ03.nltx", "ui_5010_チラシ03_thai.nltx", 1024, 1024 },
    { 123, "ui_5010_チラシ04.nltx", "ui_5010_チラシ04_thai.nltx", 1024, 1024 },
    { 124, "ui_5010_チラシ05.nltx", "ui_5010_チラシ05_thai.nltx", 1024, 1024 },
    { 125, "ui_5010_チラシ06.nltx", "ui_5010_チラシ06_thai.nltx", 1024, 1024 },
    { 126, "ui_5010_チラシ07.nltx", "ui_5010_チラシ07_thai.nltx", 1024, 1024 },
    { 127, "ui_5010_チラシ08.nltx", "ui_5010_チラシ08_thai.nltx", 1024, 1024 },
    { 128, "ui_5010_チラシ09.nltx", "ui_5010_チラシ09_thai.nltx", 1024, 1024 },
    { 129, "ui_5010_チラシ10.nltx", "ui_5010_チラシ10_thai.nltx", 1024, 1024 },
    { 130, "ui_5010_チラシ11.nltx", "ui_5010_チラシ11_thai.nltx", 1024, 1024 },
    { 131, "ui_5010_チラシ12.nltx", "ui_5010_チラシ12_thai.nltx", 1024, 1024 },
    { 132, "ui_5010_チラシ13.nltx", "ui_5010_チラシ13_thai.nltx", 1024, 1024 },
    { 133, "ui_5010_チラシ14.nltx", "ui_5010_チラシ14_thai.nltx", 1024, 1024 },
    { 134, "ui_5010_チラシ15.nltx", "ui_5010_チラシ15_thai.nltx", 1024, 1024 },
    { 135, "ui_5010_チラシ16.nltx", "ui_5010_チラシ16_thai.nltx", 1024, 1024 },
    { 136, "ui_5010_チラシ17.nltx", "ui_5010_チラシ17_thai.nltx", 1024, 1024 },
    { 137, "ui_5010_チラシ18.nltx", "ui_5010_チラシ18_thai.nltx", 1024, 1024 },
    { 138, "ui_5010_チラシ19.nltx", "ui_5010_チラシ19_thai.nltx", 1024, 1024 },
    { 139, "ui_5010_チラシ20.nltx", "ui_5010_チラシ20_thai.nltx", 1024, 1024 },
    { 140, "ui_5010_チラシ30.nltx", "ui_5010_チラシ30_thai.nltx", 1024, 1024 },
    { 141, "ui_5010_チラシ31.nltx", "ui_5010_チラシ31_thai.nltx", 1024, 1024 },
    { 142, "ui_5010_チラシ32.nltx", "ui_5010_チラシ32_thai.nltx", 1024, 1024 },
    { 143, "ui_5010_チラシ33.nltx", "ui_5010_チラシ33_thai.nltx", 1024, 1024 },
    { 144, "ui_5010_チラシ34.nltx", "ui_5010_チラシ34_thai.nltx", 1024, 1024 },
    { 145, "ui_5010_チラシ35.nltx", "ui_5010_チラシ35_thai.nltx", 1024, 1024 },
    { 146, "ui_5010_チラシ36.nltx", "ui_5010_チラシ36_thai.nltx", 1024, 1024 },
    { 168, "鐘.nltx", "鐘_thai.nltx", 2200, 1300 },
    { 171, "ui_3440_00.nltx", "ui_3440_00_thai.nltx", 4096, 2048 },
    { 187, "ui_5010_項目02.nltx", "ui_5010_項目02_thai.nltx", 256, 1024 },
    { 189, "ui_5060_家畜一覧_01.nltx", "ui_5060_家畜一覧_01_thai.nltx", 2048, 2048 },
    { 191, "ui_0010_itemcategory2.nltx", "ui_0010_itemcategory2_thai.nltx", 1024, 256 },
    { 195, "ui_2220_post03.nltx", "ui_2220_post03_thai.nltx", 512, 1024 },
    { 196, "ui_2220_post01.nltx", "ui_2220_post01_thai.nltx", 2048, 2048 },
    { 199, "ui_0990_初回起動時ポエム.nltx", "ui_0990_初回起動時ポエム_thai.nltx", 1024, 512 },
    { 205, "ui_1000_title01.nltx", "ui_1000_タイトル01.nltx", 2048, 512 },
    { 206, "ui_0990_localize_00.nltx", "ui_0990_localize_00_thai.nltx", 1024, 512 },
    { 207, "ui_1000_02.nltx", "ui_1000_02_thai.nltx", 2048, 256 },
    { 218, "ui_2100_00.nltx", "ui_2100_00_thai.nltx", 256, 256 },
    { 226, "ene_3020_1_02.nltx", "ene_3020_1_02_thai.nltx", 512, 256 },
    { 231, "bg_8080_00_tex.nltx", "bg_8080_00_tex_thai.nltx", 512, 256 },
    { 232, "bg_8080_04_tex.nltx", "bg_8080_04_tex_thai.nltx", 1024, 2048 },
    { 233, "bg_8080_01_tex.nltx", "bg_8080_01_tex_thai.nltx", 2048, 256 },
    { 313, "ui_2210_日リザルト02.nltx", "ui_2210_日リザルト02_thai.nltx", 1024, 256 },
    { 318, "ui_0030_汎用アイコン_はんこ.nltx", "ui_0030_汎用アイコン_はんこ_thai.nltx", 1024, 512 },
    { 341, "ui_2020_コックピット_text.nltx", "ui_2020_コックピット_text_thai.nltx", 512, 256 },
    { 342, "ui_3030_家具配置01.nltx", "ui_3030_家具配置01_thai.nltx", 2048, 512 },
};

typedef struct {
    uint64_t offset;          /* Offset in fairy_1_00.dat */
    const char* filename;      /* Canonical filename, e.g. "ui_1000_title01.nltx" */
    const char* alt_filename;  /* Alt filename, e.g. "ui_1000_title01_thai.nltx" */
    uint16_t width;
    uint16_t height;
    BOOL has_fad_descriptor;  /* TRUE if offset is at 32-byte FAD descriptor */
} FadSubFile;

#define MAX_FAD_RUNTIME_SUBFILES 256
static FadSubFile g_fad_runtime_subfiles[MAX_FAD_RUNTIME_SUBFILES];
static int g_fad_runtime_count = 0;
static uint64_t g_fad_base_offset = 0;
static BOOL g_fad_resolved = FALSE;

static void resolve_dynamic_fad_offsets_w(const wchar_t* fairy_path_w)
{
    if (g_fad_resolved) return;

    uint64_t resident_lang_jp_offset = 0;
    for (int i = 0; i < g_vfs_count; i++) {
        if (g_vfs[i].archive_id == 4 && strstr(g_vfs[i].name, "resident_lang_jp.fad") != NULL) {
            resident_lang_jp_offset = g_vfs[i].offset;
            break;
        }
    }

    FILE* f = _wfopen(fairy_path_w, L"rb");
    if (!f) {
        log_msg("[FAD RESOLVER] Cannot open fairy_1_00.dat: %ls", fairy_path_w);
        return;
    }

    if (resident_lang_jp_offset == 0) {
        FAFULLFS_Header hdr;
        if (fread(&hdr, 1, sizeof(hdr), f) == sizeof(hdr) && memcmp(hdr.magic, "FAFULLFS", 8) == 0) {
            FAFULLFS_TocEntry* tocs = (FAFULLFS_TocEntry*)malloc(hdr.count * sizeof(FAFULLFS_TocEntry));
            char* str_table = (char*)malloc(hdr.str_len);
            if (tocs && str_table) {
                _fseeki64(f, (int64_t)hdr.toc_off, SEEK_SET);
                fread(tocs, sizeof(FAFULLFS_TocEntry), hdr.count, f);

                _fseeki64(f, (int64_t)hdr.str_off, SEEK_SET);
                fread(str_table, 1, hdr.str_len, f);

                for (uint32_t i = 0; i < hdr.count; i++) {
                    uint64_t n_off = tocs[i].name_off;
                    if (n_off < hdr.str_len) {
                        const char* name = str_table + n_off;
                        if (strstr(name, "resident_lang_jp.fad") != NULL) {
                            resident_lang_jp_offset = tocs[i].offset;
                            break;
                        }
                    }
                }
            }
            if (tocs) free(tocs);
            if (str_table) free(str_table);
        }
    }

    if (resident_lang_jp_offset == 0) {
        log_msg("[FAD RESOLVER] resident_lang_jp.fad not found in %ls TOC", fairy_path_w);
        fclose(f);
        return;
    }

    g_fad_base_offset = resident_lang_jp_offset;
    log_msg("[FAD RESOLVER] Detected resident_lang_jp.fad base offset: 0x%llX", (unsigned long long)g_fad_base_offset);

    /* Read FAD TOC (16 KB header) */
    uint8_t fad_hdr[0x4000];
    _fseeki64(f, (int64_t)g_fad_base_offset, SEEK_SET);
    size_t nread = fread(fad_hdr, 1, sizeof(fad_hdr), f);
    fclose(f);

    if (nread < 0x4000) {
        log_msg("[FAD RESOLVER] Failed to read FAD header (read %zu bytes)", nread);
        return;
    }

    EnterCriticalSection(&g_cs);
    g_fad_runtime_count = 0;
    size_t num_defs = sizeof(g_fad_mapping_defs) / sizeof(g_fad_mapping_defs[0]);

    for (size_t i = 0; i < num_defs; i++) {
        int idx = g_fad_mapping_defs[i].toc_index;
        size_t pos = 0x1018 + (size_t)idx * 32;
        if (pos + 12 > sizeof(fad_hdr)) continue;

        uint64_t entry_sz = *(uint64_t*)(fad_hdr + pos + 0);
        uint32_t rel_off = *(uint32_t*)(fad_hdr + pos + 8);
        if (entry_sz == 0 && rel_off == 0) continue;

        uint64_t desc_off = g_fad_base_offset + (uint64_t)rel_off + 32;
        uint64_t data_off = g_fad_base_offset + (uint64_t)rel_off + 64;

        if (g_fad_runtime_count + 2 <= MAX_FAD_RUNTIME_SUBFILES) {
            /* Descriptor entry */
            FadSubFile* e1 = &g_fad_runtime_subfiles[g_fad_runtime_count++];
            e1->offset = desc_off;
            e1->filename = g_fad_mapping_defs[i].filename;
            e1->alt_filename = g_fad_mapping_defs[i].alt_filename;
            e1->width = g_fad_mapping_defs[i].width;
            e1->height = g_fad_mapping_defs[i].height;
            e1->has_fad_descriptor = TRUE;

            /* Data entry */
            FadSubFile* e2 = &g_fad_runtime_subfiles[g_fad_runtime_count++];
            e2->offset = data_off;
            e2->filename = g_fad_mapping_defs[i].filename;
            e2->alt_filename = g_fad_mapping_defs[i].alt_filename;
            e2->width = g_fad_mapping_defs[i].width;
            e2->height = g_fad_mapping_defs[i].height;
            e2->has_fad_descriptor = FALSE;
        }
    }

    g_fad_resolved = TRUE;
    LeaveCriticalSection(&g_cs);

    log_msg("[FAD RESOLVER] Dynamic resolution complete: %d subfile targets mapped in RAM (base=0x%llX)!",
            g_fad_runtime_count, (unsigned long long)g_fad_base_offset);
}

static const FadSubFile* lookup_fad_subfile(uint64_t offset)
{
    for (int i = 0; i < g_fad_runtime_count; i++) {
        if (g_fad_runtime_subfiles[i].offset == offset) {
            return &g_fad_runtime_subfiles[i];
        }
    }
    return NULL;
}"""

content = content[:start_idx] + new_fad_section + content[end_idx:]

# 2. Update hk_CreateFileW for fairy_1_00.dat dynamic resolution
create_file_w_marker = 'if (wcsstr(lower, L"data") || wcsstr(lower, L".dat") || wcsstr(lower, L".fad") || wcsstr(lower, L".nltx")) {\n            log_file_access("[OPEN_FILE] %ls", lpFileName);\n        }'
create_file_w_repl = '''if (wcsstr(lower, L"data") || wcsstr(lower, L".dat") || wcsstr(lower, L".fad") || wcsstr(lower, L".nltx")) {
            log_file_access("[OPEN_FILE] %ls", lpFileName);
        }

        if (wcsstr(lower, L"fairy_1_00.dat")) {
            if (!g_fad_resolved) {
                resolve_dynamic_fad_offsets_w(lpFileName);
            }
        }'''

if create_file_w_marker not in content:
    print("ERROR: create_file_w_marker not found!")
    sys.exit(1)

content = content.replace(create_file_w_marker, create_file_w_repl, 1)

# 3. Update hk_ReadFile: FAD TOC patch logic
read_file_target = '''    /* 1b. Check if the game is reading the FAD Header/TOC for resident_lang_jp.fad */
    if (arch_id == 4 && offset == 0x42590C00ULL && nNumberOfBytesToRead >= 0x4000) {
        BOOL res = fp_original_ReadFile(hFile, lpBuffer, nNumberOfBytesToRead, lpNumberOfBytesRead, lpOverlapped);
        if (!res && GetLastError() == ERROR_IO_PENDING && lpOverlapped) {
            DWORD transferred = 0;
            if (GetOverlappedResult(hFile, lpOverlapped, &transferred, TRUE)) {
                res = TRUE;
                if (lpNumberOfBytesRead) *lpNumberOfBytesRead = transferred;
                if (lpOverlapped->hEvent) {
                    SetEvent(lpOverlapped->hEvent);
                }
            }
        }
        if (res && lpBuffer) {
            int patched = 0;
            size_t fad_sub_count = sizeof(g_fad_subfiles) / sizeof(g_fad_subfiles[0]);
            for (size_t i = 0; i < fad_sub_count; i++) {
                if (!g_fad_subfiles[i].has_fad_descriptor) continue;

                wchar_t override_path_w[MAX_PATH];
                long ext_size = 0;
                BOOL found = find_override_file_w(g_fad_subfiles[i].filename, override_path_w, MAX_PATH, &ext_size);
                if (!found && g_fad_subfiles[i].alt_filename) {
                    found = find_override_file_w(g_fad_subfiles[i].alt_filename, override_path_w, MAX_PATH, &ext_size);
                }

                if (found && ext_size > 0) {
                    uint32_t target_rel_off = (uint32_t)(g_fad_subfiles[i].offset - 0x42590C00ULL - 32);

                    /* Walk FAD entry table in lpBuffer between 0x1018 and 0x3B00 in 32-byte strides */
                    for (size_t pos = 0x1018; pos + 32 <= nNumberOfBytesToRead && pos < 0x4000; pos += 32) {
                        uint32_t entry_off = *(uint32_t*)((char*)lpBuffer + pos + 8);
                        if (entry_off == target_rel_off) {
                            uint64_t* p_sz = (uint64_t*)((char*)lpBuffer + pos + 0);
                            /* Needed entry size in table: ext_size + 64 bytes (aligned to 64 bytes) */
                            uint64_t needed_sz = ((uint64_t)ext_size + 64 + 63) & ~63ULL;
                            if (needed_sz > *p_sz) {
                                log_msg("[VFS FAD TOC Patch] Expanding size for [%s]: %llu -> %llu bytes (rel_off=0x%X at TOC+0x%X)",
                                        g_fad_subfiles[i].filename, *p_sz, needed_sz, target_rel_off, (unsigned int)pos);
                                *p_sz = needed_sz;
                                patched++;
                            }
                            break;
                        }
                    }
                }
            }
            if (patched > 0) {
                log_msg("[VFS FAD TOC Patch] Successfully patched %d / 65 FAD TOC entries in RAM!", patched);
            }
        }
        return res;
    }'''

read_file_repl = '''    /* 1b. Check if the game is reading the FAD Header/TOC for resident_lang_jp.fad */
    if (arch_id == 4 && g_fad_base_offset != 0 && offset == g_fad_base_offset && nNumberOfBytesToRead >= 0x4000) {
        BOOL res = fp_original_ReadFile(hFile, lpBuffer, nNumberOfBytesToRead, lpNumberOfBytesRead, lpOverlapped);
        if (!res && GetLastError() == ERROR_IO_PENDING && lpOverlapped) {
            DWORD transferred = 0;
            if (GetOverlappedResult(hFile, lpOverlapped, &transferred, TRUE)) {
                res = TRUE;
                if (lpNumberOfBytesRead) *lpNumberOfBytesRead = transferred;
                if (lpOverlapped->hEvent) {
                    SetEvent(lpOverlapped->hEvent);
                }
            }
        }
        if (res && lpBuffer) {
            int patched = 0;
            size_t fad_sub_count = (size_t)g_fad_runtime_count;
            for (size_t i = 0; i < fad_sub_count; i++) {
                if (!g_fad_runtime_subfiles[i].has_fad_descriptor) continue;

                wchar_t override_path_w[MAX_PATH];
                long ext_size = 0;
                BOOL found = find_override_file_w(g_fad_runtime_subfiles[i].filename, override_path_w, MAX_PATH, &ext_size);
                if (!found && g_fad_runtime_subfiles[i].alt_filename) {
                    found = find_override_file_w(g_fad_runtime_subfiles[i].alt_filename, override_path_w, MAX_PATH, &ext_size);
                }

                if (found && ext_size > 0) {
                    uint32_t target_rel_off = (uint32_t)(g_fad_runtime_subfiles[i].offset - g_fad_base_offset - 32);

                    /* Walk FAD entry table in lpBuffer between 0x1018 and 0x3B00 in 32-byte strides */
                    for (size_t pos = 0x1018; pos + 32 <= nNumberOfBytesToRead && pos < 0x4000; pos += 32) {
                        uint32_t entry_off = *(uint32_t*)((char*)lpBuffer + pos + 8);
                        if (entry_off == target_rel_off) {
                            uint64_t* p_sz = (uint64_t*)((char*)lpBuffer + pos + 0);
                            /* Needed entry size in table: ext_size + 64 bytes (aligned to 64 bytes) */
                            uint64_t needed_sz = ((uint64_t)ext_size + 64 + 63) & ~63ULL;
                            if (needed_sz > *p_sz) {
                                log_msg("[VFS FAD TOC Patch] Expanding size for [%s]: %llu -> %llu bytes (rel_off=0x%X at TOC+0x%X)",
                                        g_fad_runtime_subfiles[i].filename, *p_sz, needed_sz, target_rel_off, (unsigned int)pos);
                                *p_sz = needed_sz;
                                patched++;
                            }
                            break;
                        }
                    }
                }
            }
            if (patched > 0) {
                log_msg("[VFS FAD TOC Patch] Successfully patched %d / %d FAD TOC entries in RAM!",
                        patched, (int)(g_fad_runtime_count / 2));
            }
        }
        return res;
    }'''

if read_file_target not in content:
    print("ERROR: read_file_target not found!")
    sys.exit(1)

content = content.replace(read_file_target, read_file_repl, 1)

# 4. Update init section to call resolve_dynamic_fad_offsets_w
init_target = '''    load_archive_toc_w(tex_path_w, 3);
    load_archive_toc_w(fairy_path_w, 4);
    log_msg("[VFS] Total files indexed for redirection: %d", g_vfs_count);'''

init_repl = '''    load_archive_toc_w(tex_path_w, 3);
    load_archive_toc_w(fairy_path_w, 4);
    log_msg("[VFS] Total files indexed for redirection: %d", g_vfs_count);

    /* Dynamically resolve FAD sub-file offsets across all game versions */
    resolve_dynamic_fad_offsets_w(fairy_path_w);'''

if init_target not in content:
    print("ERROR: init_target not found!")
    sys.exit(1)

content = content.replace(init_target, init_repl, 1)

with open(c_file, 'w', encoding='utf-8') as f:
    f.write(content)

with open(dev_c_file, 'w', encoding='utf-8') as f:
    f.write(content)

print("[SUCCESS] Successfully updated text_dump.c in both repositories!")
