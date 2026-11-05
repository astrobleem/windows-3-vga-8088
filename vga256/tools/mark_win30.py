#!/usr/bin/env python3
"""Tag a linked Win16 test program for the Windows 3.0 API contract."""
from pathlib import Path
import struct,sys
p=Path(sys.argv[1]); b=bytearray(p.read_bytes())
assert b[:2]==b'MZ'
n=struct.unpack_from('<I',b,0x3c)[0]
assert b[n:n+2]==b'NE' and len(b)>=n+0x40
# LINK 5.01 leaves this at zero. Palette color flags require the 3.0 contract.
struct.pack_into('<H',b,n+0x3e,0x0300)
struct.pack_into('<I',b,n+8,0)
p.write_bytes(b)
print(f'{p.name}: expected Windows version 0300h')
