from pathlib import Path
import re,json,subprocess,hashlib,argparse
ap=argparse.ArgumentParser(description='Normalize diagnostic VGA captures using the inherited EGA E9 record marker.');ap.add_argument('--host-log',type=Path,required=True);ap.add_argument('--input',type=Path,required=True,help='JSON containing diagnostic driver sha256');ap.add_argument('--out',type=Path,required=True);a=ap.parse_args();out=a.out;out.mkdir(parents=True,exist_ok=False)
chunks=[]
for line in a.host_log.read_text(errors='replace').splitlines():
 if 'Bochs port E9h: ' in line:
  s=line.split('Bochs port E9h: ',1)[1]
  if s.startswith('EGA:'):chunks.append(s)
  elif chunks:chunks[-1]+=s
records=[]
for i,s in enumerate(chunks):
 _,seg,off,n,phase,data=s.split(':');n=int(n,16)
 assert len(data)==4*n,(i,n,len(data))
 b=bytes(int(data[j:j+4],16) for j in range(0,len(data),4));assert b[-1]==0xcb
 f=out/f'BUFFER{i:02}.bin';f.write_bytes(b)
 dis=subprocess.check_output(['objdump','-D','-b','binary','-m','i8086','-Mintel',str(f)],text=True)
 (out/f'BUFFER{i:02}.asm').write_text(dis.replace(str(f),'captured-buffer'))
 assert '(bad)' not in dis
 rows=[line for line in dis.splitlines() if re.match(r'^\s*[0-9a-f]+:\s',line)]
 unsupported=[];rot=[]
 for line in rows:
  z=line.split('\t');raw=bytes.fromhex(z[1]);mn=' '.join(z[2:])
  prefixes=[];op=0
  while op<len(raw) and raw[op] in (0x26,0x2e,0x36,0x3e,0xf0,0xf2,0xf3):prefixes.append(raw[op]);op+=1
  if op==len(raw) or raw[op] in set(range(0x60,0x70))|{0x0f,0xc0,0xc1,0xc8,0xc9,0xf1}:unsupported.append(line)
  if any(v in (0xf2,0xf3) for v in prefixes) and len(prefixes)>1:unsupported.append(line)
  if raw[0]==0xd0 and len(raw)>1 and raw[1] in (0xc0,0xc8):rot.append(mn)
 assert not unsupported
 records.append(dict(index=i,segment=seg,offset=off,length=n,phase=int(phase,16),sha256=hashlib.sha256(b).hexdigest(),instructions=len(rows),single_bit_rotates=len(rot)))
assert len(records)==64
summary=dict(diagnostic_only=True,release_driver_unchanged=True,trace_driver_sha256=json.loads(a.input.read_text())['sha256'],capture='Exact bytes after generation, before execution, logged at source CBLT cblt_6420',records=len(records),phases=sorted({r['phase'] for r in records}),maximum_observed_length=max(r['length'] for r in records),single_bit_rotates=sum(r['single_bit_rotates'] for r in records),unsupported_encodings=0,limitations='Bounded first 64 nonzero-phase generated buffers; not an execution trace or exhaustive maximum-size proof',buffers=records)
(out/'SUMMARY.json').write_text(json.dumps(summary,indent=2)+'\n');print(json.dumps({k:v for k,v in summary.items() if k!='buffers'},indent=2))
