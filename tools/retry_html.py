"""Resume rate-limited W3C checks; honor Retry-After and keep successful results."""
from pathlib import Path
import json,time,ssl,sys,urllib.request,urllib.error,hashlib
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'evidence';V=OUT/'validators'
progress=[json.loads(line) for line in (OUT/'validator-progress.jsonl').read_text().splitlines() if line.startswith('{')]
names=[row['page'] for row in progress if 'service_error' in row]
summary={row['page']:row for row in json.loads((V/'html-summary.json').read_text())}
if '--errors-only' in sys.argv:
 names=[name for name,row in summary.items() if row['errors']]
if '--batch' in sys.argv:
 batch=int(sys.argv[sys.argv.index('--batch')+1]);names=sorted(p.stem for p in (OUT/'html').glob('*.html'))[batch*5:batch*5+5]
for name in names:
 for attempt in range(5):
  request=urllib.request.Request('https://validator.w3.org/nu/?out=json',data=(OUT/'html'/(name+'.html')).read_bytes(),headers={'Content-Type':'text/html; charset=utf-8','User-Agent':'PracticalWork24/1.0'})
  try:
   with urllib.request.urlopen(request,timeout=60,context=ssl.create_default_context()) as response:result=json.load(response)
  except urllib.error.HTTPError as exc:
   if exc.code!=429:raise
   pause=int(exc.headers.get('Retry-After','90'))
   print(json.dumps({'page':name,'rateLimit':True,'retryAfter':pause}),flush=True)
   if pause>600:raise RuntimeError('W3C requests a long pause; retry later')
   for _ in range((pause+29)//30):time.sleep(30)
   continue
  errors=[row for row in result.get('messages',[]) if row.get('type')=='error']
  (V/(name+'.json')).write_text(json.dumps(result,ensure_ascii=False,indent=2))
  summary[name]=dict(page=name,errors=len(errors),messages=errors)
  (V/'html-summary.json').write_text(json.dumps(list(summary.values()),ensure_ascii=False,indent=2))
  print(json.dumps(summary[name],ensure_ascii=False),flush=True);time.sleep(1);break
 else:raise RuntimeError('W3C rate limit did not clear')
assert all(summary[name]['errors']==0 for name in names)
print('Requested final HTML captures pass W3C.',flush=True)
