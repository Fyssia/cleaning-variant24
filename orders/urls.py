from django.urls import path
from . import views

app_name = 'orders'
urlpatterns = [
    path('orders/new/', views.create, name='create'),
    path('api/estimate/', views.estimate, name='estimate'),
    path('account/orders/', views.mine, name='mine'),
    path('account/orders/<int:pk>/', views.detail, name='detail'),
    path('account/addresses/', views.addresses, name='addresses'),
    path('account/series/', views.series, name='series'),
]
