#!/usr/bin/env python3
"""Independent read-only check of captured E9-generated VGA instruction buffers.
Does not invoke an emulator or trust the supplied disassembly for decoding.
The decoder deliberately accepts only documented 8086 forms needed by these
captures and fails closed on an unknown opcode.
"""
import argparse,collections,hashlib,json,re,struct
from pathlib import Path

def decode(b):
 out=[];p=0
 while p<len(b):
  at=p;prefix=[]
  while p<len(b) and b[p] in (0x26,0x2e,0x36,0x3e,0xf2,0xf3,0xf0):prefix.append(b[p]);p+=1
  assert len(prefix)<=1,('multiple prefixes',at,prefix)
  assert p<len(b);op=b[p];p+=1;target=None;kind='next';stack=0;rotate=None
  if 0x40<=op<=0x5f:
   if 0x50<=op<=0x57:stack=2
   elif 0x58<=op<=0x5f:stack=-2
  elif 0xb0<=op<=0xbf:p+=1 if op<0xb8 else 2
  elif op in (0x04,0x0c,0x14,0x1c,0x24,0x2c,0x34,0x3c):p+=1
  elif op in (0x05,0x0d,0x15,0x1d,0x25,0x2d,0x35,0x3d):p+=2
  elif (0x70<=op<=0x7f) or op in (0xe0,0xe1,0xe2,0xe3,0xeb):
   d=struct.unpack_from('b',b,p)[0];p+=1;target=p+d;kind='jump' if op==0xeb else 'conditional'
  elif op==0xe9:
   d=struct.unpack_from('<h',b,p)[0];p+=2;target=p+d;kind='jump'
  elif op in (0xc3,0xcb):kind='return'
  elif op in (0xa4,0xa5,0xaa,0xab,0xac,0xad,0xec,0xed,0xee,0xef,0x90,0xf8,0xf9,0xfc,0xfd):pass
  elif op in tuple(x for base in (0x00,0x08,0x10,0x18,0x20,0x28,0x30,0x38) for x in range(base,base+4))+(0x80,0x81,0x83,0x84,0x85,0x86,0x87,0x88,0x89,0x8a,0x8b,0x8c,0x8d,0x8e,0x8f,0xc6,0xc7,0xd0,0xd1,0xd2,0xd3,0xf6,0xf7,0xfe,0xff):
   modrm=b[p];p+=1;mod=modrm>>6;reg=(modrm>>3)&7;rm=modrm&7
   p+=2 if mod==2 or (mod==0 and rm==6) else 1 if mod==1 else 0
   if op in (0x80,0x83,0xc6):p+=1
   if op in (0x81,0xc7):p+=2
   if op in (0xc6,0xc7,0x8f):assert reg==0,('invalid group',at,op,reg)
   if op in (0x8c,0x8e):assert reg<4,('non-8086 segment',at,reg)
   if op in (0xd0,0xd1,0xd2,0xd3):assert reg!=6,('undocumented shift',at)
   if op in (0xf6,0xf7):
    assert reg!=1
    if reg==0:p+=1 if op==0xf6 else 2
   if op==0x8f:stack=-2
   if op==0xfe:assert reg<2
   if op==0xff:
    assert reg in (0,1,6),('indirect control transfer cannot be bounded here',at,reg)
    if reg==6:stack=2
   if op==0xd0 and modrm in (0xc0,0xc8):rotate='rol' if modrm==0xc0 else 'ror'
  else:raise AssertionError(('unsupported or unknown 8086 opcode',hex(at),hex(op)))
  assert p<=len(b),('truncated instruction',at,p,len(b))
  out.append({'offset':at,'end':p,'opcode':op,'prefix':prefix,'kind':kind,'target':target,'stack_delta':stack,'rotate':rotate,'hex':b[at:p].hex()})
 return out

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--marker',choices=['VGA','EGA'],default='VGA',help='Exact diagnostic record prefix; EGA permits the inherited logger marker');ap.add_argument('--log',type=Path,required=True);ap.add_argument('--buffers',type=Path,required=True);ap.add_argument('--output',type=Path,required=True);a=ap.parse_args()
 data=a.log.read_text();payload=''.join(line.split('LOG: Bochs port E9h: ',1)[1].strip() for line in data.splitlines() if 'LOG: Bochs port E9h: ' in line)
 headers=list(re.finditer(re.escape(a.marker)+r':([0-9A-F]{4}):([0-9A-F]{4}):([0-9A-F]{4}):([0-9A-F]{4}):',payload));assert len(headers)==64
 rows=[];opcodecounts=collections.Counter();rotates=0;groups=0;branches=0;instructions=0
 for i,h in enumerate(headers):
  sg,off,n,phase=(int(x,16) for x in h.groups());raw=payload[h.end():headers[i+1].start() if i+1<len(headers) else len(payload)]
  assert re.fullmatch(r'[0-9A-F]*',raw) and len(raw)==4*n,(i,n,len(raw))
  words=[int(raw[j:j+4],16) for j in range(0,len(raw),4)];assert all(x<=255 for x in words)
  b=bytes(words);assert b==(a.buffers/f'BUFFER{i:02}.bin').read_bytes();assert 0<n<=600 and off+n<=65536 and 1<=phase<=7
  ins=decode(b);offsets={x['offset']:x for x in ins};assert ins[-1]['opcode']==0xcb and ins[-1]['offset']==len(b)-1;assert sum(x['kind']=='return' for x in ins)==1
  edges={};bc=0
  for x in ins:
   opcodecounts[f'{x["opcode"]:02X}']+=1
   successors=[] if x['kind']=='return' else [x['target']] if x['kind']=='jump' else [x['end'],x['target']] if x['kind']=='conditional' else [x['end']]
   assert all(t in offsets for t in successors),(i,x,successors)
   edges[x['offset']]=successors;bc+=x['target'] is not None
  # All syntactic paths share a consistent stack depth at join/loop targets,
  # and the generated far-return endpoint is reached with balanced data pushes.
  pending=[(0,0)];seen={}
  while pending:
   pos,depth=pending.pop()
   if pos in seen:assert seen[pos]==depth,(i,pos,seen[pos],depth);continue
   seen[pos]=depth;x=offsets[pos];after=depth+x['stack_delta'];assert after>=0,(i,pos,after)
   if x['kind']=='return':assert after==0
   pending.extend((nxt,after) for nxt in edges[pos])
  assert ins[-1]['offset'] in seen and len(seen)==len(ins),(i,'unreachable instructions')
  # Every contiguous AL-rotation group implements the header phase using the
  # shortest-direction count-one sequence, without an immediate-count opcode.
  expected_direction='rol' if phase<=4 else 'ror';expected_count=phase if phase<=4 else 8-phase;gs=[];j=0
  while j<len(ins):
   if ins[j]['rotate']:
    direction=ins[j]['rotate'];run=0
    while j<len(ins) and ins[j]['rotate']==direction:run+=1;j+=1
    assert direction==expected_direction and run==expected_count,(i,direction,run,phase);gs.append(run)
   else:j+=1
  assert gs;rc=sum(gs);rotates+=rc;groups+=len(gs);branches+=bc;instructions+=len(ins)
  rows.append({'index':i,'length':n,'phase':phase,'sha256':hashlib.sha256(b).hexdigest(),'instructions':len(ins),'rotation_groups':len(gs),'single_bit_rotates':rc,'branches':bc,'all_branches_internal_and_aligned':True,'balanced_stack_at_far_return':True})
 result={'passed':True,'record_marker':a.marker,'records':len(rows),'host_log_sha256':hashlib.sha256(a.log.read_bytes()).hexdigest(),'phases':sorted({r['phase'] for r in rows}),'minimum_length':min(r['length'] for r in rows),'maximum_length':max(r['length'] for r in rows),'reserved_bytes':600,'minimum_unused_reservation':600-max(r['length'] for r in rows),'instruction_count':instructions,'single_bit_rotates':rotates,'phase_correct_rotation_groups':groups,'branch_count':branches,'unsupported_or_unknown_opcodes':0,'all_bytes_match_independently_normalized_log':True,'all_buffers_end_with_far_return':True,'all_control_flow_targets_internal_and_instruction_aligned':True,'all_reachable_stack_depths_consistent_and_balanced_at_return':True,'opcode_counts':dict(sorted(opcodecounts.items())),'limits':['Diagnostic-only pre-execution snapshots, not a dynamic execution trace.','First 64 nonzero-phase buffers; phase 0 is intentionally not logged.','Observed generated extent is below600, but no capture guard bytes or exhaustive maximum-size proof are present.','Does not prove arbitrary input behavior, physical8088 timing, or interrupt interleavings.'],'buffers':rows}
 a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:v for k,v in result.items() if k not in ('buffers','opcode_counts')},indent=2))
if __name__=='__main__':main()
