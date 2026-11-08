# Rare ore boost: Spring Mine rocks drop Gold, Mystrile, Orichalc, Adamantite and Mythic
# Stone about twice as often, and Lake Mine rocks drop the rarer jewels (Kappa Jewel,
# Pink Diamond, Alexandrite, Moon Stone, Sand Rose, Diamond, Emerald) about twice as
# often. Same floors as vanilla. Data only.
# Input: tle.gba.  Output: ores.ips (relative to TLE).
#
# Floor generator 0x080A20BC -> rock filler 0x080A22F0 (Spring Mine; 0x080A2688 is the
# Lake Mine). Each rock rolls rand&0xFF against the 10 weights of its row
# (0x0810CCE4 + row*10); past the total the rock is empty. The contents code goes into
# tile bits 4-9 and is the material id - 5. Codes (0x0810CCBC, u32 each):
#   0x0A ?, 0x20 ?, 0x0C junk, 0x0D copper, 0x0E silver, 0x0F gold, 0x10 mystrile,
#   0x11 orichalc, 0x12 adamantite, 0x17 mythic stone (always 0 here)
# The row comes from 0x080A25F8(floor), NOT 0x080A25A0 (that band is only used for the
# first pass, terrain/buried items via 0x0810CC70): 21 rows,
#   0-10 = floors 0-10 | 11 = 11-19 | 12 = 20 | 13 = 21-29 | 14 = 30 | 15 = 31-39 |
#   16 = 40 | 17 = 41-230 | 18 = special floors 60,102,123,152,155,171,190,202,222 |
#   19 = 231-254 | 20 = 255
# Vanilla: gold from floor 3, mystrile from 6, orichalc/adamantite from 10, mythic 1/256
# on rows 18-20. The new weights double gold..adamantite and mythic, making room from
# empty rocks, then junk, then copper/silver (never below half), then capping at 255.
from ipslib import make_ips

# Lake Mine (filler 0x080A2688): codes at 0x0810C914 (14 x u32), weights at 0x0810C94C
# (14 per row, 56 rows). Row = 0x080A2960(floor): floors 0-20 -> row = floor; 21-99 ->
# 20+rand(10); 100-199 -> 32+rand(10); 200-250 -> 43+rand(10); 251-254 -> 54; 255 -> 55;
# special floors -> 30 (30,70,90), 31 (40,60,80), 32 (50,100,150,200),
# 42 (110,130,170,190), 43 (120,140,160,180).
# Codes (material - 5): 0x21 Kappa Jewel, 0x0C junk, 0x15 Pink Diamond, 0x16 Alexandrite,
# 0x13 Moon Stone, 0x14 Sand Rose, 0x18 Diamond, 0x19 Emerald, then Ruby, Topaz, Peridot,
# Fluorite, Agate, Amethyst. Many vanilla rows already sum past 256, so the last
# (cheap) gems are partly unreachable; the roll walks the list in order.
LAKE_CODES, LAKE_TABLE, LAKE_ROWS = 0x10C914, 0x10C94C, 56
LAKE_RARE = (0, 2, 3, 4, 5, 6, 7)
LAKE_JUNK = 1

def lake_row(w):
    w2 = list(w)
    for i in LAKE_RARE: w2[i] = min(255, w[i] * 2)
    added = sum(w2) - sum(w)
    room = max(0, 256 - sum(w))                 # empty rocks absorb this first
    cut = min(w2[LAKE_JUNK], max(0, added - room))
    w2[LAKE_JUNK] -= cut                        # then junk; any rest trims the cheap gems at the end
    return w2

TABLE = 0x10CCE4
BANDS = 21
def new_band(w):
    w = list(w)
    J, RARE = 2, (5, 6, 7, 8, 9)   # indices: 2 junk, 3 copper, 4 silver, 5-8 gold..adamantite, 9 mythic
    w2 = w[:]
    for i in RARE: w2[i] = w[i] * 2
    over = sum(w2) - 255                       # empty rocks absorb up to (255 - sum)
    if over > 0:
        cut = min(w2[J], over); w2[J] -= cut; over -= cut
    if over > 0:                               # copper/silver down to half, proportionally
        room = sum(w[i] - w[i] // 2 for i in (3, 4))
        take = min(room, over)
        for i in (3, 4):
            share = (w[i] - w[i] // 2) * take // room if room else 0
            w2[i] -= share
        over = sum(w2) - 255
    if over > 0:                               # finally scale gold..adamantite to fit (mythic keeps x2)
        main = (5, 6, 7, 8)
        rare = sum(w2[i] for i in main); keep = rare - over
        for i in main: w2[i] = w2[i] * keep // rare
    assert sum(w2) <= 255 and all(0 <= x <= 255 for x in w2)
    return w2

tle = open('tle.gba', 'rb').read()
rom = bytearray(tle)
assert rom[0x10CCBC:0x10CCBC+40:4] == bytes([0x0A, 0x20, 0x0C, 0x0D, 0x0E, 0x0F, 0x10, 0x11, 0x12, 0x17])
for b in range(BANDS):
    o = TABLE + b * 10
    old = rom[o:o+10]
    new = new_band(old)
    assert new[0] == old[0] and new[1] == old[1]          # codes 0x0A / 0x20 (unknown) untouched
    rom[o:o+10] = bytes(new)

assert rom[LAKE_CODES:LAKE_CODES+56:4] == bytes([0x21, 0x0C, 0x15, 0x16, 0x13, 0x14, 0x18, 0x19,
                                                  0x1A, 0x1B, 0x1C, 0x1D, 0x1E, 0x1F])
for b in range(LAKE_ROWS):
    o = LAKE_TABLE + b * 14
    rom[o:o+14] = bytes(lake_row(rom[o:o+14]))

recs = make_ips(tle, rom, 'ores.ips')
print(f'{len(recs)} IPS records')
