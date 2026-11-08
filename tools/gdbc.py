import socket,time,sys
class G:
    def __init__(s,port=2345):
        for _ in range(50):
            try: s.s=socket.create_connection(('127.0.0.1',port)); break
            except OSError: time.sleep(0.2)
        s.s.settimeout(30); s.buf=b''
    def _read(s):
        while True:
            i=s.buf.find(b'$')
            if i>=0:
                j=s.buf.find(b'#',i)
                if j>=0 and len(s.buf)>=j+3:
                    pkt=s.buf[i+1:j]; s.buf=s.buf[j+3:]; s.s.sendall(b'+'); return pkt.decode()
            s.buf+=s.s.recv(65536)
    def cmd(s,c,wait=True):
        cs=sum(c.encode())&0xff
        s.s.sendall(f'${c}#{cs:02x}'.encode())
        return s._read() if wait else None
    def regs(s):
        r=s.cmd('g'); return [int.from_bytes(bytes.fromhex(r[i*8:i*8+8]),'little') for i in range(16)]
    def mem(s,a,n):
        out=b''
        while n>0:
            k=min(n,0x200); out+=bytes.fromhex(s.cmd(f'm{a:x},{k:x}')); a+=k; n-=k
        return out
    def wmem(s,a,b): return s.cmd(f'M{a:x},{len(b):x}:{b.hex()}')

def attach():
    g=G(); g.s.settimeout(2)
    try: g.cmd('?')
    except Exception: pass
    g.s.sendall(b'\x03')
    try: g._read()
    except Exception: pass
    g.s.settimeout(30); g.buf=b''
    return g
