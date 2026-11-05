#!/usr/bin/env python3
"""Compare two completed VGA EGAQA capture directories without Windows files."""
from pathlib import Path
import argparse,hashlib,json

def validate(path):
 log=(path/'QA.LOG').read_text(errors='replace')
 expected=['REAL_MODE=1','WIDTH=640','HEIGHT=480','COLORS=16','FAILURES=0','COMPLETE=1']
 if any(line not in log.splitlines() for line in expected):raise ValueError('GUI run did not complete successfully: '+str(path))
 if 'BLIT_FAIL=' in log or 'QA_ABORT=' in log:raise ValueError('GUI API failure: '+str(path))
 if sum(line.startswith('FRAME=') for line in log.splitlines())!=8:raise ValueError('Incorrect GUI frame count')
 return log

def main():
 ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('reference',type=Path);ap.add_argument('candidate',type=Path);ap.add_argument('--output',type=Path);a=ap.parse_args()
 report={'reference':a.reference.name,'candidate':a.candidate.name,'reference_log':validate(a.reference),'candidate_log':validate(a.candidate),'frames':[],'all_equal':True}
 for i in range(8):
  x=(a.reference/f'P{i:02}.BIN').read_bytes();y=(a.candidate/f'P{i:02}.BIN').read_bytes()
  if len(x)!=153600 or len(y)!=153600:raise ValueError('Unexpected four-plane capture size')
  item={'frame':i,'bytes':len(x),'reference_sha256':hashlib.sha256(x).hexdigest(),'candidate_sha256':hashlib.sha256(y).hexdigest(),'equal':x==y}
  report['frames'].append(item);report['all_equal'] &= x==y
 text=json.dumps(report,indent=2)+'\n';print(text,end='')
 if a.output:a.output.write_text(text)
 if not report['all_equal']:raise SystemExit(1)
if __name__=='__main__':main()
