# Ports the FoMT Proofread "grind reduction" tweaks to MFoMT + TLE v4.0.
# Input: tle.gba.  Output: tweaks.ips (relative to TLE).
import subprocess, struct, re
from ipslib import make_ips

LLVM = '/opt/homebrew/opt/llvm/bin'
BASE = 'tle.gba'
tle = open(BASE, 'rb').read()
rom = bytearray(tle)

def patch(off, old, new):
    assert rom[off:off+len(old)] == old, (hex(off), rom[off:off+len(old)], old)
    assert len(old) == len(new)
    rom[off:off+len(new)] = new

# ---------- 1. Vacation house: 100,000,000G -> 2,500,000G ----------
patch(0x108458, struct.pack('<I', 100_000_000), struct.pack('<I', 2_500_000))
patch(0x108264, b'100,000,000G', b'  2,500,000G')          # build menu text (column kept)

# ---------- 2. Mountain cottage: 50 years married -> 5 ----------
# script: push 5; push 0x278; op16; getvar(0x2A6) [21 3e]; push 50; cmp; jump  -- one block per spouse
blk = bytes.fromhex('2305237802 16 22a602 213e000000 2332 121b'.replace(' ', ''))
hits = [m.start() for m in re.finditer(re.escape(blk), rom)]
assert len(hits) == 8, [hex(h) for h in hits]
for h in hits:
    rom[h + len(blk) - 3] = 5            # the '32' after '23'

# dialog: "50th"/"50 years" -> "5th"/"5 years" (drop the 0, pad a space before the line break)
TEXT = [0x7a8a9d, 0x7a96a1, 0x7a96e2, 0x7aa318, 0x7aa38b, 0x7aafa4, 0x7aafef, 0x7abbb8,
        0x7e93e5, 0x7e965b, 0x7e9841]
for a in TEXT:
    assert rom[a:a+2] == b'50', hex(a)
    e = a + 2
    while rom[e] not in (0x0d, 0x05, 0x00): e += 1
    seg = bytes(rom[a+2:e])
    assert all(0x20 <= c < 0x7f for c in seg), (hex(a), seg)
    rom[a:e] = b'5' + seg + b' '


