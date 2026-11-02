# validate_tags.py
# Tool for programmer to verify control tags (<cmd ...>, <color ...>, etc.) in CSV files

import os, re, csv

def check_csv(filepath):
    issues = []
    with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
        reader = csv.reader(f)
        for line_idx, row in enumerate(reader, start=1):
            text = ' | '.join(row)
            broken_cmds = re.findall(r'<cmd[^\s>][^>]*>', text)
            if broken_cmds:
                issues.append(f'Line {line_idx}: Broken cmd tag without space: {broken_cmds}')
            open_brackets = text.count('<')
            close_brackets = text.count('>')
            if open_brackets != close_brackets:
                issues.append(f'Line {line_idx}: Mismatched bracket count: < count={open_brackets}, > count={close_brackets}')
    return issues

if __name__ == '__main__':
    base_dir = os.path.dirname(os.path.abspath(__file__))
    parent_dir = os.path.dirname(base_dir)
    print('Scanning all subfolders for tag issues...')
    total_issues = 0
    for root, dirs, files in os.walk(parent_dir):
        for file in files:
            if file.endswith('.csv'):
                p = os.path.join(root, file)
                errs = check_csv(p)
                if errs:
                    print(f'\n[!] Issues in {os.path.relpath(p, parent_dir)}:')
                    for err in errs[:5]:
                        print('  -', err)
                    if len(errs) > 5:
                        print(f'  ... and {len(errs)-5} more')
                    total_issues += len(errs)
    print(f'\nScan complete. Total tag issues found: {total_issues}')
