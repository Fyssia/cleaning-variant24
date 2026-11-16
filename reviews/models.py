from django.core.validators import MaxLengthValidator, MaxValueValidator, MinValueValidator
from django.db import models
from django.db.models import Q


class Review(models.Model):
    """Отзыв заказчика о выполненном заказе: один отзыв на заказ (FR-20)."""
    order = models.OneToOneField('orders.Order', on_delete=models.CASCADE, related_name='review', verbose_name='заказ')
    rating = models.PositiveSmallIntegerField('оценка', validators=[MinValueValidator(1), MaxValueValidator(5)])
    text = models.TextField('текст', blank=True, validators=[MaxLengthValidator(2000)])
    is_published = models.BooleanField('опубликован', default=True)
    created_at = models.DateTimeField('оставлен', auto_now_add=True)

    class Meta:
        verbose_name = 'отзыв'
        verbose_name_plural = 'отзывы'
        ordering = ['-created_at']
        constraints = [models.CheckConstraint(condition=Q(rating__gte=1, rating__lte=5), name='review_rating_1_5')]

    def __str__(self):
        return f'Отзыв на заказ № {self.order_id}: {self.rating}'


class ReviewPhoto(models.Model):
    """Фото к отзыву: до 3 штук, JPEG/PNG/WebP не больше 5 МБ (проверка в форме, NFR-13)."""
    review = models.ForeignKey(Review, on_delete=models.CASCADE, related_name='photos', verbose_name='отзыв')
    image = models.ImageField('фото', upload_to='reviews/%Y/%m/')
    uploaded_at = models.DateTimeField('загружено', auto_now_add=True)

    class Meta:
        verbose_name = 'фото к отзыву'
        verbose_name_plural = 'фото к отзывам'
        ordering = ['review', 'id']

    def __str__(self):
        return f'Фото {self.pk} к отзыву {self.review_id}'
