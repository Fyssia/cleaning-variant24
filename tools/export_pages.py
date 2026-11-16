"""Inventory UI screens and capture server HTML using real model objects."""
from pathlib import Path
import json,os,sys,re
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT));os.environ.setdefault('DJANGO_SETTINGS_MODULE','config.settings')
import django;django.setup()
from django.test import Client,override_settings
from django.contrib.auth.models import User
from django.urls import reverse
from orders.models import Order,RecurrenceRule
from crews.models import Employee
rows=[]
def add(key,name,role=None,args=None,query='',status=200):rows.append(dict(key=key,url=reverse(name,args=args)+query,role=role,status=status))
for key,name in [('home','home'),('services','services'),('service','service'),('guarantee','guarantee'),('contacts','contacts'),('search','search'),('privacy','privacy')]:add(key,'catalog:'+name,args=['general'] if key=='service' else None,query='?q=уборка' if key=='search' else '')
for key in ['login','register']:add(key,'accounts:'+key)
add('password','accounts:password','client1')
for key,name in [('order_new','create'),('account_orders','mine'),('addresses','addresses'),('series','series')]:add(key,'orders:'+name,'client1')
order=Order.objects.filter(customer__user__username='client1').first();add('order','orders:detail','client1',[order.pk])
order=Order.objects.filter(status='done',review__isnull=True).select_related('customer__user').first();assert order
add('review','reviews:create',order.customer.user.username,[order.pk])
add('dispatch','crews:dispatch','dispatcher');add('schedule','crews:schedule','dispatcher',query='?date=2026-11-14')
add('assign','crews:assign','dispatcher',[Order.objects.filter(status='new',crew=None).first().pk])
add('series_assign','crews:series_assign','dispatcher',[RecurrenceRule.objects.first().pk])
crew=Employee.objects.get(user__username='crew1').crew;order=Order.objects.filter(crew=crew).first()
add('crew_day','crews:day','crew1',query='?date='+order.start.date().isoformat());add('crew_print','crews:print','crew1',[order.pk])
for key in ['dashboard','manage']:add(key,'crews:'+key,'admin')
add('error','catalog:not_found',status=404)
OUT=ROOT/'evidence';(OUT/'html').mkdir(parents=True,exist_ok=True)
with override_settings(ALLOWED_HOSTS=['testserver','localhost','127.0.0.1']):
 for row in rows:
  client=Client()
  if row['role']:client.force_login(User.objects.get(username=row['role']))
  response=client.get(row['url']);assert response.status_code==row['status'],(row,response.status_code)
  html=response.content.decode();html=re.sub(r'(name="csrfmiddlewaretoken" value=")[^"]+',r'\1REDACTED',html)
  (OUT/'html'/(row['key']+'.html')).write_text(html)
(OUT/'pages.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2));print(len(rows),'UI pages and matching HTML captures')
