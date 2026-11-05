#!/usr/bin/env python3
"""MAP-derived exact-fragment semantics for the source-built VGA 8086 port.
Independent NE/MAP parsing; reuses the already mutation-tested checker/oracles,
not binary-patcher offsets or implementations. Produces three DOS COM suites.
"""
import argparse,hashlib,json,re,struct,subprocess,sys
from pathlib import Path
P=Path(__file__).resolve().parent

def segs(b):
 ne=struct.unpack_from('<I',b,0x3c)[0]
 assert b[:2]==b'MZ' and b[ne:ne+2]==b'NE'
 sh=struct.unpack_from('<H',b,ne+0x32)[0];st=ne+struct.unpack_from('<H',b,ne+0x22)[0];out=[]
 for i in range(struct.unpack_from('<H',b,ne+0x1c)[0]):
  start=struct.unpack_from('<H',b,st+i*8)[0]<<sh;length=struct.unpack_from('<H',b,st+i*8+2)[0] or 65536
  assert start+length<=len(b)
  out.append(b[start:start+length])
 return out

def db(b):return '.byte '+','.join(hex(c) for c in b)+'\n' 

def sha(b):return hashlib.sha256(b).hexdigest()
def unique(haystack,needle):
 assert haystack.count(needle)==1,(haystack.hex(),needle.hex())
 return haystack.index(needle)
