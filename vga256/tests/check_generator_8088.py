#!/usr/bin/env python3
"""Instruction-focused checks, not a Windows or original-8088 hardware test.
Requires unicorn and capstone. This models emitted rotations and gen_loop;
source guards tie the model to the bounded paths. Whole CBLT coverage is separate.
"""
from pathlib import Path
import re
from unicorn import Uc, UC_ARCH_X86, UC_MODE_16
from unicorn.x86_const import *
from capstone import Cs, CS_ARCH_X86, CS_MODE_16
src = Path(__file__).resolve().parents[1] / 'src'
def source(n): return (src / n).read_text()
const = {k:int(v,16) for k,v in re.findall(r'^(I_\w+)\s+equ\s+([0-9A-Fa-f]+)h',source('GENCONST.BLT'),re.M)}
def word(n): return const[n].to_bytes(2,'little')
for n in ('CBLT11.BLT','CBLT81.BLT','CBLT88.BLT'):
    s = '\n'.join(x.split(';')[0] for x in source(n).splitlines())
    assert not re.search(r'\brep\s+movs.*(?:es|cs):',s,re.I)
    assert not re.search(r'\bpush\s+sp\b|I_RO[LR]_\w+_N\b',s,re.I)
assert not re.search(r'I_RO[LR]_\w+_N\s+equ',source('GENCONST.BLT'))
assert source('CBLT.ASM').count('CBLT_COPY macro source_segment') == 1
assert sum(source(n).count('CBLT_COPY ') for n in ('CBLT11.BLT','CBLT81.BLT','CBLT88.BLT')) == 7
md=Cs(CS_ARCH_X86,CS_MODE_16)
uc=Uc(UC_ARCH_X86,UC_MODE_16);uc.mem_map(0,0x100000)
regs=(UC_X86_REG_AX,UC_X86_REG_BX,UC_X86_REG_CX,UC_X86_REG_DX,UC_X86_REG_SI,UC_X86_REG_DI,UC_X86_REG_BP,UC_X86_REG_SP)
initial=(0xA500,0x5A00,0x8193,0x4567,0x6000,0x7000,0x8ACE,0x9000)
rot_tests=0
for target in ('AL','BL'):
 for n in range(8):
    if target=='AL':
        code=word('I_ROL_AL_1')*n if n<=4 else word('I_ROR_AL_1')*(8-n)
    else: code=word('I_ROL_BL_1')*n
    assert len(code)<=(8 if target=='AL' else 14)
    assert all(i.mnemonic in ('rol','ror') and i.op_str.endswith(', 1') for i in md.disasm(code,0x1000))
    for value in range(256):
        before=list(initial);idx=0 if target=='AL' else 1;before[idx]|=value
        for reg,val in zip(regs,before):uc.reg_write(reg,val)
        if code:
            uc.mem_write(0x1000,code);uc.ctl_remove_cache(0x1000,0x1020)
            uc.emu_start(0x1000,0x1000+len(code),count=16)
        expected=((value<<n)|(value>>(8-n)))&255
        after=[uc.reg_read(reg) for reg in regs]
        before[idx]=(before[idx]&0xFF00)|expected
        assert after==before,(target,n,value,after,before)
        rot_tests+=1
print(f'PASS: {rot_tests} bounded emitted rotation cases, all non-target registers preserved')
# Exact JCXZ + segment MOVSB + LOOP macro encoding, with forward/backward DF.
copy_tests=0
for prefix,segment in ((0x26,UC_X86_REG_ES),(0x2e,UC_X86_REG_CS)):
 for direction in (1,-1):
  for count in (0,1,2,7,255,512):
   for status in (0x2,0x8D7):
    uc.reg_write(UC_X86_REG_CS,0x100);uc.reg_write(UC_X86_REG_ES,0x2000)
    uc.reg_write(UC_X86_REG_DS,0x3000)
    code=bytes([0xe3,4,prefix,0xa4,0xe2,0xfc]);base=0x1100
    uc.mem_write(base,code);uc.ctl_remove_cache(base,base+16)
    for reg,val in zip(regs,initial):uc.reg_write(reg,val)
    start=0x4000 if direction==1 else 0x4400
    dest=0x6000 if direction==1 else 0x6400
    uc.reg_write(UC_X86_REG_SI,start);uc.reg_write(UC_X86_REG_DI,dest);uc.reg_write(UC_X86_REG_CX,count)
    flags=status|(0x400 if direction<0 else 0);uc.reg_write(UC_X86_REG_EFLAGS,flags)
    segbase=uc.reg_read(segment)*16
    for i in range(count):uc.mem_write(segbase+start+direction*i,bytes([(i*37+11)&255]))
    uc.emu_start(base,base+len(code),count=2*count+2)
    for i in range(count):assert uc.mem_read(0x20000+dest+direction*i,1)==bytes([(i*37+11)&255])
    assert uc.reg_read(UC_X86_REG_CX)==0
    assert uc.reg_read(UC_X86_REG_SI)==start+direction*count
    assert uc.reg_read(UC_X86_REG_DI)==dest+direction*count
    assert uc.reg_read(UC_X86_REG_EFLAGS)==flags
    for reg,val in zip(regs,initial):
     if reg not in (UC_X86_REG_CX,UC_X86_REG_SI,UC_X86_REG_DI):assert uc.reg_read(reg)==val
    copy_tests+=1
print(f'PASS: {copy_tests} exact copy-macro cases (ES/CS, DF both ways, zero/nonzero, FLAGS preserved)')
for length in range(1,2049):
 displacement=-length
 if (displacement&65535)>=(2-127)&65535:
    code=bytes([0xe2,(displacement-2)&255]);assert -128<=displacement-2<=127
    target=length+2+int.from_bytes(code[1:],'little',signed=True)
 else:
    code=b'\x49\x74\x03\xe9'+((displacement-6)&65535).to_bytes(2,'little')
    target=length+6+int.from_bytes(code[4:],'little',signed=True)
 assert target==0
print('PASS: 2048 gen_loop backward distances have valid short or near target')
print('LIMIT: No full-CBLT buffer bound or hardware interrupt restart emulation claimed.')
