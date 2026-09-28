import re

with open('src/text_dump.c', 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Clean lookup_translation
old_lookup_start = 'static const char* lookup_translation(const char* orig)\n{'
old_lookup_end = '    /* 3. Exact Match */\n    const char* rep = lookup_exact_translation(orig);'

new_lookup = '''static const char* lookup_translation(const char* orig)
{
    if (!orig || g_trans_count == 0) return NULL;

    /* 1. Exact Match */
    const char* rep = lookup_exact_translation(orig);'''

if old_lookup_start in content and old_lookup_end in content:
    idx_start = content.index(old_lookup_start)
    idx_end = content.index(old_lookup_end) + len(old_lookup_end)
    content = content[:idx_start] + new_lookup + content[idx_end:]
    print("Cleaned lookup_translation successfully.")
else:
    print("Could not find lookup_translation pattern!")

# 2. Clean check_default_name_screen
def_pattern = r'static const char\* check_default_name_screen\(const char\* str\)\s*\{.*?\n\}'
new_def = '''static const char* check_default_name_screen(const char* str)
{
    (void)str;
    return NULL;
}'''

content, count = re.subn(def_pattern, new_def, content, flags=re.DOTALL)
print(f"Cleaned check_default_name_screen: {count} occurrence(s).")

with open('src/text_dump.c', 'w', encoding='utf-8') as f:
    f.write(content)

print("Finished cleaning src/text_dump.c.")
