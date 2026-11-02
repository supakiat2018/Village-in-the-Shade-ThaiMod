# pua_converter.py
# Reference implementation for converting Normal Thai text to PUA text (and vice versa)
# with proper control tag (<cmd ...>, <color ...>) preservation.

import os, json, re

class PUAConverter:
    def __init__(self, mapping_path=None):
        if mapping_path is None:
            mapping_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'Mapping.json')
        with open(mapping_path, 'r', encoding='utf-8') as f:
            self.mapping = json.load(f)
        # Sort keys by length descending for Greedy Longest Match First
        self.sorted_keys = sorted(self.mapping.keys(), key=lambda x: len(x), reverse=True)
        # Reverse mapping (PUA -> Normal)
        self.rev_mapping = {v: k for k, v in self.mapping.items()}

    def to_pua(self, text: str) -> str:
        """Converts normal Thai text to PUA while strictly preserving control tags."""
        if not text:
            return text
        
        # Split text into tags and non-tags
        parts = re.split(r'(<[^>]+>)', text)
        result = []
        for part in parts:
            if part.startswith('<') and part.endswith('>'):
                # Control tag: keep 100% intact, do not touch spaces or content!
                result.append(part)
            else:
                # Text content: apply greedy longest match PUA mapping
                i = 0
                n = len(part)
                out_chars = []
                while i < n:
                    matched = False
                    for k in self.sorted_keys:
                        kl = len(k)
                        if i + kl <= n and part[i:i+kl] == k:
                            out_chars.append(self.mapping[k])
                            i += kl
                            matched = True
                            break
                    if not matched:
                        out_chars.append(part[i])
                        i += 1
                result.append(''.join(out_chars))
        return ''.join(result)

    def to_normal(self, pua_text: str) -> str:
        """Reverses PUA text back to normal Thai."""
        if not pua_text:
            return pua_text
        out = []
        for ch in pua_text:
            if ch in self.rev_mapping:
                out.append(self.rev_mapping[ch])
            else:
                out.append(ch)
        return ''.join(out)

if __name__ == '__main__':
    converter = PUAConverter()
    sample = 'ดัน<cmd CMD_UNIT_MOVE_STICK -offsetY -5>เพื่อวิ่งเคลื่อนที่'
    pua = converter.to_pua(sample)
    normal = converter.to_normal(pua)
    print('Sample Original:', sample)
    print('Sample PUA:     ', pua)
    print('Reversed:       ', normal)
    assert normal == sample, 'Reversal verification failed!'
    print('Verification SUCCESS!')
