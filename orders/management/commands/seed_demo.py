"""Демонстрационные данные (общее требование 13): python manage.py seed_demo [--flush].
Все люди и адреса вымышленные. Генератор детерминированный (seed 24), даты - вокруг 13.11.2026.
Бригаде не ставятся пересекающиеся интервалы и заказы в её выходной - те же правила, что у сервиса назначения."""
import io
import random
from datetime import date, datetime, time, timedelta
from decimal import ROUND_HALF_UP, Decimal
from zoneinfo import ZoneInfo

from django.contrib.auth.models import Group, User
from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand
from django.db import transaction

from accounts.models import Address, Customer
from catalog.models import Material, RoomType, Service, ServiceMaterial
from crews.models import Crew, Employee, ScheduleSlot
from orders.models import Order, OrderItem, RecurrenceRule
from reviews.models import Review, ReviewPhoto

TZ = ZoneInfo('Europe/Moscow')
TODAY = date(2026, 11, 13)
DEMO_PASSWORD = 'demo-pass-24'  # только для учебного стенда

ROOM_TYPES = [('Квартира', 'flat', '1.00', '1.00'), ('Частный дом', 'house', '1.20', '1.15'), ('Офис', 'office', '0.90', '0.85')]
MAIN = [  # название, slug, руб. за м², мин на м², скидка серии, типы помещений, что входит
    ('Поддерживающая уборка', 'support', '100', '1.6', 10, ['flat', 'house', 'office'],
     'Влажная уборка полов\nПыль на открытых поверхностях\nКухня: плита, раковина, фасады\nСанузел: ванна, раковина, унитаз\nВынос мусора'),
    ('Генеральная уборка', 'general', '200', '3.0', 0, ['flat', 'house', 'office'],
     'Всё из поддерживающей уборки\nПыль в труднодоступных местах\nДвери, плинтусы, батареи\nУдаление налёта в санузле\nМытьё зеркал и стёкол мебели'),
    ('Уборка после ремонта', 'after-repair', '250', '4.0', 0, ['flat', 'house', 'office'],
     'Удаление строительной пыли\nОтмывание следов краски и клея\nМытьё окон изнутри\nВынос строительного мусора до 5 мешков'),
    ('Ежедневная уборка офиса', 'office-daily', '60', '0.8', 15, ['office'],
     'Полы и рабочие поверхности\nКухня и переговорные\nСанузлы\nВынос мусора'),
]
EXTRA = [  # название, slug, руб. за шт., мин за шт.
    ('Мытьё окна (створка)', 'window', '350', '15'), ('Холодильник внутри', 'fridge', '700', '40'),
    ('Духовка внутри', 'oven', '600', '40'), ('Микроволновка внутри', 'microwave', '300', '15'),
    ('Кухонные шкафы внутри', 'cabinets', '800', '45'), ('Уборка балкона', 'balcony', '1200', '60'),
    ('Глажка белья (час)', 'ironing', '900', '60'), ('Химчистка дивана', 'sofa', '2500', '90'),
    ('Мытьё люстры', 'chandelier', '500', '30'), ('Удаление налёта в санузле', 'limescale', '900', '40'),
]
MATERIALS = [  # название, единица, остаток, минимум
    ('Универсальное моющее средство', 'l', '40', '10'), ('Средство для стёкол', 'l', '25', '5'),
    ('Антижир для кухни', 'l', '15', '4'), ('Средство для сантехники', 'l', '20', '5'),
    ('Дезинфицирующее средство', 'l', '12', '3'), ('Салфетки из микрофибры', 'pcs', '120', '30'),
    ('Губки', 'pcs', '200', '50'), ('Мешки для мусора', 'roll', '30', '8'),
    ('Перчатки нитриловые', 'pcs', '150', '40'), ('Полироль для мебели', 'l', '8', '2'),
]
NORMS = {  # slug услуги: [(материал, расход на единицу)]
    'support': [('Универсальное моющее средство', '0.005'), ('Салфетки из микрофибры', '0.020'), ('Мешки для мусора', '0.010')],
    'general': [('Универсальное моющее средство', '0.010'), ('Средство для сантехники', '0.004'), ('Салфетки из микрофибры', '0.040'),
                ('Полироль для мебели', '0.002')],
    'after-repair': [('Универсальное моющее средство', '0.015'), ('Губки', '0.050'), ('Мешки для мусора', '0.040')],
    'office-daily': [('Универсальное моющее средство', '0.003'), ('Дезинфицирующее средство', '0.002')],
    'window': [('Средство для стёкол', '0.050')], 'fridge': [('Антижир для кухни', '0.050'), ('Губки', '1')],
    'oven': [('Антижир для кухни', '0.150'), ('Губки', '1')], 'limescale': [('Средство для сантехники', '0.200')],
}
FIRST_M = ['Алексей', 'Дмитрий', 'Сергей', 'Андрей', 'Михаил', 'Игорь', 'Павел']
FIRST_F = ['Анна', 'Елена', 'Ольга', 'Марина', 'Татьяна', 'Наталья', 'Ирина', 'Светлана', 'Юлия']
LAST = ['Смирнов', 'Кузнецов', 'Попов', 'Соколов', 'Лебедев', 'Козлов', 'Новиков', 'Морозов', 'Волков', 'Соловьёв',
        'Васильев', 'Зайцев', 'Павлов', 'Семёнов', 'Голубев', 'Виноградов', 'Богданов', 'Воробьёв', 'Фёдоров', 'Михайлов',
        'Беляев', 'Тарасов', 'Белов', 'Комаров', 'Орлов', 'Киселёв', 'Макаров', 'Андреев', 'Ковалёв', 'Ильин']
