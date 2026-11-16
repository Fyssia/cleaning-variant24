from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.db.models import Q


class RoomType(models.Model):
    """Тип помещения: квартира, частный дом, офис. Коэффициенты умножают цену и длительность уборки."""
    name = models.CharField('название', max_length=50, unique=True)
    slug = models.SlugField('код', max_length=50, unique=True)
    price_factor = models.DecimalField('коэффициент цены', max_digits=4, decimal_places=2, default=1)
    duration_factor = models.DecimalField('коэффициент длительности', max_digits=4, decimal_places=2, default=1)
    sort = models.PositiveSmallIntegerField('порядок вывода', default=0)

    class Meta:
        verbose_name = 'тип помещения'
        verbose_name_plural = 'типы помещений'
        ordering = ['sort', 'name']
        constraints = [
            models.CheckConstraint(condition=Q(price_factor__gt=0, price_factor__lte=5), name='roomtype_price_factor_range'),
            models.CheckConstraint(condition=Q(duration_factor__gt=0, duration_factor__lte=5), name='roomtype_duration_factor_range'),
        ]

    def __str__(self):
        return self.name


class Material(models.Model):
    """Расходный материал на складе службы."""
    class Unit(models.TextChoices):
        PCS = 'pcs', 'шт.'
        LITRE = 'l', 'л'
        KG = 'kg', 'кг'
        ROLL = 'roll', 'рулон'

    name = models.CharField('название', max_length=100, unique=True)
    unit = models.CharField('единица', max_length=5, choices=Unit.choices)
    stock = models.DecimalField('остаток', max_digits=10, decimal_places=2, default=0)
    min_stock = models.DecimalField('минимальный остаток', max_digits=10, decimal_places=2, default=0)

    class Meta:
        verbose_name = 'расходный материал'
        verbose_name_plural = 'расходные материалы'
        ordering = ['name']
        constraints = [
            models.CheckConstraint(condition=Q(stock__gte=0), name='material_stock_not_negative'),
            models.CheckConstraint(condition=Q(min_stock__gte=0), name='material_min_stock_not_negative'),
        ]

    def __str__(self):
        return self.name


class Service(models.Model):
    """Услуга каталога: вид уборки (цена за м²) или дополнительная услуга (цена за штуку)."""
    class Kind(models.TextChoices):
        MAIN = 'main', 'вид уборки'
        EXTRA = 'extra', 'дополнительная услуга'

    class Unit(models.TextChoices):
        M2 = 'm2', 'м²'
        PCS = 'pcs', 'шт.'

    name = models.CharField('название', max_length=120, unique=True)
    slug = models.SlugField('адрес страницы', max_length=120, unique=True)
    kind = models.CharField('вид', max_length=5, choices=Kind.choices, default=Kind.MAIN)
    unit = models.CharField('единица', max_length=3, choices=Unit.choices, default=Unit.M2)
    price = models.DecimalField('цена за единицу, руб.', max_digits=9, decimal_places=2)
    minutes_per_unit = models.DecimalField('норма времени, мин на единицу', max_digits=6, decimal_places=2)
    description = models.TextField('описание')
    includes = models.TextField('что входит', blank=True, help_text='каждый пункт с новой строки')
    series_discount = models.PositiveSmallIntegerField('скидка в серии, %', default=0, validators=[MaxValueValidator(50)])
    room_types = models.ManyToManyField(RoomType, related_name='services', blank=True, verbose_name='типы помещений')
    materials = models.ManyToManyField(Material, through='ServiceMaterial', related_name='services', blank=True,
                                       verbose_name='расходные материалы')
    image = models.ImageField('изображение', upload_to='services/', blank=True)
    is_active = models.BooleanField('показывать в каталоге', default=True)

    class Meta:
        verbose_name = 'услуга'
        verbose_name_plural = 'услуги'
        ordering = ['kind', 'name']
        constraints = [
            models.CheckConstraint(condition=Q(price__gte=0), name='service_price_not_negative'),
            models.CheckConstraint(condition=Q(minutes_per_unit__gt=0), name='service_minutes_positive'),
            models.CheckConstraint(condition=Q(series_discount__lte=50), name='service_series_discount_max_50'),
        ]

    def __str__(self):
        return self.name


class ServiceMaterial(models.Model):
    """Норма расхода материала на единицу услуги (связь M:N услуга - материал с собственным атрибутом)."""
    service = models.ForeignKey(Service, on_delete=models.CASCADE, related_name='material_norms', verbose_name='услуга')
    material = models.ForeignKey(Material, on_delete=models.PROTECT, related_name='service_norms', verbose_name='материал')
    norm = models.DecimalField('расход на единицу услуги', max_digits=8, decimal_places=3,
                               validators=[MinValueValidator(0.001)])

    class Meta:
        verbose_name = 'норма расхода'
        verbose_name_plural = 'нормы расхода'
        ordering = ['service', 'material']
        constraints = [
            models.UniqueConstraint(fields=['service', 'material'], name='service_material_unique'),
            models.CheckConstraint(condition=Q(norm__gt=0), name='service_material_norm_positive'),
        ]

    def __str__(self):
        return f'{self.service}: {self.material} {self.norm}'
