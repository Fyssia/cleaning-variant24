from django.urls import path
from . import views

app_name = 'catalog'
urlpatterns = [
    path('', views.home, name='home'),
    path('services/', views.service_list, name='services'),
    path('services/<slug:slug>/', views.service_detail, name='service'),
    path('search/', views.service_list, name='search'),
    path('guarantee/', views.information, {'page': 'guarantee'}, name='guarantee'),
    path('contacts/', views.information, {'page': 'contacts'}, name='contacts'),
    path('privacy/', views.information, {'page': 'privacy'}, name='privacy'),
]
