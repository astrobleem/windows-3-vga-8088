"""Build a separate diagnostic source variant that logs generated buffers to E9.
The normal driver is not changed. Only CBLT is reassembled; other objects reused.
"""
from pathlib import Path
import shutil,sys
original=Path(sys.argv[1]).resolve();out=Path(sys.argv[2]).resolve();out.mkdir(exist_ok=False)
(out/'SRC').mkdir()
for f in (original/'SRC').iterdir():
 if f.name=='CBLT.ASM':shutil.copyfile(f,out/'SRC'/f.name)
 elif f.suffix not in {'.LST','.LOG','.MAP','.DRV'} and f.name!='CBLT.OBJ':(out/'SRC'/f.name).symlink_to(f)
for name in ['INC','BIN','LIB']:(out/name).symlink_to(original/name,target_is_directory=True)
source=out/'SRC/CBLT.ASM';text=source.read_bytes().replace(b'\r\n',b'\n').decode('latin1')
needle='\tmov\tal,I_RET_FAR\t\t;Stuff the far return instruction\n\tstosb'
trace='''
; Diagnostic-only read-only dump before execution, bounded to 64 phased BLTs.
 pushf
 push ax
 push bx
 push cx
 push dx
 push si
 cmp word ptr cs:ega_trace_count,64
 jae ega_trace_done
 cmp gl_phase_h,0
 je ega_trace_done
 inc word ptr cs:ega_trace_count
 mov si,off_gl_blt_addr
 mov cx,di
 sub cx,si
 mov dx,0e9h
 mov al,'E'
 out dx,al
 mov al,'G'
 out dx,al
 mov al,'A'
 out dx,al
 mov al,':'
 out dx,al
 mov ax,ss
 call ega_trace_hex
 mov al,':'
 out dx,al
 mov ax,si
 call ega_trace_hex
 mov al,':'
 out dx,al
 mov ax,cx
 call ega_trace_hex
 mov al,':'
 out dx,al
 xor ax,ax
 mov al,gl_phase_h
 call ega_trace_hex
 mov al,':'
 out dx,al
 jcxz ega_trace_newline
ega_trace_bytes:
 mov al,es:[si]
 xor ah,ah
 call ega_trace_hex
 inc si
 loop ega_trace_bytes
ega_trace_newline:
 mov al,10
 out dx,al
ega_trace_done:
 pop si
 pop dx
 pop cx
 pop bx
 pop ax
 popf
'''
if text.count(needle)!=1:raise ValueError('Unexpected CBLT end sequence')
text=text.replace(needle,needle+trace)
helper='''
ega_trace_count dw 0
ega_trace_hex proc near
 push ax
 push cx
 mov cx,4
ega_trace_digit:
 rol ax,1
 rol ax,1
 rol ax,1
 rol ax,1
 push ax
 and al,15
 cmp al,9
 jbe ega_trace_numeric
 add al,7
ega_trace_numeric:
 add al,'0'
 out dx,al
 pop ax
 loop ega_trace_digit
 pop cx
 pop ax
 ret
ega_trace_hex endp
'''
# Place helper before segment closure, outside any procedure.
pos=text.lower().rfind('send\tcode')
if pos<0:
 import re
 m=list(re.finditer(r'(?im)^\s*sEnd\s+Code\b',text));pos=m[-1].start() if m else -1
if pos<0:raise ValueError('Code segment closure not found')
text=text[:pos]+helper+text[pos:];source.write_bytes(text.replace('\n','\r\n').encode('latin1'))
(out/'BUILD.BAT').write_bytes(b'@echo off\r\nSET INCLUDE=R:\\INC;R:\\SRC\r\nSET LIB=R:\\LIB\r\nR:\r\nCD \\SRC\r\nR:\\BIN\\MASM -LA -I. -DPUBDEFS -D?QUIET -D_EGA=0 -D_VGA=1 -D_NEW_COLOR_ADD -ML -W2 -T CBLT.ASM,CBLT.OBJ,CBLT.LST; > CBLT.LOG\r\nR:\\BIN\\LINK4 @VGA88.LNK > LINK.LOG\r\nexit\r\n')
print(out)
