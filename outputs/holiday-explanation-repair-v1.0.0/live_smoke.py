"""One synthetic, third-person holiday example; normal provider limits apply."""
import json
import argparse
from pathlib import Path
from unittest.mock import patch
from backend.application.service import ApplicationService
from backend.application.controls import CancellableTransport

ROOT=Path(__file__).resolve().parents[2]
QUESTION='A private-sector employer refuses to pay a worker for Christmas Day because the office was closed and no work was performed. What holiday-pay rules and exceptions apply?'
captures=[]

class Capture(CancellableTransport):
    def __call__(self,request,timeout):
        body=json.loads(request.data)
        payload=json.loads(body['messages'][-1]['content'])
        if payload.get('question_text',payload.get('question'))!=QUESTION:raise RuntimeError('Unexpected question')
        result=super().__call__(request,timeout)
        captures.append({'request':body,'response':result})
        return result

def main(name):
    out=Path(__file__).resolve().parent
    packet_path=out/(name+'-packet.json')
    if packet_path.exists():raise RuntimeError('Choose a new smoke name; preserve earlier attempts')
    service=ApplicationService.configured()
    with patch('backend.application.service.CancellableTransport',Capture):
        packet=service.chat({'question_text':QUESTION,'request_id':'holiday-repair-live-smoke','use_ai':True,'save_history':False})
    private=ROOT/('.local/website/holiday-provider-debug-'+name+'.json')
    private.write_text(json.dumps(captures,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    packet_path.write_text(json.dumps(packet,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'explanation':{k:v for k,v in packet['explanation'].items() if k!='claims'},
        'claims':len(packet['explanation']['claims']),'components':len(packet['result']['components']),
        'references':sum(len(c['candidates']) for c in packet['result']['components']),
        'time_ms':packet['total_query_ms'],'network_requests':packet['network_requests']}))

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--name',required=True,choices=['live-smoke-conditional','live-smoke-final','live-smoke-source-hold','live-smoke-qualification-revision','live-smoke-schema-bound'])
    main(parser.parse_args().name)