# ---------- 3. Mines: stairs down always visible ----------
# Floors with stairs up: stairs up directly above the player's arrival tile and stairs down
# directly below it. The generator returns the arrival tile (x, y bytes at sp+0x30) to its
# callers (0x080162aa/0x080166ac place the player there), so the hook rewrites it.
# Floor 0 (no stairs up): reveal the hidden stairs closest to the entrance.
# Hook the end of the floor generator (0x080A20BC). At 0x080A22D8 r6 = map struct,
# tiles at r6+4: 28x28 halfwords, 56 bytes/row. bits0-3 type (2 down, 3 up, 4 rock),
# byte1 bits2-7 buried item (1 = hidden stairs, 2 gold, 3 power berry ...).
# All of r1-r7 are restored by the generator's epilogue, so they're free here.
MINE_HOOK = 0x089DB000
MINE_SITE = 0x080A22D8
asm = f"""
.syntax unified
.thumb
.text
start:
    adds r1, r6, #4          @ tiles
    ldr  r2, =0x61e          @ last tile
    movs r4, #0              @ hidden-stairs count
    movs r5, #0
    mvns r5, r5              @ stairs-up offset = -1
    movs r7, #0
    mvns r7, r7              @ lowest hidden stairs on open ground = -1
scan:
    ldrb r3, [r1, r2]
    lsls r3, r3, #28
    lsrs r3, r3, #28
    cmp  r3, #3
    bne  1f
    adds r5, r2, #0
1:
    adds r2, #1
    ldrb r3, [r1, r2]
    subs r2, #1
    lsrs r3, r3, #2
    cmp  r3, #1
    bne  2f
    adds r4, #1
    cmp  r7, #0
    bge  2f                  @ scanning bottom-up: keep the first (closest to the entrance)
    ldrb r3, [r1, r2]
    lsls r3, r3, #28         @ open ground only (type 0)
    bne  2f
    adds r7, r2, #0
2:
    subs r2, #2
    bpl  scan
    cmp  r4, #0              @ no hidden stairs -> not a normal floor, leave it
    beq  orig
    cmp  r5, #0
    blt  reveal              @ no stairs up (floor 0: you walk in) -> reveal a real hidden stairs
    lsrs r3, r5, #1          @ tile index -> x (r3), y (r2)
    movs r2, #0
3:
    cmp  r3, #28
    blt  4f
    subs r3, #28
    adds r2, #1
    b    3b
4:
    ldr  r0, [r6]            @ room height by map type (0x080A2A40): 1 -> 28, 2 -> 14, else 6
    movs r4, #6
    cmp  r0, #1
    bne  6f
    movs r4, #28
6:
    cmp  r0, #2
    bne  7f
    movs r4, #14
7:
    subs r4, #3              @ last row the stairs up can use with two rows below it
    cmp  r2, r4
    ble  8f
    ldrb r0, [r1, r5]        @ too low: drop the old stairs up (type -> 0) and use row h-3
    lsrs r0, r0, #4
    lsls r0, r0, #4
    strb r0, [r1, r5]
    adds r2, r4, #0
8:
    movs r0, #56
    muls r0, r2, r0
    adds r5, r0, r3
    adds r5, r5, r3          @ (y*28 + x)*2
    movs r0, #3              @ stairs up at (x, y)
    strh r0, [r1, r5]
    adds r5, #56
    ldrh r0, [r1, r5]        @ player at (x, y+1): no rock, keep any buried item
    lsrs r0, r0, #10
    lsls r0, r0, #10
    strh r0, [r1, r5]
    adds r5, #56
    movs r0, #2              @ stairs down at (x, y+2)
    strh r0, [r1, r5]
    add  r0, sp, #0x30       @ spawn tile the generator returns to its caller
    strb r3, [r0]
    adds r2, #1
    strb r2, [r0, #1]
    b    clearhidden
reveal:
    cmp  r7, #0
    blt  orig
    adds r3, r7, #0
place:
    ldrh r2, [r1, r3]
    ldr  r4, =0x0300         @ keep bits 8-9 (preserved by the generator), drop item/type
    ands r2, r4
    adds r2, #2              @ stairs down
    strh r2, [r1, r3]
clearhidden:
    ldr  r2, =0x61f          @ remove hidden stairs (item 1) everywhere; keep other items
clear:
    ldrb r3, [r1, r2]
    lsrs r4, r3, #2
    cmp  r4, #1
    bne  5f
    movs r4, #3
    ands r3, r4
    strb r3, [r1, r2]
5:
    subs r2, #2
    bpl  clear
orig:
    ldr  r0, [sp, #0x30]     @ replaced instructions
    ldr  r1, [sp, #0x34]
    str  r0, [r1]
    ldr  r0, [sp, #0x34]
    ldr  r3, ={MINE_SITE + 8 + 1:#x}
    bx   r3
.ltorg
"""
open('mine.s', 'w').write(asm)
subprocess.run(['clang', '-target', 'armv4t-none-eabi', '-mthumb', '-c', 'mine.s', '-o', 'mine.o'], check=True)
subprocess.run([f'{LLVM}/llvm-objcopy', '-O', 'binary', '-j', '.text', 'mine.o', 'mine.bin'], check=True)
code = open('mine.bin', 'rb').read()
off = MINE_HOOK - 0x08000000
assert all(b == 0xFF for b in rom[off:off+len(code)])
rom[off:off+len(code)] = code
patch(MINE_SITE - 0x08000000, bytes.fromhex('0c980d9908600d98'),
      struct.pack('<HH', 0x4B00, 0x4718) + struct.pack('<I', MINE_HOOK | 1))

recs = make_ips(tle, rom, 'tweaks.ips')
print(f'mine hook {len(code)} bytes; cottage blocks {[hex(h) for h in hits]}; {len(recs)} IPS records')
