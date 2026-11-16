from datetime import date
from django.db.models import Count, Sum
from django.shortcuts import get_object_or_404, render
from django.utils import timezone
from accounts.access import roles
from catalog.models import Material, RoomType, Service
from orders.models import Order, RecurrenceRule
from .models import Crew, Employee, ScheduleSlot


def chosen_date(request):
    try:
        return date.fromisoformat(request.GET.get('date', ''))
    except ValueError:
        return timezone.localdate()


@roles('Диспетчер', 'Администратор')
def dispatch(request):
    return render(request, 'crews/dispatch.html', {'title': 'Заказы без бригады', 'orders': Order.objects.filter(crew=None, status='new').select_related('address', 'customer__user'), 'rules': RecurrenceRule.objects.filter(orders__status='new').distinct()})


@roles('Диспетчер', 'Администратор')
def schedule(request):
    day = chosen_date(request)
    return render(request, 'crews/schedule.html', {'title': 'Расписание бригад', 'day': day, 'crews': Crew.objects.filter(is_active=True).prefetch_related('members'), 'slots': ScheduleSlot.objects.filter(start__date=day).select_related('crew', 'order')})


@roles('Сотрудник бригады')
def crew_day(request):
    employee = get_object_or_404(Employee, user=request.user, is_active=True)
    day = chosen_date(request)
    orders = Order.objects.filter(crew=employee.crew, start__date=day).exclude(status='cancelled').select_related('address', 'customer__user').prefetch_related('items__service')
    return render(request, 'crews/day.html', {'title': 'Наряд на день', 'day': day, 'orders': orders, 'employee': employee})


@roles('Сотрудник бригады')
def crew_print(request, pk):
    employee = get_object_or_404(Employee, user=request.user, is_active=True)
    order = get_object_or_404(Order.objects.select_related('address', 'customer__user', 'room_type'), pk=pk, crew=employee.crew)
    return render(request, 'crews/print.html', {'title': f'Наряд на заказ №{pk}', 'order': order})


@roles('Администратор')
def dashboard(request):
    return render(request, 'crews/dashboard.html', {'title': 'Сводка', 'total': Order.objects.aggregate(count=Count('pk'), revenue=Sum('price')), 'by_status': Order.objects.values('status').annotate(count=Count('pk')).order_by('status'), 'crews': Crew.objects.annotate(order_count=Count('orders'), revenue=Sum('orders__price')), 'materials': Material.objects.all()})


@roles('Администратор')
def manage(request):
    return render(request, 'crews/manage.html', {'title': 'Справочники', 'services': Service.objects.all(), 'rooms': RoomType.objects.all(), 'materials': Material.objects.all()})
