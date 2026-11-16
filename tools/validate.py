"""Submit captured HTML and the real stylesheet to the official W3C services."""
from pathlib import Path
import urllib.request,urllib.parse,urllib.error,json,time,sys,ssl,uuid
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'evidence';(OUT/'validators').mkdir(exist_ok=True)
summary=[]
for p in ([] if '--css-only' in sys.argv else sorted((OUT/'html').glob('*.html'))):
 request=urllib.request.Request('https://validator.w3.org/nu/?out=json',data=p.read_bytes(),headers={'Content-Type':'text/html; charset=utf-8','User-Agent':'PracticalWork24/1.0'})
 try:
  with urllib.request.urlopen(request,timeout=60) as response:result=json.load(response)
 except Exception as exc:
  print(json.dumps({'page':p.stem,'service_error':str(exc)}),flush=True);continue
 (OUT/'validators'/(p.stem+'.json')).write_text(json.dumps(result,ensure_ascii=False,indent=2))
 errors=[m for m in result.get('messages',[]) if m.get('type')=='error'];summary.append(dict(page=p.stem,errors=len(errors),messages=errors))
 print(json.dumps(summary[-1],ensure_ascii=False),flush=True);time.sleep(1)
if summary: (OUT/'validators/html-summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2))

# The public service rejects text POSTs on some deployments. Use its file-upload protocol.
boundary='----practica'+uuid.uuid4().hex
parts=[]
for name,value in [('output','json'),('profile','css3'),('warning','1')]:
 parts.append(f'--{boundary}\r\nContent-Disposition: form-data; name="{name}"\r\n\r\n{value}\r\n'.encode())
parts.append(f'--{boundary}\r\nContent-Disposition: form-data; name="file"; filename="site.css"\r\nContent-Type: text/css\r\n\r\n'.encode()+(ROOT/'static/css/site.css').read_bytes()+f'\r\n--{boundary}--\r\n'.encode())
request=urllib.request.Request('https://jigsaw.w3.org/css-validator/validator',data=b''.join(parts),headers={'Content-Type':f'multipart/form-data; boundary={boundary}'})
with urllib.request.urlopen(request,timeout=90,context=ssl.create_default_context()) as response:body=response.read().decode()
(OUT/'validators/css.json').write_text(body)
result=json.loads(body)['cssvalidation'];print(json.dumps({'cssValid':result['validity'],**result['result']},ensure_ascii=False),flush=True)
