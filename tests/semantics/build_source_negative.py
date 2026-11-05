#!/usr/bin/env python3
"""Mutate only copied test COMs to prove the source checker rejects defects."""
from pathlib import Path
import argparse,hashlib,json
P=Path(__file__).resolve().parent
ap=argparse.ArgumentParser();ap.add_argument('--build',type=Path,default=P/'build');a=ap.parse_args()
for name,suite,old,new,stage,why in [
 ('negative_shift','base','d1ead1ead1eac3','d1e2d1ead1eac3',1,'Replace first SHR DX,1 with SHL DX,1.'),
 ('negative_prefix','rep','e30426a4e2fcc3','e3043ea4e2fcc3',5,'Replace first ES source override with DS.'),
 ('negative_rotate','emitter','b8d0c0','b8d0c8',6,'Make emitter choose ROR when it should choose ROL.')]:
 src=a.build/suite;out=a.build/name;out.mkdir(exist_ok=True);original=(src/'SEMANTIC.COM').read_bytes();old=bytes.fromhex(old);new=bytes.fromhex(new);off=original.index(old)
 if name=='negative_rotate':assert original.count(old)==1
 mutant=original[:off]+new+original[off+len(old):];(out/'SEMANTIC.COM').write_bytes(mutant)
 meta=json.loads((src/'BUILD.json').read_text());meta.update(negative_control=True,mutation={'description':why,'com_file_offset':off,'old':old.hex(),'new':new.hex()},expected_failure_stage=stage,original_com_sha256=hashlib.sha256(original).hexdigest(),com_sha256=hashlib.sha256(mutant).hexdigest());(out/'BUILD.json').write_text(json.dumps(meta,indent=2)+'\n')
 print(name,'expected failure stage',stage)
