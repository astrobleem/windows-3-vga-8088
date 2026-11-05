#!/usr/bin/env python3
"""Test-only wrong-return-IP mutant; preserve the landing marker to isolate IP check."""
import argparse, hashlib, json, re, struct, subprocess
from pathlib import Path
P=Path(__file__).resolve().parent

def main():
 ap=argparse.ArgumentParser(description=__doc__)
 ap.add_argument('--build',type=Path,default=P/'build')
 a=ap.parse_args(); src=a.build/'base'; out=a.build/'negative_dda_return'
 original=(src/'SEMANTIC.COM').read_bytes()
 symbols={name:int(value,16) for name,value in re.findall(r'^(\S+)\s+[tT]\s+([0-9a-fA-F]+)\s*$',subprocess.check_output(['nm','-P',str(src/'SEMANTIC.O')],text=True),re.M)}
 word=symbols['call_word0']; target0=symbols['call_target0']+0x100; target1=symbols['call_target1']+0x100
 assert struct.unpack_from('<H',original,word)[0]==target0
 # The wrong return destination remains valid code, so the subject cannot hang.
 # Change target1's diagnostic marker to zero. This prevents the separate
 # target_seen check from rejecting first; callee_return_ip must reject it.
 marker=symbols['call_target1']; assert original[marker:marker+3]==bytes.fromhex('2ec706')
 assert struct.unpack_from('<H',original,marker+5)[0]==1
 mutant=bytearray(original);struct.pack_into('<H',mutant,word,target1);struct.pack_into('<H',mutant,marker+5,0)
 out.mkdir(parents=True,exist_ok=False);(out/'SEMANTIC.COM').write_bytes(mutant)
 meta=json.loads((src/'BUILD.json').read_text());meta.update(suite='negative_dda_return',negative_control=True,expected_failure_stage=4,original_com_sha256=hashlib.sha256(original).hexdigest(),com_sha256=hashlib.sha256(mutant).hexdigest(),mutation={'description':'Push a different valid return IP while preserving target_seen=0, requiring the callee-observed return-IP check to reject it.','stored_return_word_com_offset':word,'old_return_ip':target0,'new_return_ip':target1,'diagnostic_marker_com_offset':marker+5,'old_marker':1,'new_marker':0})
 (out/'BUILD.json').write_text(json.dumps(meta,indent=2)+'\n');print('negative_dda_return expected failure stage 4')
if __name__=='__main__':main()
