from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator, RegexValidator
from django.db import models
from django.db.models import Q

phone_validator = RegexValidator(r'^\+7\d{10}$', 'Телефон в формате +7XXXXXXXXXX')


class Customer(models.Model):
    """Заказчик: профиль пользователя Django (ФИО и e-mail - в User) с телефоном и согласием на обработку ПДн."""
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='customer',
                                verbose_name='пользователь')
    middle_name = models.CharField('отчество', max_length=60, blank=True)
    phone = models.CharField('телефон', max_length=12, unique=True, validators=[phone_validator])
    pd_consent_at = models.DateTimeField('согласие на обработку ПДн')
    created_at = models.DateTimeField('зарегистрирован', auto_now_add=True)

    class Meta:
        verbose_name = 'заказчик'
        verbose_name_plural = 'заказчики'
        ordering = ['user__last_name', 'user__first_name']

    def __str__(self):
        return ' '.join(p for p in (self.user.last_name, self.user.first_name, self.middle_name) if p) or self.user.username


class Address(models.Model):
    """Адрес уборки. Видят его только заказчик, бригада заказа, диспетчер и администратор (FR-21)."""
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name='addresses', verbose_name='заказчик')
    city = models.CharField('город', max_length=60, default='Москва')
    street = models.CharField('улица', max_length=120)
    house = models.CharField('дом, корпус', max_length=20)
    flat = models.CharField('квартира, офис', max_length=10, blank=True)
    floor = models.SmallIntegerField('этаж', null=True, blank=True,
                                     validators=[MinValueValidator(-3), MaxValueValidator(100)])
    comment = models.CharField('комментарий для бригады', max_length=255, blank=True)
    created_at = models.DateTimeField('добавлен', auto_now_add=True)

    class Meta:
        verbose_name = 'адрес'
        verbose_name_plural = 'адреса'
        ordering = ['customer', 'city', 'street', 'house']
        constraints = [
            models.UniqueConstraint(fields=['customer', 'city', 'street', 'house', 'flat'], name='address_unique_per_customer'),
            models.CheckConstraint(condition=Q(floor__isnull=True) | Q(floor__gte=-3, floor__lte=100), name='address_floor_range'),
        ]

    def __str__(self):
        s = f'{self.city}, {self.street}, д. {self.house}'
        return f'{s}, кв. {self.flat}' if self.flat else s
