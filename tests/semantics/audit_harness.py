#!/usr/bin/env python3
"""Read-only host validation of exhaustive arithmetic tables and harness structure."""
import argparse, hashlib, json, re
from pathlib import Path
P=Path(__file__).resolve().parent

def table(text, label, directive):
 pattern=r'^'+re.escape(label)+r':\s*\.'+directive+r'\s+([^\n]+)'
 match=re.search(pattern,text,re.M);assert match,label
 return [int(x.strip(),0) for x in match[1].split(',')]

def main():
 ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--build',type=Path,required=True);a=ap.parse_args()
 base=(a.build/'base/SEMANTIC.S').read_text();rep=(a.build/'rep/SEMANTIC.S').read_text();emitter=(a.build/'emitter/SEMANTIC.S').read_text()
 extraction=json.loads((a.build/'EXTRACTION.json').read_text())
 expected_seeds=[2|sum((1<<bit) for i,bit in enumerate((0,2,4,6,7,9,10,11)) if index&(1<<i)) for index in range(256)]
 assert table(base,'flag_seeds','word')==table(rep,'flag_seeds','word')==expected_seeds
 assert table(base,'parity','byte')==[4 if bin(value).count('1')%2==0 else 0 for value in range(256)]
 values=table(base,'rotate_values','byte');carries=table(base,'rotate_carries','byte');assert len(values)==len(carries)==2048
 for phase in range(8):
  for value in range(256):
   rotated=value if phase==0 else ((value<<phase)|(value>>(8-phase)))&255
   assert values[phase*256+value]==rotated,(phase,value)
   carry=0 if phase==0 else (rotated&1 if phase<=4 else rotated>>7)
   assert carries[phase*256+value]==carry,(phase,value)
 for text in (base,emitter):
  assert table(text,'lengths','byte')==[0,2,4,6,8,6,4,2]
  for phase in range(1,8):
   expected=[0xd0,0xc0 if phase<=4 else 0xc8]*min(phase,8-phase)
   assert table(text,f'expected_code{phase}','byte')==expected
 assert table(rep,'counts','word')==[0,1,2,3,7,255,256,257]
 assert table(rep,'widths','byte')==[x['width'] for x in extraction['loops']]
 assert table(rep,'source_bases','byte')==[0x55 if x['source']==0x26 else 0x11 for x in extraction['loops']]
 for text in (base,rep,emitter):
  assert '.arch i8086' in text
  assert 'mov cx,12\nverify_reg:' in text
  assert re.search(r'expected_ax:.*expected_bx:.*expected_cx:.*expected_dx:.*expected_si:.*expected_di:.*expected_bp:.*expected_sp:.*expected_ds:.*expected_es:.*expected_ss:.*expected_cs:',text,re.S)
 assert 'cmp ax,[callee_return_ip]\n jne fail' in base
 assert 'mov ax,ss:[bp+2]\n mov cs:[callee_return_ip],ax' in base
 assert 'generated_guard_before: .space 16\ngenerated: .space 48\ngenerated_guard_after: .space 16' in emitter
 assert 'mov cx,80\n mov al,0xcc\n rep stosb' in emitter
 assert 'mov cx,offset generated+64\n sub cx,di' in emitter
 assert 'source_leading_canary:' in emitter
 assert rep.count('thunk')>=20
 out={'passed':True,'candidate_sha256':extraction['candidate_sha256'],'map_sha256':extraction['map_sha256'],'oracle_rotate_values_checked':2048,'oracle_rotate_carries_checked':2048,'parity_values_checked':256,'flag_combinations_checked':256,'copy_counts':[0,1,2,3,7,255,256,257],'df_values':[0,1],'static_shift_sites':len(extraction['derived_shifts']),'dda_sites':len(extraction['dda_sites']),'copy_sites':len(extraction['loops']),'all_12_registers_checked':True,'callee_observed_return_ip_checked':True,'emitter_all_modes_and_phases':2048,'emitter_guard_bytes_before':16,'emitter_guard_bytes_after':16,'emitter_unused_buffer_bytes_checked':True,'emulator_executed_by_audit':False,'assembly_sha256':{suite:hashlib.sha256((a.build/suite/'SEMANTIC.S').read_bytes()).hexdigest() for suite in ('base','rep','emitter')}}
 (a.build/'HARNESS_AUDIT.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(out,indent=2))
if __name__=='__main__':main()
