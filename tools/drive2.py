# Full-speed input driver: redirects the game's KEYINPUT literal (ROM 0x080091A0)
# to a RAM word we control, so no per-frame breakpoints are needed.
import sys, time
sys.path.insert(0, '.')
from gdbc import attach
from render import render

K = dict(A=1, B=2, SEL=4, START=8, RIGHT=16, LEFT=32, UP=64, DOWN=128, R=256, L=512)
FAKE = 0x0203FF00   # top of EWRAM, assumed unused
LIT = 0x080091A0
FPS = 59.73

class D:
    def __init__(s):
        s.g = attach(); s.g.cmd('z0,8009198,2')
        s.set(''); s.g.wmem(FAKE, s.cur)
        s.g.wmem(LIT, FAKE.to_bytes(4, 'little'))
        assert s.g.mem(LIT, 4) == FAKE.to_bytes(4, 'little'), 'ROM write failed'
        s.g.cmd('c', wait=False)
    def _halt(s):
        s.g.s.sendall(b'\x03'); s.g._read()
    def set(s, keys):
        m = 0
        for k in keys.split('+') if keys else []:
            m |= K[k]
        s.cur = (0x3ff & ~m).to_bytes(2, 'little')
    def apply(s):
        s._halt(); s.g.wmem(FAKE, s.cur); s.g.cmd('c', wait=False)
    def hold(s, keys, frames):
        s.set(keys); s.apply(); time.sleep(frames / FPS)
    def tap(s, keys, n=1, gap=20):
        for _ in range(n):
            s.hold(keys, 8); s.hold('', gap)
    def shot(s, p):
        s._halt(); render(s.g, p); s.g.cmd('c', wait=False)

def run(script, shot='cur.png'):
    d = D()
    for step in script:
        if step[0] == 'wait': d.hold('', step[1])
        elif step[0] == 'hold': d.hold(step[1], step[2])
        else: d.tap(step[1], *step[2:])
    d.set(''); d.apply(); d.shot(shot)
    return d

if __name__ == '__main__':
    run(eval(sys.argv[1]), sys.argv[2] if len(sys.argv) > 2 else 'cur.png')
