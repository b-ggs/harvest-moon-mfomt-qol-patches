import sys
d=open(sys.argv[1],'rb').read(); rom=bytearray(open(sys.argv[2],'rb').read())
i=5
while d[i:i+3]!=b'EOF':
    off=int.from_bytes(d[i:i+3],'big'); sz=int.from_bytes(d[i+3:i+5],'big'); i+=5
    if sz==0: new=bytes([d[i+2]])*int.from_bytes(d[i:i+2],'big'); i+=3
    else: new=d[i:i+sz]; i+=sz
    if off+len(new)>len(rom): rom.extend(b'\0'*(off+len(new)-len(rom)))
    rom[off:off+len(new)]=new
open(sys.argv[3],'wb').write(rom)
