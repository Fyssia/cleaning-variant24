from datetime import timedelta

from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.db.models import F, Q
from django.utils import timezone


class RecurrenceRule(models.Model):
    """Правило повторения: по нему создаётся серия заказов на срок до 6 месяцев (FR-15)."""
    class Period(models.TextChoices):
        WEEK = 'week', 'раз в неделю'
        TWO_WEEKS = 'two_weeks', 'раз в две недели'
        MONTH = 'month', 'раз в месяц'

    customer = models.ForeignKey('accounts.Customer', on_delete=models.CASCADE, related_name='recurrence_rules',
                                 verbose_name='заказчик')
    period = models.CharField('периодичность', max_length=10, choices=Period.choices)
    start_date = models.DateField('первая уборка')
    end_date = models.DateField('последняя дата серии')
    created_at = models.DateTimeField('создано', auto_now_add=True)

    class Meta:
        verbose_name = 'правило повторения'
        verbose_name_plural = 'правила повторения'
        ordering = ['-start_date']
        constraints = [models.CheckConstraint(condition=Q(end_date__gte=F('start_date')), name='rule_end_not_before_start')]

    def clean(self):
        if self.start_date and self.end_date and self.end_date - self.start_date > timedelta(days=183):
            raise ValidationError({'end_date': 'Серия создаётся не больше чем на 6 месяцев.'})

    def __str__(self):
        return f'{self.get_period_display()} с {self.start_date:%d.%m.%Y} по {self.end_date:%d.%m.%Y}'


class Order(models.Model):
    """Заказ уборки. Цена, скидка и длительность фиксируются при оформлении и не меняются при смене тарифа."""
    class Status(models.TextChoices):
        NEW = 'new', 'новый'
        ASSIGNED = 'assigned', 'бригада назначена'
        IN_PROGRESS = 'in_progress', 'в работе'
        DONE = 'done', 'выполнен'
        CANCELLED = 'cancelled', 'отменён'

    customer = models.ForeignKey('accounts.Customer', on_delete=models.PROTECT, related_name='orders', verbose_name='заказчик')
    address = models.ForeignKey('accounts.Address', on_delete=models.PROTECT, related_name='orders', verbose_name='адрес')
    room_type = models.ForeignKey('catalog.RoomType', on_delete=models.PROTECT, related_name='orders',
                                  verbose_name='тип помещения')
    area = models.DecimalField('площадь, м²', max_digits=6, decimal_places=1,
                               validators=[MinValueValidator(10), MaxValueValidator(1000)])
    start = models.DateTimeField('начало уборки')
    duration_min = models.PositiveIntegerField('длительность, мин', validators=[MinValueValidator(30)])
    price = models.DecimalField('стоимость, руб.', max_digits=10, decimal_places=2)
    discount_percent = models.PositiveSmallIntegerField('скидка, %', default=0, validators=[MaxValueValidator(50)])
    status = models.CharField('статус', max_length=12, choices=Status.choices, default=Status.NEW)
    crew = models.ForeignKey('crews.Crew', on_delete=models.PROTECT, null=True, blank=True, related_name='orders',
                             verbose_name='бригада')
    rule = models.ForeignKey(RecurrenceRule, on_delete=models.SET_NULL, null=True, blank=True, related_name='orders',
                             verbose_name='правило повторения')
    services = models.ManyToManyField('catalog.Service', through='OrderItem', related_name='orders', verbose_name='услуги')
    comment = models.TextField('комментарий заказчика', blank=True)
    materials_written_off_at = models.DateTimeField('материалы списаны', null=True, blank=True)
    created_at = models.DateTimeField('оформлен', auto_now_add=True)
    updated_at = models.DateTimeField('изменён', auto_now=True)

    class Meta:
        verbose_name = 'заказ'
        verbose_name_plural = 'заказы'
        ordering = ['-start']
        indexes = [models.Index(fields=['status', 'start'], name='order_status_start_idx')]
        constraints = [
            models.CheckConstraint(condition=Q(area__gte=10, area__lte=1000), name='order_area_range'),
            models.CheckConstraint(condition=Q(price__gte=0), name='order_price_not_negative'),
            models.CheckConstraint(condition=Q(duration_min__gte=30), name='order_duration_min_30'),
            models.CheckConstraint(condition=Q(discount_percent__lte=50), name='order_discount_max_50'),
            # назначенный, начатый и выполненный заказ обязательно с бригадой
            models.CheckConstraint(condition=Q(status__in=['new', 'cancelled']) | Q(crew__isnull=False),
                                   name='order_crew_required_after_assign'),
        ]

    @property
    def end(self):
        return self.start + timedelta(minutes=self.duration_min)

    def clean(self):
        if self.address_id and self.customer_id and self.address.customer_id != self.customer_id:
            raise ValidationError({'address': 'Адрес принадлежит другому заказчику.'})

    def __str__(self):
        return f'Заказ № {self.pk} на {timezone.localtime(self.start):%d.%m.%Y %H:%M}'


class OrderItem(models.Model):
    """Позиция заказа: услуга, количество (м² или штуки) и цена на момент заказа (M:N заказ - услуга)."""
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items', verbose_name='заказ')
    service = models.ForeignKey('catalog.Service', on_delete=models.PROTECT, related_name='order_items', verbose_name='услуга')
    quantity = models.DecimalField('количество', max_digits=8, decimal_places=2, validators=[MinValueValidator(0.01)])
    unit_price = models.DecimalField('цена за единицу, руб.', max_digits=9, decimal_places=2)

    class Meta:
        verbose_name = 'позиция заказа'
        verbose_name_plural = 'позиции заказов'
        ordering = ['order', 'id']
        constraints = [
            models.UniqueConstraint(fields=['order', 'service'], name='order_item_unique_service'),
            models.CheckConstraint(condition=Q(quantity__gt=0), name='order_item_quantity_positive'),
            models.CheckConstraint(condition=Q(unit_price__gte=0), name='order_item_price_not_negative'),
        ]

    @property
    def amount(self):
        return self.quantity * self.unit_price

    def __str__(self):
        return f'{self.service} × {self.quantity}'
