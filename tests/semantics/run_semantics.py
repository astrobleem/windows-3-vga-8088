#!/usr/bin/env python3
"""Run a generated DOS semantics COM with an owned-child POSIX emulator guard.
Requires an existing nonempty shared lease file and an installed DOSBox-X.
Never initializes a lease, never stops another owner's process, and refuses an
existing live emulator. Coordinate use with other emulator owners beforehand.
"""
import argparse,datetime,fcntl,hashlib,json,os,re,shutil,signal,subprocess
from pathlib import Path

def main():
 ap=argparse.ArgumentParser(description=__doc__)
 ap.add_argument('--dosbox',type=Path,required=True)
 ap.add_argument('--lease',type=Path,required=True)
 ap.add_argument('--build',type=Path,required=True)
 ap.add_argument('--out',type=Path,required=True)
 ap.add_argument('--timeout',type=int,default=120)
 ap.add_argument('--expect-failure-stage',type=int)
 a=ap.parse_args()
 if not 1<=a.timeout<=300:ap.error('--timeout must be between 1 and 300 seconds')
 a.out=a.out.resolve();exe=a.dosbox.resolve();a.out.mkdir(parents=True,exist_ok=False)
 build=json.loads((a.build/'BUILD.json').read_text());com=(a.build/'SEMANTIC.COM').read_bytes()
 if hashlib.sha256(com).hexdigest()!=build['com_sha256']:raise ValueError('Test COM does not match BUILD.json')
 if hashlib.sha256(Path(build['candidate']).read_bytes()).hexdigest()!=build['candidate_sha256']:raise ValueError('Driver changed since test extraction')
 if hashlib.sha256(Path(build['map']).read_bytes()).hexdigest()!=build['map_sha256']:raise ValueError('MAP changed since test extraction')
 if bool(build.get('negative_control'))!=(a.expect_failure_stage is not None):raise ValueError('Positive/negative expectation differs from BUILD.json')
 if a.expect_failure_stage is not None and build['expected_failure_stage']!=a.expect_failure_stage:raise ValueError('Negative failure stage differs from BUILD.json')
 shutil.copy2(a.build/'SEMANTIC.COM',a.out/'SEMANTIC.COM');shutil.copy2(a.build/'BUILD.json',a.out/'BUILD.json')
 config=a.out/'SEMANTIC.CONF'
 config.write_text('''[sdl]\noutput=surface\nfullscreen=false\n[dosbox]\nmachine=vgaonly\nsplash logo=false\nshow basic information=false\n[render]\nscaler=none\n[cpu]\ncore=normal\ncputype=8086_prefetch\ncycles=max\n[mixer]\nnosound=true\n[midi]\nmididevice=none\n[joystick]\njoysticktype=none\n[autoexec]\nmount c "'''+str(a.out)+'''"\nc:\nSEMANTIC.COM > RESULT.TXT\nexit\n''')
 result={'started':datetime.datetime.now(datetime.timezone.utc).isoformat(),'emulator':str(exe),'config':str(config),'emulator_sha256':hashlib.sha256(exe.read_bytes()).hexdigest(),'timeout':a.timeout,'platform':'posix'}
 child=None
 try:
  with a.lease.open('rb') as lease:
   if not lease.read(1):raise ValueError('Shared lease is empty; do not initialize it here')
   fcntl.flock(lease.fileno(),fcntl.LOCK_EX|fcntl.LOCK_NB);result['lease_acquired']=True
   try:
    inv=subprocess.run(['ps','-eo','stat=,comm='],capture_output=True,text=True,timeout=10)
    if inv.returncode:raise RuntimeError('Emulator process inventory unavailable')
    matches=[]
    for line in inv.stdout.splitlines():
     parts=line.strip().split(None,1)
     if len(parts)==2 and not parts[0].startswith('Z') and re.fullmatch(r'(?i)(dosbox-x|dosbox|86box|pcem|tandybox|fixbox|traceio|mesen|mesen2)',parts[1]):matches.append(line)
    result['inventory']=matches
    if matches:raise RuntimeError('Existing emulator found; wait for its owner')
    env=os.environ.copy();env.update(SDL_VIDEODRIVER='dummy',SDL_AUDIODRIVER='dummy')
    with (a.out/'HOST.LOG').open('wb') as log:
     child=subprocess.Popen([str(exe),'-defaultconf','-nopromptfolder','-conf',str(config)],cwd=a.out,stdout=log,stderr=subprocess.STDOUT,env=env,start_new_session=True)
     result['pid']=child.pid;result['return']=child.wait(timeout=a.timeout)
   finally:
    if child is not None and child.poll() is None:
     os.killpg(child.pid,signal.SIGKILL);child.wait(timeout=5);result['watchdog']=True
    result['owned_child_stopped']=child is None or child.poll() is not None
    fcntl.flock(lease.fileno(),fcntl.LOCK_UN);result['lease_released']=True
 except Exception as error:result['error']=str(error)
 (a.out/'PROCESS.JSON').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result),flush=True)
 if result.get('return')!=0 or 'error' in result:raise SystemExit('Emulator did not complete normally; see PROCESS.JSON')
 output=(a.out/'RESULT.TXT').read_text();print(output)
 if a.expect_failure_stage is None:
  if 'ALL PASS:' not in output or 'FAIL stage=' in output:raise SystemExit('Guest did not pass all cases')
 elif f'FAIL stage={a.expect_failure_stage:04X}' not in output or 'ALL PASS:' in output:raise SystemExit('Negative control did not fail at the expected stage')
 (a.out/'PASS.json').write_text(json.dumps({'passed':True,'negative_control':a.expect_failure_stage is not None,'expected_failure_stage':a.expect_failure_stage,'cpu_model':'8086_prefetch','not_true_8088':True,'result':output,'candidate_sha256':build['candidate_sha256'],'map_sha256':build['map_sha256'],'com_sha256':build['com_sha256']},indent=2)+'\n')
if __name__=='__main__':main()
