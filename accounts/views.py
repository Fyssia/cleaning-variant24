from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import Group
from django.contrib.auth.views import LoginView as DjangoLoginView
from django.db import transaction
from django.shortcuts import redirect, render
from django.urls import reverse
from django.utils import timezone
from .forms import LoginForm, RegisterForm
from .models import Customer


def workspace_name(user):
    if user.is_superuser or user.groups.filter(name='Администратор').exists():
        return 'crews:dashboard'
    if user.groups.filter(name='Диспетчер').exists():
        return 'crews:dispatch'
    if user.groups.filter(name='Сотрудник бригады').exists():
        return 'crews:day'
    return 'orders:mine'


class LoginView(DjangoLoginView):
    authentication_form = LoginForm
    template_name = 'accounts/login.html'
    extra_context = {'title': 'Вход'}

    def get_success_url(self):
        return self.get_redirect_url() or reverse(workspace_name(self.request.user))


def register(request):
    if request.user.is_authenticated:
        return redirect(workspace_name(request.user))
    form = RegisterForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        with transaction.atomic():
            user = form.save()
            Customer.objects.create(user=user, phone=form.cleaned_data['phone'], pd_consent_at=timezone.now())
            user.groups.add(Group.objects.get_or_create(name='Заказчик')[0])
        login(request, user)
        messages.success(request, 'Аккаунт создан. Добавьте адрес, чтобы оформить уборку.')
        return redirect('orders:addresses')
    return render(request, 'accounts/register.html', {'title': 'Регистрация', 'form': form})


@login_required
def password_done(request):
    messages.success(request, 'Пароль изменён.')
    return redirect(workspace_name(request.user))
