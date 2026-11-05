#!/usr/bin/env python3
"""Execute linked CBLT11/81/88 generators, inspect output, bound writes.
Not a Windows integration test or exhaustive proof over every valid input.
"""
from pathlib import Path
import struct,re,itertools,time,sys
from unicorn import Uc,UC_ARCH_X86,UC_MODE_16,UC_HOOK_MEM_WRITE
from unicorn.x86_const import *
from capstone import Cs,CS_ARCH_X86,CS_MODE_16
root=Path(__file__).resolve().parents[1];b=Path(sys.argv[1]) if len(sys.argv)>1 else root/'build01'/'SRC'
if (b/'SRC').is_dir():b=b/'SRC'
drv=(b/'VGA256.DRV').read_bytes();u16=lambda off:struct.unpack_from('<H',drv,off)[0]
ne=struct.unpack_from('<I',drv,0x3c)[0];assert drv[ne:ne+2]==b'NE'
segtab=ne+u16(ne+0x22);shift=u16(ne+0x32)
sector,size,flags,minimum=struct.unpack_from('<4H',drv,segtab)
code=drv[sector<<shift:(sector<<shift)+(size or 65536)]
listing=(b/'CBLT.LST').read_text(errors='replace');mp=(b/'VGA256.MAP').read_text()
locals={n:int(d) for n,d in re.findall(r'^(\w+) .+TEXT\s+\([^\n]*\[bp([+-]\d+)\]',listing,re.M)}
entries={n:int(o,16) for o,n in re.findall(r'^ 0001:([0-9A-F]{4})\s+(\w+)\s*$',mp,re.M)}
uc=Uc(UC_ARCH_X86,UC_MODE_16);uc.mem_map(0,0x100000)
CS=0x1000;SS=0x3000;BP=0xc000;OUT=0x4000;STOP=0xf000
# Apply the NE loader's internal segment-reference chains for DGROUP.
# No imports are executed by these generator entrypoints.
loaded=bytearray(code);reloc=(sector<<shift)+(size or 65536)
for i in range(u16(reloc)):
 typ,kind,where,target,extra=struct.unpack_from('<BBHHH',drv,reloc+2+8*i)
 if typ==2 and kind==0 and target==9:
  seen=set()
  while where!=0xffff:
   assert where not in seen;seen.add(where)
   nxt=int.from_bytes(loaded[where:where+2],'little')
   loaded[where:where+2]=(0x5000).to_bytes(2,'little');where=nxt
uc.mem_write(CS*16,bytes(loaded))
dssector,dssize,dsflags,dsmin=struct.unpack_from('<4H',drv,segtab+8*8)
uc.mem_write(0x50000,drv[dssector<<shift:(dssector<<shift)+(dssize or 65536)])
md=Cs(CS_ARCH_X86,CS_MODE_16)
def wloc(frame,n,val,size=2):
 off=0x100+locals[n];frame[off:off+size]=(val&((1<<(8*size))-1)).to_bytes(size,'little')
def dev(frame,name,huge):
 off=0x100+locals[name]
 frame[off:off+26]=struct.pack('<HHHHHHHHBBHHHH',1024,100,128,0,0x6000,0x1000 if huge else 0,512,64 if huge else 0,0,0,0,128,0,0x6000)
def onwrite(uc,access,address,size,value,data):
 if SS*16+OUT<=address<SS*16+OUT+0x2000:
  assert address+size<=SS*16+OUT+452,('buffer overflow',case,address,size)
