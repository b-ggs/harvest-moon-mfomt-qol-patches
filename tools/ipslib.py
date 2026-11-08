# Shared IPS helpers for the patch build scripts.

def make_ips(base, new, path):
    """Write an IPS that turns `base` into `new` (same length). Returns the records."""
    assert len(base) == len(new)
    recs, i = [], 0
    while i < len(new):
        if new[i] != base[i]:
            j = i
            # merge across single unchanged bytes (cheaper than a new 5-byte record header)
            while j < len(new) and j - i < 0xFFFF and (new[j] != base[j] or (j + 1 < len(new) and new[j+1] != base[j+1])):
                j += 1
            recs.append((i, bytes(new[i:j]))); i = j
        else:
            i += 1
    ips = bytearray(b'PATCH')
    for o, d in recs:
        assert o != 0x454F46, 'offset collides with the EOF marker'
        ips += o.to_bytes(3, 'big') + len(d).to_bytes(2, 'big') + d
    ips += b'EOF'
    open(path, 'wb').write(ips)
    return recs

def read_ips(path):
    """Return [(offset, bytes)] for every record (RLE records expanded)."""
    d = open(path, 'rb').read()
    assert d[:5] == b'PATCH', path
    i, out = 5, []
    while d[i:i+3] != b'EOF':
        o = int.from_bytes(d[i:i+3], 'big'); n = int.from_bytes(d[i+3:i+5], 'big'); i += 5
        if n == 0:
            out.append((o, bytes([d[i+2]]) * int.from_bytes(d[i:i+2], 'big'))); i += 3
        else:
            out.append((o, d[i:i+n])); i += n
    return out

def apply_ips(rom, path):
    rom = bytearray(rom)
    for o, b in read_ips(path):
        if o + len(b) > len(rom):
            rom.extend(b'\0' * (o + len(b) - len(rom)))
        rom[o:o+len(b)] = b
    return bytes(rom)
