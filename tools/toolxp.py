# Fast tool XP: tools gain 5x experience per use.
# Input: tle.gba.  Output: toolxp.ips (relative to TLE).
#
# 0x0800F064(xp_ptr, amount) is the only XP adder: xp = min(xp + amount, 0xFFFF).
# Its 7 callers (0x08030392 ... 0x08031C26, one per tool action) pass 50, or 100
# when a flag is set. The function is rewritten in place (44 bytes) to multiply
# the amount by 5 first. It returns the new value in r0 like the original, and
# only touches r0-r3.
import subprocess
from ipslib import make_ips

LLVM = '/opt/homebrew/opt/llvm/bin'
FUNC = 0x0800F064
SIZE = 0x2C                      # up to and including the old 0xFFFF literal
ORIG = bytes.fromhex('10b582b0041c2088401800900649019101aa6b46884200d9131c1868208002b010bc01bc00470000ffff0000')

tle = open('tle.gba', 'rb').read()
rom = bytearray(tle)
off = FUNC - 0x08000000
assert rom[off:off+SIZE] == ORIG[:SIZE], rom[off:off+SIZE].hex()

asm = """
.syntax unified
.thumb
.text
    ldrh r2, [r0]
    lsls r3, r1, #2
    adds r1, r1, r3          @ amount * 5
    adds r2, r2, r1
    movs r3, #1
    lsls r3, r3, #16
    subs r3, #1              @ 0xFFFF
    cmp  r2, r3
    bls  1f
    adds r2, r3, #0
1:
    strh r2, [r0]
    adds r0, r2, #0
    bx   lr
"""
open('toolxp.s', 'w').write(asm)
subprocess.run(['clang', '-target', 'armv4t-none-eabi', '-mthumb', '-c', 'toolxp.s', '-o', 'toolxp.o'], check=True)
subprocess.run([f'{LLVM}/llvm-objcopy', '-O', 'binary', '-j', '.text', 'toolxp.o', 'toolxp.bin'], check=True)
code = open('toolxp.bin', 'rb').read()
assert len(code) <= SIZE and len(code) % 2 == 0
code += bytes.fromhex('c046') * ((SIZE - len(code)) // 2)   # nop padding
rom[off:off+SIZE] = code

recs = make_ips(tle, rom, 'toolxp.ips')
print(f'{len(code)} bytes, {len(recs)} IPS records')
