from django.conf import settings
from django.db import models
from django.db.models import F, Q
from django.utils import timezone

from accounts.models import phone_validator


class Crew(models.Model):
    """Бригада: группа сотрудников с общим расписанием."""
    name = models.CharField('название', max_length=50, unique=True)
    leader = models.ForeignKey('Employee', on_delete=models.SET_NULL, null=True, blank=True,
                               related_name='leading_crews', verbose_name='бригадир')
    is_active = models.BooleanField('работает', default=True)

    class Meta:
        verbose_name = 'бригада'
        verbose_name_plural = 'бригады'
        ordering = ['name']

    def __str__(self):
        return self.name


class Employee(models.Model):
    """Сотрудник бригады. Учётная запись нужна, чтобы открывать наряд (FR-18)."""
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
                                related_name='employee', verbose_name='учётная запись')
    crew = models.ForeignKey(Crew, on_delete=models.SET_NULL, null=True, blank=True, related_name='members',
                             verbose_name='бригада')
    full_name = models.CharField('ФИО', max_length=150)
    phone = models.CharField('телефон', max_length=12, validators=[phone_validator])
    photo = models.ImageField('фото', upload_to='employees/', blank=True)
    hired_on = models.DateField('дата приёма')
    is_active = models.BooleanField('работает', default=True)

    class Meta:
        verbose_name = 'сотрудник'
        verbose_name_plural = 'сотрудники'
        ordering = ['crew', 'full_name']

    def __str__(self):
        return self.full_name


class ScheduleSlot(models.Model):
    """Интервал расписания бригады [start; end): заказ или выходной.
    Пересечения интервалов одной бригады запрещает сервис назначения (FR-12) в transaction.atomic:
    в SQLite нет ограничения-исключения, которое сделало бы это на уровне базы."""
    class Kind(models.TextChoices):
        ORDER = 'order', 'заказ'
        DAY_OFF = 'day_off', 'выходной'

    crew = models.ForeignKey(Crew, on_delete=models.CASCADE, related_name='slots', verbose_name='бригада')
    kind = models.CharField('вид', max_length=8, choices=Kind.choices, default=Kind.ORDER)
    order = models.OneToOneField('orders.Order', on_delete=models.CASCADE, null=True, blank=True,
                                 related_name='slot', verbose_name='заказ')
    start = models.DateTimeField('начало')
    end = models.DateTimeField('конец')
    note = models.CharField('примечание', max_length=120, blank=True)

    class Meta:
        verbose_name = 'интервал расписания'
        verbose_name_plural = 'расписание бригад'
        ordering = ['start', 'crew']
        indexes = [models.Index(fields=['crew', 'start'], name='slot_crew_start_idx')]
        constraints = [
            models.CheckConstraint(condition=Q(end__gt=F('start')), name='slot_end_after_start'),
            models.CheckConstraint(condition=Q(kind='order', order__isnull=False) | Q(kind='day_off', order__isnull=True),
                                   name='slot_order_matches_kind'),
        ]

    def __str__(self):
        return f'{self.crew}: {timezone.localtime(self.start):%d.%m.%Y %H:%M}-{timezone.localtime(self.end):%H:%M}'
