import fs from 'node:fs';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
const {default:lighthouse}=await import('lighthouse').catch(()=>import('/tmp/practica-qa/node_modules/lighthouse/core/index.js'));
const {launch}=await import('chrome-launcher').catch(()=>import('/tmp/practica-qa/node_modules/chrome-launcher/dist/index.js'));
const {chromium}=await import('playwright').catch(()=>import('/tmp/practica-qa/node_modules/playwright/index.mjs'));
const ROOT=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'..'),OUT=path.join(ROOT,'evidence','lighthouse'),BASE=process.env.SITE_URL||'http://127.0.0.1:8024';
fs.mkdirSync(OUT,{recursive:true});
let rows=JSON.parse(fs.readFileSync(path.join(ROOT,'evidence/pages.json'),'utf8')).filter(row=>row.status===200);
if(process.argv[2])rows=rows.filter(row=>process.argv.slice(2).includes(row.key));
const summary=[];
for(const row of rows){
 const chrome=await launch({chromePath:process.env.CHROME_PATH||(fs.existsSync('/run/current-system/sw/bin/chromium')?'/run/current-system/sw/bin/chromium':undefined),chromeFlags:['--headless=new','--no-sandbox','--disable-dev-shm-usage']});
 try{
  const browser=await chromium.connectOverCDP('http://127.0.0.1:'+chrome.port);const context=browser.contexts()[0];
  if(row.role){const r=await context.request.get(BASE+'/accounts/login/');const html=await r.text();const csrf=html.match(/name="csrfmiddlewaretoken" value="([^"]+)"/)[1];await context.request.post(BASE+'/accounts/login/',{form:{username:row.role,password:'demo-pass-24',csrfmiddlewaretoken:csrf},headers:{Referer:BASE+'/accounts/login/'}});}
  const result=await lighthouse(BASE+row.url,{port:chrome.port,output:['html','json'],onlyCategories:['performance','accessibility'],formFactor:'mobile',disableStorageReset:true,logLevel:'error',throttlingMethod:'simulate'});
  fs.writeFileSync(path.join(OUT,row.key+'.html'),result.report[0]);fs.writeFileSync(path.join(OUT,row.key+'.json'),result.report[1]);
  const score={page:row.key,url:result.lhr.finalDisplayedUrl,performance:Math.round(result.lhr.categories.performance.score*100),accessibility:Math.round(result.lhr.categories.accessibility.score*100),failedAudits:Object.values(result.lhr.audits).filter(a=>a.scoreDisplayMode==='binary'&&a.score===0).map(a=>({id:a.id,title:a.title,details:a.details})),runtimeError:result.lhr.runtimeError};summary.push(score);console.log(JSON.stringify({page:score.page,performance:score.performance,accessibility:score.accessibility,runtimeError:score.runtimeError}));
 }catch(error){summary.push({page:row.key,error:error.message});console.log(JSON.stringify({page:row.key,error:error.message}));}
 finally{await chrome.kill();}
 fs.writeFileSync(path.join(OUT,'summary.json'),JSON.stringify(summary,null,2));
}
