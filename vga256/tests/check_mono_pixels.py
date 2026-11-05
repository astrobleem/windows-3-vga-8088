#!/usr/bin/env python3
"""Execute actual linked mono-to-packed8 generated code against pixel reference."""
import check_compiled_cblt as h
from unicorn.x86_const import *
uc=h.uc;count=0
for swap in range(2):
 for phase in range(8):
  for width in range(1,18):
   h.case=('pixels',swap,phase,width)
   text,bg=(213,12) if swap else (12,213)
   frame=bytearray(512)
   operand=int.from_bytes(h.code[h.entries['roptable']+2*(255-0xcc):][:2],'little')^0x8000
   for n,v in [('off_gl_blt_addr',h.OUT),('gl_operands',operand),('cl_both_colors',(bg<<8)|text),('xExt',width),('yExt',8),('SrcxOrg',phase)]:h.wloc(frame,n,v)
   for n,v in [('gl_flag0',0x11),('gl_direction',1)]:h.wloc(frame,n,v,1)
   h.dev(frame,'gl_src',False);h.dev(frame,'gl_dest',False)
   o=0x100+h.locals['gl_src'];frame[o+4:o+6]=(4).to_bytes(2,'little')
   o=0x100+h.locals['gl_dest'];frame[o+4:o+6]=(32).to_bytes(2,'little')
   uc.mem_write(h.SS*16+h.BP-256,bytes(frame))
   for r,v in [(UC_X86_REG_CS,h.CS),(UC_X86_REG_SS,h.SS),(UC_X86_REG_DS,h.CS),(UC_X86_REG_ES,h.SS),(UC_X86_REG_BP,h.BP),(UC_X86_REG_SP,0xaffe),(UC_X86_REG_DI,h.OUT),(UC_X86_REG_CX,0),(UC_X86_REG_EFLAGS,2)]:uc.reg_write(r,v)
   uc.mem_write(h.SS*16+0xaffe,h.STOP.to_bytes(2,'little'))
   uc.emu_start(h.CS*16+h.entries['cblt88'],h.CS*16+h.STOP,count=20000)
   length=uc.reg_read(UC_X86_REG_DI)-h.OUT;assert uc.reg_read(UC_X86_REG_IP)==h.STOP
   bits=bytearray(32)
   for y in range(8):
    for x in range(32):
     if ((x*5+y*3+(x>>2))&7)<3:bits[y*4+x//8]|=0x80>>(x&7)
   uc.mem_write(0x60000,bytes(bits)+b'\x00'*16);uc.mem_write(0x70000,b'\xcc'*256)
   for r,v in [(UC_X86_REG_CS,h.SS),(UC_X86_REG_DS,0x6000),(UC_X86_REG_ES,0x7000),(UC_X86_REG_SI,0),(UC_X86_REG_DI,0),(UC_X86_REG_CX,8),(UC_X86_REG_SP,0xaffe),(UC_X86_REG_EFLAGS,2)]:uc.reg_write(r,v)
   uc.mem_write(h.SS*16+0xaffe,h.STOP.to_bytes(2,'little')+h.SS.to_bytes(2,'little'))
   uc.ctl_remove_cache(h.SS*16+h.OUT,h.SS*16+h.OUT+452)
   uc.emu_start(h.SS*16+h.OUT,h.SS*16+h.STOP,count=20000)
   assert uc.reg_read(UC_X86_REG_IP)==h.STOP
   output=uc.mem_read(0x70000,256)
   for y in range(8):
    for x in range(32):
     want=(bg if (((phase+x)*5+y*3+((phase+x)>>2))&7)<3 else text) if x<width else 0xcc
     assert output[y*32+x]==want,(swap,phase,width,x,y,output[y*32+x],want)
   count+=1
print(f'PASS: {count} compiled mono-to-packed8 pixel cases: phases0..7, widths1..17,8 rows,swapped colors12/213, untouched destination padding.')
print('Scope: memory buffers and pretranslated color indices; no GDI palette realization or device bank paths.')
