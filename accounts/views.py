from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect


@login_required
def password_done(request):
    messages.success(request, 'Пароль изменён.')
    return redirect('orders:mine')
