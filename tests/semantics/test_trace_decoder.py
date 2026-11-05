#!/usr/bin/env python3
"""Read-only fail-closed tests for the limited generated-buffer decoder."""
import argparse, json, struct
from pathlib import Path
from verify_generated_trace import decode
P=Path(__file__).resolve().parent

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--out',type=Path,default=P/'TRACE_DECODER_SELFTEST.json');a=ap.parse_args()
 rejected=['c0c003','c1e803','6601c0','0f','d0f0','b834','26f3a4','60','8ee0','fff0ff','ff16ff00']
 for value in rejected:
  try: decode(bytes.fromhex(value))
  except (AssertionError,IndexError,struct.error):pass
  else:raise AssertionError(('decoder accepted forbidden or malformed control',value))
 valid='d0c0d0c8cb';rows=decode(bytes.fromhex(valid));assert len(rows)==3 and rows[0]['rotate']=='rol' and rows[1]['rotate']=='ror' and rows[2]['kind']=='return'
 # Prefixes remain attached to a single MOVS instruction, not separate bytes.
 assert decode(bytes.fromhex('26a42ea5'))==[
  {'offset':0,'end':2,'opcode':0xa4,'prefix':[0x26],'kind':'next','target':None,'stack_delta':0,'rotate':None,'hex':'26a4'},
  {'offset':2,'end':4,'opcode':0xa5,'prefix':[0x2e],'kind':'next','target':None,'stack_delta':0,'rotate':None,'hex':'2ea5'}]
 out={'passed':True,'rejected_encodings':rejected,'valid_control':valid,'single_override_movs_control':'26a42ea5','emulator_executed':False};a.out.write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(out,indent=2))
if __name__=='__main__':main()
