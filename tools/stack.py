# Checks that every patch stacks with every other, then builds qol.gba (TLE + all patches).
# Usage: uv run python stack.py a.ips b.ips ...   (run in the dir with tle.gba)
# If no two patches write the same byte, any subset in any order gives the same bytes.
import sys
from itertools import combinations
from ipslib import read_ips, apply_ips

paths = sys.argv[1:]
tle = open('tle.gba', 'rb').read()
spans = {p: [(o, o + len(b)) for o, b in read_ips(p)] for p in paths}
for p in paths:
    assert all(e <= len(tle) for _, e in spans[p]), f'{p} grows the ROM'
ok = True
for a, b in combinations(paths, 2):
    for s1, e1 in spans[a]:
        for s2, e2 in spans[b]:
            if s1 < e2 and s2 < e1:
                print(f'OVERLAP {a} [{s1:#x},{e1:#x}) vs {b} [{s2:#x},{e2:#x})'); ok = False
assert ok, 'patches overlap'
rom = tle
for p in paths:
    rom = apply_ips(rom, p)
rev = tle
for p in reversed(paths):
    rev = apply_ips(rev, p)
assert rom == rev
open('qol.gba', 'wb').write(rom)
print(f'{len(paths)} patches, no overlaps; wrote qol.gba')
