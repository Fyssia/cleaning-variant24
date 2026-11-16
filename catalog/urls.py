from django.urls import path
from . import views

app_name = 'catalog'
urlpatterns = [
    path('', views.home, name='home'),
    path('guarantee/', views.information, {'page': 'guarantee'}, name='guarantee'),
    path('contacts/', views.information, {'page': 'contacts'}, name='contacts'),
    path('privacy/', views.information, {'page': 'privacy'}, name='privacy'),
]
