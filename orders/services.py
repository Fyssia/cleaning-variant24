"""Единый расчёт и атомарные операции. Ценам и длительности из браузера не доверяем."""
from calendar import monthrange
from datetime import datetime, timedelta
from decimal import Decimal, ROUND_CEILING, ROUND_HALF_UP

from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone

from crews.models import Crew, ScheduleSlot
from .models import Order, OrderItem, RecurrenceRule


def quote(data):
    service, room, area = data['service'], data['room_type'], data['area']
    items = [(service, area)]
    for extra in data.get('extras', []):
        quantity = data.get(f'extra_{extra.pk}', 0)
        if quantity:
            items.append((extra, Decimal(quantity)))
    discount = service.series_discount if data.get('period') else 0
    base = sum((item.price * quantity for item, quantity in items), Decimal(0))
    price = (base * room.price_factor * Decimal(100-discount) / 100).quantize(Decimal('.01'), ROUND_HALF_UP)
    minutes = sum((item.minutes_per_unit * quantity for item, quantity in items), Decimal(0)) * room.duration_factor
    duration = max(60, int((minutes/30).to_integral_value(ROUND_CEILING))*30)
    return {'price': price, 'duration_min': duration, 'discount_percent': discount, 'items': items, 'factor': room.price_factor}


def free_crews(start, end, ignore_order=None):
    busy = ScheduleSlot.objects.filter(start__lt=end, end__gt=start)
    if ignore_order:
        busy = busy.exclude(order_id=ignore_order)
    return Crew.objects.filter(is_active=True).exclude(pk__in=busy.values('crew_id'))


def ensure_capacity(start, duration):
    end = start + timedelta(minutes=duration)
    pending = Order.objects.filter(status='new', crew=None, start__lt=end)
    overlap = sum(order.end > start for order in pending)
    if free_crews(start, end).count() <= overlap:
        raise ValidationError('На это время все бригады заняты. Выберите другой интервал.')


def recurrence_dates(start, end, period):
    current = start; index = 0
    while current.date() <= end:
        yield current
        index += 1
        if period == 'month':
            month_number = start.year*12 + start.month-1 + index
            year, month = divmod(month_number, 12); month += 1
            current = start.replace(year=year, month=month, day=min(start.day, monthrange(year, month)[1]))
        else:
            current = start + timedelta(days=index*(7 if period == 'week' else 14))


@transaction.atomic
def create_orders(customer, data):
    calculated = quote(data)
    dates = list(recurrence_dates(data['start'], data['end_date'], data['period'])) if data.get('period') else [data['start']]
    # Serialize reservation writes on engines supporting row locks.
    list(Crew.objects.select_for_update().filter(is_active=True))
    for start in dates:
        ensure_capacity(start, calculated['duration_min'])
    rule = None
    if data.get('period'):
        rule = RecurrenceRule.objects.create(customer=customer, period=data['period'], start_date=data['start'].date(), end_date=data['end_date'])
    result = []
    for start in dates:
        order = Order(customer=customer, address=data['address'], room_type=data['room_type'], area=data['area'], start=start, duration_min=calculated['duration_min'], price=calculated['price'], discount_percent=calculated['discount_percent'], comment=data.get('comment', ''), rule=rule)
        order.full_clean(); order.save()
        OrderItem.objects.bulk_create([OrderItem(order=order, service=item, quantity=quantity, unit_price=item.price) for item, quantity in calculated['items']])
        result.append(order)
    return result


@transaction.atomic
def assign_crew(order_id, crew):
    crew = Crew.objects.select_for_update().get(pk=crew.pk, is_active=True)
    order = Order.objects.select_for_update().get(pk=order_id)
    if order.status not in ['new', 'assigned']:
        raise ValidationError('Заказ уже выполняется, завершён или отменён. Назначение недоступно.')
    if not free_crews(order.start, order.end, order.pk).filter(pk=crew.pk).exists():
        raise ValidationError('У бригады есть пересечение в расписании. Выберите другую бригаду.')
    ScheduleSlot.objects.update_or_create(order=order, defaults={'crew': crew, 'start': order.start, 'end': order.end, 'kind': 'order'})
    order.crew = crew; order.status = 'assigned'; order.save(update_fields=['crew', 'status', 'updated_at'])
    return order


@transaction.atomic
def assign_series(rule, crew):
    orders = list(rule.orders.filter(status='new').order_by('start'))
    if not orders:
        raise ValidationError('В серии нет заказов, ожидающих назначения.')
    return [assign_crew(order.pk, crew) for order in orders]
