from django.urls import path
from . import views

app_name = 'crews'
urlpatterns = [
    path('dispatch/', views.dispatch, name='dispatch'),
    path('dispatch/schedule/', views.schedule, name='schedule'),
    path('crew/', views.crew_day, name='day'),
    path('crew/orders/<int:pk>/print/', views.crew_print, name='print'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('manage/', views.manage, name='manage'),
]
