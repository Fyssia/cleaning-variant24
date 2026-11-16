from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, render
from accounts.access import roles
from accounts.models import Address, Customer
from .models import Order, RecurrenceRule


def customer_for(user):
    return get_object_or_404(Customer, user=user)


@roles('Заказчик')
def mine(request):
    orders = Order.objects.filter(customer=customer_for(request.user)).select_related('address', 'crew', 'room_type')
    status = request.GET.get('status', '')
    if status in Order.Status.values:
        orders = orders.filter(status=status)
    return render(request, 'orders/list.html', {'title': 'Мои заказы', 'page_obj': Paginator(orders, 20).get_page(request.GET.get('page')), 'statuses': Order.Status.choices, 'status': status, 'querystring': 'status='+status})


@roles('Заказчик')
def detail(request, pk):
    order = get_object_or_404(Order.objects.select_related('address', 'room_type', 'crew'), pk=pk, customer=customer_for(request.user))
    return render(request, 'orders/detail.html', {'title': f'Заказ №{order.pk}', 'order': order})


@roles('Заказчик')
def addresses(request):
    return render(request, 'orders/addresses.html', {'title': 'Мои адреса', 'addresses': Address.objects.filter(customer=customer_for(request.user))})


@roles('Заказчик')
def series(request):
    return render(request, 'orders/series.html', {'title': 'Серии уборок', 'rules': RecurrenceRule.objects.filter(customer=customer_for(request.user)).prefetch_related('orders')})
