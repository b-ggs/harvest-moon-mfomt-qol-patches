# Faster animal affection: positive affection gains are multiplied by 5.
# Input: tle.gba.  Output: affection.ips (relative to TLE).
#
# Animal record = slot + 4 (barn slots G+0x600+0x2C+i*0x3C, coop G+0x420+0x18+i*0x30).
# Affection = bits 13-20 of the u32 at animal+0x18, 0..250 (accessor 0x080A0194).
# 0x080A0214(animal, delta) is the only adder: aff = clamp(aff + delta, 0, 250).
# Gains (brushing, talking, milking, feeding...) pass +1, one site +50, a few variable;
# penalties go through 0x080A0248, which negates and calls the adder (-10 hitting, -1
# neglect). The adder is rewritten in place (52 bytes incl. its literal) to multiply
# positive deltas by 5; negative ones are unchanged.
import subprocess
from ipslib import make_ips

LLVM = '/opt/homebrew/opt/llvm/bin'
FUNC = 0x080A0214
SIZE = 0x34
ORIG = bytes.fromhex('00b5031c9869c002000e4218002a01da002202e0fa2a00d9fa22ff20024052039869'
                     '034908401043986101bc00470000ff1fe0ff')

tle = open('tle.gba', 'rb').read()
rom = bytearray(tle)
off = FUNC - 0x08000000
assert rom[off:off+SIZE] == ORIG, rom[off:off+SIZE].hex()

asm = """
.syntax unified
.thumb
.text
    push {r4, lr}
    ldr  r4, [r0, #0x18]
    lsls r2, r4, #11
    lsrs r2, r2, #24         @ affection
    cmp  r1, #0
    ble  1f
    lsls r3, r1, #2
    adds r1, r1, r3          @ gains x5
1:
    adds r2, r2, r1
    cmp  r2, #0
    bge  2f
    movs r2, #0
2:
    cmp  r2, #0xfa
    bls  3f
    movs r2, #0xfa
3:
    lsls r2, r2, #13
    ldr  r3, =0xffe01fff
    ands r4, r3
    orrs r4, r2
    str  r4, [r0, #0x18]
    pop  {r4}
    pop  {r0}
    bx   r0
.ltorg
"""
open('affection.s', 'w').write(asm)
subprocess.run(['clang', '-target', 'armv4t-none-eabi', '-mthumb', '-c', 'affection.s', '-o', 'affection.o'], check=True)
subprocess.run([f'{LLVM}/llvm-objcopy', '-O', 'binary', '-j', '.text', 'affection.o', 'affection.bin'], check=True)
code = open('affection.bin', 'rb').read()
assert len(code) <= SIZE, len(code)
code += b'\xff' * (SIZE - len(code)) if len(code) % 2 else bytes.fromhex('c046') * ((SIZE - len(code)) // 2)
rom[off:off+SIZE] = code

recs = make_ips(tle, rom, 'affection.ips')
print(f'{len(code)} bytes, {len(recs)} IPS records')
