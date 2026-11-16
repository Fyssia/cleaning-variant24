from django.shortcuts import render
from reviews.models import Review
from .models import Service, RoomType


def home(request):
    return render(request, 'catalog/home.html', {
        'title': 'Уборка квартир, домов и офисов',
        'services': Service.objects.filter(is_active=True, kind='main').prefetch_related('room_types')[:3],
        'main_services': Service.objects.filter(is_active=True, kind='main'),
        'extra_services': Service.objects.filter(is_active=True, kind='extra'),
        'room_types': RoomType.objects.all(),
        'reviews': Review.objects.filter(is_published=True).select_related('order__customer__user').prefetch_related('order__items__service')[:3],
    })


def information(request, page):
    pages = {
        'guarantee': ('Гарантии и условия', 'guarantee.html'),
        'contacts': ('Контакты', 'contacts.html'),
        'privacy': ('Обработка персональных данных', 'privacy.html'),
    }
    title, template = pages[page]
    return render(request, 'catalog/' + template, {'title': title})
