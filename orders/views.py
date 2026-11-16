from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, render, redirect
from django.contrib import messages
from django.core.exceptions import ValidationError
from django.http import JsonResponse
from accounts.forms import AddressForm
from .forms import OrderForm, QuoteForm
from .services import create_orders, quote
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
    customer = customer_for(request.user)
    form = AddressForm(request.POST or None)
    form.instance.customer = customer
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Адрес сохранён.')
        return redirect('orders:addresses')
    return render(request, 'orders/addresses.html', {'title': 'Мои адреса', 'addresses': Address.objects.filter(customer=customer), 'form': form})


@roles('Заказчик')
def series(request):
    return render(request, 'orders/series.html', {'title': 'Серии уборок', 'rules': RecurrenceRule.objects.filter(customer=customer_for(request.user)).prefetch_related('orders')})


@roles('Заказчик')
def create(request):
    customer = customer_for(request.user)
    initial = {key: value for key, value in request.GET.items() if key.startswith('extra_') or key in ['service', 'room_type', 'area', 'period']}
    form = OrderForm(request.POST or None, customer=customer, initial=initial)
    if request.method == 'POST' and form.is_valid():
        try:
            orders = create_orders(customer, form.cleaned_data)
        except ValidationError as exc:
            form.add_error(None, exc)
        else:
            messages.success(request, f'Заказ оформлен. Уборок в заказе: {len(orders)}.')
            return redirect('orders:detail', pk=orders[0].pk)
    return render(request, 'orders/create.html', {'title': 'Оформление заказа', 'form': form, 'has_addresses': customer.addresses.exists()})


def estimate(request):
    form = QuoteForm(request.GET)
    if not form.is_valid():
        return JsonResponse({'errors': form.errors.get_json_data()}, status=400)
    calculated = quote(form.cleaned_data)
    return JsonResponse({'price': str(calculated['price']), 'duration_min': calculated['duration_min'], 'discount_percent': calculated['discount_percent'], 'factor': str(calculated['factor']), 'items': [{'name': item.name, 'quantity': str(quantity), 'amount': str(item.price*quantity)} for item, quantity in calculated['items']]})