uc.hook_add(UC_HOOK_MEM_WRITE,onwrite)
if __name__ == '__main__':
 maxima={};cases=0;unique=set();start=time.time()
 # Full ROP set; each alignment; empty/short/long inner spans; partial ends;
 # both directions; both ordinary and huge source/destination update sequences.
 shapes=[(0,0,0,0,0),(0,0x0ff0,0,1,4),(1,0xffff,0,0,0),(2,0x0ff0,0xf00f,1,4),(3,0xffff,0xffff,0,7),(17,0x0ff0,0xf00f,1,4),(256,0xffff,0xffff,0,7)]
 for name in ('cblt11','cblt81','cblt88_mono','cblt88_color'):
  maxsize=0;maxcase=None;startcases=cases
  for rop,phase,shape,direction,huge in itertools.product(range(256),range(8),shapes,(1,-1),(False,True)):
   inner,first,last,firstbit,lastbit=shape
   operand=int.from_bytes(code[entries['roptable']+2*(rop if rop<128 else 255-rop):][:2],'little')^(0x8000 if rop>=128 else 0)
   flags=(operand>>9)&0x30
   if name=='cblt81':flags|=0x14 # source is color, destination is monochrome
   if name.startswith('cblt88'):flags|=1|(4 if name.endswith('color') else 0)
   frame=bytearray(0x200)
   for n,v in [('off_gl_blt_addr',OUT),('gl_operands',operand),('gl_inner_count',inner),('gl_first_mask',first),('gl_final_mask',last),('gl_align_mask',0xff00 if phase else 0),('cl_both_colors',0x1703),('xExt',inner*8+8),('yExt',3),('SrcxOrg',phase)]:wloc(frame,n,v)
   for n,v in [('gl_phase_h',phase),('gl_direction',direction),('gl_flag0',flags),('gl_extra_fetch',int(phase!=0)),('gl_first_bit',firstbit),('gl_final_bit',lastbit)]:wloc(frame,n,v,1)
   dev(frame,'gl_src',huge);dev(frame,'gl_dest',huge)
   uc.mem_write(SS*16+BP-0x100,bytes(frame));uc.mem_write(SS*16+OUT,b'\xcc'*512)
   for r,v in [(UC_X86_REG_CS,CS),(UC_X86_REG_SS,SS),(UC_X86_REG_DS,CS),(UC_X86_REG_ES,SS),(UC_X86_REG_BP,BP),(UC_X86_REG_SP,0xaffe),(UC_X86_REG_DI,OUT),(UC_X86_REG_AX,0),(UC_X86_REG_BX,0),(UC_X86_REG_CX,0),(UC_X86_REG_DX,0),(UC_X86_REG_SI,0),(UC_X86_REG_EFLAGS,2)]:uc.reg_write(r,v)
   uc.mem_write(SS*16+0xaffe,STOP.to_bytes(2,'little'))
   case=(name,rop,phase,shape,direction,huge)
   uc.emu_start(CS*16+entries['cblt88' if name.startswith('cblt88') else name],CS*16+STOP,count=20000)
   assert uc.reg_read(UC_X86_REG_IP)==STOP,('did not return',case,hex(uc.reg_read(UC_X86_REG_IP)))
   length=uc.reg_read(UC_X86_REG_DI)-OUT;assert 0<length<=452,(case,length)
   blob=bytes(uc.mem_read(SS*16+OUT,length));assert blob[-1]==0xcb,(case,blob.hex())
   if length>maxsize:maxsize,maxcase=length,case
   # Decoding unique programs avoids repeated disassembly for equivalent shapes.
   if blob not in unique:
    ins=list(md.disasm(blob,OUT));assert sum(i.size for i in ins)==length,(case,'decode gap')
    boundaries={i.address for i in ins}|{OUT+length}
    for i in ins:
     raw=i.bytes;z=0
     while raw[z] in (0x26,0x2e,0x36,0x3e,0xf2,0xf3):z+=1
     assert raw[z] not in (0xc0,0xc1,0x60,0x61,0x68,0x6a,0xc8,0xc9),(case,i.mnemonic,i.op_str)
     assert not ((0xf3 in raw[:z] or 0xf2 in raw[:z]) and any(p in raw[:z] for p in (0x26,0x2e,0x36,0x3e))),case
     if i.mnemonic.startswith('j') or i.mnemonic.startswith('loop'):
      target=int(i.op_str,16);assert target in boundaries,(case,i.mnemonic,i.op_str)
    unique.add(blob)
   cases+=1
  print(f'PASS {name}: {cases-startcases} compiled-generator inputs; maximum {maxsize}/452 bytes; case {maxcase}',flush=True)
  maxima[name]=maxsize
 print(f'PASS total {cases} inputs, {len(unique)} distinct generated programs, {time.time()-start:.1f}s')
 print('Scope: synthetic local frames spanning every ROP and phase, representative masks/counts, both directions, ordinary/huge bitmaps. Generated programs decoded, not executed against pixel references.')
