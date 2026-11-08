import sys,struct,capstone
rom=open('tle.gba','rb').read()
md=capstone.Cs(capstone.CS_ARCH_ARM,capstone.CS_MODE_THUMB)
start=int(sys.argv[1],16); n=int(sys.argv[2],0)
off=start-0x08000000
for ins in md.disasm(rom[off:off+n],start):
    extra=''
    if ins.mnemonic=='ldr' and 'pc' in ins.op_str:
        imm=int(ins.op_str.split('#')[1].rstrip(']'),16)
        a=((ins.address+4)&~3)+imm
        extra=f'   ; ={struct.unpack("<I",rom[a-0x08000000:a-0x08000000+4])[0]:#010x}'
    print(f'{ins.address:08x}: {ins.mnemonic} {ins.op_str}{extra}')
