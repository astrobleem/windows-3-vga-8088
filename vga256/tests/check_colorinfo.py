#!/usr/bin/env python3
"""Instruction-level ColorInfo ABI test against a linked NE build.
Usage: PYTHONPATH=<unicorn installation> python check_colorinfo.py [build-dir]
Does not boot Windows, realize a palette, or emulate an 8088's bus timing.
"""
from pathlib import Path
import sys,struct,re
from unicorn import Uc,UC_ARCH_X86,UC_MODE_16,UC_HOOK_MEM_READ,UC_HOOK_MEM_WRITE,UC_HOOK_CODE
from unicorn.x86_const import *
root=Path(__file__).resolve().parents[1]
b=Path(sys.argv[1]) if len(sys.argv)>1 else root/'build01'/'SRC'
if (b/'SRC').is_dir():b=b/'SRC'
blob=(b/'VGA256.DRV').read_bytes();mp=(b/'VGA256.MAP').read_text()
sym={name:(int(seg,16),int(off,16)) for seg,off,name in re.findall(r'^ ([0-9A-F]{4}):([0-9A-F]{4})\s+(\w+)\s*$',mp,re.M)}
w=lambda off:struct.unpack_from('<H',blob,off)[0]
ne=struct.unpack_from('<I',blob,60)[0];assert blob[ne:ne+2]==b'NE'
tab=ne+w(ne+34);shift=w(ne+50);num=w(ne+28)
segments={};flags={};records={}
for n in range(1,num+1):
 sec,size,flag,minimum=struct.unpack_from('<4H',blob,tab+(n-1)*8)
 data=bytearray(65536);length=size or 65536
 if sec:data[:length]=blob[sec<<shift:(sec<<shift)+length]
 segments[n]=data;flags[n]=flag
 if sec and flag&0x100:
  r=(sec<<shift)+length;records[n]=[struct.unpack_from('<BBHHH',blob,r+2+i*8) for i in range(w(r))]
for n,rr in records.items():
 for typ,kind,where,target,offset in rr:
  if typ!=2 or kind!=0 or target not in segments:continue
  seen=set()
  while where!=0xffff:
   assert where not in seen;seen.add(where)
   nxt=int.from_bytes(segments[n][where:where+2],'little')
   segments[n][where:where+2]=(target*0x1000).to_bytes(2,'little');where=nxt
uc=Uc(UC_ARCH_X86,UC_MODE_16);uc.mem_map(0,0x100000)
for n,data in segments.items():uc.mem_write(n*0x10000,bytes(data))
entryseg,entryoff=sym['ColorInfo'];DS=sym['Palette'][0]*0x1000;SS=0xb000;ES=0xc000;OUT=0x4000;SP=0x8000;STOP=0xf000
# Windows patches SetCursor's WIN prologue to MOV AX,DGROUP; _cstods
# labels that immediate word. Reproduce the loader's documented setup.
csseg,csoff=sym['_cstods']
uc.mem_write(csseg*0x10000+csoff-1,b'\xb8'+DS.to_bytes(2,'little'))
pal=sym['Palette'][1];ad=sym['adPalette'][1];data=segments[sym['Palette'][0]]
triples=[int.from_bytes(data[pal+3*i:pal+3*i+3],'little') for i in range(20)]
indices=[i if i<10 else i+236 for i in range(20)]
physical=[int.from_bytes(data[pal+60+2*i:pal+62+2*i],'little') for i in range(20)]
assert [v&255 for v in physical]==indices
initial_quad=[int.from_bytes(data[ad+4*i:ad+4*i+4],'little')&0xffffff for i in range(256)]
mode='';case=None;reads=0;writes=[]
def mem_read(uc,access,address,size,value,unused):
 global reads
 if DS*16<=address<DS*16+65536:
  off=address-DS*16;reads+=1
  allowed=[]
  if mode=='rgb':allowed=[(pal,pal+60),(pal+60,pal+100)]
  elif mode=='system_forward':allowed=[(pal,pal+60)]
  elif mode=='system_reverse':allowed=[(ad,ad+1024)]
  assert any(lo<=off and off+size<=hi for lo,hi in allowed),('unexpected/OOB data read',case,hex(off),size,allowed)
def mem_write(uc,access,address,size,value,unused):
 if ES*16<=address<ES*16+65536:
  writes.append((address-ES*16,size))
  assert OUT<=address-ES*16 and address-ES*16+size<=OUT+4,('PCOLOR write out of bounds',case,address,size)