def build(out,name,source,meta):
 d=out/name;d.mkdir(parents=True,exist_ok=True);asm=d/'SEMANTIC.S';asm.write_text(source)
 subprocess.run(['as','--32','-o',str(d/'SEMANTIC.O'),str(asm)],check=True)
 subprocess.run(['ld','-m','elf_i386','-Ttext','0x100','--oformat','binary','-e','_start','-o',str(d/'SEMANTIC.COM'),str(d/'SEMANTIC.O')],check=True)
 with (d/'SEMANTIC.DIS').open('w') as f:subprocess.run(['objdump','-D','-b','binary','-mi8086','-Mintel',str(d/'SEMANTIC.COM')],stdout=f,check=True)
 info=dict(meta,suite=name,assembly_sha256=sha(asm.read_bytes()),com_sha256=sha((d/'SEMANTIC.COM').read_bytes()))
 (d/'BUILD.json').write_text(json.dumps(info,indent=2)+'\n');return info

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--candidate',type=Path,required=True);ap.add_argument('--map',type=Path,required=True);ap.add_argument('--out',type=Path,default=P/'build');a=ap.parse_args()
 blob=a.candidate.read_bytes();segments=segs(blob);maptext=a.map.read_text();m={n.lower():(int(s,16),int(o,16)) for s,o,n in re.findall(r'^ ([0-9A-Fa-f]{4}):([0-9A-Fa-f]{4})\s+([^\s]+)\s*$',maptext,re.M)}
 def label(name):return m[name.lower()]
 def region(start,end):
  sg,off=label(start);sg2,last=label(end);assert sg==sg2 and last>off
  return sg,off,segments[sg-1][off:last]
 # Locate the direct repeated shifts within public-label-bounded code regions.
 shifts=[]
 for lo,hi,needle in [('phase_proc_50','phase_proc_60',bytes.fromhex('d1ead1ead1ea')),('cblt_4000','cblt_4020',bytes.fromhex('d1ebd1eb'))]:
  sg,base,r=region(lo,hi);delta=unique(r,needle);shifts.append({'segment':sg,'anchor':lo,'offset':base+delta,'delta':delta,'bytes':needle.hex()})
 sg,base,whole=region('cblt_3240','cblt_3280');delta=unique(whole,bytes.fromhex('33c90af6'));emitter=whole[delta:]+b'\xc3'
 assert emitter.startswith(bytes.fromhex('33c90af674')) and bytes.fromhex('b8d0c0') in emitter and bytes.fromhex('f3ab32ed') in emitter
 phseg,phoff=label('phase_align');assert phseg==sg;suffix=segments[phseg-1][phoff:phoff+8]
 siat=unique(emitter,b'\xbe'+struct.pack('<H',phoff));assert emitter[siat+3:]==bytes.fromhex('b104e3042ea5e2fcc3')
 # Ten explicit copies, all anchored to public source labels. Counts/relative
 # locations are checked; no historical driver offsets are assumed.
 anchors=[('middle_grey_dpx',0x26,0xa4,1),('cblt_2020',0x2e,0xa5,1),('cblt_3260',0x2e,0xa5,1),('cblt_3280',0x26,0xa4,1),('cblt_4000',0x2e,0xa4,1),('cblt_5560',0x26,0xa4,2),('cblt_6000',0x26,0xa4,1),('cblt_6160',0x2e,0xa5,1),('GetDeviceBitmapBits',0x2e,0xa5,1)]
 loops=[]
 for anchor,prefix,op,wanted in anchors:
  ls,lo=label(anchor);following=sorted(set(v[1] for v in m.values() if v[0]==ls and v[1]>lo));hi=following[0] if following else len(segments[ls-1]);r=segments[ls-1][lo:hi];pat=bytes([0xe3,4,prefix,op,0xe2,0xfc]);positions=[q.start() for q in re.finditer(re.escape(pat),r)]
  assert len(positions)==wanted,(anchor,lo,hi,positions)
  loops.extend({'segment':ls,'anchor':anchor,'offset':lo+d,'delta':d,'bytes':pat.hex(),'width':op-0xa3,'source':prefix} for d in positions)
 assert len(loops)==10
 # DDA table supplies the true return targets, independently of each push.
 ds,table=label('dda_table');s=segments[ds-1];entries=list(struct.unpack_from('<8H',s,table));ddas=[]
 for i,entry in enumerate(entries):
  hi=entries[i+1] if i<7 else len(s);r=s[entry:hi];matches=list(re.finditer(b'\x2e\xff\x36(..)\xff\x66\xd6',r,re.S));assert len(matches)==1,(i,entry,hi,len(matches));match=matches[0];off=entry+match.start();wordptr=struct.unpack('<H',match.group(1))[0];assert wordptr==off+8;assert struct.unpack_from('<H',s,wordptr)[0]==entry
  ddas.append({'segment':ds,'table_anchor':'dda_table','table_index':i,'return_target':entry,'offset':off,'word_address':wordptr,'bytes':s[off:off+10].hex()})
 common={'candidate':str(a.candidate.resolve()),'candidate_sha256':sha(blob),'map':str(a.map.resolve()),'map_sha256':sha(a.map.read_bytes()),'derived_shifts':shifts,'emitter':{'segment':sg,'anchor':'cblt_3240','offset':base+delta,'delta':delta,'end_label':'cblt_3280','bytes_plus_test_ret':emitter.hex(),'suffix_label':'phase_align','suffix_offset':phoff,'suffix_bytes':suffix.hex()},'loops':loops,'dda_sites':ddas,'limits':['DOSBox-X 8086_prefetch is not true 8088.','This is exact-fragment semantics, not a complete Windows or hardware-interrupt claim.','REP-copy test counts are bounded, with nonoverlapping buffers and no 16-bit address wrap.','Full optional suffix output is inspected rather than executed as a complete graphics routine.']}
 # Base checker: direct shift fragments are wrapped with a test-only RET.
 # Exact emitter bytes are used with optional suffix disabled here.
 text=(P/'templates/base.s').read_text()
 text=re.sub(r'shift1_thunk:.*?emitter:', 'shift1_thunk:\n'+db(bytes.fromhex(shifts[0]['bytes'])+b'\xc3')+'shift2_thunk:\n'+db(bytes.fromhex(shifts[1]['bytes'])+b'\xc3')+'emitter:',text,flags=re.S)
 slots=[]
 for i in range(8):slots.append(f'call_target{i}:\n mov word ptr cs:[target_seen],{i}\n jmp call_returned\ncall_entry{i}:\n'+db(bytes.fromhex('2eff36'))+f'.word call_word{i}\n'+db(bytes.fromhex('ff66d6'))+f'call_word{i}: .word call_target{i}\n jmp fail\n')
 text=re.sub(r'emitter:.*?expected_ax:', 'emitter:\n'+db(emitter)+''.join(slots)+'expected_ax:',text,flags=re.S)
 text=text.replace(' mov [current_entry],ax\n mov word ptr [target_seen]', ' mov [current_entry],ax\n mov ax,[call_targets+bx]\n mov [expected_return_ip],ax\n mov word ptr [target_seen]')
 text=text.replace(' cmp ax,[callee_sp]\n jne fail\n', ' cmp ax,[callee_sp]\n jne fail\n mov ax,[expected_return_ip]\n cmp ax,[callee_return_ip]\n jne fail\n')
 text=text.replace(' pop word ptr cs:[callee_flags]\n ret\nprint:', ''' pop word ptr cs:[callee_flags]
 push bp
 mov bp,sp
 push ax
 mov ax,ss:[bp+2]
 mov cs:[callee_return_ip],ax
 pop ax
 pop bp
 ret
print:''')
 text+='\nexpected_return_ip: .word 0\ncallee_return_ip: .word 0\ncall_targets: .word '+','.join('call_target'+str(i) for i in range(8))+'\n'
 text=text.replace('VGA independent instruction semantics v1; 8086-only test instructions','Source-built VGA MAP-derived instruction semantics; 8086-only test instructions').replace('PASS exact CALL/JMP sites:','PASS source DDA memory-PUSH/JMP sites and callee return IP:')
 baseinfo=build(a.out,'base',text,dict(common,cases=268288,additional_exact_emitter_cases=8,dda_relocations=['CS memory operand and stored return IP relocated into COM; all instruction opcodes retained.']))
 # Full-register, flag, copy and guard-byte tests of exact inline loops plus RET.
 text=(P/'templates/rep.s').read_text();thunks=''.join(f'thunk{i}:\n'+db(bytes.fromhex(row['bytes'])+b'\xc3') for i,row in enumerate(loops))
 text=re.sub(r'thunk0:.*?expected_ax:',thunks+'expected_ax:',text,flags=re.S)
 text=re.sub(r'widths:\n.byte [^\n]*','widths:\n'+db(bytes(x['width'] for x in loops)).rstrip(),text)
 text=re.sub(r'source_bases:\n.byte [^\n]*','source_bases:\n'+db(bytes(0x55 if x['source']==0x26 else 0x11 for x in loops)).rstrip(),text)
 text=text.replace('VGA exact REP+segment trampoline semantics','Source-built VGA exact inline-loop semantics')
 repinfo=build(a.out,'rep',text,dict(common,cases=20480))
 # Full emitter: only MOV SI's absolute data address is relocated. All control
 # transfers and the inline copy loop are exactly the candidate's bytes.
 text=(P/'templates/emitter.s').read_text();new='emitter:\n'+db(emitter[:siat])+'mov si,offset suffix_source\n'+db(emitter[siat+3:])+'suffix_source:\n'+db(suffix)
 text=re.sub(r'emitter:.*?expected_ax:',new+'expected_ax:',text,flags=re.S)
 text=text.replace('VGA emitter full suffix semantics; relocated embedded address and CALL only','Source-built VGA emitter; only embedded source address relocated')
 # Check all unused bytes plus 16-byte leading and trailing canaries.
 text=text.replace('frame: .space 64\ngenerated: .space 48', 'frame: .space 64\ngenerated_guard_before: .space 16\ngenerated: .space 48\ngenerated_guard_after: .space 16')
 text=text.replace(' mov di,offset generated\n mov cx,48\n mov al,0xcc\n rep stosb',' mov di,offset generated_guard_before\n mov cx,80\n mov al,0xcc\n rep stosb')
 text=text.replace(' cmp byte ptr [di],0xcc\n jne fail\n inc word ptr [input]', ''' mov cx,offset generated+64
 sub cx,di
 jcxz source_canaries_done
source_canary_loop:
 cmp byte ptr [di],0xcc
 jne fail
 inc di
 loop source_canary_loop
source_canaries_done:
 mov di,offset generated_guard_before
 mov cx,16
source_leading_canary:
 cmp byte ptr [di],0xcc
 jne fail
 inc di
 loop source_leading_canary
 inc word ptr [input]''')
 emitterinfo=build(a.out,'emitter',text,dict(common,cases=2048,relocations=['Only MOV SI absolute operand adjusted from MAP phase_align to the test suffix_source.']))
 # Independent opcode check: generated rotation instructions are necessarily
 # D0 C0 / D0 C8, never C0 immediate-rotate instructions.
 assert '0xd0,0xc0' in text and '0xd0,0xc8' in text
 (a.out/'EXTRACTION.json').write_text(json.dumps(common,indent=2)+'\n')
 print(json.dumps({'candidate_sha256':sha(blob),'base_com':baseinfo['com_sha256'],'rep_com':repinfo['com_sha256'],'emitter_com':emitterinfo['com_sha256'],'cases':290816,'additional_exact_emitter_cases':8},indent=2))
if __name__=='__main__':main()
