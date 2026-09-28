import sys
sys.path.append('C:/Users/Supakiat/Desktop/Village_in_the_Shade_ThaiMod_Dev/scripts')
import test_fad

# Also check special alt filenames from original g_fad_subfiles
special_alts = {
    'タイトル白.nltx': 'title_white.nltx',
    'ui_1000_title01.nltx': 'ui_1000_タイトル01.nltx',
}

print("static const FadMappingDef g_fad_mapping_defs[] = {")
for k in sorted(test_fad.mapping_dict.keys()):
    fn, w, h = test_fad.mapping_dict[k]
    alt = special_alts.get(fn, fn.replace('.nltx', '_thai.nltx'))
    print(f'    {{ {k:3d}, "{fn}", "{alt}", {w}, {h} }},')
print("};")