uc.hook_add(UC_HOOK_MEM_READ,mem_read);uc.hook_add(UC_HOOK_MEM_WRITE,mem_write)
# Unicorn 2.1.4 repeatedly executes RETF imm16 with unchanged IP here.
# Stop immediately before the terminal instruction and validate its complete
# return frame and immediate cleanup; all ColorInfo body/epilogue runs natively.
returned=False
def terminal_return(u,address,size,unused):
 global returned
 if bytes(u.mem_read(address,3))==b'\xca\x0c\x00' and u.reg_read(UC_X86_REG_SP)==SP:
  assert bytes(u.mem_read(SS*16+SP,4))==struct.pack('<HH',STOP,entryseg*0x1000)
  returned=True;u.emu_stop()
uc.hook_add(UC_HOOK_CODE,terminal_return)
def run(color,forward,df,label):
 global case,writes,returned
 returned=False
 case=(label,hex(color),'forward' if forward else 'reverse',df);writes=[]
 # FAR Pascal arguments follow the return address, lowest argument first.
 args=struct.pack('<HHIII',STOP,entryseg*0x1000,(ES<<16)|OUT if forward else 0,color,0)
 uc.mem_write(SS*16+SP,args);uc.mem_write(ES*16+OUT-8,b'\xa5'*20)
 saved={UC_X86_REG_SI:0x1234,UC_X86_REG_DI:0x5678,UC_X86_REG_BP:0x9000,UC_X86_REG_DS:DS,UC_X86_REG_ES:ES}
 for reg,val in {**saved,UC_X86_REG_CS:entryseg*0x1000,UC_X86_REG_SS:SS,UC_X86_REG_SP:SP,UC_X86_REG_EFLAGS:2|(df<<10)}.items():uc.reg_write(reg,val)
 uc.emu_start(entryseg*0x10000+entryoff,entryseg*0x10000+STOP,count=20000)
 assert returned,('did not reach terminal RETF12',case)
 assert uc.reg_read(UC_X86_REG_SP)==SP,('pre-return stack imbalance',case)
 for reg,val in saved.items():assert uc.reg_read(reg)==val,('preserved register changed',case,reg)
 sentinel=bytes(uc.mem_read(ES*16+OUT-8,20))
 assert sentinel[:8]==b'\xa5'*8 and sentinel[12:]==b'\xa5'*8,('output sentinel damaged',case)
 if not forward:assert sentinel==b'\xa5'*20 and not writes,case
 else:assert sum(n for _,n in writes)==4,('PCOLOR not fully written',case,writes)
 return (uc.reg_read(UC_X86_REG_DX)<<16)|uc.reg_read(UC_X86_REG_AX),int.from_bytes(sentinel[8:12],'little')
count=0
for df in (0,1):
 for index in range(256):
  dynamic=10<=index<=245
  mode='dynamic_forward' if dynamic else 'system_forward'
  result,pcolor=run(0xff000000|index,True,df,'indexed')
  assert pcolor==0xff000000|index,('wrong PCOLOR',case,hex(pcolor))
  slot=index if index<10 else index-236
  expected=(0xff000000|index) if dynamic else triples[slot]
  assert result==expected,('wrong color return',case,hex(result),hex(expected))
  count+=1
  for pflags in (0,3,0x80):
   mode='dynamic_reverse' if dynamic else 'system_reverse'
   result,_=run(0xff000000|(pflags<<8)|index,False,df,'reverse')
   expected=(0xff000000|index) if dynamic else initial_quad[index]
   assert result==expected,('wrong reverse return',case,hex(result),hex(expected))
   count+=1
print(f'PASS {count} indexed/reverse cases, all indices0..255, both DF states, reverse accelerator flags0/3/80h',flush=True)
for df in (0,1):
 for slot,rgb in enumerate(triples):
  mode='rgb';result,pcolor=run(rgb,True,df,'exact-system-RGB')
  assert result==rgb,('wrong exact RGB',case,hex(result),hex(rgb))
  assert pcolor==0xff008000|physical[slot],('wrong RGB PCOLOR',case,hex(pcolor),hex(physical[slot]))
  count+=1
print(f'PASS {count} total cases, including40 exact RGB conversions; {reads} bounded palette/table reads')
print('PASS PCOLOR write placement, 4-byte representation, canonical FF0000II dynamic outputs, system RGB, preserved registers and Pascal stack cleanup')
print('Scope: linked instruction execution with initial palette tables; terminal RETF12 validated but not executed due to Unicorn2.1.4 return bug. Not Windows palette realization or VGA hardware.')
