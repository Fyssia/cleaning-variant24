from django.contrib.auth import views as auth_views
from django.urls import path, reverse_lazy
from . import views

app_name = 'accounts'
urlpatterns = [
    path('login/', auth_views.LoginView.as_view(template_name='accounts/login.html', extra_context={'title': 'Вход'}), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('password_change/', auth_views.PasswordChangeView.as_view(template_name='accounts/password.html', success_url=reverse_lazy('accounts:password_done'), extra_context={'title': 'Смена пароля'}), name='password'),
    path('password_changed/', views.password_done, name='password_done'),
]
