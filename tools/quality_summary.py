"""Build a readable index from the real attached check results."""
from pathlib import Path
import json,html,re,hashlib
R=Path(__file__).resolve().parents[1];E=R/'evidence';V=E/'validators'
browser=json.loads((E/'browser-checks.json').read_text());pages=json.loads((E/'pages.json').read_text());validation=json.loads((V/'html-summary.json').read_text());css=json.loads((V/'css.json').read_text())['cssvalidation'];lh=json.loads((E/'lighthouse/summary.json').read_text());tests=(E/'django-tests.txt').read_text();count=int(re.search(r'Ran (\d+) tests',tests)[1])
assert len(pages)==25 and len(browser['checks'])==125 and not browser['failures']
assert len(validation)==25 and not any(row['errors'] for row in validation)
assert css['validity'] and css['result']['errorcount']==0
assert len(lh)>=3 and all(row['performance']>=85 and row['accessibility']>=85 for row in lh)
assert count>=13 and '\nOK\n' in tests
summary=dict(pages=25,browserChecks=125,browserFailures=0,screenshots=50,htmlPages=25,htmlErrors=0,cssErrors=0,cssWarnings=css['result']['warningcount'],serverTests=count,lighthouse=[{k:row[k] for k in ['page','performance','accessibility']} for row in lh],sourceHashes={name:hashlib.sha256((R/name).read_bytes()).hexdigest() for name in ['static/css/site.css','static/js/site.js','requirements.txt']})
(E/'quality-summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2))
style='<style>body{max-width:1100px;margin:32px auto;padding:0 20px;color:#1c2430;font:16px/1.5 system-ui}table{border-collapse:collapse;width:100%}th,td{text-align:left;padding:10px;border:1px solid #d8dee6}a{color:#1f5fad}code{overflow-wrap:anywhere}</style>'
text='<!doctype html><html lang="ru"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Проверки W3C</title>'+style+'<h1>Отчёты официальных валидаторов W3C</h1><p>HTML отправлен в validator.w3.org/nu. CSRF-токены заменены на REDACTED. Ниже ссылки на исходные ответы сервиса.</p><table><tr><th>Страница</th><th>Ошибки</th><th>Ответ W3C</th></tr>'
for row in sorted(validation,key=lambda r:r['page']):text+=f'<tr><td>{html.escape(row["page"])}</td><td>{row["errors"]}</td><td><a href="{row["page"]}.json">JSON</a></td></tr>'
text+='</table><h2>CSS</h2><p>Сервис: jigsaw.w3.org/css-validator. Проверен реальный файл site.css в режиме CSS3, загрузкой файла.</p>'+f'<p>Ошибок: 0. Предупреждений: {css["result"]["warningcount"]}. Валидность: true.</p><p><a href="css.json">Полный ответ CSS Validator</a></p>'
(V/'index.html').write_text(text+'</html>')
text='<!doctype html><html lang="ru"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Материалы проверки · Вариант 24</title>'+style+'<h1>Занятия 7–9 · Материалы проверки</h1><p>25 страниц, 125 проверок адаптивности, 50 скриншотов, HTML и CSS без ошибок, '+str(count)+' серверных тестов.</p><p><a href="validators/index.html">Валидаторы W3C</a> · <a href="comparison/index.html">Сравнение с макетами</a> · <a href="browser-checks.json">Проверки Chromium</a> · <a href="django-tests.txt">Серверные тесты</a></p><h2>Скриншоты всех страниц</h2><table><tr><th>Страница</th><th>Телефон</th><th>Компьютер</th></tr>'
for row in pages:text+=f'<tr><td>{row["key"]}</td><td><a href="screenshots/375/{row["key"]}.png">375 px</a></td><td><a href="screenshots/1440/{row["key"]}.png">1440 px</a></td></tr>'
text+='</table><h2>Мобильный Lighthouse</h2><table><tr><th>Страница</th><th>Performance</th><th>Accessibility</th><th>Полный отчёт</th></tr>'
for row in lh:text+=f'<tr><td>{row["page"]}</td><td>{row["performance"]}</td><td>{row["accessibility"]}</td><td><a href="lighthouse/{row["page"]}.html">HTML</a></td></tr>'
(E/'index.html').write_text(text+'</table></html>')
print(json.dumps(summary,ensure_ascii=False))
