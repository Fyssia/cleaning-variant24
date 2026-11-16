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


def service_list(request):
    from django.core.paginator import Paginator
    from django.db.models import Q
    services = Service.objects.filter(is_active=True).prefetch_related('room_types')
    query = request.GET.get('q', '').strip()[:100]
    if query:
        services = services.filter(Q(name__icontains=query) | Q(description__icontains=query))
    kind = request.GET.get('kind', '')
    if kind in ['main', 'extra']:
        services = services.filter(kind=kind)
    room = request.GET.get('room', '')
    if room.isdigit():
        services = services.filter(room_types__pk=room)
    sorting = request.GET.get('sort', 'name')
    ordering = {'name': 'name', 'price': 'price', '-price': '-price'}.get(sorting, 'name')
    page = Paginator(services.order_by(ordering, 'pk').distinct(), 20).get_page(request.GET.get('page'))
    params = request.GET.copy(); params.pop('page', None)
    context = {'title': 'Результаты поиска' if request.resolver_match.url_name == 'search' else 'Каталог услуг', 'page_obj': page, 'query': query, 'kind': kind, 'room': room, 'sort': sorting, 'querystring': params.urlencode(), 'room_types': RoomType.objects.all()}
    if request.resolver_match.url_name == 'service_api':
        from django.http import JsonResponse
        from django.template.loader import render_to_string
        return JsonResponse({'html': render_to_string('catalog/results.html', context, request), 'count': page.paginator.count, 'page': page.number})
    return render(request, 'catalog/list.html', context)


def not_found(request, exception=None):
    return render(request, '404.html', {'title': 'Страница не найдена'}, status=404)


def forbidden(request, exception=None):
    return render(request, '403.html', {'title': 'Нет доступа'}, status=403)


def service_detail(request, slug):
    from django.shortcuts import get_object_or_404
    service = get_object_or_404(Service.objects.prefetch_related('room_types'), slug=slug, is_active=True)
    reviews = Review.objects.filter(is_published=True, order__items__service=service).select_related('order__customer__user').prefetch_related('photos').distinct()[:12]
    return render(request, 'catalog/detail.html', {'title': service.name, 'service': service, 'includes': service.includes.splitlines(), 'reviews': reviews})