MIDDLE_M = ['Андреевич', 'Сергеевич', 'Игоревич', 'Павлович']
MIDDLE_F = ['Андреевна', 'Сергеевна', 'Игоревна', 'Павловна']
STREETS = ['ул. Лесная', 'ул. Садовая', 'ул. Школьная', 'ул. Полевая', 'Береговой пр.', 'ул. Молодёжная', 'Зелёный пр.',
           'ул. Цветочная', 'ул. Речная', 'Тихий пер.']
REVIEWS = {
    5: ['Всё чисто, приехали вовремя.', 'Отлично отмыли кухню и санузел, спасибо бригаде.', 'Аккуратно, ничего не сдвинули без спроса.',
        'Окна без разводов, буду заказывать регулярно.', ''],
    4: ['Хорошо, но пришлось напомнить про плинтусы.', 'Убрали чисто, опоздали на 15 минут, предупредили заранее.'],
    3: ['В целом нормально, балкон помыли не до конца.'],
}


def female(last):
    return last[:-1] + 'а' if last.endswith('й') else last + 'а'


def money(x):
    return Decimal(x).quantize(Decimal('0.01'), ROUND_HALF_UP)


class Command(BaseCommand):
    help = 'Заполнить базу демонстрационными данными (вымышленные люди и адреса)'

    def add_arguments(self, parser):
        parser.add_argument('--flush', action='store_true', help='удалить прежние данные приложений перед заполнением')

    @transaction.atomic
    def handle(self, *args, **opts):
        if opts['flush']:
            for m in (ReviewPhoto, Review, ScheduleSlot, OrderItem, Order, RecurrenceRule, Address, Customer,
                      ServiceMaterial, Service, Material, RoomType):
                m.objects.all().delete()
            Crew.objects.update(leader=None)
            Employee.objects.all().delete()
            Crew.objects.all().delete()
            User.objects.filter(is_superuser=False).delete()
        if Order.objects.exists():
            self.stderr.write('В базе уже есть заказы. Запустите с --flush.')
            return
        rnd = random.Random(24)
        groups = {n: Group.objects.get_or_create(name=n)[0] for n in ('Заказчик', 'Сотрудник бригады', 'Диспетчер', 'Администратор')}

        def user(username, first, last, email, group, **kw):
            u = User.objects.create_user(username, email, DEMO_PASSWORD, first_name=first, last_name=last, **kw)
            u.groups.add(groups[group])
            return u

        if not User.objects.filter(username='admin').exists():
            user('admin', 'Администратор', 'Службы', 'admin@cleaning.local', 'Администратор', is_staff=True, is_superuser=True)
        user('dispatcher', 'Ольга', 'Диспетчерова', 'dispatcher@cleaning.local', 'Диспетчер', is_staff=True)

        # справочники
        rooms = {s: RoomType.objects.create(name=n, slug=s, price_factor=Decimal(p), duration_factor=Decimal(d), sort=i)
                 for i, (n, s, p, d) in enumerate(ROOM_TYPES)}
        materials = {n: Material.objects.create(name=n, unit=u, stock=Decimal(st), min_stock=Decimal(mn)) for n, u, st, mn in MATERIALS}
        services = {}
        for n, slug, price, minutes, disc, types, inc in MAIN:
            s = Service.objects.create(name=n, slug=slug, kind='main', unit='m2', price=Decimal(price), minutes_per_unit=Decimal(minutes),
                                       series_discount=disc, includes=inc, description=f'{n}: цена за 1 м², итог зависит от типа помещения.')
            s.room_types.set(rooms[t] for t in types)
            services[slug] = s
        for n, slug, price, minutes in EXTRA:
            s = Service.objects.create(name=n, slug=slug, kind='extra', unit='pcs', price=Decimal(price), minutes_per_unit=Decimal(minutes),
                                       description=f'{n}: дополнительная услуга к любому виду уборки, цена за штуку.')
            s.room_types.set(rooms.values())
            services[slug] = s
        for slug, norms in NORMS.items():
            for mat, norm in norms:
                ServiceMaterial.objects.create(service=services[slug], material=materials[mat], norm=Decimal(norm))

        # бригады: 4 по 3 сотрудника, у бригадира есть учётная запись, выходной - один день недели
        crews, crew_off = [], {}
        last_pool = LAST[:]
        rnd.shuffle(last_pool)
        for i, title in enumerate(['Бригада 1', 'Бригада 2', 'Бригада 3', 'Бригада 4']):
            crew = Crew.objects.create(name=title)
            members = []
            for j in range(3):
                last = last_pool.pop()
                fem = rnd.random() < 0.7
                full = f'{female(last) if fem else last} {rnd.choice(FIRST_F if fem else FIRST_M)} {rnd.choice(MIDDLE_F if fem else MIDDLE_M)}'
                u = None
                if j == 0:
                    first, l = full.split()[1], full.split()[0]
                    u = user(f'crew{i + 1}', first, l, f'crew{i + 1}@cleaning.local', 'Сотрудник бригады')
                members.append(Employee.objects.create(user=u, crew=crew, full_name=full, phone=f'+7916{rnd.randint(1000000, 9999999)}',
                                                       hired_on=date(2024, 1, 15) + timedelta(days=rnd.randint(0, 600))))
            crew.leader = members[0]
            crew.save()
            crews.append(crew)
            crew_off[crew.id] = (6 + i) % 7  # 6 - воскресенье, далее понедельник, вторник, среда

        # заказчики и адреса
        customers = []
        for i in range(14):
            last = last_pool.pop() if last_pool else rnd.choice(LAST)
            fem = i % 2 == 0
            first = rnd.choice(FIRST_F if fem else FIRST_M)
            u = user(f'client{i + 1}', first, female(last) if fem else last, f'client{i + 1}@example.com', 'Заказчик')
            c = Customer.objects.create(user=u, middle_name=rnd.choice(MIDDLE_F if fem else MIDDLE_M),
                                        phone=f'+7925{1000000 + i * 37791:07d}',
                                        pd_consent_at=datetime(2026, 10, 1, 12, tzinfo=TZ) + timedelta(days=i))
            for k in range(2 if i % 3 == 0 else 1):
                Address.objects.create(customer=c, street=rnd.choice(STREETS), house=str(rnd.randint(1, 60)),
                                       flat=str(rnd.randint(1, 240)) if i % 5 else '', floor=rnd.randint(1, 16),
                                       comment=rnd.choice(['', '', 'Код домофона скажем по телефону', 'Есть кошка', 'Парковка во дворе']))
            customers.append(c)
        room_of_address = {}
        for a in Address.objects.all():
            room_of_address[a.id] = 'office' if not a.flat else ('house' if a.floor and a.floor <= 2 and rnd.random() < 0.4 else 'flat')

        busy = {c.id: [] for c in crews}  # занятые интервалы бригад (начало, конец)
        # выходные бригад на 6 недель - интервалы day_off
        d = date(2026, 10, 26)
        while d <= date(2026, 12, 20):
            for c in crews:
                if d.weekday() == crew_off[c.id]:
                    s, e = datetime.combine(d, time(8), TZ), datetime.combine(d, time(21), TZ)
                    ScheduleSlot.objects.create(crew=c, kind='day_off', start=s, end=e, note='выходной')
                    busy[c.id].append((s, e))
            d += timedelta(days=1)

        def free_crew(start, end):
            cand = [c for c in crews if all(end <= s or start >= e for s, e in busy[c.id])]  # стык не пересечение
            return rnd.choice(cand) if cand else None

        def make_order(customer, addr, start_day, rule=None, main_slug=None):
            room = rooms[room_of_address[addr.id]]
            area = Decimal(rnd.randint(*{'flat': (28, 110), 'house': (90, 240), 'office': (40, 260)}[room.slug]))
            main = services[main_slug or rnd.choice(['support', 'support', 'general', 'general', 'after-repair'] +
                                                     (['office-daily'] if room.slug == 'office' else []))]
            extras = rnd.sample([s for s in services.values() if s.kind == 'extra'], k=rnd.choice([0, 1, 1, 2, 3]))
            qty = {s.id: Decimal(rnd.randint(2, 8) if s.slug == 'window' else 1) for s in extras}
            base = area * main.price + sum(qty[s.id] * s.price for s in extras)
            discount = main.series_discount if rule else 0
            price = money(base * room.price_factor * (100 - discount) / 100)
            minutes = (area * main.minutes_per_unit + sum(qty[s.id] * s.minutes_per_unit for s in extras)) * room.duration_factor
            duration = max(60, int((minutes / 30).to_integral_value(ROUND_HALF_UP)) * 30)
            duration = min(duration, 600)
            latest = min(16, (21 * 60 - duration) // 60)  # уборка заканчивается не позже 21:00
            hour = rnd.randint(8, max(8, latest))
            minute = rnd.choice([0, 30]) if (hour * 60 + 30 + duration) <= 21 * 60 else 0
            start = datetime.combine(start_day, time(hour, minute), TZ)
            end = start + timedelta(minutes=duration)
            past = start_day < TODAY
            crew = free_crew(start, end)
            if past:
                status = 'cancelled' if rnd.random() < 0.1 or crew is None else 'done'
            else:
                status = 'assigned' if crew and rnd.random() < 0.6 else 'new'
            if status in ('new', 'cancelled'):
                crew = None
            o = Order.objects.create(customer=customer, address=addr, room_type=room, area=area, start=start, duration_min=duration,
                                     price=price, discount_percent=discount, status=status, crew=crew, rule=rule,
                                     materials_written_off_at=end if status == 'done' else None)
            OrderItem.objects.create(order=o, service=main, quantity=area, unit_price=main.price)
            for s in extras:
                OrderItem.objects.create(order=o, service=s, quantity=qty[s.id], unit_price=s.price)
            if crew:
                ScheduleSlot.objects.create(crew=crew, kind='order', order=o, start=start, end=end)
                busy[crew.id].append((start, end))
            return o

        # серии повторяющихся уборок
        def next_date(d, period):
            if period == 'month':  # тот же день следующего месяца
                y, m = (d.year + 1, 1) if d.month == 12 else (d.year, d.month + 1)
                return d.replace(year=y, month=m)
            return d + timedelta(days=7 if period == 'week' else 14)
        for k, (ci, period, first) in enumerate([(0, 'week', date(2026, 10, 27)), (3, 'two_weeks', date(2026, 10, 29)),
                                                  (6, 'month', date(2026, 11, 2)), (9, 'week', date(2026, 11, 16))]):
            c = customers[ci]
            rule = RecurrenceRule.objects.create(customer=c, period=period, start_date=first, end_date=first + timedelta(days=55))
            addr = c.addresses.first()
            d = first
            while d <= rule.end_date:
                make_order(c, addr, d, rule, main_slug='office-daily' if room_of_address[addr.id] == 'office' else 'support')
                d = next_date(d, period)
        # разовые заказы
        for _ in range(34):
            c = rnd.choice(customers)
            make_order(c, rnd.choice(list(c.addresses.all())), date(2026, 10, 26) + timedelta(days=rnd.randint(0, 50)))

        # отзывы на выполненные заказы, у нескольких - фото
        try:
            from PIL import Image, ImageDraw
        except ImportError:
            Image = None
        for n, o in enumerate(Order.objects.filter(status='done').order_by('start')):
            if rnd.random() < 0.65:
                rating = rnd.choices([5, 4, 3], weights=[70, 22, 8])[0]
                r = Review.objects.create(order=o, rating=rating, text=rnd.choice(REVIEWS[rating]))
                if Image and n % 4 == 0:
                    img = Image.new('RGB', (800, 600), (rnd.randint(170, 230), rnd.randint(190, 235), rnd.randint(200, 240)))
                    ImageDraw.Draw(img).text((40, 40), f'Demo photo, order {o.pk}', fill=(40, 40, 40))
                    buf = io.BytesIO()
                    img.save(buf, 'JPEG', quality=80)
                    ReviewPhoto.objects.create(review=r, image=ContentFile(buf.getvalue(), name=f'order_{o.pk}.jpg'))

        counts = {m._meta.verbose_name_plural: m.objects.count() for m in
                  (Customer, Address, RoomType, Service, Material, ServiceMaterial, Crew, Employee, ScheduleSlot,
                   RecurrenceRule, Order, OrderItem, Review, ReviewPhoto)}
        for k, v in counts.items():
            self.stdout.write(f'{k}: {v}')
        self.stdout.write(f'Пароль демо-учётных записей: {DEMO_PASSWORD} (admin, dispatcher, crew1-4, client1-14)')
